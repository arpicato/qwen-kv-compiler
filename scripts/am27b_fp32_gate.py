"""Train-only failed-head FP32 preservation and EXL3 sidecar generation gate."""
import argparse
import json
import math
import os
from pathlib import Path
import pickle
import sys
import time

import torch
from safetensors.torch import load_file, save_file
from am27b import digest, save, progress

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def solver(a):
    import numpy as np
    import subprocess
    sys.path.insert(0, os.environ['COMPACTION_DIR'])
    from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction
    from am_block_scores import block_scores
    start = time.monotonic()
    a.out.mkdir(parents=True, exist_ok=True)
    upstream = os.environ['COMPACTION_DIR']
    assert subprocess.check_output(['git','-C',upstream,'rev-parse','HEAD'], text=True).strip() == '2020f6d37940fe013e7e7f1ebf409e5d107c5670'
    subprocess.run(['git','-C',upstream,'diff','--quiet','HEAD'], check=True)
    state_path = a.original/'am8192/heads/head_022.safetensors'
    source = a.reference/'traj/layer_023.pkl'
    diagnostic = json.loads((a.original/'failure_diagnostic.json').read_text())
    state = load_file(str(state_path))
    torch.set_rng_state(state['cpu_rng'])
    torch.cuda.set_rng_state(state['cuda_rng'])
    with source.open('rb') as f:
        shard = pickle.load(f)
    q = torch.from_numpy(np.concatenate([r['q_rot'][0,18:24].reshape(-1,256) for r in shard['traj']])).cuda()
    algorithm = HighestAttentionKeysCompaction(score_method='rms',nnls_iters=2,
        nnls_lower_bound=math.exp(-3),nnls_upper_bound=math.exp(3),c2_method='lsq')
    original_lstsq = torch.linalg.lstsq
    solutions = []
    def lstsq(*args, **kw):
        result = original_lstsq(*args, **kw)
        solutions.append(result.solution.detach().cpu())
        return result
    torch.linalg.lstsq = lstsq
    try:
        with block_scores(rows=128, values_dtype=torch.float32):
            result = algorithm.compute_compacted_cache(torch.from_numpy(shard['k_sys'][0,3]).cuda(),
                torch.from_numpy(shard['v_sys'][0,3]).cuda(),q,8192)
    finally:
        torch.linalg.lstsq = original_lstsq
    tensors = {n:t.cpu().contiguous() for n,t in zip(('k','beta','v'),result[:3])}
    assert tensors['v'].dtype == torch.float32 and all(torch.isfinite(t).all() for t in tensors.values())
    maximum = float(tensors['v'].abs().max())
    save(a.out/'replay.json', dict(max_abs=maximum, expected=diagnostic['lstsq'][-1]['max_abs'],
        fp16_nonfinite=int((~torch.isfinite(tensors['v'].half())).sum()), torch=torch.__version__,
        block_module=sys.modules[block_scores.__module__].__file__, elapsed_s=time.monotonic()-start))
    print(f'replay max_abs={maximum} expected={diagnostic["lstsq"][-1]["max_abs"]}',flush=True)
    assert torch.equal(tensors['v'], solutions[-1]), 'FP32 retention changed LSQ solution'
    assert not torch.isfinite(tensors['v'].half()).all(), 'original overflow not reproduced'
    save_file(tensors, str(a.out/'head.safetensors'))
    loaded = load_file(str(a.out/'head.safetensors'))
    assert all(torch.equal(t, loaded[n]) for n,t in tensors.items())
    record = dict(complete=True, max_abs=maximum, previous_max_abs=diagnostic['lstsq'][-1]['max_abs'],
        same_run_lsq_exact=True, fp16_nonfinite=int((~torch.isfinite(tensors['v'].half())).sum()),
        head_sha256=digest(a.out/'head.safetensors'), rng_sha256=digest(state_path), capture_sha256=digest(source),
        source_sha256=digest(__file__), block_sha256=digest(Path(__file__).with_name('am_block_scores.py')),
        torch=torch.__version__, elapsed_s=time.monotonic()-start)
    save(a.out/'solver.json', record)
    print(f'DONE total_duration={record["elapsed_s"]:.3f}s artifact={a.out}/solver.json', flush=True)


