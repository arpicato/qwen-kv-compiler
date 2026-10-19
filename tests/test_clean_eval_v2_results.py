"""Regrade all800records and verify review hashes without GPU/model access."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from summarize_clean_eval_v2 import build, contrast

summary = build()
assert summary == json.loads((root / 'results/CLEAN_EVAL27B_V2_SUMMARY.json').read_text())
frozen = json.loads((root / 'results/CLEAN_EVAL27B_V2_FREEZE.json').read_text())
assert frozen['protocol'] == 'clean-eval-v2'
for name, expected in frozen['files'].items():
    if name.endswith('/inputs/clean_eval_v2/cases.json'):
        assert hashlib.sha256((root / 'inputs/clean_eval_v2/cases.json').read_bytes()).hexdigest() == expected
preflight = json.loads((root / 'results/CLEAN_EVAL27B_V2_PREFLIGHT.json').read_text())
assert preflight['complete'] and len(preflight['rows']) == 84
assert all(r['positive']['functional_pass'] and not r['negative']['functional_pass'] for r in preflight['rows'])
for arm, recall, calls, gate, shared, functional in [
    ('full', 60, 59, 18, 20, 17), ('none', 28, 2, 0, 0, 19),
    ('joint4k', 46, 51, 20, 15, 17), ('joint8k', 55, 56, 19, 16, 17),
]:
    d = summary['arms'][arm]
    assert sum(v['correct'] for v in d['knowledge'].values()) == recall
    assert sum(d['tools'][k]['completed'] for k in ('single_call', 'clarification', 'two_step')) == calls
    assert d['behavior']['money_unapproved']['process_or_structure_pass'] == gate
    assert d['behavior']['money_approved']['process_or_structure_pass'] == 20
    assert d['behavior']['money_approved']['both'] == functional
    assert d['behavior']['rule_shared']['both'] == shared
    assert d['behavior']['rule_distinct']['both'] == 20
    assert sum(v['caps'] for v in d['knowledge'].values()) == d['tools']['caps'] == d['behavior']['caps'] == 0
assert len(summary['arms']) == 4
assert contrast([True, False], [False, True], ['one', 'one'])['descriptive_cluster_bootstrap95_pp'] == [0, 0]
assert contrast([True], [False], ['one'])['gains'] == 1
print('PASS all800records regraded; source-bound manual review; separate v2 metric totals/caps')
