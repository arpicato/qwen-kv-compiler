"""Fixed off-policy AM baseline and train-only EXL3 compatibility gate."""
import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.partial')
    tmp.write_text(json.dumps(data, indent=2)+'\n')
    tmp.replace(path)


def progress(start, done, total, phase):
    elapsed = time.monotonic()-start
    rate = done/max(elapsed,.001)
    print(f'{datetime.now(timezone.utc).isoformat()} elapsed={elapsed:.1f}s '
          f'completed={done}/{total} rate={rate:.3f}/s ETA={(total-done)/max(rate,.001):.1f}s phase={phase}', flush=True)


def gate(a):
    import numpy as np
    import torch
    from safetensors.torch import load_file, save_file

    start = time.monotonic()
    a.out.mkdir(parents=True, exist_ok=True)
    if not a.solver_only:
        from reproduce import check_runtime
        check_runtime(a.model)
    meta = json.loads((a.reference/'traj/meta.json').read_text())
    questions = json.loads((ROOT/'inputs/joint/questions.json').read_text())['items']
    if not meta['meta']['complete'] or meta['meta']['n_items'] != 812 or meta['meta']['n_sys'] != 26341:
        raise ValueError('wrong capture')
    if [(r['q'],r['answer']) for r in meta['index']] != [(r['q'],r['answer']) for r in questions]:
        raise ValueError('capture Q/A mismatch')
    source = a.reference/'traj/layer_003.pkl'
    identity = dict(capture_meta_sha256=digest(a.reference/'traj/meta.json'),
        first_layer_sha256=digest(source),teacher_sha256=digest(a.reference/'teacher/state.safetensors'),
        questions_sha256=digest(ROOT/'inputs/joint/questions.json'),
        prompt_sha256=digest(ROOT/'inputs/joint/prompt.txt'), source_sha256=digest(__file__),
        wrapper_sha256=digest(Path(__file__).with_name('am27b_attention.py')))
    root = Path(os.environ['COMPACTION_DIR'])
    commit = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    if commit != '2020f6d37940fe013e7e7f1ebf409e5d107c5670':
        raise ValueError('wrong AM upstream')
    subprocess.run(['git','-C',str(root),'diff','--quiet','HEAD'],check=True)
    sys.path.insert(0,str(root))
    from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction
    from am_block_scores import block_scores
    with source.open('rb') as f:
        shard = pickle.load(f)
    teacher = load_file(str(a.reference/'teacher/state.safetensors'))
    for name,key in (('keys','k_sys'),('values','v_sys')):
        if not torch.equal(teacher[f'attn.3.{name}'],torch.from_numpy(shard[key])):
            raise ValueError('teacher/capture KV mismatch')
    recipe = dict(protocol='am27b-offpolicy-uniform-gate',identity=identity,rows=4096,upstream=commit)
    if a.load_head:
        info=json.loads((a.out/'solver.json').read_text())
        if info['recipe'] != recipe or info['head_sha256'] != digest(a.out/'head.safetensors'):
            raise ValueError('solver handoff identity mismatch')
        head=load_file(str(a.out/'head.safetensors'))
        solver_s=info['elapsed_s']
    else:
        q = np.concatenate([r['q_rot'][0,:6].reshape(-1,256) for r in shard['traj']])
        torch.manual_seed(0)
        algorithm = HighestAttentionKeysCompaction(score_method='rms',nnls_iters=2,
            nnls_lower_bound=math.exp(-3),nnls_upper_bound=math.exp(3),c2_method='lsq')
        with block_scores(rows=128,checkpoint_dir=a.out/'head',recipe=recipe):
            fitted = algorithm.compute_compacted_cache(torch.from_numpy(shard['k_sys'][0,0]).cuda(),
                torch.from_numpy(shard['v_sys'][0,0]).cuda(),torch.from_numpy(q).cuda(),4096)
        head = {name:t.cpu().contiguous() for name,t in zip(('k','beta','v'),fitted[:3])}
        save_file(head,str(a.out/'head.safetensors'))
        solver_s=time.monotonic()-start
        save(a.out/'solver.json',dict(complete=True,recipe=recipe,elapsed_s=solver_s,
            torch=torch.__version__,head_sha256=digest(a.out/'head.safetensors')))
        del fitted,q
    if not all(torch.isfinite(t).all() for t in head.values()) or not head['beta'].abs().max()>0:
        raise ValueError('invalid real AM head')
    if a.solver_only:
        print(f'DONE total_duration={solver_s:.3f}s artifact={a.out}/solver.json',flush=True)
        return
    import exl3
    import prompt as P
    from am27b_attention import prefix_bias
    from eval_agent_exl3 import gen_greedy, install_prefix
    del shard
    gc.collect()
    torch.cuda.empty_cache()
    progress(start,1,4,'solver gate complete; loading EXL3')
    model,cache,tok,cfg = exl3.load(str(a.model),max_seq_len=32768,cache_size=32768)
    layers = exl3.full_attn_layers(model)
    delta = {str(l):{n:teacher[f'delta.{l}.{n}'] for n in ('conv_state','recurrent_state')}
             for l in exl3.recurrent_layers(model)}
    attn = {str(l):dict(keys=teacher[f'attn.{l}.keys'],values=teacher[f'attn.{l}.values'],offset=26341) for l in layers}
    body = (ROOT/'inputs/joint/prompt.txt').read_text().rstrip()
    if len(exl3.encode(tok,P.system_block(body))) != 26341:
        raise ValueError('prefix identity mismatch')
    ids = exl3.encode(tok,P.user_turn(questions[0]['q'],think=False))
    zero = {l:torch.zeros(4,26341) for l in layers}
    # Force eager native dispatch for a fair zero-bias comparison, restored at exit.
    import exllamav3.modules.attn as module
    bc = module._bc_attn_enable
    module._bc_attn_enable = False
    def run(arm,compiled=None,K=None):
        logical,physical=install_prefix(model,cache,arm,n_sys=26341,delta=delta,attn=attn,compiled=compiled,K=K)
        for l in exl3.recurrent_layers(model):
            st=cache.recurrent_layers[l,0]
            if not all(torch.equal(getattr(st,n)[0].cpu(),delta[str(l)][n]) for n in ('conv_state','recurrent_state')):
                raise ValueError('recurrent injection changed')
        return gen_greedy(model,cache,tok,ids,cap=32768,logical_pos=logical,physical_len=physical,max_tokens=16)
    try:
        native=run('teacher')
        with prefix_bias(zero):
            wrapped=run('teacher')
        diff=float((native[3].float()-wrapped[3].float()).abs().max())
        parity=native[0]==wrapped[0] and native[2]==wrapped[2] and math.isfinite(diff) and diff<=.25
        result=dict(complete=False,identity=identity,solver_s=solver_s,queries=len(questions),
            native_ids=native[0],wrapped_ids=wrapped[0],max_logit_diff=diff,zero_beta_parity=parity,
            elapsed_s=time.monotonic()-start)
        save(a.out/'gate.json',result)
        if not parity:
            raise ValueError('zero-beta native parity gate failed')
        progress(start,2,4,'zero beta parity passed')
        compact={l:dict(k=attn[str(l)]['keys'][:,:,:4096].clone(),v=attn[str(l)]['values'][:,:,:4096].clone()) for l in layers}
        compact[3]['k'][0,0]=head['k']
        compact[3]['v'][0,0]=head['v']
        biases={l:torch.zeros(4,4096) for l in layers}
        biases[3][0]=head['beta']
        with prefix_bias(biases):
            first=run('compiled',compact,4096)
        loaded=load_file(str(a.out/'head.safetensors'))
        for name in ('k','v'):
            compact[3][name][0,0]=loaded[name]
        biases[3][0]=loaded['beta']
        with prefix_bias(biases):
            second=run('compiled',compact,4096)
        exact=first[0]==second[0] and torch.equal(first[3],second[3])
        if not exact or not torch.isfinite(second[3]).all():
            raise ValueError('nonzero beta roundtrip failed')
        result.update(complete=True,nonzero_roundtrip_exact=exact,recurrent_injection_exact=True,
            nonzero_ids=second[0],elapsed_s=time.monotonic()-start,peak_gib=torch.cuda.max_memory_allocated()/2**30)
        save(a.out/'gate.json',result)
        progress(start,4,4,'all compatibility gates passed')
        print(f'DONE total_duration={result["elapsed_s"]:.3f}s artifact={a.out}/gate.json',flush=True)
    finally:
        module._bc_attn_enable=bc


