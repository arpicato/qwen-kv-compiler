"""ExLlamaV3 (ROCm) runtime adapter for the KV-compiler research.

CUDA/ROCm counterpart of the MLX path in ``capture.py`` / ``model.py``. Loads
the EXL3-quantized 27B on the 7900 XTX, runs cached prefill/decode, and
extracts / injects the teacher prefix state in the schema the rest of the
pipeline consumes:

* full-attention layers ``[3,7,...,63]`` -> paged fp16 K/V, sliced to the
  *occupied* token count (never the page capacity).
* GatedDeltaNet layers -> per-layer conv_state + recurrent_state.

Two quantities are kept distinct (conflating them was the exact bug the MLX v2
capture fixed):

* **physical cache length** -- slots filled in the paged cache (``past_len`` /
  ``cache_seqlens``). For a compiled prefix this equals K.
* **logical position** -- RoPE / recurrence position, i.e. real tokens preceding
  the current one. For a compiled prefix this stays n_sys.

ExLlama contract (from ``examples/generation_loop.py``):

    params = {"attn_mode": "flash_attn", "cache": cache, "past_len": P,
              "batch_shape": (1, CAP)}
    model.prefill(input_ids, params)          # advances cache + recurrent state
    rs = params.get("recurrent_states")       # MUST be echoed on every later call
    logits = model.forward(input_ids[:, -1:], {..., "past_len": NEW, "recurrent_states": rs})

If ``recurrent_states`` is omitted from a later call the linear-attention
state is re-allocated and cleared, so it must always be threaded through.
"""

from __future__ import annotations

import hashlib
import os
import sys
from typing import Optional

import torch

_EXL3_PATH = os.environ.get("EXLLAMAV3_PATH", os.path.expanduser("~/exllamav3-rocm"))


def _ensure_exl3_on_path():
    if _EXL3_PATH not in sys.path:
        sys.path.insert(0, _EXL3_PATH)


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def full_attn_layers(model) -> list[int]:
    return [a.layer_idx for a in model.get_cache_layers()]


def recurrent_layers(model) -> list[int]:
    return [a.layer_idx for a in model.get_recurrent_layers()]


def attn_modules(model) -> dict[int, object]:
    """Map ``layer_idx -> Attention module`` for the full-attention layers.

    ``model.modules`` holds TransformerBlocks; the attention module is
    ``block.attn`` and its ``layer_idx`` is what the state extraction uses.
    """
    out = {}
    for b in model.modules:
        a = getattr(b, "attn", None)
        if a is not None and hasattr(a, "decode_flash_attn"):
            out[a.layer_idx] = a
    return out


def load(model_dir: str, max_seq_len: int = 32768, cache_size: Optional[int] = None,
         max_batch_size: int = 1, vision: bool = False):
    """Load model + tokenizer + a cache. Returns (model, cache, tok, cfg)."""
    _ensure_exl3_on_path()
    from exllamav3 import Config, Model, Cache, Tokenizer

    cfg = Config.from_directory(model_dir)
    cfg.vision = vision
    cfg.max_seq_len = max_seq_len
    cfg.cache_size = cache_size if cache_size is not None else max_seq_len
    model = Model.from_config(cfg)
    cache = Cache(model, max_num_tokens=cfg.cache_size, max_batch_size=max_batch_size)
    tok = Tokenizer(cfg)
    model.load(progressbar=False)
    return model, cache, tok, cfg


def make_cache(model, max_num_tokens: int, max_batch_size: int = 1, max_history: int = 0):
    _ensure_exl3_on_path()
    from exllamav3 import Cache
    return Cache(model, max_num_tokens=max_num_tokens, max_batch_size=max_batch_size,
                 max_history=max_history)


def encode(tok, text: str) -> list[int]:
    """Tokenize a single string, honouring special tokens (``<|im_start|>`` etc.)."""
    ids = tok.encode(text, encode_special_tokens=True)
    if hasattr(ids, "tolist"):
        ids = ids[0].tolist() if ids.dim() == 2 else ids.tolist()
    return list(ids)


def batch_params(cache, cap: int, past_len: int, recurrent_states=None):
    p = {"attn_mode": "flash_attn", "cache": cache, "past_len": past_len,
         "batch_shape": (1, cap)}
    if recurrent_states is not None:
        p["recurrent_states"] = recurrent_states
    return p


