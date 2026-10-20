"""Fixed-grid 27B allocation experiment. GPU commands require --allow-gpu.

Prepare/allocate/export/freeze only hash/read CPU artifacts. Other commands are
explicit execution steps, never an automatic launcher. See the protocol report.
"""
import argparse
import json
from pathlib import Path
import pickle
import sys
import time

from am27b import progress
from head_allocation import allocate
from run_clean_eval import digest, save

ROOT = Path(__file__).resolve().parents[1]
LAYERS = list(range(3,64,4))
GRID = (2048,4096,6144)


def byte_budget(cap):
    row_bytes=256*(2+4)+2  # FP16 K, FP32 V, FP16 beta, per head-row.
    mean=cap//(64*row_bytes)
    step=mean//2+1
    return dict(cap_bytes=cap,am_mean_rows=mean,am_total_rows=64*mean,
        am_grid=[mean-step,mean,mean+step],am_payload_bytes=64*mean*row_bytes,
        unused_bytes=cap-64*mean*row_bytes)


def method_grid(d,method):
    return d.get('am_grid',list(GRID)) if method=='am' else list(GRID)


def method_total(d,method):
    return d.get('am_total_rows',64*4096) if method=='am' else d.get('total_rows',64*4096)


def identity(root):
    d = json.loads((root/'protocol.json').read_text())
    for p,h in d['files'].items():
        if digest(p) != h:
            raise ValueError(f'protocol input changed: {p}')
    return d


def checkpoint(path, config):
    if path.exists():
        d = json.loads(path.read_text())
        if d['identity'] != config or not set(d['layers'])<=set(map(str,LAYERS)):
            raise ValueError(f'resume identity mismatch: {path}')
        return d
    return dict(complete=False, identity=config, layers={})


def prepare(a):
    import numpy as np
    from compile_torch_v2 import sample_indices
    reference = a.reference.resolve()
    run = json.loads((reference/'run.json').read_text())
    if not run['complete'] or len(run['phases']) != 19:
        raise ValueError('reference reproduction incomplete')
    sampling = json.loads((ROOT/'inputs/joint/sampling.json').read_text())
    indices = sample_indices(np.random.default_rng(1729),812,72,sampling)
    files = [ROOT/'inputs/joint/sampling.json',ROOT/'inputs/joint/questions.json',ROOT/'inputs/joint/prompt.txt',
             ROOT/'inputs/publication_final/cases.json', ROOT/'runtime.json',
             ROOT/'results/NONUNIFORM_ALLOCATION_PLAN.md',reference/'run.json',
             reference/'traj/meta.json',reference/'teacher/state.safetensors',reference/'teacher/state.json']
    files += list((ROOT/'scripts').glob('*.py')) + list((ROOT/'src').glob('*.py'))
    files += [reference/f'traj/layer_{l:03d}.pkl' for l in LAYERS]
    files += [reference/f'oproj/oproj_L{l}.pt' for l in LAYERS]
    files += [reference/'compiled4096/manifest.json']
    files += [reference/f'compiled4096/layer_{l:03d}.safetensors' for l in LAYERS]
    if a.am_values_fp32:
        if a.original is None:
            raise ValueError('FP32 extension requires --original failed FP16 root')
        original=a.original.resolve()
        files += [original/'am6144_failure_diagnostic.json',original/'am6144/manifest.json',
                  original/'am6144/heads/head_016.safetensors']
    # Verify reference phase identities, not only their complete flag.
    for phase in run['phases'].values():
        for name,h in phase['outputs'].items():
            if digest(name) != h:
                raise ValueError(f'reproduction output changed: {name}')
    config = dict(version='nonuniform27b-fp32v-v1' if a.am_values_fp32 else 'nonuniform27b-v1',
        am_values_dtype='float32' if a.am_values_fp32 else 'float16',reference=str(reference),grid=list(GRID),
        mean_rows=4096,total_rows=64*4096,indices=indices,selection='training proxy, not validation',
        files={str(p.resolve()):digest(p) for p in sorted(files)})
    if a.am_values_fp32:
        config['failed_fp16_root']=str(original)
    if a.equal_memory_from:
        if not a.am_values_fp32:
            raise ValueError('equal-memory extension requires FP32 AM values')
        previous=a.equal_memory_from.resolve()
        prior=identity(previous)
        if prior.get('am_values_dtype')!='float32' or prior['reference']!=str(reference):
            raise ValueError('wrong compiler reuse study')
        from nonuniform_cache import load_prefix
        reuse=[previous/'protocol.json',previous/'compiler-allocation.json',previous/'compiler-curves.json',
               previous/'compiler_allocated/fit.json']
        for variant in ('uniform','allocated'):
            folder=previous/f'compiler_{variant}'
            load_prefix(folder)
            manifest=json.loads((folder/'manifest.json').read_text())
            if manifest['identity']['protocol']!=digest(previous/'protocol.json') or manifest['identity']['method']!='compiler' or manifest['identity']['variant']!=variant:
                raise ValueError('compiler reuse identity differs')
            if manifest['payload_bytes']!=256*2**20:
                raise ValueError('compiler reuse payload differs from byte cap')
            reuse += [folder/'manifest.json',*[folder/f'layer_{l:03d}.safetensors' for l in LAYERS]]
        config.update(version='nonuniform27b-equal-payload-v1',compiler_reuse=str(previous),
            **byte_budget(256*2**20))
        config['files'].update({str(p):digest(p) for p in reuse})
        config['files'].update(grid_files(prior,previous,'compiler'))
        config['files'][str(ROOT/'results/EQUAL_MEMORY_PLAN.md')]=digest(ROOT/'results/EQUAL_MEMORY_PLAN.md')
    path=a.out/'protocol.json'
    if not path.exists() and a.out.exists() and any(a.out.iterdir()):
        raise ValueError('new protocol requires empty output directory')
    if path.exists() and json.loads(path.read_text()) != config:
        raise ValueError('existing protocol differs')
    save(path,config)


