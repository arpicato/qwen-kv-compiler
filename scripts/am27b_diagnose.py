"""Replay one failed AM head without changing the solver or retained precision."""
import json
import argparse
import math
import os
from pathlib import Path
import pickle
import subprocess
import sys
import time

import numpy as np
import torch
from safetensors.torch import load_file
from am27b import save
from run_clean_eval import digest


def solution_stats(x):
    return dict(solution_shape=list(x.shape),dtype=str(x.dtype),
        fp32_finite=bool(torch.isfinite(x).all()),fp16_finite=bool(torch.isfinite(x.half()).all()),
        max_abs=float(x.abs().max()),nonfinite_fp16=int((~torch.isfinite(x.half())).sum()))


def main():
    start=time.monotonic()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--slots',type=int,choices=(2048,4096,6144,8192),default=8192)
    p.add_argument('--layer',type=int,choices=range(3,64,4),default=23)
    p.add_argument('--head',type=int,choices=range(4),default=3)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    out=a.original
    destination=a.out or out/'failure_diagnostic.json'
    if destination.exists():
        p.error('refusing to overwrite diagnostic')
    index=list(range(3,64,4)).index(a.layer)*4+a.head
    if index==0:
        p.error('replay requires preceding head RNG checkpoint')
    folder=out/f'am{a.slots}'
    manifest=json.loads((folder/'manifest.json').read_text())
    recipe=manifest['recipe']
    capture=a.reference/f'traj/layer_{a.layer:03d}.pkl'
    if manifest['complete'] or manifest['slots']!=a.slots or recipe['torch']!=torch.__version__:
        raise ValueError('expected incomplete fit with identical budget/runtime')
    if digest(capture)!=recipe['captures'][str(a.layer)]:
        raise ValueError('capture differs from failed fit')
    if recipe.get('values_dtype')=='float32' or any(recipe[k]!=v for k,v in
            dict(score_method='rms',nnls_iters=2,beta_bounds=[-3,3],c2_method='lsq',on_policy=False).items()):
        raise ValueError('unexpected failed-fit recipe')
    checkpoint=folder/f'heads/head_{index-1:03d}.safetensors'
    if (folder/f'heads/head_{index:03d}.safetensors').exists():
        raise ValueError('requested head already completed')
    if json.loads((folder/'heads/recipe.json').read_text())!=recipe:
        raise ValueError('checkpoint recipe differs')
    upstream=subprocess.check_output(['git','-C',os.environ['COMPACTION_DIR'],'rev-parse','HEAD'],text=True).strip()
    if upstream!=recipe['upstream_commit']:
        raise ValueError('upstream differs from failed fit')
    subprocess.run(['git','-C',os.environ['COMPACTION_DIR'],'diff','--quiet','HEAD'],check=True)
    if digest(Path(__file__).with_name('am_block_scores.py'))!=recipe['block_source_sha256']:
        raise ValueError('solver wrapper differs from failed fit')
    sys.path.insert(0,os.environ['COMPACTION_DIR'])
    from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction
    from am_block_scores import block_scores
    state=load_file(str(checkpoint))
    torch.set_rng_state(state['cpu_rng'])
    torch.cuda.set_rng_state(state['cuda_rng'])
    with capture.open('rb') as f:
        shard=pickle.load(f)
    queries=torch.from_numpy(np.concatenate([r['q_rot'][0,a.head*6:(a.head+1)*6].reshape(-1,256) for r in shard['traj']])).cuda()
    original=torch.linalg.lstsq
    calls=[]
    def lstsq(*args,**kw):
        result=original(*args,**kw)
        x=result.solution
        row=dict(matrix_shape=list(args[0].shape),**solution_stats(x))
        calls.append(row)
        print(json.dumps(row),flush=True)
        return result
    torch.linalg.lstsq=lstsq
    try:
        algorithm=HighestAttentionKeysCompaction(score_method='rms',nnls_iters=2,
            nnls_lower_bound=math.exp(-3),nnls_upper_bound=math.exp(3),c2_method='lsq')
        with block_scores(rows=128):
            result=algorithm.compute_compacted_cache(torch.from_numpy(shard['k_sys'][0,a.head]).cuda(),
                torch.from_numpy(shard['v_sys'][0,a.head]).cuda(),queries,a.slots)
        record=dict(complete=True,layer=a.layer,kv_head=a.head,slots=a.slots,lstsq=calls,
            files={str(p.resolve()):digest(p) for p in (capture,checkpoint,folder/'manifest.json',
                Path(__file__),Path(__file__).with_name('am_block_scores.py'))},upstream_commit=upstream,
            output_finite={n:bool(torch.isfinite(t).all()) for n,t in zip(('k','beta','v'),result[:3])},
            elapsed_s=time.monotonic()-start,torch=torch.__version__)
        save(destination,record)
        print(f'DONE total_duration={record["elapsed_s"]:.3f}s artifact={destination}',flush=True)
    finally:
        torch.linalg.lstsq=original


if __name__=='__main__':
    main()
