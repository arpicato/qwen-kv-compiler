"""CPU-only protocol/resume/allocation/gate boundaries and isolated-cost reference."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import nonuniform27b as n
from nonuniform_eval import accepted_smoke,ARMS
from run_clean_eval import digest,save
import compile_torch_v2 as c

budget=n.byte_budget(256*2**20)
assert budget==dict(cap_bytes=268435456,am_mean_rows=2727,am_total_rows=174528,
    am_grid=[1363,2727,4091],am_payload_bytes=268424064,unused_bytes=11392)
assert n.method_grid(dict(am_grid=budget['am_grid']),'am')==budget['am_grid']
assert n.method_total(dict(am_total_rows=174528),'am')==174528

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    save(root/'protocol.json',dict(files={}))
    a=SimpleNamespace(out=root,method='am',variant='uniform')
    fitted=dict(k=torch.ones(1,4,2,256).half(),v=torch.full((1,4,2,256),71021.34375),
                beta=torch.zeros(1,4,2).half())
    with patch.object(n,'grid_files',return_value={}),patch('safetensors.torch.load_file',return_value=fitted):
        n.export(a,dict(am_values_dtype='float32',am_grid=[1,2,3],am_total_rows=128))
    from nonuniform_cache import load_prefix
    _,_,values=load_prefix(root/'am_uniform',with_values=True)
    assert values[3][0,0,0,0]==71021.34375
    m=json.loads((root/'am_uniform/manifest.json').read_text())
    assert m['lengths']['3']==[2]*4 and m['payload_bytes']==128*1538
print('PASS byte-cap calculation and protocol-derived AM uniform export without FP32 loss')

# Distinct per-budget/head sentinels catch wrong-grid and wrong-head assembly.
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    save(root/'protocol.json',dict(files={}))
    counts={str(l):[1,2,3,2] for l in n.LAYERS}
    save(root/'am-allocation.json',dict(lengths=counts))
    from safetensors.torch import load_file as real_load
    def fitted(path):
        if Path(path).parent.name=='am_allocated':
            return real_load(path)
        slots=int(Path(path).parent.name.removeprefix('am'))
        k=torch.stack([torch.full((slots,256),slots*10+h) for h in range(4)])[None]
        return dict(k=k.half(),v=k.float()+70000,beta=k[:,:,:,0].half()/100)
    with patch.object(n,'grid_files',return_value={}),patch.object(n,'selected',return_value=counts), \
         patch('safetensors.torch.load_file',side_effect=fitted):
        n.export(SimpleNamespace(out=root,method='am',variant='allocated'),
                 dict(am_values_dtype='float32',am_grid=[1,2,3],am_total_rows=128))
    from nonuniform_cache import load_prefix
    compiled,bias,values=load_prefix(root/'am_allocated',with_values=True)
    for l in n.LAYERS:
        for h,slots in enumerate(counts[str(l)]):
            assert compiled[l]['k'][0,h,:slots].eq(slots*10+h).all()
            assert values[l][0,:slots,h].eq(70000+slots*10+h).all()
            assert values[l][0,slots:,h].eq(0).all()
            assert bias[l][h,slots:].isneginf().all()
            assert not compiled[l]['v'].any()
print('PASS allocated AM selects each head from its own grid fit with exact FP32 sidecars and masked padding')

for command in ('compiler-grid','curves','compiler-fit','solver-gate','native-gate','fp32-solver-gate','fp32-native-gate','am-fit','smoke','evaluate'):
    r=subprocess.run([sys.executable,str(ROOT/'scripts/nonuniform27b.py'),command,
        '--out','/nonexistent'],capture_output=True,text=True,timeout=10)
    assert r.returncode!=0 and 'GPU step blocked' in r.stderr

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    save(root/'protocol.json',dict(files={},total_rows=64*4096))
    d=n.identity(root)
    config={'protocol':digest(root/'protocol.json'),'method':'compiler','grids':{}}
    layers={str(l):{str(h):[[2048,8.],[4096,2.],[6144,1.]] for h in range(4)} for l in n.LAYERS}
    save(root/'compiler-curves.json',dict(complete=True,identity=config,layers=layers))
    a=SimpleNamespace(out=root,method='compiler')
    with patch.object(n,'grid_files',return_value={}):
        n.choose(a,d)
        assert n.selected(a,d)=={str(l):[4096]*4 for l in n.LAYERS}
        before=(root/'compiler-allocation.json').read_bytes()
        n.choose(a,d)
        assert (root/'compiler-allocation.json').read_bytes()==before
    save(root/'state.json',dict(identity={'x':1},layers={}))
    assert n.checkpoint(root/'state.json',{'x':1})['layers']=={}
    try:n.checkpoint(root/'state.json',{'x':2})
    except ValueError:pass
    else:raise AssertionError('changed recipe resumed')
    # Smoke is bound to all exports, model and protocol, not just complete=True.
    files={'file':'hash'}
    rows={}
    for arm in ARMS:
        save(root/arm/'manifest.json',dict(fixture=arm))
        rows[arm]=dict(roundtrip_exact=True,recurrent_injection_exact=True,
                       manifest_sha256=digest(root/arm/'manifest.json'))
    smoke=dict(complete=True,protocol_sha256='p',files=files,model=str(root.resolve()),
               rows=rows,native_parity=dict(ids_equal=True,max_logit_diff=.01))
    save(root/'smoke.json',smoke)
    accepted_smoke(root,files,'p',root)
    for field,value in (('complete',False),('files',{}),('protocol_sha256','other')):
        save(root/'smoke.json',dict(smoke,**{field:value}))
        try:accepted_smoke(root,files,'p',root)
        except ValueError:pass
        else:raise AssertionError(f'accepted wrong smoke {field}')
    bad=json.loads(json.dumps(smoke))
    bad['native_parity']['max_logit_diff']=float('nan')
    save(root/'smoke.json',bad)
    try:accepted_smoke(root,files,'p',root)
    except ValueError:pass
    else:raise AssertionError('accepted NaN parity')

torch.manual_seed(6)
k,v=torch.randn(1,2,5,4),torch.randn(1,2,5,4)
q=torch.randn(1,4,2,4)
kl,vl=torch.randn(1,2,3,4),torch.randn(1,2,3,4)
traj=[dict(q_rot=q.numpy(),k_live=kl.numpy(),v_live=vl.numpy(),
           q_logical=np.array([5,7]),k_logical=np.array([5,6,7]),
           gate=torch.randn(1,2,16).numpy())]
proj=torch.randn(16,7)
bl=c.BatchedCausalTorchLoss(k,v,traj,3,gate_weight=True,o_proj=proj,device='cpu')
ki,vi=c.init_from_teacher(k,v,3,0)
# Independently calculate the single-head replacement and projected metric.
for head in range(2):
    got=n.isolated_cost(bl,ki[:,head:head+1],vi[:,head:head+1],torch.zeros(3),head)
    t=bl._chunk_tensors(0,1)
    keys=torch.cat((ki[:,head:head+1],kl[:,head:head+1]),dim=2)
    vals=torch.cat((vi[:,head:head+1],vl[:,head:head+1]),dim=2)
    output=t['T'].clone()
    output[:,head*2:head*2+2]=torch.nn.functional.scaled_dot_product_attention(
        q[:,head*2:head*2+2],keys.repeat_interleave(2,1),vals.repeat_interleave(2,1),attn_mask=t['add'],scale=.5)
    gate=torch.sigmoid(t['G']).reshape(1,2,4,4).permute(0,2,1,3)
    x=(output*gate).permute(0,2,1,3).reshape(1,2,16)@proj
    y=(t['T']*gate).permute(0,2,1,3).reshape(1,2,16)@proj
    expected=(((x-y).square().mean(-1)*t['wq']).sum()*bl.c_layer+
              ((1-torch.nn.functional.cosine_similarity(x,y,dim=-1))*t['wq']).sum())
    assert abs(got-float(expected))<1e-5,(got,expected)
print('PASS GPU opt-in guard, exact allocation/resume, identity-bound gates, isolated projected loss vs independent reference')

# Exercise the actual shared evaluation loop with a CPU-only fake model. This
# verifies layout loading, routing, persistence and completed/partial resume.
from types import ModuleType
import run_clean_eval as runner
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    cases=dict(version='publication-final-v1',cap=32768,n_sys=2,limits={'knowledge':4},
        knowledge=[dict(id='k1',q='fixture?',answers=['answer'])],tools=[],behavior=[])
    save(root/'cases.json',cases)
    (root/'prompt.txt').write_text('fixture')
    slots_by_arm={arm:i+2 for i,arm in enumerate(ARMS)}
    for arm in ARMS:
        save(root/arm/'manifest.json',dict(slots=slots_by_arm[arm]))
    f=dict(cache_layout='padded-head-lengths-v1',cases=str(root/'cases.json'),
        prompt=str(root/'prompt.txt'),teacher=str(root/'teacher'),model='fake',code_image='unused',
        arms={a:str(root/a) for a in ARMS},files={str(root/'cases.json'):digest(root/'cases.json')})
    save(root/'freeze.json',f)
    exl=ModuleType('exl3')
    exl.load=lambda *a,**k:(object(),object(),object(),None)
    exl.encode=lambda *a:[1,2]
    exl.recurrent_layers=lambda m:[]
    exl.full_attn_layers=lambda m:[3]
    fake=ModuleType('eval_agent_exl3')
    calls=[]
    routed=[]
    def install(*a,**kw):
        marker=int(kw['compiled'][3]['k'].item())
        assert kw['K']==slots_by_arm[ARMS[marker]]
        routed.append(ARMS[marker])
        return 2,kw['K']
    fake.install_prefix=install
    fake.load_compiled=lambda *a:(_ for _ in ()).throw(AssertionError('wrong cache loader'))
    def generate(*a,**kw):
        calls.append(kw)
        return [1],'answer','eos',None
    fake.gen_greedy=generate
    def load(folder,device='cpu',with_values=False):
        assert with_values
        marker=ARMS.index(folder.name)
        return {3:{'k':torch.tensor([marker]),'v':torch.zeros(1)}},{3:torch.tensor([marker])},{3:torch.tensor([71021.34375+marker])}
    def bias_context(biases,values):
        assert int(biases[3][0])==ARMS.index(routed[-1])
        assert values[3].dtype==torch.float32 and values[3][0]==71021.34375+ARMS.index(routed[-1])
        return __import__('contextlib').nullcontext()
    with patch.dict(sys.modules,{'exl3':exl,'eval_agent_exl3':fake}), \
         patch('safetensors.torch.load_file',return_value={'attn.3.keys':torch.zeros(1),
             'attn.3.values':torch.zeros(1),'attn.3.offset':torch.tensor([2])}), \
         patch('nonuniform_cache.load_prefix',side_effect=load) as loader, \
         patch('am27b_attention.prefix_bias',side_effect=bias_context), \
         patch.object(runner,'schemas',return_value={}):
        runner.run(root/'freeze.json',root/'raw.json','test',list(ARMS))
        assert loader.call_count==4 and len(calls)==4
        assert routed==list(ARMS)
        raw=json.loads((root/'raw.json').read_text())
        assert raw['complete'] and all(s['knowledge'][0]['correct'] for s in raw['rows'].values())
        runner.run(root/'freeze.json',root/'raw.json','test',list(ARMS))
        assert len(calls)==4
        raw['complete']=False
        raw['rows']['am_allocated']['knowledge']=[]
        save(root/'raw.json',raw)
        runner.run(root/'freeze.json',root/'raw.json','test',list(ARMS))
        assert len(calls)==5
        assert routed==[*ARMS,'am_allocated']
print('PASS shared padded-layout evaluation routing, four-arm persistence and exact partial/completed resume')