def grid_folder(d, root, method, rows):
    if method == 'compiler' and rows == 4096:
        return Path(d['reference'])/'compiled4096'
    if method=='compiler' and d.get('compiler_reuse'):
        root=Path(d['compiler_reuse'])
    return root/f'{method}{rows}'


def grid_files(d, root, method):
    files = {}
    for rows in method_grid(d,method):
        folder = grid_folder(d,root,method,rows)
        m = json.loads((folder/'manifest.json').read_text())
        if not m['complete'] or m['slots'] != rows:
            raise ValueError('incomplete/wrong grid fit')
        if method=='compiler':
            if [x['layer'] for x in m['layers']] != LAYERS or m['steps']!=400:
                raise ValueError('wrong compiler grid layers/steps')
            expected=dict(lr=.001,cosine_weight=1.,seed=0,gate_weight=True,
                freeze_sink=True,examples_per_update=72,batch_chunk=4,batched=True,
                kv_dtype='torch.bfloat16',clean_traj=None,init_from_dir=None,
                sampling_plan=json.loads((ROOT/'inputs/joint/sampling.json').read_text()))
            if any(m.get(k)!=v for k,v in expected.items()) or Path(m['traj']).resolve()!=Path(d['reference'])/'traj' or Path(m['oproj_dir']).resolve()!=Path(d['reference'])/'oproj':
                raise ValueError('compiler grid recipe/input mismatch')
        elif m['layers'] != LAYERS or m['recipe']['slots'] != rows:
            raise ValueError('wrong AM grid layers/budget')
        else:
            r=m['recipe']
            if r.get('values_dtype','float16')!=d.get('am_values_dtype','float16') or r['score_method']!='rms' or r['nnls_iters']!=2 or r['c2_method']!='lsq' or r['on_policy'] or r['beta_bounds']!=[-3,3] or r['upstream_commit']!='2020f6d37940fe013e7e7f1ebf409e5d107c5670':
                raise ValueError('AM grid recipe mismatch')
            if d.get('am_values_dtype')=='float32' and r['precision_gate_sha256']!=digest(root/'fp32-gate/gate.json'):
                raise ValueError('AM grid precision gate mismatch')
            if set(m['files'])!={f'layer_{l:03d}.safetensors' for l in LAYERS}:
                raise ValueError('incomplete AM grid inventory')
            for l in LAYERS:
                if r['captures'][str(l)]!=d['files'][str(Path(d['reference'])/f'traj/layer_{l:03d}.pkl')]:
                    raise ValueError('AM grid capture identity mismatch')
            for name,h in m['files'].items():
                if Path(name).name!=name or digest(folder/name)!=h:
                    raise ValueError('AM grid file changed')
        for p in [folder/'manifest.json',*[folder/f'layer_{l:03d}.safetensors' for l in LAYERS]]:
            files[str(p.resolve())]=digest(p)
    return files


