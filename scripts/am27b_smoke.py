"""Train-only all-layer AM cache roundtrip before scored evaluation."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))


def smoke(a):
    import torch
    from safetensors.torch import load_file
    import exl3
    import prompt as P
    from am27b_attention import prefix_bias,load_fp32_prefix
    from am27b import digest,save,progress
    from eval_agent_exl3 import install_prefix,gen_greedy,load_compiled
    from reproduce import check_runtime
    started=time.monotonic()
    check_runtime(a.model)
    model,cache,tok,_=exl3.load(str(a.model),max_seq_len=32768,cache_size=32768)
    teacher=load_file(str(a.reference/'teacher/state.safetensors'))
    layers=exl3.full_attn_layers(model)
    delta={str(l):{n:teacher[f'delta.{l}.{n}'] for n in ('conv_state','recurrent_state')} for l in exl3.recurrent_layers(model)}
    q=json.loads((Path(__file__).resolve().parents[1]/'inputs/joint/questions.json').read_text())['items'][0]['q']
    ids=exl3.encode(tok,P.user_turn(q,think=False))
    rows=[]
    budgets=tuple(int(k) for k in a.slots.split(','))
    if not budgets or not set(budgets)<={4096,8192}:
        raise ValueError('invalid smoke budgets')
    for slots in budgets:
        folder=a.artifacts/f'am{slots}'
        manifest=json.loads((folder/'manifest.json').read_text())
        if not manifest['complete'] or manifest['slots']!=slots or manifest['layers']!=layers:
            raise ValueError('wrong AM cache')
        for n,h in manifest['files'].items():
            if digest(folder/n)!=h:
                raise ValueError('changed AM export')
        runs=[]
        for repeat in range(2):
            values=None
            if manifest['recipe'].get('values_dtype') == 'float32':
                compiled,bias,values=load_fp32_prefix(folder,slots)
            else:
                compiled=load_compiled(folder,slots)
                bias={l:load_file(str(folder/f'layer_{l:03d}.safetensors'))['beta'][0] for l in layers}
            if any(not torch.isfinite(t).all() for c in compiled.values() for t in c.values()):
                raise ValueError('nonfinite AM cache')
            logical,physical=install_prefix(model,cache,'compiled',n_sys=26341,delta=delta,attn=None,compiled=compiled,K=slots)
            for l in exl3.recurrent_layers(model):
                st=cache.recurrent_layers[l,0]
                if not all(torch.equal(getattr(st,n)[0].cpu(),delta[str(l)][n]) for n in ('conv_state','recurrent_state')):
                    raise ValueError('recurrent injection changed')
            with prefix_bias(bias,values):
                result=gen_greedy(model,cache,tok,ids,cap=32768,logical_pos=logical,physical_len=physical,max_tokens=16)
            if not torch.isfinite(result[3]).all():
                raise ValueError('nonfinite generation')
            runs.append(result)
            del compiled,bias,values
        if runs[0][0]!=runs[1][0] or not torch.equal(runs[0][3],runs[1][3]):
            raise ValueError('all-layer roundtrip generation mismatch')
        rows.append(dict(slots=slots,manifest_sha256=digest(folder/'manifest.json'),roundtrip_exact=True,
                         ids=runs[0][0],stop=runs[0][2]))
        progress(started,len(rows),len(budgets),'all-layer native smoke')
    save(a.out,dict(complete=True,rows=rows,elapsed_s=time.monotonic()-started,
        recurrent_injection_exact=True,wrapper_sha256=digest(Path(__file__).with_name('am27b_attention.py')),
        peak_gib=torch.cuda.max_memory_allocated()/2**30))
    print(f'DONE total_duration={time.monotonic()-started:.3f}s artifact={a.out}',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--artifacts',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--slots',default='4096,8192')
    smoke(p.parse_args())
