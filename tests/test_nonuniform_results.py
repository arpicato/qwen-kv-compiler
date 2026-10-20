"""Recorded four-arm study: response-bound labels, frozen tasks and exact budgets."""
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evaluate import report
from run_clean_eval import digest
from clean_eval import knowledge,tool,replacement,signatures_match,common_private_helpers
from task_eval27b import schemas
from head_allocation import allocate

paths={n:ROOT/f'results/NONUNIFORM_{n}.json' for n in ('RAW','FREEZE','REVIEW','SUMMARY','SMOKE')}
raw=json.loads(paths['RAW'].read_text());frozen=json.loads(paths['FREEZE'].read_text())
casespath=ROOT/'inputs/publication_final/cases.json';cases=json.loads(casespath.read_text())
assert raw['complete'] and raw['config']['freeze_sha256']==digest(paths['FREEZE'])
assert frozen['cache_layout']=='padded-head-lengths-v1' and frozen['files'][frozen['cases']]==digest(casespath)
schema=schemas((ROOT/'inputs/joint/prompt.txt').read_text())
for arm,suites in raw['rows'].items():
    for suite in ('knowledge','tools','behavior'):
        assert [r['id'] for r in suites[suite]]==[c['id'] for c in cases[suite]]
    for c,r in zip(cases['knowledge'],suites['knowledge'],strict=True):
        assert knowledge(r['pred'],c['answers'],r['stop'])['correct']==r['correct']
    for c,r in zip(cases['tools'],suites['tools'],strict=True):
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
summary=report(paths['RAW'],paths['REVIEW'],casespath)
assert summary==json.loads(paths['SUMMARY'].read_text())
for arm,k,t,shared,false,premature in (
        ('compiler_uniform',46,51,19,18,0),('compiler_allocated',53,48,23,9,1),
        ('am_uniform',55,52,22,10,3),('am_allocated',53,52,29,7,0)):
    assert summary['task_scores'][arm]==dict(knowledge=dict(n=60,correct=k),tools=dict(n=60,correct=t))
    s=summary['scores'][arm]
    assert s['rule_shared']['joint']==shared and s['rule_shared']['false_pauses']==false
    assert s['premature_implementation']==premature and s['rule_distinct']['joint']==39
smoke=json.loads(paths['SMOKE'].read_text())
assert smoke['complete'] and smoke['native_parity']['ids_equal'] and smoke['native_parity']['max_logit_diff']<=.25
assert all(r['roundtrip_exact'] and r['recurrent_injection_exact'] for r in smoke['rows'].values())
for method in ('COMPILER','AM'):
    a=json.loads((ROOT/f'results/NONUNIFORM_{method}_ALLOCATION.json').read_text())
    p=ROOT/f'results/NONUNIFORM_{method}_CURVES.json';c=json.loads(p.read_text())
    assert a['curves_sha256']==digest(p) and a['complete'] and c['complete']
    points={f'{l:03d}/{h}':c['layers'][str(l)][str(h)] for l in range(3,64,4) for h in range(4)}
    selected,cost=allocate(points,262144)
    assert cost==a['proxy_cost'] and a['total_rows']==262144
    assert a['lengths']=={str(l):[selected[f'{l:03d}/{h}'] for h in range(4)] for l in range(3,64,4)}
with tempfile.TemporaryDirectory() as tmp:
    review=json.loads(paths['REVIEW'].read_text())
    review['arms']['am_allocated'][0]['pred_sha256']='wrong'
    p=Path(tmp)/'review.json';p.write_text(json.dumps(review))
    try:report(paths['RAW'],p,casespath)
    except ValueError as e:assert 'response identity' in str(e)
    else:raise AssertionError('accepted altered review binding')
print('PASS nonuniform960records/480reviews, regraded tasks/extraction, exact DP allocations, smoke and tamper rejection')

from datetime import datetime
timing=json.loads((ROOT/'results/NONUNIFORM_TIMING.json').read_text())
assert timing['complete'] and len(timing['stages'])==22
for stage in timing['stages'].values():
    assert abs((datetime.fromisoformat(stage['end_utc'])-datetime.fromisoformat(stage['start_utc'])).total_seconds()-stage['wall_s'])<1e-6
assert abs(sum(a['wall_interval_s'] for a in timing['evaluation_arms'].values())-raw['elapsed_s'])<.1
assert timing['stages']['evaluate']['wall_s']>raw['elapsed_s']
assert abs(sum(s['wall_s'] for s in timing['stages'].values())-timing['total_wall_s'])<1
print('PASS recorded UTC stage/arm wall-clock accounting; first interval setup and reused costs disclosed')