def isolated_cost(bl, k, v, beta, head):
    """Replace one head-group output; preserve the joint projected loss metric."""
    import torch
    import torch.nn.functional as F
    total = 0.
    group = bl.Hq // bl.Hkv
    lohead, hihead = head*group,(head+1)*group
    with torch.no_grad():
        for lo in range(0, bl.NT, bl.chunk):
            c = bl._chunk_tensors(lo,min(lo+bl.chunk,bl.NT))
            n = c['n']
            keys = torch.cat((k.expand(n,1,-1,-1),c['KL'][:,head:head+1]),dim=2)
            values = torch.cat((v.expand(n,1,-1,-1),c['VL'][:,head:head+1]),dim=2)
            mask = c['add'].clone()
            mask[:,:,:,:k.shape[2]] += beta[None,None,None,:]
            replacement = F.scaled_dot_product_attention(c['Q'][:,lohead:hihead],
                keys,values,attn_mask=mask,scale=bl.scale,enable_gqa=True)
            out,tgt = c['T'].clone(),c['T']
            out[:,lohead:hihead] = replacement
            if bl.gate_weight:
                gate=torch.sigmoid(c['G']).reshape(n,bl.Lq,bl.Hq,bl.D).permute(0,2,1,3)
                out,tgt = out*gate,tgt*gate
            out=out.permute(0,2,1,3).reshape(n,bl.Lq,-1) @ bl.o_proj
            tgt=tgt.permute(0,2,1,3).reshape(n,bl.Lq,-1) @ bl.o_proj
            mse=(((out-tgt)**2).mean(-1)*c['wq']).sum()*bl.c_layer
            cosine=((out/(out.norm(dim=-1,keepdim=True)+1e-8)) *
                    (tgt/(tgt.norm(dim=-1,keepdim=True)+1e-8))).sum(-1)
            total += float(mse + bl.cosine_weight*((1-cosine)*c['wq']).sum())
    return total/bl.NT


def curves(a,d):
    import numpy as np
    import torch
    from safetensors.torch import load_file
    from compile_torch_v2 import BatchedCausalTorchLoss
    config=dict(protocol=digest(a.out/'protocol.json'),method=a.method,
                grids=grid_files(d,a.out,a.method))
    path=a.out/f'{a.method}-curves.json'
    result=checkpoint(path,config)
    start=time.monotonic()
    previous=result.get('elapsed_s',0)
    for l in LAYERS:
        if str(l) in result['layers']:
            continue
        with (Path(d['reference'])/f'traj/layer_{l:03d}.pkl').open('rb') as f:
            sh=pickle.load(f)
        ks,vs=(torch.from_numpy(sh[n].astype(np.float32)).cuda() for n in ('k_sys','v_sys'))
        trajectories=[sh['traj'][i] for i in d['indices']]
        projection=torch.load(Path(d['reference'])/f'oproj/oproj_L{l}.pt',map_location='cpu',weights_only=True)['weight']
        points={str(h):[] for h in range(4)}
        for rows in method_grid(d,a.method):
            fitted=load_file(str(grid_folder(d,a.out,a.method,rows)/f'layer_{l:03d}.safetensors'))
            # Compiler BF16->native FP16 cast is part of the deployed artifact.
            fp32v=a.method=='am' and d.get('am_values_dtype')=='float32'
            if not all(torch.isfinite(t if n=='v' and fp32v else t.half()).all() for n,t in fitted.items()):
                raise ValueError('grid FP16 cast overflow')
            bl=BatchedCausalTorchLoss(ks,vs,trajectories,rows,gate_weight=True,
                o_proj=projection,device='cuda',chunk=4)
            for h in range(4):
                k=fitted['k'][:,h:h+1].half().float().cuda()
                v=fitted['v'][:,h:h+1].to(torch.float32 if fp32v else torch.float16).float().cuda()
                beta=fitted['beta'][0,h].float().cuda() if 'beta' in fitted else torch.zeros(rows,device='cuda')
                points[str(h)].append([rows,isolated_cost(bl,k,v,beta,h)])
            del bl,fitted
        result['layers'][str(l)]=points
        result['elapsed_s']=previous+time.monotonic()-start
        save(path,result)
        del ks,vs,sh,trajectories
        torch.cuda.empty_cache()
        progress(start,len(result['layers']),16,'allocation curves')
    result.update(complete=True)
    save(path,result)
    print(f'DONE total_duration={previous+time.monotonic()-start:.3f}s artifact={path}',flush=True)


