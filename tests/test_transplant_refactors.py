"""Original questions, not retrospectively invented approximations."""
import ast
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from prepare_transplant_refactors import build
from clean_eval import signatures_match, common_private_helpers

data = build()
assert len(data['cases']) == 40
assert sum(c['source'].startswith('results/') for c in data['cases']) == 28
for c in data['cases']:
    obj = json.loads((root / c['source']).read_text())
    rows = obj['probes'] if isinstance(obj, dict) else obj
    assert next(r['q'] for r in rows if r['id'] == c['source_id']) == c['q']
    assert signatures_match(c['reference'], c['code'])
    assert common_private_helpers(c['reference']) == ['_validate']
    ast.parse(c['reference']+'\n'+c['checks'])
path = root / 'inputs/transplant_refactors_v4/cases.json'
if path.exists():
    assert json.loads(path.read_text()) == data
print('PASS40verbatimhistoricalquestions,28target+12longprefix,reference/signatureparity')
