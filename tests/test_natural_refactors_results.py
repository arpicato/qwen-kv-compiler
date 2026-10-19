"""Check all natural-refactor outputs and reviewed source identities."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from clean_eval import common_private_helpers, replacement, signatures_match

read = lambda name: json.loads((root / name).read_text())
cases = read('inputs/natural_refactors_v3/cases.json')['cases']
raw = read('results/NATURAL_REFACTORS_V3_RAW.json')
review = read('results/NATURAL_REFACTORS_V3_REVIEW.json')
freeze = root / 'results/NATURAL_REFACTORS_V3_FREEZE.json'
assert raw['complete'] and review['complete']
assert raw['config']['freeze_sha256'] == hashlib.sha256(freeze.read_bytes()).hexdigest()
assert review['raw_sha256'] == hashlib.sha256((root / 'results/NATURAL_REFACTORS_V3_RAW.json').read_bytes()).hexdigest()
assert raw['config']['arms'] == ['full', 'none', 'joint4k', 'joint8k']
for arm, expected in [('full', (14, 38, 13)), ('none', (0, 37, 0)),
                      ('joint4k', (10, 37, 10)), ('joint8k', (9, 37, 9))]:
    rows = raw['rows'][arm]['behavior']
    judgments = review['arms'][arm]
    assert len(rows) == len(judgments) == 40
    assert not raw['rows'][arm]['knowledge'] and not raw['rows'][arm]['tools']
    for c, r, j in zip(cases, rows, judgments):
        assert c['id'] == r['id'] == j['id'] and c['family'] == j['family']
        assert hashlib.sha256(r['pred'].encode()).hexdigest() == j['pred_sha256']
        code = replacement(r['pred'])
        assert code and signatures_match(code, c['code'])
        assert common_private_helpers(code, c['functions']) == r['code_check']['common_private_helpers']
        assert j['functional_pass'] == r['code_check']['functional_pass']
        assert j['both'] == (j['structure_pass'] and j['functional_pass'])
        assert j['rationale'] and r['stop'] == 'eos'
    assert tuple(sum(j[k] for j in judgments) for k in ('structure_pass', 'functional_pass', 'both')) == expected
preflight = read('results/NATURAL_REFACTORS_V3_PREFLIGHT.json')
assert preflight['complete'] and len(preflight['rows']) == 40
assert all(r['positive']['functional_pass'] and not r['negative']['functional_pass'] for r in preflight['rows'])
print('PASS all160responses,source-hashedreview,helperdiagnostics,40positive/40negativechecks;14/0/10/9structure,13/0/10/9joint')