def native(a):
    import exl3
    import prompt as P
    from eval_agent_exl3 import gen_greedy, install_prefix
    from reproduce import check_runtime
    from am27b_attention import prefix_bias
    start = time.monotonic()
    check_runtime(a.model)
    solver_record = json.loads((a.out/'solver.json').read_text())
    assert solver_record['complete'] and solver_record['head_sha256'] == digest(a.out/'head.safetensors')
    head = load_file(str(a.out/'head.safetensors'))
    model,cache,tok,_ = exl3.load(str(a.model), max_seq_len=32768, cache_size=32768)
    layers = exl3.full_attn_layers(model)
    teacher = load_file(str(a.reference/'teacher/state.safetensors'))
    delta = {str(l):{n:teacher[f'delta.{l}.{n}'] for n in ('conv_state','recurrent_state')} for l in exl3.recurrent_layers(model)}
    compiled = {l:dict(k=teacher[f'attn.{l}.keys'][:,:,:8192].clone(),v=teacher[f'attn.{l}.values'][:,:,:8192].clone()) for l in layers}
    biases = {l:torch.zeros(4,8192) for l in layers}
    q = json.loads((ROOT/'inputs/joint/questions.json').read_text())['items'][0]['q']
    ids = exl3.encode(tok,P.user_turn(q,think=False))
    def run(values):
        logical,physical = install_prefix(model,cache,'compiled',n_sys=26341,delta=delta,attn=None,compiled=compiled,K=8192)
        for l in exl3.recurrent_layers(model):
            st = cache.recurrent_layers[l,0]
            assert all(torch.equal(getattr(st,n)[0].cpu(),delta[str(l)][n]) for n in ('conv_state','recurrent_state'))
        with prefix_bias(biases, values):
            r = gen_greedy(model,cache,tok,ids,cap=32768,logical_pos=logical,physical_len=physical,max_tokens=16)
        assert torch.isfinite(r[3]).all()
        return r
    # Promotion control uses the same representable prefix, not a quality comparison.
    normal = run({})
    sidecar = compiled[23]['v'].transpose(1,2).float().contiguous()
    promoted = run({23:sidecar})
    diff = float((normal[3].float()-promoted[3].float()).abs().max())
    record = dict(complete=False, promotion_ids_equal=normal[0]==promoted[0], max_logit_diff=diff,
        solver_sha256=digest(a.out/'solver.json'), wrapper_sha256=digest(Path(__file__).with_name('am27b_attention.py')))
    save(a.out/'gate.json',record)
    assert record['promotion_ids_equal'] and diff <= .25, 'FP32 promotion control failed'
    progress(start,1,3,'promotion control passed')
    compiled[23]['k'][0,3] = head['k']
    biases[23][3] = head['beta']
    # Deliberately never put fitted V into the native FP16 cache: sidecar overrides it.
    sidecar[0,:,3] = head['v']
    first = run({23:sidecar})
    reloaded = load_file(str(a.out/'head.safetensors'))
    reconstructed = compiled[23]['v'].transpose(1,2).float().contiguous()
    reconstructed[0,:,3] = reloaded['v']
    assert torch.equal(sidecar,reconstructed)
    second = run({23:reconstructed})
    exact = first[0]==second[0] and torch.equal(first[3],second[3])
    assert exact, 'FP32 sidecar roundtrip changed generation'
    record.update(complete=True, nonzero_roundtrip_exact=True, recurrent_injection_exact=True,
        ids=second[0], stop=second[2], fp32_max_abs=float(sidecar.abs().max()),
        elapsed_s=time.monotonic()-start, peak_gib=torch.cuda.max_memory_allocated()/2**30)
    save(a.out/'gate.json',record)
    progress(start,3,3,'FP32 failed-head generation gate passed')
    print(f'DONE total_duration={record["elapsed_s"]:.3f}s artifact={a.out}/gate.json',flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=('solver','native'))
    for name in ('original','reference','model','out'):
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    (solver if a.phase=='solver' else native)(a)
