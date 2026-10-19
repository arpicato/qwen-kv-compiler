"""Final AM4k source-bound behavior and regraded knowledge/tool traces."""
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from evaluate import report
from clean_eval import knowledge,tool
from task_eval27b import schemas

cases=json.loads((root/'inputs/publication_final/cases.json').read_text())
raw=json.loads((root/'results/AM27B_4K_RAW.json').read_text())
freeze=json.loads((root/'results/AM27B_4K_FREEZE.json').read_text())
from run_clean_eval import digest
assert raw['config']['freeze_sha256']==digest(root/'results/AM27B_4K_FREEZE.json')
assert 'am4k' in freeze['arms'] and 'am8k' not in freeze['arms']
schema=schemas((root/'inputs/joint/prompt.txt').read_text())
for suite in ('knowledge','tools','behavior'):
    assert [r['id'] for r in raw['rows']['am4k'][suite]]==[c['id'] for c in cases[suite]]
for c,r in zip(cases['knowledge'],raw['rows']['am4k']['knowledge'],strict=True):
    assert knowledge(r['pred'],c['answers'],r['stop'])['correct']==r['correct']
for c,r in zip(cases['tools'],raw['rows']['am4k']['tools'],strict=True):
    for step,t in zip(c['steps'],r['trace']):
        assert all(t[k]==v for k,v in tool(t['pred'],step,schema,t['stop']).items())
    assert r['correct']==(len(r['trace'])==len(c['steps']) and all(t['correct'] for t in r['trace']))
d=report(root/'results/AM27B_4K_RAW.json',root/'results/AM27B_4K_REVIEW.json',root/'inputs/publication_final/cases.json')
assert d==json.loads((root/'results/AM27B_4K_SUMMARY.json').read_text())
s=d['scores']['am4k']
assert s['money_unapproved']['joint']==16 and s['premature_implementation']==3
assert s['rule_shared']['joint']==23 and s['rule_shared']['false_pauses']==12
assert s['rule_distinct']['joint']==39 and s['pair_joint']==dict(money=15,refactor=23)
assert d['task_scores']['am4k']==dict(knowledge=dict(n=60,correct=55),tools=dict(n=60,correct=52))
print('PASS AM27B4k240cases/120response-boundreviews, frozen identity, regraded tasks and pairs')

prefix=root/'results/AM27B_8K_FP32'
paths={s:Path(str(prefix)+'_'+s+'.json') for s in ('RAW','FREEZE','MANIFEST','SMOKE','REVIEW','SUMMARY')}
raw=json.loads(paths['RAW'].read_text())
freeze=json.loads(paths['FREEZE'].read_text())
manifest=json.loads(paths['MANIFEST'].read_text())
smoke=json.loads(paths['SMOKE'].read_text())
arm='am8k_fp32'
assert raw['complete'] and raw['config']['freeze_sha256']==digest(paths['FREEZE'])
assert arm in freeze['arms'] and 'am8k' not in freeze['arms']
assert manifest['complete'] and manifest['slots']==8192 and manifest['layers']==list(range(3,64,4))
assert manifest['recipe']['values_dtype']=='float32'
assert smoke['complete'] and smoke['recurrent_injection_exact'] and smoke['rows'][0]['roundtrip_exact']
assert smoke['rows'][0]['manifest_sha256']==digest(paths['MANIFEST'])
assert freeze['files'][manifest['recipe']['precision_gate']]==manifest['recipe']['precision_gate_sha256']
for suite in ('knowledge','tools','behavior'):
    assert [r['id'] for r in raw['rows'][arm][suite]]==[c['id'] for c in cases[suite]]
for c,r in zip(cases['knowledge'],raw['rows'][arm]['knowledge'],strict=True):
    assert knowledge(r['pred'],c['answers'],r['stop'])['correct']==r['correct']
for c,r in zip(cases['tools'],raw['rows'][arm]['tools'],strict=True):
    for step,t in zip(c['steps'],r['trace']):
        assert all(t[k]==v for k,v in tool(t['pred'],step,schema,t['stop']).items())
    assert r['correct']==(len(r['trace'])==len(c['steps']) and all(t['correct'] for t in r['trace']))
assert all(r['stop']=='eos' for r in raw['rows'][arm]['behavior'])
d=report(paths['RAW'],paths['REVIEW'],root/'inputs/publication_final/cases.json')
assert d==json.loads(paths['SUMMARY'].read_text())
s=d['scores'][arm]
assert s['money_unapproved']['joint']==16 and s['premature_implementation']==4
assert s['rule_shared']['joint']==29 and s['rule_shared']['false_pauses']==9
assert s['rule_distinct']['joint']==38 and s['pair_joint']==dict(money=15,refactor=27)
assert d['task_scores'][arm]==dict(knowledge=dict(n=60,correct=57),tools=dict(n=60,correct=54))
print('PASS AM27B8kFP32 240cases/120response-boundreviews, precision/smoke freeze identity and regraded tasks')
