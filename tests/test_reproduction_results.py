"""Check fresh rerun records without requiring the GPU or private artifact folders."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from task_eval27b import grade, schemas


def read(name):
    return json.loads((root / 'results' / ('REPRODUCTION27B_' + name + '.json')).read_text())


summary, review, audit, run = map(read, ('SUMMARY', 'REVIEW', 'AUDIT', 'RUN'))
assert all(x['complete'] for x in (summary, review, audit, run))
assert len(run['phases']) == 19
for label, expected in [('AGENT78', (62, 72)), ('STRESS197', (157, 181))]:
    for budget, want in zip(('4K', '8K'), expected):
        d = read(label + '_' + budget)
        assert d['summary']['complete'] and d['config']['n_sys'] == 26341
        assert sum(r['ok'] for r in d['rows']['compiled']) == want
        parity = audit['probe_parity'][f'{label.lower()}_{4096 if budget == "4K" else 8192}']['compiled']
        assert parity['gains'] == parity['losses'] == 0
for arm, expected in [('full', 23), ('none', 0), ('joint4k', 17), ('joint8k', 22),
                      ('control', 17), ('candidate', 15)]:
    rows = review['arms'][arm]['rows']
    assert len(rows) == 24 and sum(r['behavior'] for r in rows) == expected
    assert review['arms'][arm]['behavior'] == expected
assert review['joint8k_formula_as_proposal_sensitivity'] == 23
for arm, filename in [('full', 'GATE4K'), ('none', 'GATE4K'), ('joint4k', 'GATE4K'),
                       ('joint8k', 'GATE8K'), ('control', 'CONTROL'), ('candidate', 'CANDIDATE')]:
    path = root / 'results' / f'REPRODUCTION27B_{filename}.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == review['arms'][arm]['raw_sha256']
schema = schemas((root / 'inputs/joint/prompt.txt').read_text())
cases = json.loads((root / 'inputs/joint/tasks.json').read_text())['test']
tasks = read('TASKS')
assert tasks['complete']
for arm, want in [('full', 40), ('none', 1), ('joint4k', 24), ('joint8k', 29)]:
    rows = tasks['rows'][arm]
    assert len(rows) == 40 and sum(r['ok'] for r in rows) == want
    for case, row in zip(cases, rows):
        assert row['id'] == case['id']
        assert 1 <= len(row['trace']) <= len(case['steps'])
        for i, t in enumerate(row['trace']):
            ok, reason = grade(t['pred'], case['steps'][i], schema)
            assert t['ok'] == (ok and t['stop'] != 'cap')
            assert t['reason'] == ('cap' if t['stop'] == 'cap' else reason)
            assert i == len(row['trace'])-1 or t['ok']
        assert row['ok'] == (len(row['trace']) == len(case['steps']) and all(t['ok'] for t in row['trace']))
assert all(v['projection_equal'] for v in audit['layers'].values())
assert not all(all(v['prefix_equal'].values()) for v in audit['layers'].values())
print('PASS fresh19phases, compiledtool/task parity,17/22behavior,negative17/15,numerical differences disclosed')
