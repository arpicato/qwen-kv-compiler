"""Frozen tool regression evaluation of existing joint catalog/behavior caches."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

from freeze_task27b import digest
from task_eval27b import grade, schemas


def write(path, payload):
    text = json.dumps(payload, indent=2, sort_keys=True) + '\n'
    if path.exists():
        assert path.read_text() == text, f'frozen input changed: {path}'
    else:
        path.write_text(text)


def prepare(root, artifacts):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from probesets import load_probeset
    old = artifacts / 'long_policy4k27b_v1'
    source = artifacts / 'task27b_v1/frozen.json'
    frozen = json.loads(source.read_text())
    items = json.loads((old / 'questions.json').read_text())['items']
    assert len(items) == 812
    assert json.loads((old / 'traj/meta.json').read_text())['meta']['n_sys'] == 26341
    root.mkdir(parents=True, exist_ok=True)
    frozen.update(protocol='joint-tools27b-v1', n_sys=26341,
                  prompt=str(old / 'prompt.txt'), teacher=str(old / 'teacher'),
                  arms={'full': str(old / 'teacher'), 'none': str(old / 'teacher'),
                        'joint4k': str(old / 'compiled'),
                        'joint8k': str(artifacts / 'long_policy8k27b_v1/compiled')})
    schema = schemas(Path(frozen['prompt']).read_text())
    texts = [r['q'] + '\n' + r.get('answer_text', r['answer']) for r in items]
    for case in frozen['test']:
        names = frozen['overlap'][case['id']]['tools']
        assert all(name in schema for name in names)
        assert all(case['q'] != r['q'] for r in items)
        frozen['overlap'][case['id']] = {
            'tools': names,
            'tool_mentions': {n: sum(n in t or n.removeprefix('mcp__github__') in t for t in texts) for n in names},
            'exact_question_in_calibration': False}
    paths = [source, old / 'questions.json', Path(frozen['prompt']), old / 'teacher/state.json',
             old / 'teacher/state.safetensors']
    for arm in ('joint4k', 'joint8k'):
        compiled = Path(frozen['arms'][arm])
        mf = json.loads((compiled / 'manifest.json').read_text())
        assert mf['complete'] and mf['slots'] == (4096 if arm == 'joint4k' else 8192)
        assert mf['steps'] == 400 and mf['init_from_dir'] is None
        layers = sorted(compiled.glob('layer_*.safetensors'))
        assert len(layers) == 16
        paths += [compiled / 'manifest.json', *layers]
    code = Path(__file__).resolve().parent
    paths += [code / n for n in ('joint_tools27b.py', 'eval_agent_exl3.py', 'eval_tasks27b.py',
                                 'task_eval27b.py', 'freeze_task27b.py', 'task_cases27b.py')]
    paths += sorted((code.parent / 'src').glob('*.py'))
    paths += [Path(frozen['model']) / n for n in ('config.json', 'quantization_config.json',
                                                'tokenizer.json', 'tokenizer_config.json')]
    for name in ('agent78', 'stress197'):
        baseline = artifacts / 'position8k27b_v1' / f'{name}_candidate.json'
        data = json.loads(baseline.read_text())
        rows = data['rows']['teacher']
        assert len(rows) == (78 if name == 'agent78' else 197)
        probes = load_probeset('agent' if name == 'agent78' else str(artifacts / 'probes_agent_heldout.json'))
        assert [(p['q'], p['answer'], p['kind']) for p in probes] == [(r['q'], r['answer'], r['kind']) for r in rows]
        assert all(p['q'] != r['q'] for p in probes for r in items)
        dest = root / f'{name}.json'
        write(dest, {'probes': probes})
        paths += [baseline, dest]
    frozen['files'] = {str(p): digest(p) for p in sorted(set(paths))}
    write(root / 'frozen.json', frozen)
    print(f'FROZEN joint tools: 275 probes, 40 tasks, four task arms; artifact={root}', flush=True)


def run(root):
    frozen = json.loads((root / 'frozen.json').read_text())
    for path, expected in frozen['files'].items():
        assert digest(path) == expected, path
    code = Path(__file__).resolve().parent
    started = time.time()
    commands = []
    for suite in ('agent78', 'stress197'):
        for arm in ('joint4k', 'joint8k'):
            commands.append([sys.executable, '-B', str(code / 'eval_agent_exl3.py'),
                '--teacher', frozen['teacher'], '--prompt-file', frozen['prompt'],
                '--model', frozen['model'], '--compiled', frozen['arms'][arm],
                '--probeset', str(root / f'{suite}.json'),
                '--arms', 'teacher,none,compiled' if arm == 'joint4k' else 'compiled',
                '--out', str(root / f'{suite}_{arm}.json'), '--resume'])
    commands.append([sys.executable, '-B', str(code / 'eval_tasks27b.py'),
        '--frozen', str(root / 'frozen.json'), '--out', str(root / 'tasks.json'),
        '--split', 'test', '--arms', 'full,none,joint4k,joint8k'])
    for i, cmd in enumerate(commands, 1):
        print(f'{datetime.now(timezone.utc).isoformat()} phase={i}/{len(commands)} elapsed={time.time()-started:.1f}s', flush=True)
        subprocess.run(cmd, check=True)
    summarize(root)
    print(f'DONE total_duration={time.time()-started:.3f}s artifact={root}', flush=True)


def summarize(root):
    frozen = json.loads((root / 'frozen.json').read_text())
    tasks = json.loads((root / 'tasks.json').read_text())
    assert tasks['complete'] and tasks['config']['frozen_sha256'] == digest(root / 'frozen.json')
    result = {'complete': True, 'probes': {}, 'tasks': {}, 'elapsed_s': tasks['elapsed_s']}
    schema = schemas(Path(frozen['prompt']).read_text())
    for arm, rows in tasks['rows'].items():
        assert len(rows) == len(frozen['test']) == 40
        for case, row in zip(frozen['test'], rows):
            assert case['id'] == row['id']
            assert 1 <= len(row['trace']) <= len(case['steps'])
            for i, trace in enumerate(row['trace']):
                ok, reason = grade(trace['pred'], case['steps'][i], schema)
                assert trace['ok'] == (ok and trace['stop'] != 'cap')
                assert trace['reason'] == ('cap' if trace['stop'] == 'cap' else reason)
                assert i == len(row['trace']) - 1 or trace['ok']
            assert row['ok'] == (len(row['trace']) == len(case['steps']) and all(t['ok'] for t in row['trace']))
        result['tasks'][arm] = {'correct': sum(r['ok'] for r in rows), 'n': 40,
            'by_kind': {kind: sum(r['ok'] for r in rows if r['kind'] == kind) for kind in sorted({r['kind'] for r in rows})},
            'failures': [r['id'] for r in rows if not r['ok']],
            'caps': sum(t['stop'] == 'cap' for r in rows for t in r['trace'])}
    for suite in ('agent78', 'stress197'):
        arms = {}
        for arm in ('joint4k', 'joint8k'):
            data = json.loads((root / f'{suite}_{arm}.json').read_text())
            assert data['summary']['complete']
            result['elapsed_s'] += data['summary']['elapsed_s']
            probes = json.loads((root / f'{suite}.json').read_text())['probes']
            for label, rows in data['rows'].items():
                assert [(r['q'], r['answer']) for r in rows] == [(p['q'], p['answer']) for p in probes]
                arms[arm if label == 'compiled' else label] = {
                    'correct': sum(r['ok'] for r in rows), 'n': len(rows),
                    'caps': sum(r['stop'] == 'cap' for r in rows),
                    'by_kind': {kind: sum(r['ok'] for r in rows if r['kind'] == kind) for kind in sorted({r['kind'] for r in rows})}}
        result['probes'][suite] = arms
    (root / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=('prepare', 'run', 'summarize'))
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--artifacts', type=Path)
    a = p.parse_args()
    if a.phase == 'prepare':
        if a.artifacts is None:
            p.error('--artifacts is required for prepare')
        prepare(a.root, a.artifacts)
    elif a.phase == 'run':
        run(a.root)
    else:
        summarize(a.root)
