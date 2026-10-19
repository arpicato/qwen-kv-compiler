"""Recompute frozen publication counts from saved records, without model dependencies."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from task_eval27b import grade, schemas


def read(name):
    return json.loads((root / 'results' / name).read_text())


summary = read('JOINT_TOOLS27B_SUMMARY.json')
for suite, total, expected in [('AGENT78', 78, [76, 32, 62, 72]),
                               ('STRESS197', 197, [197, 90, 157, 181])]:
    arms = {}
    for budget in ('4K', '8K'):
        data = read(f'JOINT_TOOLS27B_{suite}_{budget}.json')
        assert data['summary']['complete'] and data['config']['n_sys'] == 26341
        for arm, rows in data['rows'].items():
            assert len(rows) == total
            label = ('joint' + budget.lower()) if arm == 'compiled' else arm
            arms[label] = sum(r['ok'] for r in rows)
            counts = summary['probes'][suite.lower()][label]
            assert counts['correct'] == arms[label]
            assert counts['caps'] == sum(r['stop'] == 'cap' for r in rows)
    assert [arms[k] for k in ('teacher', 'none', 'joint4k', 'joint8k')] == expected

tasks = read('JOINT_TOOLS27B_TASKS.json')
cases = read('TASK27B_FROZEN.json')['test']
schema = schemas((root / 'prompts/agent_resident.txt').read_text())
assert tasks['complete']
for arm, expected in zip(('full', 'none', 'joint4k', 'joint8k'), (40, 1, 24, 29)):
    rows = tasks['rows'][arm]
    assert len(rows) == len(cases) == 40
    for case, row in zip(cases, rows):
        assert row['id'] == case['id'] and row['kind'] == case['kind']
        assert 1 <= len(row['trace']) <= len(case['steps'])
        for i, trace in enumerate(row['trace']):
            ok, reason = grade(trace['pred'], case['steps'][i], schema)
            assert trace['ok'] == (ok and trace['stop'] != 'cap')
            assert trace['reason'] == ('cap' if trace['stop'] == 'cap' else reason)
            assert i == len(row['trace']) - 1 or trace['ok']
        assert row['ok'] == (len(row['trace']) == len(case['steps']) and all(t['ok'] for t in row['trace']))
    assert sum(r['ok'] for r in rows) == expected == summary['tasks'][arm]['correct']

four = read('LONG_POLICY4K27B_SUMMARY.json')['compiled_rows']
eight = read('LONG_POLICY8K27B_SUMMARY.json')['rows']
assert sum(r['behavior'] for r in four) == 18
assert sum(r['behavior'] for r in eight) == 22  # conservative annotation
assert sum(r['code_ok'] is True for r in four) == 5
assert sum(r['code_ok'] is True for r in eight) == 12
continuation = read('POLICY_COVERAGE_CONTINUE27B_SUMMARY.json')
for arm, expected in [('control', 17), ('candidate', 15)]:
    assert sum(r['behavior'] for r in continuation['arms'][arm]['rows']) == expected
print('PASS unified tables, 160 task records regraded, behavior annotations and negative result')
