"""Final 4B evidence has all cases, response-bound reviews and frozen scores."""
import json
import tempfile
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from evaluate import report
from clean_eval import knowledge as grade_knowledge, tool
from task_eval27b import schemas

cases = json.loads((root/'inputs/publication_final/cases.json').read_text())
schema = schemas((root/'inputs/joint/prompt.txt').read_text())

for arm, knowledge, tools in [('full',46,28), ('none',7,0), ('compiler',28,19),
                              ('am',35,17), ('cartridges',26,5)]:
    d = report(root/f'results/FINAL_EVAL4B_{arm.upper()}_RAW.json',
               root/f'results/FINAL_EVAL4B_{arm.upper()}_REVIEW.json',
               root/'inputs/publication_final/cases.json')
    assert d['task_scores'][arm]['knowledge']['correct'] == knowledge
    assert d['task_scores'][arm]['tools']['correct'] == tools
    s = d['scores'][arm]
    assert s['rule_shared']['joint'] == 0
    assert s['money_approved']['false_pauses'] == 0
    assert sum(s[c]['n'] for c in ('money_unapproved','money_approved','rule_shared','rule_distinct')) == 120
    assert not any(s[c]['false_pauses'] for c in ('rule_shared','rule_distinct'))
    raw = json.loads((root/f'results/FINAL_EVAL4B_{arm.upper()}_RAW.json').read_text())
    for c, r in zip(cases['knowledge'], raw['rows']['knowledge'], strict=True):
        assert grade_knowledge(r['pred'], c['answers'], r['stop'])['correct'] == r['correct']
    for c, r in zip(cases['tools'], raw['rows']['tools'], strict=True):
        for step, trace in zip(c['steps'], r['trace']):
            assert all(trace[k] == v for k, v in tool(trace['pred'], step, schema, trace['stop']).items())
        assert r['correct'] == (len(r['trace']) == len(c['steps']) and all(t['correct'] for t in r['trace']))
    assert d == json.loads((root/f'results/FINAL_EVAL4B_{arm.upper()}_SUMMARY.json').read_text())
with tempfile.TemporaryDirectory() as tmp:
    review = json.loads((root/'results/FINAL_EVAL4B_FULL_REVIEW.json').read_text())
    review['arms']['full'][0]['pred_sha256'] = 'wrong'
    p = Path(tmp)/'review.json'
    p.write_text(json.dumps(review))
    try:
        report(root/'results/FINAL_EVAL4B_FULL_RAW.json', p, root/'inputs/publication_final/cases.json')
    except ValueError as error:
        assert 'response identity' in str(error)
    else:
        raise AssertionError('accepted changed response hash')
print('PASS five final4B arms, 1200 cases, 600 response-bound reviews and frozen task scores')