def choose(a,d):
    path=a.out/f'{a.method}-curves.json'
    curves=json.loads(path.read_text())
    config=dict(protocol=digest(a.out/'protocol.json'),method=a.method,grids=grid_files(d,a.out,a.method))
    if not curves['complete'] or curves['identity']!=config or set(curves['layers'])!=set(map(str,LAYERS)):
        raise ValueError('incomplete/mismatched curves')
    points={f'{l:03d}/{h}':curves['layers'][str(l)][str(h)] for l in LAYERS for h in range(4)}
    if any([r for r,c in p]!=method_grid(d,a.method) for p in points.values()):
        raise ValueError('wrong curve grid')
    counts,cost=allocate(points,method_total(d,a.method))
    selected={str(l):[counts[f'{l:03d}/{h}'] for h in range(4)] for l in LAYERS}
    dest=a.out/f'{a.method}-allocation.json'
    result=dict(complete=True,protocol_sha256=digest(a.out/'protocol.json'),curves_sha256=digest(path),
                lengths=selected,total_rows=sum(map(sum,selected.values())),proxy_cost=cost)
    if dest.exists() and json.loads(dest.read_text())!=result:
        raise ValueError('refusing changed allocation')
    save(dest,result)


def selected(a,d):
    if a.method=='compiler' and d.get('compiler_reuse'):
        previous=Path(d['compiler_reuse'])
        from types import SimpleNamespace
        return selected(SimpleNamespace(out=previous,method='compiler'),identity(previous))
    path=a.out/f'{a.method}-allocation.json'
    r=json.loads(path.read_text())
    if not r['complete'] or r['protocol_sha256']!=digest(a.out/'protocol.json') or r['curves_sha256']!=digest(a.out/f'{a.method}-curves.json'):
        raise ValueError('allocation identity mismatch')
    from nonuniform_cache import validate_lengths
    if set(r['lengths'])!=set(map(str,LAYERS)):
        raise ValueError('missing allocated layer')
    for lengths in r['lengths'].values():
        validate_lengths(lengths,4,max(method_grid(d,a.method)))
        if not set(lengths)<=set(method_grid(d,a.method)):
            raise ValueError('allocated count outside grid')
    if sum(map(sum,r['lengths'].values()))!=method_total(d,a.method):
        raise ValueError('allocated total differs')
    return r['lengths']


def compiler_fit(a,d):
    if d.get('compiler_reuse'):
        raise ValueError('equal-memory study reuses verified compiler fits; do not refit')
    import torch
    from compile_torch_v2 import optimize_layer
    from nonuniform_cache import compiler_lengths,write_layer
    counts=selected(a,d)
    folder=a.out/'compiler_allocated'
    config=dict(protocol=digest(a.out/'protocol.json'),allocation=digest(a.out/'compiler-allocation.json'))
    path=folder/'fit.json'
    state=checkpoint(path,config)
    sampling=json.loads((ROOT/'inputs/joint/sampling.json').read_text())
    start=time.monotonic()
    previous=state.get('elapsed_s',0)
    for l in LAYERS:
        layerpath=folder/f'layer_{l:03d}.safetensors'
        if str(l) in state['layers']:
            if digest(layerpath)!=state['layers'][str(l)]['sha256']:
                raise ValueError('changed completed fit layer')
            continue
        projection=torch.load(Path(d['reference'])/f'oproj/oproj_L{l}.pt',map_location='cpu',weights_only=True)['weight']
        with compiler_lengths(counts[str(l)]):
            k,v,hist=optimize_layer(str(Path(d['reference'])/f'traj/layer_{l:03d}.pkl'),
                max(GRID),400,.001,1.,0,25,'cuda',batched=True,chunk=4,gate_weight=True,
                freeze_sink=True,examples_per_update=72,o_proj=projection,sampling_plan=sampling)
        # Preserve compiler's normal BF16 export before native FP16 conversion.
        write_layer(folder,l,k.bfloat16(),v.bfloat16(),torch.zeros(1,4,max(GRID)),counts[str(l)],max(GRID))
        state['layers'][str(l)]=dict(sha256=digest(layerpath),initial_loss=hist[0],final_loss=hist[-1])
        state['elapsed_s']=previous+time.monotonic()-start
        save(path,state)
        del k,v,hist
        torch.cuda.empty_cache()
        progress(start,len(state['layers']),16,'allocated compiler')
    state['complete']=True
    save(path,state)
    print(f'DONE total_duration={state.get("elapsed_s",0):.3f}s artifact={folder}',flush=True)


