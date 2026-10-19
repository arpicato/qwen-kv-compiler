"""Shared 4B framing/split/query contract; no model or dependencies."""
import json
from pathlib import Path
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from compare4b import prepare, positions, target_indices, grouped_mean, native_stop

with tempfile.TemporaryDirectory() as directory:
    d = Path(directory)
    repaired = d / 'repaired.json'
    repaired.write_text(json.dumps({'rows': [
        {'q': 'validation question', 'answer': 'answer', 'split': 'val'},
        {'q': 'validation question', 'answer': 'answer', 'split': 'val'},
        {'q': 'unused old train', 'answer': 'answer', 'split': 'train'}]}))
    data = prepare(repaired)
    assert len(data['train']) == 812 and len(data['validation']) == 1
    assert data['train'] == json.loads((root / 'inputs/joint/questions.json').read_text())['items']
    assert data['budget_rows'] == 2509
    repaired.write_text(json.dumps({'rows': [dict(q=data['train'][0]['q'], answer='wrong', split='val')]}))
    try:
        prepare(repaired)
    except ValueError as error:
        assert 'overlap' in str(error)
    else:
        raise AssertionError('accepted train/validation overlap')

# Query i predicts token i+1. Keep last user query and EOS predictor explicitly.
assert positions(5, 4, 10) == [4, 5, 6, 7]
selected = positions(5, 100, 10)
assert len(selected) == 11 and selected[0] == 4 and selected[-1] == 103
assert positions(5, 100, 1) == [4, 103]
assert target_indices(5, 4, 0) == [4, 5, 6, 7]
assert target_indices(5, 4, 100) == [104, 105, 106, 107]
assert grouped_mean([2, 4, 9], ['a', 'a', 'b']) == 6
assert native_stop([42], 151645, {151645}, 2) == ([42, 151645], 'eos')
assert native_stop([42, 43], 43, {151645}, 2) == ([42, 43], 'cap')
try:
    positions(0, 2, 10)
except ValueError:
    pass
else:
    raise AssertionError('accepted empty user turn')
print('PASS 812 shared examples, grouped validation, fixed budget, causal query/EOS contract')
data = json.loads((root / 'inputs/controlled4b/cases.json').read_text())
assert len(data['train']) == 812 and len(data['validation']) == 89
assert len({r['group'] for r in data['validation']}) == 75
normalize = lambda q: ' '.join(q.split()).casefold()
train = {normalize(r['q']) for r in data['train']}
assert not train & {normalize(r['q']) for r in data['validation']}
publication = json.loads((root / 'inputs/publication_eval/cases.json').read_text())
assert not train & {normalize(r['q']) for suite in ('knowledge', 'tools', 'behavior') for r in publication[suite]}
