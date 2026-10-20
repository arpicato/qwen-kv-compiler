"""Padded research prefix with per-KV-head lengths; no native runtime edits."""
from contextlib import contextmanager
import json
from pathlib import Path
import torch


def validate_lengths(lengths, heads, slots):
    if type(slots) is not int or slots<1 or heads<1 or len(lengths) != heads or any(type(n) is not int or not 1 <= n <= slots for n in lengths):
        raise ValueError('invalid per-head lengths')
    return torch.tensor(lengths, dtype=torch.long)


def prefix_mask(lengths, slots, device):
    counts = validate_lengths(lengths, len(lengths), slots).to(device)
    return torch.arange(slots, device=device)[None] >= counts[:, None]


@contextmanager
def compiler_lengths(lengths):
    """Retain the existing joint loss/optimizer; only initialization/mask differ."""
    import compile_torch_v2 as compiler
    base, initialize = compiler.BatchedCausalTorchLoss, compiler.init_from_teacher

    class Loss(base):
        def _chunk_tensors(self, lo, hi):
            c = super()._chunk_tensors(lo, hi)
            masked = prefix_mask(lengths, self.n_syn, self.dev)
            if len(lengths) != self.Hkv:
                raise ValueError('wrong number of fitted heads')
            # Original query/live causality remains; expand the shared head axis.
            c['add'] = c['add'].expand(-1, self.Hq, -1, -1).clone()
            masked = masked.repeat_interleave(self.Hq // self.Hkv, 0)
            c['add'][:, :, :, :self.n_syn].masked_fill_(masked[None, :, None], float('-inf'))
            return c

    def init(k, v, slots, seed, freeze_sink=False):
        validate_lengths(lengths, k.shape[1], slots)
        keys, values = torch.zeros_like(k[:, :, :slots]), torch.zeros_like(v[:, :, :slots])
        for h, count in enumerate(lengths):
            kh, vh = initialize(k[:, h:h+1], v[:, h:h+1], count, seed, freeze_sink)
            keys[:, h:h+1, :count], values[:, h:h+1, :count] = kh, vh
        return keys, values

    compiler.BatchedCausalTorchLoss, compiler.init_from_teacher = Loss, init
    try:
        yield
    finally:
        compiler.BatchedCausalTorchLoss, compiler.init_from_teacher = base, initialize


def load_prefix(folder, device='cpu', with_values=False):
    from safetensors.torch import load_file
    from run_clean_eval import digest
    folder = Path(folder)
    m = json.loads((folder/'manifest.json').read_text())
    if not m['complete'] or m['layout'] != 'padded-head-lengths-v1':
        raise ValueError('incomplete/non-ragged manifest')
    precision=m['identity'].get('values_dtype','float16')
    if precision not in ('float16','float32') or (precision=='float32' and not with_values):
        raise ValueError('FP32 prefix requires explicit sidecar loading')
    row_bytes=256*(2+(4 if precision=='float32' else 2))
    count=sum(sum(validate_lengths(v,4,m['slots']).tolist()) for v in m['lengths'].values())
    expected=count*(row_bytes+(2 if m['identity'].get('method')=='am' else 0))
    if m['payload_bytes']!=expected or m['padded_tensor_bytes']!=16*4*m['slots']*(row_bytes+2):
        raise ValueError('export byte accounting mismatch')
    if m.get('native_value_placeholder_bytes',0)!=(16*4*m['slots']*256*2 if precision=='float32' else 0):
        raise ValueError('native placeholder byte accounting mismatch')
    layers = list(range(3, 64, 4))
    expected = {f'layer_{l:03d}.safetensors' for l in layers}
    if set(m['files']) != expected or set(m['lengths']) != set(map(str, layers)):
        raise ValueError('incomplete head-length export inventory')
    compiled, biases, values = {}, {}, {}
    for l in layers:
        path = folder/f'layer_{l:03d}.safetensors'
        if digest(path) != m['files'][path.name]:
            raise ValueError('changed head-length export')
        d = load_file(str(path))
        slots, lengths = m['slots'], m['lengths'][str(l)]
        validate_lengths(lengths, 4, slots)
        if set(d) != {'k', 'v', 'beta'} or d['k'].shape != (1, 4, slots, 256) or d['v'].shape != d['k'].shape or d['beta'].shape != (1, 4, slots):
            raise ValueError('invalid padded shapes')
        if d['k'].dtype != torch.float16 or d['v'].dtype != (torch.float32 if precision=='float32' else torch.float16) or d['beta'].dtype != torch.float16 or not all(torch.isfinite(t).all() for t in d.values()):
            raise ValueError('invalid padded dtype/values')
        mask = prefix_mask(lengths, slots, 'cpu')
        if any(d[n][0][mask].any() for n in ('k', 'v')) or d['beta'][0][mask].any():
            raise ValueError('nonzero padding in exported cache')
        compiled[l] = dict(k=d['k'], v=torch.zeros_like(d['k']) if precision=='float32' else d['v'])
        if precision=='float32':
            values[l]=d['v'].transpose(1,2).contiguous().to(device)
        biases[l] = d['beta'][0].to(device).masked_fill(mask.to(device), float('-inf'))
    return (compiled,biases,values) if with_values else (compiled,biases)


def write_layer(folder, layer, k, v, beta, lengths, slots, values_fp32=False):
    """Canonical explicit-precision export, never an automatic overflow fallback."""
    from safetensors.torch import save_file
    folder = Path(folder)
    validate_lengths(lengths, 4, slots)
    if k.shape != (1,4,slots,256) or v.shape != k.shape or beta.shape != (1,4,slots):
        raise ValueError('invalid export shapes')
    tensors = {n:t.detach().cpu().to(torch.float32 if n=='v' and values_fp32 else torch.float16).contiguous().clone() for n,t in (('k',k),('v',v),('beta',beta))}
    if not all(torch.isfinite(t).all() for t in tensors.values()):
        raise ValueError('nonfinite/overflowed FP16 export')
    mask = prefix_mask(lengths, slots, 'cpu')
    for t in tensors.values():
        t[0][mask] = 0
    folder.mkdir(parents=True, exist_ok=True)
    path = folder/f'layer_{layer:03d}.safetensors'
    save_file(tensors, str(path)+'.partial')
    Path(str(path)+'.partial').replace(path)


def finish_export(folder, lengths, slots, identity):
    from run_clean_eval import digest, save
    folder = Path(folder)
    if set(lengths) != set(map(str, range(3,64,4))):
        raise ValueError('incomplete export lengths')
    for counts in lengths.values():
        validate_lengths(counts,4,slots)
    files = {f'layer_{l:03d}.safetensors':digest(folder/f'layer_{l:03d}.safetensors') for l in range(3,64,4)}
    bias_bytes=2 if identity.get('method')=='am' else 0
    row_bytes=256*(2+(4 if identity.get('values_dtype')=='float32' else 2))
    save(folder/'manifest.json',dict(complete=True,layout='padded-head-lengths-v1',slots=slots,
        lengths=lengths,identity=identity,files=files,
        payload_bytes=sum(sum(v) for v in lengths.values())*(row_bytes+bias_bytes),
        padded_tensor_bytes=16*4*slots*(row_bytes+2),
        native_value_placeholder_bytes=16*4*slots*256*2 if identity.get('values_dtype')=='float32' else 0))
    load_prefix(folder,with_values=True)
