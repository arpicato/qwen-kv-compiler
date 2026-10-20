"""CPU-only check that diagnostic distinguishes solver failure from cast overflow."""
from pathlib import Path
import json
import sys
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from am27b_diagnose import solution_stats

for value,finite,cast_finite in ((1.,True,True),(67691.,True,False),(float('inf'),False,False)):
    x=torch.tensor([[value]],dtype=torch.float32)
    before=x.clone()
    r=solution_stats(x)
    assert r['fp32_finite']==finite and r['fp16_finite']==cast_finite
    assert r['nonfinite_fp16']==int(not cast_finite)
    assert torch.equal(before,x), 'diagnostic changed solution'
print('PASS same-solution finite/cast-overflow classification without mutation')

r=json.loads((Path(__file__).resolve().parents[1]/'results/NONUNIFORM_AM6144_FAILURE_DIAGNOSTIC.json').read_text())
assert r['complete'] and (r['layer'],r['kv_head'],r['slots'])==(19,1,6144)
v=[c for c in r['lstsq'] if c['solution_shape']==[6144,256]]
assert len(v)==1 and v[0]['fp32_finite'] and not v[0]['fp16_finite']
assert v[0]['max_abs']>65504 and v[0]['nonfinite_fp16']==1
assert r['output_finite']==dict(k=True,beta=True,v=False)
print('PASS recorded failed-head evidence: finite FP32 V, one FP16 overflow, finite K/beta')
