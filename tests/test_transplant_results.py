"""Recoverability, frozen-source identities and all160reviewed result records."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from clean_eval import common_private_helpers, replacement

read = lambda name: json.loads((root / name).read_text())
cases = read('inputs/transplant_refactors_v4/cases.json')['cases']
freeze_path = root / 'results/TRANSPLANT_REFACTORS_V4_FREEZE.json'
frozen = json.loads(freeze_path.read_text())
review = read('results/TRANSPLANT_REFACTORS_V4_REVIEW.json')
assert review['complete'] and frozen['protocol'] == 'transplant-refactors-v4'
for name, expected in frozen['files'].items():
    if name.endswith('/inputs/transplant_refactors_v4/cases.json'):
        assert hashlib.sha256((root / 'inputs/transplant_refactors_v4/cases.json').read_bytes()).hexdigest() == expected
expected = {'full': (35, 33, 33), 'none': (0, 39, 0), 'joint4k': (20, 19, 18), 'joint8k': (38, 37, 36)}
for suffix in ('BASELINES', 'CANDIDATES'):
    name = f'results/TRANSPLANT_REFACTORS_V4_{suffix}.json'
    raw = read(name)
    assert raw['complete'] and raw['config']['freeze_sha256'] == hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == review['raw_sha256'][name]
    for arm, ss in raw['rows'].items():
        rows = ss['behavior']
        judged = review['arms'][arm]
        assert len(rows) == len(judged) == 40
        for c, r, j in zip(cases, rows, judged):
            assert c['id'] == r['id'] == j['id']
            assert j['pred_sha256'] == hashlib.sha256(r['pred'].encode()).hexdigest()
            assert j['functional_pass'] == r['code_check']['functional_pass']
            code = replacement(r['pred'])
            if code:
                assert common_private_helpers(code) == r['code_check']['common_private_helpers']
            assert j['joint_pass'] == (j['structure_pass'] and j['functional_pass'])
            assert r['stop'] == 'eos' and j['rationale']
        assert tuple(sum(j[k] for j in judged) for k in ('structure_pass', 'functional_pass', 'joint_pass')) == expected[arm]
assert sum(r['joint_pass'] for r in review['arms']['full']) >= 32
assert sum(r['joint_pass'] for r in review['arms']['none']) <= 8
print('PASS40verbatimcases,all160responses,baselinegate33vs0,candidates18/36,sourcehashes,nocaps')
