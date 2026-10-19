"""Publication CLI verifies current inputs/results without a GPU or Git history."""
import json
import runpy
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
final = subprocess.run([sys.executable, str(root / 'scripts/evaluate.py'), 'verify'],
                       check=True, capture_output=True, text=True, timeout=60)
current = json.loads(final.stdout)
assert current['counts'] == {'knowledge': 60, 'tools': 60, 'behavior': 120}
assert current['studies']['27b']['tasks']['joint8k']['tools'] == 56
assert current['studies']['27b']['behavior']['joint8k']['rule_shared']['joint'] == 37
assert current['studies']['27b']['behavior']['am8k_fp32']['rule_shared']['joint'] == 29
assert current['studies']['4b']['tasks']['am']['knowledge'] == 35
assert all(s['rule_shared']['joint'] == 0 for s in current['studies']['4b']['behavior'].values())
result = subprocess.run([sys.executable, str(root / 'scripts/evaluate.py'), 'verify',
                         '--cases', str(root / 'inputs/publication_eval/cases.json')],
                        check=True, capture_output=True, text=True, timeout=60)
data = json.loads(result.stdout)
assert data['complete'] and data['counts'] == {'knowledge': 60, 'tools': 60, 'behavior': 40}
assert data['scores']['full'] == {'knowledge': 60, 'tools': 59, 'behavior': 33}
assert data['scores']['none'] == {'knowledge': 28, 'tools': 2, 'behavior': 0}
assert data['scores']['joint4k'] == {'knowledge': 46, 'tools': 51, 'behavior': 18}
assert data['scores']['joint8k'] == {'knowledge': 55, 'tools': 56, 'behavior': 36}
assert data['same_artifact_hashes'] and data['same_prompt_hash']
saved = root / 'results/PUBLICATION_EVAL_SUMMARY.json'
if saved.exists():
    assert json.loads(saved.read_text()) == data
preflight = root / 'results/PUBLICATION_EVAL_PREFLIGHT.json'
if preflight.exists():
    checked = json.loads(preflight.read_text())
    assert checked['complete'] and len(checked['rows']) == 40
    assert all(r['positive']['functional_pass'] and not r['negative']['functional_pass'] for r in checked['rows'])
sys.path.insert(0, str(root / 'scripts'))
import evaluate as e
from run_clean_eval import digest, run

# Reused 27B task scores require the final runs to keep the same actual cache bytes.
original_loads=e.json.loads
def changed_cache(text, *a, **kw):
    d=original_loads(text, *a, **kw)
    if isinstance(d,dict) and d.get('frozen_utc') and d.get('protocol')=='publication-final-v1':
        d['files'][d['teacher']+'/state.safetensors']='0'*64
    return d
with patch.object(e.json, 'loads', side_effect=changed_cache):
    try: e.verify()
    except ValueError as error: assert 'artifact differs' in str(error)
    else: raise AssertionError('accepted reused tasks with different final teacher')

# Freeze/run resume can be checked without importing Torch or loading a model.
with tempfile.TemporaryDirectory() as directory:
    out = Path(directory)
    frozen = out / 'freeze.json'
    frozen.write_text(json.dumps({'cases': str(e.CASES), 'protocol': 'publication-final-v1', 'model': '/external/model',
        'files': {str(e.CASES): digest(e.CASES)}, 'arms': {'full': '/external/teacher'}}))
    cases = json.loads(e.CASES.read_text())
    result = out / 'raw.json'
    result.write_text(json.dumps({'config': {'freeze_sha256': digest(frozen), 'split': 'test', 'arms': ['full']},
        'complete': True, 'rows': {'full': {s: [{'id': c['id']} for c in cases[s]]
                                         for s in ('knowledge', 'tools', 'behavior')}}}))
    with patch.dict(sys.modules, {'torch': None, 'exl3': None}):
        run(frozen, result, 'test', ['full'])
        selected = out / 'selected.json'
        selected.write_text(json.dumps({'config': {'freeze_sha256': digest(frozen), 'split': 'test',
            'arms': ['full'], 'suites': ['behavior']}, 'complete': True, 'rows': {'full': {
                'knowledge': [], 'tools': [], 'behavior': [{'id': c['id']} for c in cases['behavior']]}}}))
        run(frozen, selected, 'test', ['full'], ['behavior'])
    tampered = json.loads(result.read_text())
    tampered['rows']['full']['behavior'][0]['id'] = 'different-case'
    result.write_text(json.dumps(tampered))
    try:
        run(frozen, result, 'test', ['full'])
    except ValueError as error:
        assert 'case IDs' in str(error)
    else:
        raise AssertionError('resume accepted modified case IDs')
    tampered['rows']['full']['behavior'] = []
    result.write_text(json.dumps(tampered))
    try:
        run(frozen, result, 'test', ['full'])
    except ValueError as error:
        assert 'incomplete' in str(error)
    else:
        raise AssertionError('resume accepted complete flag with missing cases')
    with patch('reproduce.check_runtime', side_effect=ValueError('runtime mismatch')), \
         patch('run_clean_eval.run') as generate, \
         patch.object(sys, 'argv', ['evaluate.py', 'run', '--freeze', str(frozen), '--out', str(result)]):
        try:
            runpy.run_path(str(root / 'scripts/evaluate.py'), run_name='__main__')
        except ValueError as error:
            assert str(error) == 'runtime mismatch'
        else:
            raise AssertionError('publication CLI skipped runtime validation')
        generate.assert_not_called()
bad = subprocess.run([sys.executable, str(root / 'scripts/evaluate.py'), 'run'],
                     capture_output=True, text=True, timeout=10)
assert bad.returncode != 0 and '--freeze' in bad.stderr
with patch('compare4b.evaluate') as hf, patch.object(sys, 'argv', ['evaluate.py', 'run',
        '--backend', 'hf4b', '--model', '/model', '--capture', '/capture', '--arm', 'full',
        '--cases', str(root / 'inputs/publication_final/cases.json'), '--out', '/unused.json']):
    runpy.run_path(str(root / 'scripts/evaluate.py'), run_name='__main__')
    hf.assert_called_once()
    assert hf.call_args.args[0].cases.name == 'cases.json'
print('PASS final240case CLI, both studies/AM, legacy provenance, resume identities and required arguments')
