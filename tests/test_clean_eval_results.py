"""Regrade all clean-set raw records and check manual labels against source hashes."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from summarize_clean_eval import summarize

summary = summarize()
assert summary == json.loads((root / 'results/CLEAN_EVAL27B_SUMMARY.json').read_text())
for arm, recall, calls, shared, code in [('full', 24, 15, 6, 5), ('none', 6, 2, 0, 5),
                                       ('joint4k', 20, 13, 3, 6), ('joint8k', 22, 14, 2, 5)]:
    d = summary['arms'][arm]
    assert sum(v['correct'] for v in d['knowledge'].values()) == recall
    assert sum(d['tools'][k]['completed'] for k in ('single_call', 'clarification', 'two_step')) == calls
    assert d['behavior']['rule_shared']['both'] == shared
    assert d['behavior']['rule_distinct']['both'] == 6
    assert d['behavior']['money_approved']['functional_pass'] == code
    assert d['behavior']['money_unapproved']['process_or_structure_pass'] == (0 if arm == 'none' else 6)
assert len(summary['arms']) == 4
print('PASS all256rawrecords, frozen automatic grades, manual source hashes and separate metric tables')