def batch_params_split(cache, cap: int, physical_len: int, logical_pos: int,
                       seqlen: int, recurrent_states=None, block_table=None):
    """Params with the *physical* KV length decoupled from the *logical* position.

    For a compiled prefix the paged cache holds K synthetic slots
    (``physical_len`` = K) but the conversation continues at the original prompt
    length (``logical_pos`` = n_sys). ExLlama's rectangular ``past_len`` path
    forces the two equal, so use the *paged* branch instead: an explicit
    ``block_table`` + ``cache_seqlens`` (physical) with ``positions`` (logical
    RoPE). Omitting ``batch_shape`` also takes ``prepare_for_recurrence`` down
    the ``cache_seqlens`` branch, which does not assert the recurrent position,
    so ``r.position`` is set to the logical position here.

    ``positions``/``position_ids`` must be per-token ``(1, seqlen)`` -- a scalar
    RoPE position is applied to only the first row and silently corrupts the
    rest (observed: no-prefix prefill emitted ``system`` instead of ``Node``).
    """
    # position_ids is (bsz, seq_len) per-token RoPE position; positions (1-D, one
    # per batch item) and position_ids are mutually exclusive in the rope kernel.
    pos = torch.arange(logical_pos, logical_pos + seqlen, dtype=torch.int32).unsqueeze(0).contiguous()
    p = {"attn_mode": "flash_attn", "cache": cache,
         "block_table": block_table if block_table is not None
         else _block_table(1, (cap + 255) // 256),
         "cache_seqlens": torch.tensor([physical_len], dtype=torch.int32),
         "position_ids": pos}
    if recurrent_states is not None:
        for r in recurrent_states:
            r.position = logical_pos
        p["recurrent_states"] = recurrent_states
    return p


_BLOCK_TABLES = {}


def _block_table(bsz: int, pages: int):
    key = (bsz, pages)
    t = _BLOCK_TABLES.get(key)
    if t is None:
        t = torch.arange(bsz * pages, dtype=torch.int32).view(bsz, pages)
        _BLOCK_TABLES[key] = t
    return t


def prefill_tokens(model, cache, ids, *, cap: int, chunk: int = 2048,
                   past_len: int = 0, recurrent_states=None):
    """Prefill ``ids`` in chunks of ``chunk``.

    Returns ``(past_len_after, recurrent_states, last_logits)``. All but the
    final token are consumed by prefill; the caller decodes the last token or
    continues with it, matching the reference loop.
    """
    ids_t = torch.tensor([ids], dtype=torch.long, device="cuda:0")
    n = ids_t.shape[-1]
    p = past_len
    rs = recurrent_states
    # ExLlama keeps the final token for the decode step; prefill the prefix.
    body = ids_t[:, :-1] if n > 1 else ids_t
    step = 0
    while step < body.shape[-1]:
        piece = body[:, step:step + chunk]
        params = batch_params(cache, cap, p, rs)
        model.prefill(input_ids=piece, params=params)
        rs = params.get("recurrent_states", rs)
        p += piece.shape[-1]
        step += chunk
        torch.cuda.synchronize()
    last = ids_t[:, -1:]
    params = batch_params(cache, cap, p, rs)
    logits = model.forward(input_ids=last, params=params)
    rs = params.get("recurrent_states", rs)
    p += 1
    return p, rs, logits, params


def prefill_tokens_split(model, cache, ids, *, cap: int, physical_len: int,
                         logical_pos: int, chunk: int = 2048, recurrent_states=None):
    """Prefill with physical KV length decoupled from logical position.

    Returns ``(physical_len_after, logical_pos_after, rs, last_logits, params)``.
    Used for the compiled arm: the synthetic prefix occupies ``physical_len``
    slots while RoPE/recurrence continue at ``logical_pos``.
    """
    # When physical == logical (teacher/none) the rectangular past_len path is
    # exact and well-tested; only the compiled arm (K != n_sys) needs the split
    # position_ids path. Delegate otherwise to avoid rope-kernel edge cases.
    if physical_len == logical_pos:
        p, rs, logits, params = prefill_tokens(
            model, cache, ids, cap=cap, chunk=chunk, past_len=logical_pos,
            recurrent_states=recurrent_states)
        return p, p, rs, logits, params

    ids_t = torch.tensor([ids], dtype=torch.long, device="cuda:0")
    n = ids_t.shape[-1]
    pl, lp = physical_len, logical_pos
    rs = recurrent_states
    body = ids_t[:, :-1] if n > 1 else ids_t
    step = 0
    while step < body.shape[-1]:
        piece = body[:, step:step + chunk]
        params = batch_params_split(cache, cap, pl, lp, piece.shape[-1], rs)
        model.prefill(input_ids=piece, params=params)
        rs = params.get("recurrent_states", rs)
        pl += piece.shape[-1]
        lp += piece.shape[-1]
        step += chunk
        torch.cuda.synchronize()
    last = ids_t[:, -1:]
    params = batch_params_split(cache, cap, pl, lp, 1, rs)
    logits = model.forward(input_ids=last, params=params)
    rs = params.get("recurrent_states", rs)
    pl += 1
    lp += 1
    return pl, lp, rs, logits, params


# ---------------------------------------------------------------------------
# State extraction / injection
# ---------------------------------------------------------------------------

def _attn_layer(cache, layer_idx):
    return cache.layers[(layer_idx, 0)]


def extract_teacher_state(model, cache, occupied: int):
    """Slice the *occupied* prefix out of the paged cache.

    Returns ``(delta, attn)``:

    * ``delta[str(L)]`` -> {"conv_state", "recurrent_state"}  (per GDN layer)
    * ``attn[str(L)]``  -> {"keys", "values", "offset"}       (fp16, len == occupied)

    ``keys``/``values`` are reshaped from paged ``(pages, PAGE_SIZE, Hkv, D)``
    to contiguous ``(1, Hkv, occupied, D)`` so downstream code sees the same
    layout the MLX path produced.
    """
    from exllamav3.constants import PAGE_SIZE

    delta, attn = {}, {}
    for L in recurrent_layers(model):
        st = cache.recurrent_layers[(L, 0)]
        delta[str(L)] = {
            "conv_state": st.conv_state[0].detach().float().cpu().clone(),
            "recurrent_state": st.recurrent_state[0].detach().float().cpu().clone(),
        }

    for L in full_attn_layers(model):
        lay = _attn_layer(cache, L)
        pages = (occupied + PAGE_SIZE - 1) // PAGE_SIZE
        H, D = lay.k.shape[2], lay.k.shape[3]
        k = lay.k[:pages].reshape(pages * PAGE_SIZE, H, D)[:occupied]
        v = lay.v[:pages].reshape(pages * PAGE_SIZE, H, D)[:occupied]
        attn[str(L)] = {"keys": k.transpose(0, 1).unsqueeze(0).detach().cpu().contiguous(),
                        "values": v.transpose(0, 1).unsqueeze(0).detach().cpu().contiguous(),
                        "offset": int(occupied)}
    return delta, attn


@torch.inference_mode()
def write_prefix_state(model, cache, delta, attn, n_sys: int):
    """Install teacher state into the cache as a resident prefix without any
    forward pass. K/V occupy physical positions ``[0, n_sys)``; recurrent
    states are copied in directly.
    """
    from exllamav3.constants import PAGE_SIZE

    pages = (n_sys + PAGE_SIZE - 1) // PAGE_SIZE
    for L in full_attn_layers(model):
        lay = _attn_layer(cache, L)
        k = attn[str(L)]["keys"].to("cuda:0")   # (1, Hkv, n_sys, D)
        v = attn[str(L)]["values"].to("cuda:0")
        H, D = k.shape[1], k.shape[3]
        kk = k[0].transpose(0, 1).reshape(n_sys, H, D)   # (n_sys, H, D)
        vv = v[0].transpose(0, 1).reshape(n_sys, H, D)
        pad = pages * PAGE_SIZE - n_sys
        if pad:
            kk = torch.nn.functional.pad(kk, (0, 0, 0, 0, 0, pad))
            vv = torch.nn.functional.pad(vv, (0, 0, 0, 0, 0, pad))
        lay.k[:pages].copy_(kk.reshape(pages, PAGE_SIZE, H, D).to(lay.k.dtype))
        lay.v[:pages].copy_(vv.reshape(pages, PAGE_SIZE, H, D).to(lay.v.dtype))

    for L in recurrent_layers(model):
        st = cache.recurrent_layers[(L, 0)]
        st.conv_state[0].copy_(delta[str(L)]["conv_state"].to(st.conv_state.dtype))
        st.recurrent_state[0].copy_(delta[str(L)]["recurrent_state"].to(st.recurrent_state.dtype))


@torch.inference_mode()
def clear_cache(model, cache):
    """Zero every physical KV slot, clear recurrent state, and return every
    recurrent-state slot to the free pool.

    Cache tensors are created under ``torch.inference_mode`` by the loader, so
    all in-place mutation must run inside inference mode. Returning slots to the
    pool is required: ``params`` without ``recurrent_states`` calls
    ``cache.get_new_state()``, which asserts whenever the pool is empty.
    """
    for L in full_attn_layers(model):
        lay = _attn_layer(cache, L)
        lay.k.zero_()
        lay.v.zero_()
    for L in recurrent_layers(model):
        st = cache.recurrent_layers[(L, 0)]
        st.conv_state.zero_()
        st.recurrent_state.zero_()
    cache.reset_states()