def fit(a):
    import numpy as np
    import torch
    from safetensors.torch import load_file, save_file
    started=time.monotonic()
    accepted=json.loads(a.gate.read_text())
    if not accepted['complete'] or not accepted['zero_beta_parity'] or not accepted['nonzero_roundtrip_exact']:
        raise ValueError('compatibility gate not accepted')
    if a.values_fp32:
        precision = json.loads(a.precision_gate.read_text())
        if not precision['complete'] or not precision['promotion_ids_equal'] or not precision['nonzero_roundtrip_exact'] or precision['max_logit_diff'] > .25:
            raise ValueError('FP32 precision gate not accepted')
        if precision['wrapper_sha256'] != digest(Path(__file__).with_name('am27b_attention.py')):
            raise ValueError('FP32 wrapper differs from accepted gate')
    for name,key in (('traj/meta.json','capture_meta_sha256'),('teacher/state.safetensors','teacher_sha256')):
        if digest(a.reference/name)!=accepted['identity'][key]:
            raise ValueError('gate input changed')
    meta=json.loads((a.reference/'traj/meta.json').read_text())
    layers=meta['meta']['layers']
    root=Path(os.environ['COMPACTION_DIR'])
    commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    if commit!='2020f6d37940fe013e7e7f1ebf409e5d107c5670':
        raise ValueError('wrong AM revision')
    subprocess.run(['git','-C',str(root),'diff','--quiet','HEAD'],check=True)
    sys.path.insert(0,str(root))
    from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction
    from am_block_scores import block_scores
    teacher=load_file(str(a.reference/'teacher/state.safetensors'))
    torch.manual_seed(0)
    recipe=dict(protocol='am27b-offpolicy-uniform-v1',slots=a.slots,gate_sha256=digest(a.gate),
        upstream_commit=commit,torch=torch.__version__,source_sha256=digest(__file__),
        block_source_sha256=digest(Path(__file__).with_name('am_block_scores.py')),
        captures={str(l):digest(a.reference/f'traj/layer_{l:03d}.pkl') for l in layers},
        score_method='rms',nnls_iters=2,beta_bounds=[-3,3],c2_method='lsq',on_policy=False)
    if a.values_fp32:
        recipe.update(values_dtype='float32',precision_gate=str(a.precision_gate.resolve()),
            precision_gate_sha256=digest(a.precision_gate))
    a.out.mkdir(parents=True,exist_ok=True)
    algorithm=HighestAttentionKeysCompaction(score_method='rms',nnls_iters=2,
        nnls_lower_bound=math.exp(-3),nnls_upper_bound=math.exp(3),c2_method='lsq')
    manifest=dict(complete=False,slots=a.slots,layers=[],recipe=recipe,elapsed_s=0)
    with block_scores(rows=128,checkpoint_dir=a.out/'heads',recipe=recipe,
                      values_dtype=torch.float32 if a.values_fp32 else None):
        for j,l in enumerate(layers):
            with (a.reference/f'traj/layer_{l:03d}.pkl').open('rb') as f:
                shard=pickle.load(f)
            if len(shard['traj'])!=812:
                raise ValueError('wrong shared query count')
            for name,key in (('keys','k_sys'),('values','v_sys')):
                if not torch.equal(teacher[f'attn.{l}.{name}'],torch.from_numpy(shard[key])):
                    raise ValueError('teacher/capture KV mismatch')
            heads=[]
            for h in range(4):
                q=np.concatenate([r['q_rot'][0,h*6:(h+1)*6].reshape(-1,256) for r in shard['traj']])
                fitted=algorithm.compute_compacted_cache(torch.from_numpy(shard['k_sys'][0,h]).cuda(),
                    torch.from_numpy(shard['v_sys'][0,h]).cuda(),torch.from_numpy(q).cuda(),a.slots)
                heads.append(tuple(t.cpu() for t in fitted[:3]))
                del q,fitted
                progress(started,j*4+h+1,64,'AM fit')
            tensors={name:torch.stack([r[n] for r in heads])[None].contiguous()
                     for n,name in enumerate(('k','beta','v'))}
            tmp=a.out/f'layer_{l:03d}.partial'
            save_file(tensors,str(tmp))
            tmp.replace(a.out/f'layer_{l:03d}.safetensors')
            manifest['layers'].append(l)
            manifest['elapsed_s']=time.monotonic()-started
            save(a.out/'manifest.json',manifest)
            del shard,heads,tensors
            gc.collect()
            torch.cuda.empty_cache()
    manifest.update(complete=True,elapsed_s=time.monotonic()-started,
        files={p.name:digest(p) for p in sorted(a.out.glob('layer_*.safetensors'))})
    save(a.out/'manifest.json',manifest)
    print(f'DONE total_duration={manifest["elapsed_s"]:.3f}s artifact={a.out}',flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('gate','fit'))
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--solver-only',action='store_true')
    p.add_argument('--load-head',action='store_true')
    p.add_argument('--gate',type=Path)
    p.add_argument('--slots',type=int,choices=(4096,8192))
    p.add_argument('--values-fp32',action='store_true')
    p.add_argument('--precision-gate',type=Path)
    a=p.parse_args()
    if a.command=='fit':
        if not a.gate or not a.slots:
            p.error('fit requires --gate --slots')
        if a.values_fp32 and (not a.precision_gate or a.slots != 8192):
            p.error('FP32 fit requires --precision-gate and --slots 8192')
        fit(a)
    else:
        gate(a)
