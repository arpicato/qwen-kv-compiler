"""Tiny attention/training checks for unequal prefix lengths and live causality."""
from pathlib import Path
import sys
import torch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import compile_torch_v2 as c
from nonuniform_cache import compiler_lengths, prefix_mask, validate_lengths
from am27b_attention import attend

torch.manual_seed(3)
q=torch.randn(1, 3, 4, 8)
k,v=torch.randn(1, 7, 2, 8),torch.randn(1, 7, 2, 8)
beta=torch.randn(2,4)
beta.masked_fill_(prefix_mask([2,4],4,'cpu'),float('-inf'))
out=attend(q,k,v,beta,4,8**-.5)
for pos in range(3):
    for h in range(4):
        count=[2,4][h//2]
        indices=list(range(count))+list(range(4,5+pos))
        logits=q[0,pos,h] @ k[0,indices,h//2].T * 8**-.5
        logits[:count]+=beta[h//2,:count]
        want=logits.softmax(-1) @ v[0,indices,h//2]
        assert torch.allclose(out[0,pos,h],want,atol=1e-6)

ks,vs=torch.randn(1,2,6,8),torch.randn(1,2,6,8)
tr=dict(q_rot=q.transpose(1,2).numpy(), k_live=k[:,4:].transpose(1,2).numpy(),
        v_live=v[:,4:].transpose(1,2).numpy(), q_logical=np.arange(6,9),k_logical=np.arange(6,9))
original=c.BatchedCausalTorchLoss(ks,vs,[tr],4,device='cpu')
ki,vi=c.init_from_teacher(ks,vs,4,0,True)
want=original.loss_fn(ki,vi)
with compiler_lengths([4,4]):
    kr,vr=c.init_from_teacher(ks,vs,4,0,True)
    assert torch.equal(ki,kr) and torch.equal(vi,vr)
    got=c.BatchedCausalTorchLoss(ks,vs,[tr],4,device='cpu').loss_fn(kr,vr)
    assert torch.equal(want,got)
with compiler_lengths([2,4]):
    kr,vr=c.init_from_teacher(ks,vs,4,0,True)
    assert not kr[0,0,2:].any() and torch.equal(kr[:,:,0],ks[:,:,0])
    kr.requires_grad_();vr.requires_grad_()
    loss=c.BatchedCausalTorchLoss(ks,vs,[tr],4,device='cpu').loss_fn(kr,vr)
    loss.backward()
    assert torch.isfinite(loss) and kr.grad[0,0,2:].eq(0).all() and vr.grad[0,0,2:].eq(0).all()
    assert kr.grad[0,0,:2].abs().sum()>0
assert c.BatchedCausalTorchLoss is type(original)
for lengths in ([0,4],[5,4],[True,4],[2]):
    try: validate_lengths(lengths,2,4)
    except ValueError: pass
    else: raise AssertionError('accepted invalid lengths')
print('PASS ragged explicit GQA/causal attention, uniform objective/init parity, padding zero gradients and lengths validation')

import json
import tempfile
from safetensors.torch import save_file
from nonuniform_cache import load_prefix, write_layer, finish_export
from run_clean_eval import digest

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    lengths={str(l):[1,2,1,2] for l in range(3,64,4)}
    for l in range(3,64,4):
        keys=torch.ones(1,4,2,256)
        write_layer(root,l,keys,keys,torch.zeros(1,4,2),lengths[str(l)],2)
    finish_export(root,lengths,2,{'test':'fixture','method':'am'})
    compiled,bias=load_prefix(root)
    assert not compiled[3]['k'][0,0,1].any() and bias[3][0,1].isneginf()
    assert bias[3][1].eq(0).all()
    first=digest(root/'layer_003.safetensors')
    write_layer(root,3,keys,keys,torch.zeros(1,4,2),lengths['3'],2)
    assert digest(root/'layer_003.safetensors')==first
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['payload_bytes']==sum(sum(v) for v in lengths.values())*(2*256*2+2)
    for change in ('hash','length','bytes','padding','incomplete'):
        altered=json.loads(json.dumps(manifest))
        if change=='hash': altered['files']['layer_003.safetensors']='0'*64
        elif change=='length': altered['lengths']['3']=[0,2,1,2]
        elif change=='incomplete': altered['complete']=False
        elif change=='bytes': altered['payload_bytes']+=1
        else:
            save_file(dict(k=keys.half(),v=keys.half(),beta=torch.zeros(1,4,2).half()),str(root/'layer_003.safetensors'))
            altered['files']['layer_003.safetensors']=digest(root/'layer_003.safetensors')
        (root/'manifest.json').write_text(json.dumps(altered))
        try: load_prefix(root)
        except ValueError: pass
        else: raise AssertionError(f'accepted {change}')
    print('PASS padded export/reload, exact tensor identity, byte accounting, tamper/shape/padding/incomplete rejection')
    for invalid in (float('nan'),67691.0):
        bad=keys.clone();bad[0,0,0,0]=invalid
        try:write_layer(root,3,bad,keys,torch.zeros(1,4,2),lengths['3'],2)
        except ValueError:pass
        else:raise AssertionError('accepted nonfinite/cast overflow')

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    lengths={str(l):[1,2,1,2] for l in range(3,64,4)}
    keys=torch.ones(1,4,2,256)
    values=keys.clone();values[0,0,0,0]=71021.34375
    for l in range(3,64,4):
        write_layer(root,l,keys,values,torch.zeros(1,4,2),lengths[str(l)],2,values_fp32=True)
    finish_export(root,lengths,2,dict(method='am',values_dtype='float32'))
    compiled,bias,sidecars=load_prefix(root,with_values=True)
    assert compiled[3]['v'].dtype==torch.float16 and not compiled[3]['v'].any()
    assert sidecars[3].dtype==torch.float32 and sidecars[3][0,0,0,0]==values[0,0,0,0]
    assert not sidecars[3][0,1,0].any() and bias[3][0,1].isneginf()
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['payload_bytes']==sum(map(sum,lengths.values()))*(256*6+2)
    assert manifest['padded_tensor_bytes']==16*4*2*(256*6+2)
    assert manifest['native_value_placeholder_bytes']==16*4*2*256*2
    try:load_prefix(root)
    except ValueError:pass
    else:raise AssertionError('discarded FP32 sidecars without opt-in')
    # Precision tags must describe tensor bytes, not just expected useful payload.
    manifest['identity']['values_dtype']='float16'
    (root/'manifest.json').write_text(json.dumps(manifest))
    try:load_prefix(root,with_values=True)
    except ValueError:pass
    else:raise AssertionError('accepted mismatched precision manifest')
print('PASS ragged FP32V export, overflow retention, native placeholders, sidecars and precision/bytes validation')
