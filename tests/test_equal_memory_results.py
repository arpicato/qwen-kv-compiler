"""Saved byte-capped allocation and exact reuse of the compiler tensor bytes."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from head_allocation import allocate
from run_clean_eval import digest

read=lambda name:json.loads((ROOT/f'results/EQUAL_MEMORY_{name}.json').read_text())
protocol=read('PROTOCOL')
frozen=read('FREEZE')
assert protocol['cap_bytes']==268435456
assert protocol['am_grid']==[1363,2727,4091]
assert protocol['am_total_rows']==174528
assert protocol['am_payload_bytes']==174528*1538==268424064
assert protocol['unused_bytes']==11392
assert frozen['files'][frozen['cases']]==digest(ROOT/'inputs/publication_final/cases.json')
assert frozen['files'][frozen['prompt']]==digest(ROOT/'inputs/joint/prompt.txt')
curves=read('AM_CURVES');allocation=read('AM_ALLOCATION')
assert curves['complete'] and allocation['complete']
assert allocation['curves_sha256']==digest(ROOT/'results/EQUAL_MEMORY_AM_CURVES.json')
assert allocation['protocol_sha256']==digest(ROOT/'results/EQUAL_MEMORY_PROTOCOL.json')
points={f'{l:03d}/{h}':curves['layers'][str(l)][str(h)] for l in range(3,64,4) for h in range(4)}
selected,cost=allocate(points,174528)
assert cost==allocation['proxy_cost']
assert allocation['lengths']=={str(l):[selected[f'{l:03d}/{h}'] for h in range(4)] for l in range(3,64,4)}
assert [list(selected.values()).count(n) for n in protocol['am_grid']]==[23,18,23]
prior=json.loads((ROOT/'results/NONUNIFORM_FREEZE.json').read_text())
for arm in ('compiler_uniform','compiler_allocated'):
    def tensors(f):
        return {str(Path(p).relative_to(f['arms'][arm])):h for p,h in f['files'].items()
                if Path(f['arms'][arm]) in Path(p).parents and p.endswith('.safetensors')}
    assert len(tensors(frozen))==16 and tensors(frozen)==tensors(prior)
smoke=read('SMOKE')
assert smoke['complete'] and smoke['native_parity']['ids_equal']
assert smoke['native_parity']['max_logit_diff']<=.25
assert set(smoke['rows'])==set(frozen['arms'])
assert all(r['roundtrip_exact'] and r['recurrent_injection_exact'] for r in smoke['rows'].values())
audit=read('ARTIFACT_AUDIT')
assert audit['complete'] and audit['frozen_files']==len(frozen['files'])==252
assert audit['stage_receipts']==16 and audit['stage_output_hashes']==326
assert audit['freeze_sha256']==digest(ROOT/'results/EQUAL_MEMORY_FREEZE.json')
assert audit['protocol_sha256']==digest(ROOT/'results/EQUAL_MEMORY_PROTOCOL.json')
for arm,m in audit['arms'].items():
    assert m['payload_bytes']==(268424064 if arm.startswith('am') else 268435456)
    assert sum(map(sum,m['lengths'].values()))==(174528 if arm.startswith('am') else 262144)
print('PASS equal-memory cap, exact training-proxy allocation, compiler tensor-byte reuse and smoke')

recheck=read('IMPLEMENTATION_RECHECK')
assert recheck['complete'] and recheck['same_capture_and_proxy_examples']
assert recheck['same_solver_attention_loader_runner_code']
assert len(recheck['attention_checks'])==12
assert all(0<=r['max_abs_diff']<=.01 for r in recheck['attention_checks'])
assert sum(a['heads_checked'] for s in recheck['studies'].values() for a in s['arms'].values())==256
assert recheck['saved_task_regrade']['smaller']['freeze_sha256']==digest(ROOT/'results/EQUAL_MEMORY_FREEZE.json')
assert recheck['saved_task_regrade']['larger']['freeze_sha256']==digest(ROOT/'results/NONUNIFORM_FREEZE.json')
assert recheck['saved_task_regrade']['smaller']['scores']=={
    'am_uniform':dict(knowledge=50,tools=47),'am_allocated':dict(knowledge=56,tools=54)}
assert recheck['saved_task_regrade']['larger']['scores']=={
    'am_uniform':dict(knowledge=55,tools=52),'am_allocated':dict(knowledge=53,tools=52)}
print('PASS recorded 256-head implementation recheck, independent attention and saved-task regrade identities')

from evaluate import report
from clean_eval import knowledge,tool,replacement,signatures_match,common_private_helpers
from task_eval27b import schemas
from datetime import datetime
import tempfile
raw=read('RAW');casespath=ROOT/'inputs/publication_final/cases.json'
cases=json.loads(casespath.read_text());schema=schemas((ROOT/'inputs/joint/prompt.txt').read_text())
assert raw['complete'] and set(raw['rows'])=={'am_uniform','am_allocated'}
assert raw['config']['freeze_sha256']==digest(ROOT/'results/EQUAL_MEMORY_FREEZE.json')
for arm,suites in raw['rows'].items():
    for suite in ('knowledge','tools','behavior'):
        assert [r['id'] for r in suites[suite]]==[c['id'] for c in cases[suite]]
    for c,r in zip(cases['knowledge'],suites['knowledge'],strict=True):
        assert knowledge(r['pred'],c['answers'],r['stop'])['correct']==r['correct']
    for c,r in zip(cases['tools'],suites['tools'],strict=True):
        assert len(r['trace'])<=len(c['steps'])
        for step,t in zip(c['steps'],r['trace']):
            assert all(t[k]==v for k,v in tool(t['pred'],step,schema,t['stop']).items())
        assert r['correct']==(len(r['trace'])==len(c['steps']) and all(t['correct'] for t in r['trace']))
    for c,r in zip(cases['behavior'],suites['behavior'],strict=True):
        assert r['stop']=='eos'
        code=replacement(r['pred']);check=r['code_check']
        assert check['code_extracted']==(code is not None)
        if code:
            assert check['signatures_preserved']==signatures_match(code,c['code'])
            assert check['common_private_helpers']==common_private_helpers(code,c.get('functions',('primary','secondary')))
summary=report(ROOT/'results/EQUAL_MEMORY_RAW.json',ROOT/'results/EQUAL_MEMORY_REVIEW.json',casespath)
assert summary==read('SUMMARY')
for arm,k,t,shared,false,premature,gate,distinct in (
        ('am_uniform',50,47,10,31,4,16,39),('am_allocated',56,54,20,13,2,16,38)):
    assert summary['task_scores'][arm]==dict(knowledge=dict(n=60,correct=k),tools=dict(n=60,correct=t))
    s=summary['scores'][arm]
    assert s['rule_shared']['joint']==shared and s['rule_distinct']['joint']==distinct
    assert s['rule_shared']['false_pauses']+s['rule_distinct']['false_pauses']==false
    assert s['premature_implementation']==premature and s['money_unapproved']['joint']==gate
with tempfile.TemporaryDirectory() as tmp:
    review=read('REVIEW');review['arms']['am_allocated'][0]['pred_sha256']='wrong'
    path=Path(tmp)/'review.json';path.write_text(json.dumps(review))
    try:report(ROOT/'results/EQUAL_MEMORY_RAW.json',path,casespath)
    except ValueError as e:assert 'response identity' in str(e)
    else:raise AssertionError('accepted wrong response-bound review')
timing=read('TIMING')
assert timing['complete'] and len(timing['stages'])==16
for stage in timing['stages'].values():
    assert abs((datetime.fromisoformat(stage['end_utc'])-datetime.fromisoformat(stage['start_utc'])).total_seconds()-stage['wall_s'])<1e-6
assert abs(sum(x['wall_interval_s'] for x in timing['evaluation_arms'].values())-raw['elapsed_s'])<.1
assert timing['am_only_execution']['raw_sha256']==digest(ROOT/'results/EQUAL_MEMORY_RAW.json')
assert timing['interrupted_evaluation']['preserved_responses']==214
print('PASS 480 fresh AM responses, 240 response-bound reviews, independent task regrade, tamper rejection and wall time')
