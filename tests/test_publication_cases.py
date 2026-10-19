"""Final matrix has both sides of each policy without another ordinary bank."""
import ast
import json
from collections import Counter
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from publication_cases import build
from clean_eval import signatures_match, common_private_helpers

d = build()
assert d == json.loads((root / 'inputs/publication_final/cases.json').read_text())
assert len(d['knowledge']) == len(d['tools']) == 60
assert len(d['behavior']) == 120
assert Counter(r['category'] for r in d['behavior']) == dict(money_unapproved=20, money_approved=20, rule_shared=40, rule_distinct=40)
groups = {}
for c in d['behavior']:
    groups.setdefault(c['cluster'], []).append(c)
    assert signatures_match(c['reference'], c['code'])
    ast.parse(c['reference'] + '\n' + c['checks'])
    if c['category'] == 'rule_shared':
        assert common_private_helpers(c['reference']) == ['_validate']
    if c['category'] == 'rule_distinct':
        assert not common_private_helpers(c['reference'])
        assert 'secondary must keep its original' in c['q']
assert len(groups) == 60 and all(len(v) == 2 for v in groups.values())
assert len({r['q'] for r in d['behavior']}) == 120
page = next(c for c in d['behavior'] if c['id'] == 'page-size-shared')
assert 'reject page sizes above 100' in page['q']
assert sum(c['model_text_changed'] for c in d['behavior']) == 43
print('PASS final240matrix:20approvalpairs40contractpairs, provenance, signatures and no supplied solution')
