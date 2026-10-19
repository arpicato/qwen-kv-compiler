"""Controlled 4B comparison preparation/capture; no historical artifact reuse."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gc
import json
import os
from pathlib import Path
import pickle
import random
import subprocess
import sys
import time

from capture_store import CaptureStore
from run_clean_eval import digest, save

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'v2-causal-occupied'


def prepare(repaired):
    train = json.loads((ROOT / 'inputs/joint/questions.json').read_text())['items']
    normalize = lambda q: ' '.join(q.split()).casefold()
    questions = {normalize(r['q']) for r in train}
    validation = {}
    for row in json.loads(repaired.read_text())['rows']:
        if row['split'] != 'val':
            continue
        key = normalize(row['q'])
        if key in questions:
            raise ValueError('train/validation overlap')
        validation[(key, row['answer'])] = dict(q=row['q'], answer=row['answer'], group=key)
    if not validation:
        raise ValueError('empty validation')
    return dict(protocol='controlled4b-v1', budget_rows=2509, train=train,
                validation=list(validation.values()), repaired_sha256=digest(repaired),
                prompt_sha256=digest(ROOT / 'inputs/joint/prompt.txt'))


def positions(n_user, n_answer, cap=10):
    """Absolute suffix query rows; each row predicts the following token."""
    if n_user < 1 or n_answer < 1 or cap < 1:
        raise ValueError('positive user/answer lengths and query cap required')
    count = min(cap, n_answer - 1)
    answer = ([n_user + n_answer - 2] if count == 1 else
              [round(i * (n_answer - 2) / (count - 1)) + n_user for i in range(count)]
              if count else [])
    return sorted({n_user - 1, *answer})


def target_indices(n_user, n_answer, prefix_length):
    return list(range(prefix_length + n_user - 1, prefix_length + n_user + n_answer - 1))


def grouped_mean(values, groups):
    grouped = defaultdict(list)
    for value, group in zip(values, groups, strict=True):
        grouped[group].append(value)
    if not grouped:
        raise ValueError('empty validation scores')
    return sum(sum(v)/len(v) for v in grouped.values()) / len(grouped)


def native_stop(ids, last_prediction, eos, limit):
    # Upstream flex_generate deliberately omits the stopping token from its list.
    if last_prediction in eos:
        return [*ids, last_prediction], 'eos'
    if len(ids) != limit:
        raise ValueError('native generator stopped without EOS or token limit')
    return ids, 'cap'


def progress(start, done, total, **extra):
    elapsed = time.monotonic() - start
    rate = done / max(elapsed, .001)
    print(f'{datetime.now(timezone.utc).isoformat()} elapsed={elapsed:.1f}s '
          f'completed={done}/{total} rate={rate:.3f}/s ETA={(total-done)/max(rate,.001):.1f}s '
          f'{json.dumps(extra)}', flush=True)


def capture(args):
    import numpy as np
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers.cache_utils import DynamicCache
    import transformers.modeling_utils as mu
    import transformers.models.qwen3.modeling_qwen3 as q3
    sys.path.insert(0, str(ROOT / 'src'))
    import prompt as P

    start = time.monotonic()
    data = json.loads(args.data.read_text())
    body = (ROOT / 'inputs/joint/prompt.txt').read_text().rstrip()
    if digest(ROOT / 'inputs/joint/prompt.txt') != data['prompt_sha256']:
        raise ValueError('prompt changed')
    args.out.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    prefix_ids = tok(P.system_block(body), add_special_tokens=False)['input_ids']
    eos = tok.convert_tokens_to_ids('<|im_end|>')
    samples = []
    for split in ('train', 'validation'):
        for i, row in enumerate(data[split]):
            user = tok(P.user_turn(row['q'], think=False), add_special_tokens=False)['input_ids']
            answer = tok(row.get('answer_text', row['answer']) + '<|im_end|>',
                         add_special_tokens=False)['input_ids']
            if answer[-1] != eos or eos in answer[:-1]:
                raise ValueError('answer must terminate in exactly one EOS')
            joined = tok(P.system_block(body) + P.user_turn(row['q'], think=False),
                         add_special_tokens=False)['input_ids']
            if joined != prefix_ids + user:
                raise ValueError('prefix/user token boundary mismatch')
            samples.append(dict(split=split, index=i, q=row['q'], user_ids=user,
                                answer_ids=answer, positions=positions(len(user), len(answer))))
    identity = dict(data_sha256=digest(args.data), model=str(args.model),
                    source_sha256={str(p.relative_to(ROOT)): digest(p) for p in
                        (Path(__file__), ROOT / 'scripts/capture_store.py', ROOT / 'src/prompt.py')},
                    n_sys=len(prefix_ids), torch=torch.__version__, transformers=transformers.__version__,
                    teacher_forward=args.teacher_forward)
    weights = sorted(args.model.glob('*.safetensors'))
    if not weights:
        raise ValueError('missing model weights')
    identity['model_sha256'] = {}
    for p in weights + [args.model / 'config.json', args.model / 'tokenizer.json', args.model / 'tokenizer_config.json']:
        print(f'{datetime.now(timezone.utc).isoformat()} hashing model {p.name}', flush=True)
        identity['model_sha256'][p.name] = digest(p)
    meta_path = args.out / 'meta.json'
    previous = json.loads(meta_path.read_text()) if meta_path.exists() else None
    if previous and previous['identity'] != identity:
        raise ValueError('capture resume identity changed')
    if previous and previous.get('complete'):
        print('Already complete', args.out, flush=True)
        return
    mu.caching_allocator_warmup = lambda *a, **k: None
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
        device_map={'': 0}, attn_implementation='sdpa', local_files_only=True).eval()
    for p in model.parameters():
        p.requires_grad = False
    layers = list(range(model.config.num_hidden_layers))
    store = CaptureStore(args.out, layers, SCHEMA, previous.get('storage') if previous else None)
    pending = {j: [] for j in layers}
    mode, current, seen = 'prefix', None, set()
    original = q3.Qwen3Attention.forward

    def wrapped(module, hidden_states, position_embeddings, attention_mask,
                past_key_values=None, cache_position=None, **kw):
        j = module.layer_idx
        shape = (*hidden_states.shape[:-1], -1, module.head_dim)
        q = module.q_norm(module.q_proj(hidden_states).view(shape)).transpose(1, 2)
        k = module.k_norm(module.k_proj(hidden_states).view(shape)).transpose(1, 2)
        v = module.v_proj(hidden_states).view(shape).transpose(1, 2)
        q, k = q3.apply_rotary_pos_emb(q, k, *position_embeddings)
        cpu = lambda t: t.detach().to(torch.float16).cpu().numpy()
        if mode == 'prefix':
            store.write_prefix(j, dict(k_sys=cpu(k), v_sys=cpu(v)))
            torch.save({'weight': module.o_proj.weight.detach().t().cpu().contiguous()},
                       args.out / f'oproj_L{j}.pt')
        elif current['split'] == 'train':
            if args.teacher_forward == 'full':
                q, k, v = (t[:, :, len(prefix_ids):] for t in (q, k, v))
            idx = current['positions']
            pending[j].append(dict(item=current['index'], kind='agent', schema=SCHEMA,
                q_rot=cpu(q[:, :, idx]), q_logical=np.array(idx, dtype=np.int32) + len(prefix_ids),
                gate=np.ones((1, len(idx), model.config.num_attention_heads * module.head_dim), dtype=np.float16),
                k_live=cpu(k), v_live=cpu(v),
                k_logical=np.arange(k.shape[2], dtype=np.int32) + len(prefix_ids),
                n_user=len(current['user_ids']), q=current['q']))
        seen.add(j)
        return original(module, hidden_states, position_embeddings, attention_mask,
                        past_key_values=past_key_values, cache_position=cache_position, **kw)

    q3.Qwen3Attention.forward = wrapped
    try:
        with torch.no_grad():
            result = model(torch.tensor([prefix_ids], device='cuda'), use_cache=True, logits_to_keep=1)
            prefix = [(layer.keys, layer.values) for layer in result.past_key_values.layers]
            del result
            if seen != set(layers):
                raise ValueError('missing prefix layers')
            mode = 'suffix'
            completed = previous['completed'] if previous else 0
            train_done = min(completed, len(data['train']))
            store.validate(train_done)
            for number, current in enumerate(samples):
                if number < completed:
                    continue
                seen.clear()
                user, answer = current['user_ids'], current['answer_ids']
                ids = user + answer
                offset = len(prefix_ids) if args.teacher_forward == 'full' else 0
                indices = torch.tensor(target_indices(len(user), len(answer), offset), device='cuda')
                result = model(torch.tensor([prefix_ids + ids if offset else ids], device='cuda'),
                               past_key_values=None if offset else DynamicCache(prefix),
                               use_cache=True, logits_to_keep=indices)
                if seen != set(layers):
                    raise ValueError('missing suffix layers')
                if args.check_parity and number == 0 and offset:
                    q3.Qwen3Attention.forward = original
                    plain = model(torch.tensor([prefix_ids + ids], device='cuda'),
                                  use_cache=True, logits_to_keep=indices)
                    if not torch.equal(result.logits, plain.logits):
                        raise ValueError('capture hooks changed full-prefill logits')
                    save(args.out / 'parity.json', dict(hook_logits_exact=True,
                        teacher_forward='full', prefix_reuse=False, passed=True))
                    del plain
                    q3.Qwen3Attention.forward = wrapped
                if args.check_parity and number == 0 and not offset:
                    captured = result.logits.detach().clone()
                    q3.Qwen3Attention.forward = original
                    plain = model(torch.tensor([ids], device='cuda'), past_key_values=DynamicCache(prefix),
                                  use_cache=True, logits_to_keep=indices)
                    if not torch.equal(captured, plain.logits):
                        raise ValueError('capture hooks changed logits')
                    del plain
                    full = model(torch.tensor([prefix_ids + ids], device='cuda'), use_cache=True,
                                 logits_to_keep=indices + len(prefix_ids))
                    difference = (captured.float() - full.logits.float()).abs().max().item()
                    same = torch.equal(captured.argmax(-1), full.logits.argmax(-1))
                    save(args.out / 'parity.json', dict(hook_logits_exact=True,
                        full_vs_reuse_argmax_equal=same, max_abs_difference=difference,
                        reuse_argmax=captured.argmax(-1).cpu().tolist(),
                        full_argmax=full.logits.argmax(-1).cpu().tolist(),
                        threshold=.25, sample_index=0, split=current['split'], passed=same and difference <= .25))
                    if not same or difference > .25:
                        raise ValueError(f'prefix reuse parity failed: max_difference={difference}, argmax_equal={same}')
                    del full, captured
                    q3.Qwen3Attention.forward = wrapped
                logp = result.logits[0].float().log_softmax(-1)
                top_logp, top_ids = logp.topk(20, dim=-1)
                payload = dict(ids=torch.tensor(ids), answer_ids=torch.tensor(answer),
                    target_indices=indices.cpu() - offset, top_ids=top_ids.cpu(), top_logp=top_logp.cpu())
                dest = args.out / f'{current["split"]}_{current["index"]:04d}.pt'
                torch.save(payload, dest.with_suffix('.partial'))
                dest.with_suffix('.partial').replace(dest)
                if current['split'] == 'train':
                    train_done += 1
                store.checkpoint(pending, dict(identity=identity, completed=number+1,
                    meta=dict(schema=SCHEMA, n_sys=len(prefix_ids), layers=layers, n_items=len(data['train'])),
                    train_completed=train_done, complete=False, total=len(samples)))
                del result, logp, top_logp, top_ids, payload
                if any(k.shape[2] != len(prefix_ids) for k, v in prefix):
                    raise ValueError('teacher prefix mutated')
                gc.collect()
                progress(start, number+1, len(samples), split=current['split'], n_sys=len(prefix_ids))
            del prefix, model
            torch.cuda.empty_cache()
            gc.collect()
    finally:
        q3.Qwen3Attention.forward = original
    store.finalize(len(data['train']), lambda j: progress(start, j+1, len(layers), phase='export'))
    final = json.loads(meta_path.read_text())
    final.update(complete=True, elapsed_s=time.monotonic()-start)
    save(meta_path, final)
    print(f'DONE total_duration={final["elapsed_s"]:.3f}s artifact={args.out}', flush=True)


def cartridges(args):
    """Native upstream cache/model, continuous accumulation, dev-only selection."""
    import torch
    import torch.nn.functional as F
    from transformers import AutoTokenizer
    import transformers.modeling_utils as mu
    root = Path(os.environ['CARTRIDGES_DIR'])
    os.environ.setdefault('CARTRIDGES_OUTPUT_DIR', str(args.out.resolve()))
    sys.path.insert(0, str(root))
    from cartridges.models import FlexQwen3ForCausalLM
    from cartridges.cache import AttnConfig, TrainableCache
    from cartridges.initialization import KVFromText
    from cartridges.initialization.tokenization_utils import MODEL_TO_SYSTEM_PROMPT_TOKENIZER
    import cartridges.models.attention as attention
    from cartridges.generation import flex_generate
    sys.path.insert(0, str(ROOT / 'src'))
    import prompt as P

    start = time.monotonic()
    data = json.loads(args.data.read_text())
    meta = json.loads((args.capture / 'meta.json').read_text())
    if not meta['complete'] or meta['identity']['teacher_forward'] != 'full':
        raise ValueError('requires completed full-forward capture')
    if meta['identity']['data_sha256'] != digest(args.data):
        raise ValueError('capture data identity mismatch')
    upstream_commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if upstream_commit != 'ef34ba97a06049c34820506e2c283746284ae5f0':
        raise ValueError('wrong CARTRIDGES revision')
    subprocess.run(['git', '-C', str(root), 'diff', '--quiet', 'HEAD'], check=True)
    expected = dict(data_sha256=digest(args.data), capture_identity=meta['identity'],
        seed=0, lr=.02, epochs=8, accumulation=32, rows=2509, frozen=64,
        initialization='upstream-gradient-text', packing='one-sequence-padded512',
        upstream_commit=upstream_commit,
        validation='question-group-mean-top20-KL', source_sha256=digest(__file__))
    args.out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    mu.caching_allocator_warmup = lambda *a, **k: None
    tok = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    MODEL_TO_SYSTEM_PROMPT_TOKENIZER[str(args.model).lower()] = MODEL_TO_SYSTEM_PROMPT_TOKENIZER['qwen/qwen3-4b']

    def tiled(*a, **kw):
        kw['kernel_options'] = dict(BLOCK_M=32, BLOCK_N=32, num_stages=1, FORCE_USE_FLEX_ATTENTION=True)
        return attention.flex_attention(*a, **kw)

    attention.flex_attention_train = torch.compile(tiled, dynamic=False)
    attention.flex_attention_generate = torch.compile(tiled, dynamic=True)
    model = FlexQwen3ForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
        device_map={'': 0}, local_files_only=True).eval()
    for p in model.parameters():
        p.requires_grad = False
    config = AttnConfig(36, 8, 128)
    cache = KVFromText.Config(max_tokens=2509, num_frozen_tokens=64).instantiate().initialize_kv_cache(
        tokenizer=tok, model=model, attn_config=config).to('cuda')
    if cache.num_cartridge_tokens() != 2509 or cache._num_frozen_tokens != 64:
        raise ValueError('wrong cartridge partition')
    frozen = [p.detach().cpu().clone() for p in [*cache.frozen_keys, *cache.frozen_values]]
    params = {n: p for n, p in cache.named_parameters() if p.requires_grad}
    optimizer = torch.optim.Adam(params.values(), lr=.02, weight_decay=0)
    torch.cuda.reset_peak_memory_stats()
    report = dict(config=expected, history=[], steps=0, best=float('inf'), next_batch=0, complete=False)
    latest = args.out / 'latest.pt'
    if latest.exists():
        state = torch.load(latest, map_location='cpu', weights_only=True)
        if state['report']['config'] != expected:
            raise ValueError('cartridge resume identity changed')
        cache.load_state_dict(state['cache'])
        optimizer.load_state_dict(state['optimizer'])
        report = state['report']
        for n, p in params.items():
            p.grad = state['grads'][n].to('cuda') if state['grads'][n] is not None else None
        torch.set_rng_state(state['cpu_rng'])
        torch.cuda.set_rng_state(state['cuda_rng'])
        del state
    if report['complete']:
        print('Already complete', args.out, flush=True)
        return

    def loss(split, index):
        sample = torch.load(args.capture / f'{split}_{index:04d}.pt', weights_only=True)
        ids = sample['ids'].to('cuda')
        if len(ids) > 512:
            raise ValueError('sequence exceeds fixed512 packing; do not truncate EOS')
        length = len(ids)
        seq = torch.cat([torch.zeros(length, device='cuda', dtype=torch.long),
                         torch.ones(512-length, device='cuda', dtype=torch.long)])
        ids = F.pad(ids, (0, 512-length), value=151643)
        try:
            with torch.amp.autocast(device_type='cuda', dtype=torch.bfloat16):
                output = model(input_ids=ids, seq_ids=seq, position_ids=torch.arange(512, device='cuda'),
                               past_key_values=cache, use_cache=True, mode='train')
                logp = output.logits[0, sample['target_indices'].to('cuda')].float().log_softmax(-1)
                target = sample['top_logp'].to('cuda')
                chosen = logp.gather(-1, sample['top_ids'].to('cuda'))
                ce = (-target.exp() * chosen).mean()
                kl = (target.exp() * (target-chosen)).sum(-1).mean()
            return ce, kl
        finally:
            cache.clear()

    def checkpoint():
        cache.clear()
        state = dict(cache=cache.state_dict(), optimizer=optimizer.state_dict(), report=report,
                     grads={n: p.grad for n, p in params.items()}, cpu_rng=torch.get_rng_state(),
                     cuda_rng=torch.cuda.get_rng_state())
        torch.save(state, args.out / 'latest.partial')
        (args.out / 'latest.partial').replace(latest)
        save(args.out / 'report.json', report)

    def validate(epoch):
        with torch.no_grad():
            values = []
            for i in range(len(data['validation'])):
                ce, kl = loss('validation', i)
                values.append(float(kl))
                if (i+1) % 16 == 0:
                    progress(start, i+1, len(data['validation']), phase='validation', epoch=epoch)
            score = grouped_mean(values, [r['group'] for r in data['validation']])
        report['history'].append(dict(epoch=epoch, validation_top20_kl=score))
        if score < report['best']:
            report['best'], report['best_epoch'] = score, epoch
            torch.save(cache.state_dict(), args.out / 'best.partial')
            (args.out / 'best.partial').replace(args.out / 'best.pt')
        progress(start, report['next_batch'], 8*len(data['train']), validation_kl=score, epoch=epoch)

    if args.command == 'cartridges-gate':
        ce, kl = loss('train', 0)
        ce.backward()
        if not all(p.grad is not None and torch.isfinite(p.grad).all() for p in params.values()):
            raise ValueError('invalid KV gradients')
        if not any(p.grad.abs().max() > 0 for p in params.values()):
            raise ValueError('zero KV gradients')
        if any(p.grad is not None for p in model.parameters()):
            raise ValueError('base model received gradients')
        optimizer.step()
        optimizer.zero_grad()
        after = [p.detach().cpu() for p in [*cache.frozen_keys, *cache.frozen_values]]
        if not all(torch.equal(a, b) for a, b in zip(frozen, after, strict=True)):
            raise ValueError('frozen partition changed')
        query = tok(P.user_turn(data['train'][0]['q'], think=False), add_special_tokens=False)['input_ids']
        ids = torch.tensor(query, device='cuda')
        with torch.no_grad():
            generated = flex_generate(model, tok, input_ids=ids, seq_ids=torch.zeros_like(ids),
                position_ids=torch.arange(len(ids), device='cuda'), cache=cache,
                max_new_tokens=16, stop_token_ids=[151645], temperature=0).get(0, [])
        cache.clear()
        saved = cache.state_dict()
        loaded = TrainableCache(config,
            [torch.cat([cache.frozen_keys[j], cache.trainable_keys[j]], dim=2).detach() for j in range(36)],
            [torch.cat([cache.frozen_values[j], cache.trainable_values[j]], dim=2).detach() for j in range(36)],
            num_frozen_tokens=64).to('cuda')
        loaded.load_state_dict(saved)
        if loaded._num_frozen_tokens != 64 or loaded._num_trainable_tokens != 2445:
            raise ValueError('roundtrip partition changed')
        with torch.no_grad():
            reloaded = flex_generate(model, tok, input_ids=ids, seq_ids=torch.zeros_like(ids),
                position_ids=torch.arange(len(ids), device='cuda'), cache=loaded,
                max_new_tokens=16, stop_token_ids=[151645], temperature=0).get(0, [])
        if reloaded != generated:
            raise ValueError('native cache roundtrip generation changed')
        save(args.out / 'gate.json', dict(complete=True, finite_nonzero_kv_gradients=True,
            base_frozen=True, frozen64_exact=True, local_positions=True, native_tokens=generated,
            native_roundtrip_equal=True,
            ce=float(ce.detach()), kl=float(kl.detach()), config=expected,
            peak_gib=torch.cuda.max_memory_allocated()/2**30, elapsed_s=time.monotonic()-start))
        print('DONE cartridge gate', args.out / 'gate.json', flush=True)
        return
    if not report['history']:
        validate(0)
        checkpoint()
    order = []
    for epoch in range(1, 9):
        indices = list(range(len(data['train'])))
        random.Random(epoch).shuffle(indices)
        order.extend(indices)
    for n in range(report['next_batch'], len(order)):
        ce, kl = loss('train', order[n])
        if not torch.isfinite(ce):
            raise ValueError('nonfinite loss')
        (ce/32).backward()
        if (n+1) % 32 == 0:
            optimizer.step()
            optimizer.zero_grad()
            report['steps'] += 1
        report['next_batch'] = n+1
        del ce, kl
        if (n+1) % len(data['train']) == 0:
            validate((n+1)//len(data['train']))
            checkpoint()
        elif (n+1) % 32 == 0:
            checkpoint()
        if (n+1) % 16 == 0:
            progress(start, n+1, len(order), steps=report['steps'])
    report.update(complete=True, elapsed_s=time.monotonic()-start,
                  peak_gib=torch.cuda.max_memory_allocated()/2**30)
    checkpoint()
    print(f'DONE total_duration={report["elapsed_s"]:.3f}s artifact={args.out}', flush=True)


def am(args):
    """Pinned off-policy upstream AM, uniform budgets, shared captured queries."""
    import math
    import numpy as np
    import torch
    from safetensors.torch import save_file
    root = Path(os.environ['COMPACTION_DIR'])
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != '2020f6d37940fe013e7e7f1ebf409e5d107c5670':
        raise ValueError('wrong AM revision')
    subprocess.run(['git', '-C', str(root), 'diff', '--quiet', 'HEAD'], check=True)
    sys.path.insert(0, str(root))
    from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction
    from am_block_scores import block_scores
    meta = json.loads((args.capture / 'meta.json').read_text())
    if not meta['complete'] or meta['identity']['data_sha256'] != digest(args.data):
        raise ValueError('requires complete matching shared capture')
    start = time.monotonic()
    torch.manual_seed(0)
    args.out.mkdir(parents=True, exist_ok=True)
    recipe = dict(protocol='controlled4b-offpolicy-uniform-AM', upstream_commit=commit,
        capture_identity=meta['identity'], rows=2509, query_policy='all-shared-captured-rows',
        on_policy=False, allocation='uniform', nnls_iters=2, score_method='rms', c2_method='lsq',
        source_sha256=digest(__file__), block_source_sha256=digest(Path(__file__).with_name('am_block_scores.py')))
    algorithm = HighestAttentionKeysCompaction(score_method='rms', nnls_iters=2,
        nnls_lower_bound=math.exp(-3), nnls_upper_bound=math.exp(3), c2_method='lsq')
    with block_scores(rows=256, checkpoint_dir=args.out / 'heads', recipe=recipe):
        for j in range(36):
            with (args.capture / f'layer_{j:03d}.pkl').open('rb') as f:
                shard = pickle.load(f)
            keys = torch.from_numpy(shard['k_sys']).to('cuda', torch.bfloat16)[0]
            values = torch.from_numpy(shard['v_sys']).to('cuda', torch.bfloat16)[0]
            heads = []
            for h in range(8):
                # Preserve all four GQA query heads assigned to this KV head.
                q = np.concatenate([r['q_rot'][0, h*4:(h+1)*4].reshape(-1, 128)
                                    for r in shard['traj']], axis=0)
                queries = torch.from_numpy(q).to('cuda', torch.bfloat16)
                result = algorithm.compute_compacted_cache(keys[h], values[h], queries, 2509)
                heads.append(tuple(t.detach().cpu() for t in result[:3]))
                del queries, q
                progress(start, j*8+h+1, 36*8, phase='AM-head')
                if args.command == 'am-gate':
                    save(args.out / 'gate.json', dict(complete=True, recipe=recipe,
                        head=0, finite=True, shapes=[list(t.shape) for t in result[:3]],
                        elapsed_s=time.monotonic()-start,
                        peak_gib=torch.cuda.max_memory_allocated()/2**30))
                    print('DONE AM feasibility gate', args.out / 'gate.json', flush=True)
                    return
            export = dict(k=torch.stack([h[0] for h in heads])[None],
                          beta=torch.stack([h[1] for h in heads])[None],
                          v=torch.stack([h[2] for h in heads])[None])
            save_file(export, str(args.out / f'layer_{j:03d}.partial'))
            (args.out / f'layer_{j:03d}.partial').replace(args.out / f'layer_{j:03d}.safetensors')
            del shard, keys, values, heads, export
            gc.collect()
            torch.cuda.empty_cache()
    manifest = dict(complete=True, rows=2509, layers=36, padded_rows=2509,
                    recipe=recipe, elapsed_s=time.monotonic()-start)
    save(args.out / 'manifest.json', manifest)
    print(f'DONE total_duration={manifest["elapsed_s"]:.3f}s artifact={args.out}', flush=True)


def evaluate(args):
    """Current frozen suites and shared graders, with method-native generation."""
    import torch
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import transformers.modeling_utils as mu
    from clean_eval import knowledge, tool, code_check
    from task_eval27b import schemas, continuation
    sys.path.insert(0, str(ROOT / 'src'))
    import prompt as P

    start = time.monotonic()
    cases = args.cases or ROOT / 'inputs/publication_eval/cases.json'
    data = json.loads(cases.read_text())
    body = (ROOT / 'inputs/joint/prompt.txt').read_text().rstrip()
    tok = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    prefix = tok(P.system_block(body), add_special_tokens=False)['input_ids']
    if len(prefix) != 25390:
        raise ValueError('wrong 4B prefix')
    mu.caching_allocator_warmup = lambda *a, **k: None
    torch.manual_seed(0)
    arm = args.arm
    files = [cases, ROOT / 'inputs/joint/prompt.txt', Path(__file__),
             ROOT / 'scripts/clean_eval.py', ROOT / 'scripts/task_eval27b.py', ROOT / 'src/prompt.py']
    captured = json.loads((args.capture / 'meta.json').read_text()) if args.capture else None
    if captured is None:
        raise ValueError('evaluation needs --capture for model provenance')
    for name, expected in captured['identity']['model_sha256'].items():
        if digest(args.model / name) != expected:
            raise ValueError(f'model changed: {name}')
    runtime = {}
    for variable, expected in (('COMPACTION_DIR', '2020f6d37940fe013e7e7f1ebf409e5d107c5670'),
                               ('CARTRIDGES_DIR', 'ef34ba97a06049c34820506e2c283746284ae5f0')):
        root = Path(os.environ[variable])
        revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        if revision != expected:
            raise ValueError(f'wrong runtime: {variable}')
        subprocess.run(['git', '-C', str(root), 'diff', '--quiet', 'HEAD'], check=True)
        runtime[variable] = revision
    if arm == 'cartridges':
        root = Path(os.environ['CARTRIDGES_DIR'])
        os.environ.setdefault('CARTRIDGES_OUTPUT_DIR', str(args.out.parent.resolve()))
        sys.path.insert(0, str(root))
        from cartridges.models import FlexQwen3ForCausalLM
        from cartridges.cache import TrainableCache, AttnConfig
        from cartridges.generation import flex_generate
        import cartridges.models.attention as attention
        def tiled(*a, **kw):
            kw['kernel_options'] = dict(BLOCK_M=32, BLOCK_N=32, num_stages=1, FORCE_USE_FLEX_ATTENTION=True)
            return attention.flex_attention(*a, **kw)
        attention.flex_attention_generate = torch.compile(tiled, dynamic=True)
        model = FlexQwen3ForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
            device_map={'': 0}, local_files_only=True).eval()
        path = args.artifact / 'best.pt'
        files += [path, args.artifact / 'report.json']
        state = torch.load(path, map_location='cpu', weights_only=True)
        keys = [torch.cat([state[f'frozen_keys.{j}'], state[f'trainable_keys.{j}']], dim=2) for j in range(36)]
        values = [torch.cat([state[f'frozen_values.{j}'], state[f'trainable_values.{j}']], dim=2) for j in range(36)]
        cache = TrainableCache(AttnConfig(36, 8, 128), keys, values, num_frozen_tokens=64).to('cuda')
        if cache.num_cartridge_tokens() != 2509:
            raise ValueError('wrong cartridge budget')
        del state, keys, values
    elif arm in ('compiler', 'am'):
        sys.path.insert(0, os.environ['COMPACTION_DIR'])
        from models.qwen3 import Qwen3ForCausalLM
        from models.cache import CompactedPrefixCache
        model = Qwen3ForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
            device_map={'': 0}, attn_implementation='sdpa', local_files_only=True).eval()
        manifest = json.loads((args.artifact / 'manifest.json').read_text())
        if not manifest['complete']:
            raise ValueError('incomplete artifact')
        compacted = []
        for j in range(36):
            path = args.artifact / f'layer_{j:03d}.safetensors'
            files.append(path)
            s = load_file(str(path), device='cuda')
            k, v = s['k'].to(torch.bfloat16), s['v'].to(torch.bfloat16)
            beta = s.get('beta', torch.zeros(k.shape[:3], device='cuda', dtype=torch.bfloat16))
            if k.shape != (1, 8, 2509, 128) or not all(torch.isfinite(t).all() for t in (k, v, beta)):
                raise ValueError('wrong budget or invalid installed cache')
            compacted.append((k, beta, v))
        compacted = tuple(compacted)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16,
            device_map={'': 0}, attn_implementation='sdpa', local_files_only=True).eval()
    for p in model.parameters():
        p.requires_grad = False
    eos = model.generation_config.eos_token_id
    eos = set(eos if isinstance(eos, list) else [eos]) | {tok.eos_token_id, 151645}
    eos.discard(None)
    schema = schemas(body)
    identity = dict(arm=arm, files={str(p): digest(p) for p in files}, model=str(args.model),
        limits=data['limits'], greedy=True, seed=0, full_forward=True, image=args.image,
        smoke=args.smoke, model_sha256=captured['identity']['model_sha256'], upstream=runtime,
        torch=torch.__version__)
    result = dict(config=identity, complete=False, rows={s: [] for s in ('knowledge', 'tools', 'behavior')}, elapsed_s=0)
    if args.out.exists():
        result = json.loads(args.out.read_text())
        if result['config'] != identity:
            raise ValueError('evaluation resume identity mismatch')
        if args.smoke and result.get('complete') and result.get('smoke'):
            print('Already complete inference smoke', args.out, flush=True)
            return
    for suite, rows in result['rows'].items():
        if [r['id'] for r in rows] != [c['id'] for c in data[suite][:len(rows)]]:
            raise ValueError('evaluation resume case IDs mismatch')
        if result['complete'] and len(rows) != len(data[suite]):
            raise ValueError('completed evaluation missing cases')
    if result['complete']:
        print('Already complete', args.out, flush=True)
        return

    @torch.no_grad()
    def generate(history, limit):
        suffix = tok(history, add_special_tokens=False)['input_ids']
        if arm == 'cartridges':
            ids = torch.tensor(suffix, device='cuda')
            cache.clear()
            last = []
            hook = model.register_forward_hook(lambda module, inputs, output:
                last.append(int(output.logits[0, -1].argmax())))
            try:
                generated = flex_generate(model, tok, input_ids=ids, seq_ids=torch.zeros_like(ids),
                    position_ids=torch.arange(len(ids), device='cuda'), cache=cache,
                    max_new_tokens=limit, stop_token_ids=sorted(eos), temperature=0).get(0, [])
            finally:
                hook.remove()
                cache.clear()
            generated = [int(t) for t in generated]
            generated, stop = native_stop(generated, last[-1], eos, limit)
        else:
            installed = CompactedPrefixCache(compacted, original_seq_len=len(prefix)) if arm in ('compiler', 'am') else None
            ids = prefix + suffix if arm == 'full' else suffix
            output = model(torch.tensor([ids], device='cuda'), past_key_values=installed,
                           use_cache=True, logits_to_keep=1)
            past = output.past_key_values
            generated = []
            for i in range(limit):
                token = int(output.logits[0, -1].argmax())
                generated.append(token)
                if token in eos or i == limit-1:
                    break
                output = model(torch.tensor([[token]], device='cuda'), past_key_values=past,
                               use_cache=True, logits_to_keep=1)
                past = output.past_key_values
        return dict(pred=tok.decode(generated, skip_special_tokens=True).strip(),
            stop='eos' if generated and generated[-1] in eos else 'cap',
            tokens=len(generated), token_ids=generated)

    if args.smoke:
        question = json.loads((ROOT / 'inputs/controlled4b/cases.json').read_text())['train'][0]['q']
        g = generate(P.user_turn(question, think=False), 16)
        save(args.out, dict(complete=True, config=identity, smoke=True, question=question,
                           generated=g, elapsed_s=time.monotonic()-start))
        print('DONE inference smoke', args.out, flush=True)
        return

    initial = sum(map(len, result['rows'].values()))
    done = initial
    prior = result['elapsed_s']
    for suite in ('knowledge', 'tools', 'behavior'):
        for c in data[suite][len(result['rows'][suite]):]:
            history = P.user_turn(c['q'] + (data['transport'] if suite == 'tools' else ''), think=False)
            row = dict(id=c['id'], category=c.get('category', c.get('kind')))
            if suite == 'tools':
                trace = []
                for expected in c['steps']:
                    g = generate(history, data['limits'][suite])
                    g.update(tool(g['pred'], expected, schema, g['stop']))
                    trace.append(g)
                    if not g['correct']:
                        break
                    if expected.get('reply') is not None:
                        history = continuation(history, g['pred'], expected)
                row.update(trace=trace, correct=len(trace)==len(c['steps']) and all(t['correct'] for t in trace))
            else:
                row.update(generate(history, data['limits'][suite]))
                if suite == 'knowledge':
                    row.update(knowledge(row['pred'], c['answers'], row['stop']))
                else:
                    row['code_check'] = code_check(c, row['pred'], row['stop'], args.image)
            result['rows'][suite].append(row)
            done += 1
            result['elapsed_s'] = prior + time.monotonic()-start
            save(args.out, result)
            progress(start, done-initial, sum(len(data[s]) for s in ('knowledge', 'tools', 'behavior'))-initial, arm=arm, suite=suite, case=c['id'])
    result.update(complete=True, peak_gib=torch.cuda.max_memory_allocated()/2**30)
    save(args.out, result)
    print(f'DONE total_duration={result["elapsed_s"]:.3f}s artifact={args.out}', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('prepare', 'capture', 'cartridges-gate', 'cartridges', 'am', 'am-gate', 'evaluate'))
    p.add_argument('--repaired', type=Path)
    p.add_argument('--data', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--model', type=Path, default=Path('/mnt/data/models/Qwen3-4B'))
    p.add_argument('--check-parity', action='store_true')
    p.add_argument('--teacher-forward', choices=('full', 'reuse'), default='full')
    p.add_argument('--capture', type=Path)
    p.add_argument('--cases', type=Path)
    p.add_argument('--arm', choices=('full', 'none', 'compiler', 'am', 'cartridges'))
    p.add_argument('--artifact', type=Path)
    p.add_argument('--image', default='kvcompile-checks:repro')
    p.add_argument('--smoke', action='store_true', help='non-test inference wiring check only')
    a = p.parse_args()
    if a.command == 'prepare':
        if not a.repaired:
            p.error('prepare needs --repaired')
        save(a.out, prepare(a.repaired))
    elif a.command == 'evaluate':
        if not a.arm or a.arm in ('compiler', 'am', 'cartridges') and not a.artifact:
            p.error('evaluate needs --arm and compressed arms need --artifact')
        evaluate(a)
    else:
        if not a.data:
            p.error('capture needs --data')
        if a.command == 'capture':
            capture(a)
        else:
            if not a.capture:
                p.error('cartridges needs --capture')
            am(a) if a.command in ('am', 'am-gate') else cartridges(a)
