"""Bias applies only to compressed prefix, with live causal/GQA attention intact."""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from am27b_attention import attend

torch.manual_seed(0)
q = torch.randn(1, 3, 4, 8)
k, v = torch.randn(1, 7, 2, 8), torch.randn(1, 7, 2, 8)
beta = torch.randn(2, 4)
got = attend(q, k, v, beta, 4, 8**-.5)
want = torch.empty_like(got)
for pos in range(3):
    for head in range(4):
        scores = q[0,pos,head] @ k[0,:5+pos,head//2].T * 8**-.5
        scores[:4] += beta[head//2]
        want[0,pos,head] = scores.softmax(-1) @ v[0,:5+pos,head//2]
assert torch.allclose(got, want, atol=1e-6)
assert not torch.allclose(got, attend(q,k,v,torch.zeros_like(beta),4,8**-.5))
try:
    attend(q,k,v,torch.zeros(2,5),4,8**-.5)
except ValueError:
    pass
else:
    raise AssertionError('accepted beta over live tokens')
print('PASS explicit biased GQA reference, causal live rows, nonzero bias effect and boundary validation')

# Fitted V must not pass through FP16; live K/V and returned activations stay native.
wide = v.float().clone()
wide[0, 0, 0, 0] = 67691.234375
assert not torch.isfinite(wide.half()).all()
mixed = attend(q.half(), k.half(), wide, beta.half(), 4, 8**-.5)
reference = attend(q.half().float(), k.half().float(), wide, beta.half().float(), 4, 8**-.5).half()
assert mixed.dtype == torch.float16 and torch.isfinite(mixed).all()
assert torch.equal(mixed, reference)
print('PASS FP32 values above FP16 range preserved through attention with native output dtype')

# Exercise native-cache live writes plus the FP32 prefix override without EXL3.
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
from am27b_attention import prefix_bias
module = ModuleType('exllamav3.modules.attn')
original = lambda **kw: None
module.attn_dispatch, module._bc_attn_enable = original, True
class Layer:
    def __init__(self):
        self.k = torch.zeros(1, 8, 2, 8, dtype=torch.float16)
        self.v = torch.zeros_like(self.k)
        self.k.flatten(0,1)[:4] = k[0,:4].half()
        self.v.flatten(0,1)[:4] = v[0,:4].half()
    def update_kv_direct(self, lengths, table, keys, values, length):
        self.k.flatten(0,1)[4:4+length] = keys[0]
        self.v.flatten(0,1)[4:4+length] = values[0]
layer = Layer()
pkg, modules = ModuleType('exllamav3'), ModuleType('exllamav3.modules')
pkg.modules, modules.attn = modules, module
with patch.dict(sys.modules, {'exllamav3':pkg,'exllamav3.modules':modules,'exllamav3.modules.attn':module}):
    with prefix_bias({23:beta.half()}, {23:wide[:,:4].contiguous()}):
        got = module.attn_dispatch(cache_idx=23, causal=True, q=q.half(), k=k[:,4:].half(),
            v=v[:,4:].half(), block_table=torch.tensor([[0]]), cache_seqlens=torch.tensor([4]),
            cache=SimpleNamespace(layers={(23,0):layer}), sm_scale=8**-.5)
        all_values = torch.cat((wide[:,:4],v[:,4:].half().float()),dim=1)
        want = attend(q.half(), k.half(), all_values, beta.half(), 4, 8**-.5)
        assert torch.equal(got,want)
        assert torch.isfinite(layer.v).all() and torch.equal(layer.v.flatten(0,1)[4:7],v[0,4:].half())
    assert module.attn_dispatch is original and module._bc_attn_enable is True
print('PASS FP32 prefix overrides native placeholder, live cache remains FP16, dispatcher restored')

import tempfile
import json
from safetensors.torch import save_file
from am27b_attention import load_fp32_prefix
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp)
    layers=list(range(3,64,4))
    (folder/'manifest.json').write_text(json.dumps(dict(complete=True,slots=2,layers=layers,recipe=dict(values_dtype='float32'))))
    for l in layers:
        save_file(dict(k=torch.zeros(1,4,2,256,dtype=torch.float16),
            v=torch.full((1,4,2,256),67691.234375,dtype=torch.float32),
            beta=torch.zeros(1,4,2,dtype=torch.float16)),str(folder/f'layer_{l:03d}.safetensors'))
    compiled,bias,values=load_fp32_prefix(folder,2,device='cpu')
    assert set(compiled)==set(layers)
    assert all(c['v'].dtype==torch.float16 and not c['v'].any() for c in compiled.values())
    assert all(v.dtype==torch.float32 and torch.isfinite(v).all() and v.max()>65504 for v in values.values())
print('PASS all-layer FP32 loader keeps exact large V separate from zero native placeholders')
