"""Train-only native gates and response generation for the frozen allocation study."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

from run_clean_eval import digest, save

ROOT=Path(__file__).resolve().parents[1]
ARMS=('compiler_uniform','compiler_allocated','am_uniform','am_allocated')


def exports(root, protocol):
    """Validate every exported byte and bind the fit to this protocol."""
    from nonuniform_cache import load_prefix
    from nonuniform27b import method_total
    study=json.loads((root/'protocol.json').read_text())
    files={}
    for arm in ARMS:
        folder=root/arm
        load_prefix(folder,with_values=True)
        m=json.loads((folder/'manifest.json').read_text())
        method,variant=arm.split('_')
        if m['identity']['protocol']!=protocol or m['identity']['method']!=method or m['identity']['variant']!=variant:
            raise ValueError('export protocol/arm mismatch')
        precision=study.get('am_values_dtype','float16') if method=='am' else 'float16'
        if m['identity'].get('values_dtype','float16')!=precision:
            raise ValueError('export precision differs from study')
        total=method_total(study,method)
        if sum(map(sum,m['lengths'].values()))!=total:
            raise ValueError('export total row budget differs')
        if variant=='uniform' and any(v!=[total//64]*4 for v in m['lengths'].values()):
            raise ValueError('uniform export has nonuniform heads')
        if study.get('cap_bytes') and m['payload_bytes']>study['cap_bytes']:
            raise ValueError('export exceeds frozen useful-byte cap')
        for p in [folder/'manifest.json',*[folder/n for n in m['files']]]:
            files[str(p.resolve())]=digest(p)
    return files


def smoke(a,d):
    import sys
    import torch
    from safetensors.torch import load_file
    from nonuniform_cache import load_prefix
    from am27b_attention import prefix_bias
    from reproduce import check_runtime
    from eval_agent_exl3 import install_prefix,gen_greedy,load_compiled
    sys.path.insert(0,str(ROOT/'src'))
    import exl3
    import prompt as P
    if a.model is None:
        raise ValueError('smoke requires --model')
    files=exports(a.out,digest(a.out/'protocol.json'))
    check_runtime(a.model)
    started=time.monotonic()
    model,cache,tok,_=exl3.load(str(a.model),max_seq_len=32768,cache_size=32768)
    teacher=load_file(str(Path(d['reference'])/'teacher/state.safetensors'))
    delta={str(l):{n:teacher[f'delta.{l}.{n}'] for n in ('conv_state','recurrent_state')} for l in exl3.recurrent_layers(model)}
    question=json.loads((ROOT/'inputs/joint/questions.json').read_text())['items'][0]['q']
    ids=exl3.encode(tok,P.user_turn(question,think=False))
    result=dict(complete=False,protocol_sha256=digest(a.out/'protocol.json'),files=files,
                model=str(a.model.resolve()),rows={},question=question)
    def generate(compiled,slots,bias=None,values=None):
        logical,physical=install_prefix(model,cache,'compiled',n_sys=26341,delta=delta,attn=None,compiled=compiled,K=slots)
        for l in exl3.recurrent_layers(model):
            st=cache.recurrent_layers[l,0]
            if not all(torch.equal(getattr(st,n)[0].cpu(),delta[str(l)][n]) for n in ('conv_state','recurrent_state')):
                raise ValueError('recurrent injection changed')
        from contextlib import nullcontext
        with prefix_bias(bias,values) if bias is not None else nullcontext():
            r=gen_greedy(model,cache,tok,ids,cap=32768,logical_pos=logical,physical_len=physical,max_tokens=16)
        if not torch.isfinite(r[3]).all():
            raise ValueError('nonfinite smoke logits')
        return r
    native=generate(load_compiled(Path(d['reference'])/'compiled4096',4096),4096)
    for arm in ARMS:
        folder=a.out/arm
        slots=json.loads((folder/'manifest.json').read_text())['slots']
        runs=[]
        for repeat in range(2):
            compiled,bias,values=load_prefix(folder,with_values=True)
            runs.append(generate(compiled,slots,bias,values))
        if runs[0][0]!=runs[1][0] or not torch.equal(runs[0][3],runs[1][3]):
            raise ValueError(f'{arm} reload not exact')
        result['rows'][arm]=dict(roundtrip_exact=True,recurrent_injection_exact=True,
            ids=runs[0][0],stop=runs[0][2],manifest_sha256=digest(folder/'manifest.json'))
        if arm=='compiler_uniform':
            difference=float((native[3].float()-runs[0][3].float()).abs().max())
            result['native_parity']=dict(ids_equal=native[0]==runs[0][0],max_logit_diff=difference,tolerance=.25)
            if native[0]!=runs[0][0] or not math.isfinite(difference) or difference>.25:
                save(a.out/'smoke.json',result)
                raise ValueError('uniform compiler native parity failed')
        save(a.out/'smoke.json',result)
        print(f'{datetime.now(timezone.utc).isoformat()} smoke={arm} completed={len(result["rows"])}/4 elapsed={time.monotonic()-started:.1f}s',flush=True)
    result.update(complete=True,elapsed_s=time.monotonic()-started,peak_gib=torch.cuda.max_memory_allocated()/2**30)
    save(a.out/'smoke.json',result)
    print(f'DONE total_duration={result["elapsed_s"]:.3f}s artifact={a.out/"smoke.json"}',flush=True)


def accepted_smoke(root, files, protocol, model):
    s=json.loads((root/'smoke.json').read_text())
    if not s['complete'] or s['protocol_sha256']!=protocol or s['files']!=files or s['model']!=str(model.resolve()):
        raise ValueError('smoke source/artifact/model identity mismatch')
    difference=s['native_parity']['max_logit_diff']
    if set(s['rows'])!=set(ARMS) or not s['native_parity']['ids_equal'] or not math.isfinite(difference) or not 0<=difference<=.25:
        raise ValueError('smoke parity incomplete')
    for arm in ARMS:
        row=s['rows'][arm]
        if not row['roundtrip_exact'] or not row['recurrent_injection_exact'] or row['manifest_sha256']!=digest(root/arm/'manifest.json'):
            raise ValueError('smoke reload/recurrent gate incomplete')
    return s


def freeze(a,d):
    if a.model is None:
        raise ValueError('freeze requires --model')
    path=a.out/'freeze.json'
    if path.exists():
        raise ValueError('refusing to overwrite existing freeze')
    protocol=digest(a.out/'protocol.json')
    files=exports(a.out,protocol)
    accepted_smoke(a.out,files,protocol,a.model)
    for p in [a.out/'protocol.json',a.out/'smoke.json']:
        files[str(p.resolve())]=digest(p)
    files.update(d['files'])
    runtime=json.loads((ROOT/'runtime.json').read_text())
    for name,h in {**runtime['weight_sha256'],**runtime['metadata_sha256']}.items():
        if digest(a.model/name)!=h:
            raise ValueError(f'model changed: {name}')
    save(path,dict(protocol='publication-final-v1',cache_layout='padded-head-lengths-v1',
        frozen_utc=datetime.now(timezone.utc).isoformat(),model=str(a.model.resolve()),
        cases=str(ROOT/'inputs/publication_final/cases.json'),prompt=str(ROOT/'inputs/joint/prompt.txt'),
        teacher=str(Path(d['reference'])/'teacher'),arms={arm:str((a.out/arm).resolve()) for arm in ARMS},
        files=files,code_image=runtime['docker_code_check_image']))


def evaluate(a,d):
    from reproduce import check_runtime
    from run_clean_eval import run
    f=json.loads((a.out/'freeze.json').read_text())
    # The standard runner validates frozen source/exports and per-case resume.
    # Explicit runtime guard matches the supported evaluation CLI.
    check_runtime(Path(f['model']))
    run(a.out/'freeze.json',a.out/'raw.json','test',list(ARMS))
