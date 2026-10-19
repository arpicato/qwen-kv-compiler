"""Replay failed 8k head without changing solver; report FP32 vs FP16 finiteness."""
import json
import argparse
import math
import os
from pathlib import Path
import pickle
import sys
import time

import numpy as np
import torch
from safetensors.torch import load_file
from am27b import save


def main():
    start=time.monotonic()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    a=p.parse_args()
    out=a.original
    sys.path.insert(0,os.environ['COMPACTION_DIR'])
    from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction
    from am_block_scores import block_scores
    state=load_file(str(out/'am8192/heads/head_022.safetensors'))
    torch.set_rng_state(state['cpu_rng'])
    torch.cuda.set_rng_state(state['cuda_rng'])
    with (a.reference/'traj/layer_023.pkl').open('rb') as f:
        shard=pickle.load(f)
    queries=torch.from_numpy(np.concatenate([r['q_rot'][0,18:24].reshape(-1,256) for r in shard['traj']])).cuda()
    original=torch.linalg.lstsq
    calls=[]
    def lstsq(*args,**kw):
        result=original(*args,**kw)
        x=result.solution
        row=dict(matrix_shape=list(args[0].shape),solution_shape=list(x.shape),dtype=str(x.dtype),
            fp32_finite=bool(torch.isfinite(x).all()),fp16_finite=bool(torch.isfinite(x.half()).all()),
            max_abs=float(x.abs().max()),nonfinite_fp16=int((~torch.isfinite(x.half())).sum()))
        calls.append(row)
        print(json.dumps(row),flush=True)
        return result
    torch.linalg.lstsq=lstsq
    try:
        algorithm=HighestAttentionKeysCompaction(score_method='rms',nnls_iters=2,
            nnls_lower_bound=math.exp(-3),nnls_upper_bound=math.exp(3),c2_method='lsq')
        with block_scores(rows=128):
            result=algorithm.compute_compacted_cache(torch.from_numpy(shard['k_sys'][0,3]).cuda(),
                torch.from_numpy(shard['v_sys'][0,3]).cuda(),queries,8192)
        record=dict(complete=True,layer=23,kv_head=3,slots=8192,lstsq=calls,
            output_finite={n:bool(torch.isfinite(t).all()) for n,t in zip(('k','beta','v'),result[:3])},
            elapsed_s=time.monotonic()-start,torch=torch.__version__)
        save(out/'failure_diagnostic.json',record)
        print(f'DONE total_duration={record["elapsed_s"]:.3f}s artifact={out}/failure_diagnostic.json',flush=True)
    finally:
        torch.linalg.lstsq=original


if __name__=='__main__':
    main()