def compiler_grid(a,d):
    import subprocess
    if d.get('compiler_reuse'):
        raise ValueError('equal-memory study reuses verified compiler grid')
    if a.slots not in (2048,6144):
        raise ValueError('compiler-grid uses 2048 or 6144; verified 4096 is reused')
    ref=Path(d['reference'])
    subprocess.run([sys.executable,'-B',str(ROOT/'scripts/compile_torch_v2.py'),
        '--traj',str(ref/'traj'),'--out',str(a.out/f'compiler{a.slots}'),
        '--slots',str(a.slots),'--steps','400','--lr','.001','--cosine-weight','1',
        '--batched','--batch-chunk','4','--freeze-sink','--gate-weight',
        '--examples-per-update','72','--sampling-plan',str(ROOT/'inputs/joint/sampling.json'),
        '--kv-dtype','bfloat16','--oproj-dir',str(ref/'oproj'),
        '--seed','0','--log-every','25','--resume'],check=True)


def export(a,d):
    import torch
    from safetensors.torch import load_file
    from nonuniform_cache import write_layer,finish_export
    mean=method_total(d,a.method)//64
    counts=selected(a,d) if a.variant=='allocated' else {str(l):[mean]*4 for l in LAYERS}
    slots=max(max(v) for v in counts.values())
    folder=a.out/f'{a.method}_{a.variant}'
    config=dict(protocol=digest(a.out/'protocol.json'),method=a.method,variant=a.variant,
                grids=grid_files(d,a.out,a.method))
    fp32v=a.method=='am' and d.get('am_values_dtype')=='float32'
    config['values_dtype']='float32' if fp32v else 'float16'
    if a.variant=='allocated':
        allocation_root=Path(d['compiler_reuse']) if a.method=='compiler' and d.get('compiler_reuse') else a.out
        config['allocation']=digest(allocation_root/f'{a.method}-allocation.json')
    if (folder/'manifest.json').exists():
        existing=json.loads((folder/'manifest.json').read_text())
        if existing['identity']!=config:
            raise ValueError('refusing to replace different export')
        from nonuniform_cache import load_prefix
        load_prefix(folder,with_values=True)
        return
    if a.method=='compiler' and d.get('compiler_reuse'):
        source=Path(d['compiler_reuse'])/f'compiler_{a.variant}'
        manifest=json.loads((source/'manifest.json').read_text())
        if manifest['lengths']!=counts:
            raise ValueError('reused compiler lengths changed')
        slots=manifest['slots']
        for l in LAYERS:
            fitted=load_file(str(source/f'layer_{l:03d}.safetensors'))
            write_layer(folder,l,fitted['k'],fitted['v'],fitted['beta'],counts[str(l)],slots)
            if digest(folder/f'layer_{l:03d}.safetensors')!=manifest['files'][f'layer_{l:03d}.safetensors']:
                raise ValueError('reused compiler tensor bytes differ')
    elif a.method=='compiler' and a.variant=='allocated':
        fit=json.loads((folder/'fit.json').read_text())
        if not fit['complete'] or fit['identity']!={'protocol':config['protocol'],'allocation':config['allocation']}:
            raise ValueError('allocated compiler not fitted')
        # Fit pads to the fixed grid maximum, even if allocation is uniform.
        slots=max(GRID)
        for l in LAYERS:
            if digest(folder/f'layer_{l:03d}.safetensors')!=fit['layers'][str(l)]['sha256']:
                raise ValueError('allocated compiler fit changed')
    else:
        for l in LAYERS:
            k,v=torch.zeros(1,4,slots,256),torch.zeros(1,4,slots,256)
            beta=torch.zeros(1,4,slots)
            for h,n in enumerate(counts[str(l)]):
                fitted=load_file(str(grid_folder(d,a.out,a.method,n)/f'layer_{l:03d}.safetensors'))
                k[:,h,:n],v[:,h,:n]=fitted['k'][:,h],fitted['v'][:,h]
                if 'beta' in fitted: beta[:,h,:n]=fitted['beta'][:,h]
            write_layer(folder,l,k,v,beta,counts[str(l)],slots,values_fp32=fp32v)
    finish_export(folder,counts,slots,config)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('prepare','compiler-grid','curves','allocate','compiler-fit','export','solver-gate','native-gate','fp32-solver-gate','fp32-native-gate','am-fit','smoke','freeze','evaluate'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reference',type=Path)
    p.add_argument('--model',type=Path)
    p.add_argument('--method',choices=('compiler','am'),default='compiler')
    p.add_argument('--variant',choices=('uniform','allocated'),default='allocated')
    p.add_argument('--slots',type=int)
    p.add_argument('--gate',type=Path)
    p.add_argument('--original',type=Path)
    p.add_argument('--equal-memory-from',type=Path)
    p.add_argument('--am-values-fp32',action='store_true')
    p.add_argument('--allow-gpu',action='store_true')
    a=p.parse_args()
    gpu=a.command in ('compiler-grid','curves','compiler-fit','solver-gate','native-gate','fp32-solver-gate','fp32-native-gate','am-fit','smoke','evaluate')
    if gpu and not a.allow_gpu:
        p.error('GPU step blocked: requires explicit --allow-gpu')
    if a.command=='prepare':
        if a.reference is None:p.error('prepare requires --reference')
        prepare(a)
        return
    d=identity(a.out)
    if a.command=='compiler-grid':compiler_grid(a,d)
    elif a.command=='curves':curves(a,d)
    elif a.command=='allocate':choose(a,d)
    elif a.command=='compiler-fit':
        if a.method!='compiler':p.error('compiler-fit requires compiler method')
        compiler_fit(a,d)
    elif a.command=='export':export(a,d)
    elif a.command in ('solver-gate','native-gate'):
        if not a.model:p.error('AM gate requires --model')
        from am27b import gate
        a.reference=Path(d['reference'])
        a.solver_only=a.command=='solver-gate'
        a.load_head=a.command=='native-gate'
        a.out=a.out/'am-gate'
        gate(a)
    elif a.command in ('fp32-solver-gate','fp32-native-gate'):
        if not a.model or d.get('am_values_dtype')!='float32':
            p.error('FP32 gate requires --model and FP32 protocol')
        from am27b_fp32_gate import solver,native
        a.original=Path(d['failed_fp16_root'])
        a.reference=Path(d['reference'])
        a.diagnostic=a.original/'am6144_failure_diagnostic.json'
        a.out=a.out/'fp32-gate'
        (solver if a.command=='fp32-solver-gate' else native)(a)
    elif a.command=='am-fit':
        if not a.gate or not a.slots or not a.model:p.error('am-fit needs --gate --slots --model')
        if a.slots not in method_grid(d,'am'):p.error('AM slots outside frozen grid')
        from am27b import fit
        a.reference=Path(d['reference'])
        a.values_fp32=d.get('am_values_dtype')=='float32'
        a.precision_gate=a.out/'fp32-gate/gate.json'
        if a.values_fp32:
            gate=json.loads(a.precision_gate.read_text())
            solver=json.loads((a.out/'fp32-gate/solver.json').read_text())
            if gate['solver_sha256']!=digest(a.out/'fp32-gate/solver.json') or solver['diagnostic_sha256']!=digest(Path(d['failed_fp16_root'])/'am6144_failure_diagnostic.json'):
                raise ValueError('FP32 gate failed-head identity mismatch')
            if solver['capture_sha256']!=digest(a.reference/'traj/layer_019.pkl'):
                raise ValueError('FP32 gate capture mismatch')
        a.out=a.out/f'am{a.slots}'
        fit(a)
    else:
        from nonuniform_eval import smoke,freeze,evaluate
        {'smoke':smoke,'freeze':freeze,'evaluate':evaluate}[a.command](a,d)


if __name__=='__main__':
    main()
