"""Validate the targeted natural-request bank without executing generated code."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from clean_eval import common_private_helpers, signatures_match
from prepare_natural_refactors import build

data = build()
cases = data['cases']
assert len(cases) == len({c['id'] for c in cases}) == len({c['q'] for c in cases}) == 40
assert len({c['cluster'] for c in cases}) == 40
assert set(Counter(c['family'] for c in cases)) == {'numeric', 'text', 'path', 'collection', 'mapping', 'compound', 'stdlib', 'protocol'}
for c in cases:
    ast.parse(c['code'], filename=c['id']+'-original')
    ast.parse(c['reference'], filename=c['id']+'-reference')
    ast.parse(c['checks'], filename=c['id']+'-checks')
    assert signatures_match(c['reference'], c['code'])
    assert common_private_helpers(c['reference'], c['functions']) == ['_validate']
    assert common_private_helpers(c['code'], c['functions']) == []
    question = c['q'].split('\n\n', 1)[0].lower()
    assert not any(word in question for word in ('helper', 'refactor', 'approval', 'shared', 'centraliz', 'extract'))
    assert '```' not in c['q']
    assert len(c['valid_inputs']) >= 2 and len(c['invalid_inputs']) >= 2
    assert len(c['functions']) == 2
    assert all(name in {n.name for n in ast.parse(c['code']).body if isinstance(n, ast.FunctionDef)} for name in c['functions'])
prior = []
for directory in ('inputs/joint', 'inputs/clean_eval_v1', 'inputs/clean_eval_v2'):
    for path in (root / directory).glob('*.json'):
        obj = json.loads(path.read_text())
        if isinstance(obj, dict):
            for key in ('items', 'probes', 'test', 'knowledge', 'tools', 'behavior'):
                prior += [r['q'] for r in obj.get(key, []) if isinstance(r, dict) and 'q' in r]
assert not set(prior) & {c['q'] for c in cases}
path = root / 'inputs/natural_refactors_v3/cases.json'
if path.exists():
    assert json.loads(path.read_text()) == json.loads(json.dumps(data, allow_nan=False))
manifest = root / 'inputs/natural_refactors_v3/manifest.json'
if manifest.exists():
    for name, expected in json.loads(manifest.read_text()).items():
        # The historical manifest pins its original source snapshot, not future
        # shared CLI helpers. Keep verifying immutable input/evidence bytes here.
        if name.startswith(('inputs/', 'results/')):
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
print('PASS40naturalrequests,8families,syntax/signatures,boundaries,nohelperhints,noapproval,noexactoldquestionreuse')
