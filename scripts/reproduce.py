"""Redo the frozen joint experiment from tracked inputs on the pinned ROCm target.

No historical artifact directory is read. Model weights/runtime are the only
external prerequisites. Commands checkpoint layers/questions; failed phases resume.
"""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from freeze_task27b import digest

PROJECT = Path(__file__).resolve().parents[1]


def atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix('.partial')
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    partial.replace(path)


def verify_inputs():
    manifest = json.loads((PROJECT / 'inputs/manifest.json').read_text())
    for name, record in manifest.items():
        path = PROJECT / 'inputs' / name
        if not path.is_file() or digest(path) != record['sha256']:
            raise ValueError(f'published input changed: {name}')
    items = json.loads((PROJECT / 'inputs/joint/questions.json').read_text())['items']
    gate = json.loads((PROJECT / 'inputs/joint/gate.json').read_text())['probes']
    if len(items) != 812 or len(gate) != 24:
        raise ValueError('wrong calibration/evaluation counts')
    if {x['q'] for x in items} & {x['q'] for x in gate}:
        raise ValueError('exact calibration/evaluation overlap')
    return manifest


def phases(out, model):
    """Pure command plan; used by regression tests before any GPU work."""
    inputs = PROJECT / 'inputs'
    scripts = PROJECT / 'scripts'
    prompt = inputs / 'joint/prompt.txt'
    teacher = out / 'teacher'
    def cmd(script, *args):
        return [sys.executable, '-B', str(scripts / script), *map(str, args)]
    capture = cmd('capture_agent_exl3.py', '--model', model, '--items', inputs / 'joint/questions.json',
        '--out', out / 'traj', '--prompt-file', prompt, '--teacher-out', teacher,
        '--verify-roundtrip', '--checkpoint-every', 5, '--resume')
    jobs = [('capture812', capture), ('projections', cmd('export_oproj_exl3.py', '--model', model, '--out', out / 'oproj'))]
    def fit(traj, dest, slots, steps, lr, sampling, init=None):
        args = ['--traj', traj, '--out', dest, '--slots', slots, '--steps', steps,
                '--lr', lr, '--cosine-weight', 1, '--batched', '--batch-chunk', 4,
                '--freeze-sink', '--gate-weight', '--examples-per-update', 72,
                '--sampling-plan', sampling, '--kv-dtype', 'bfloat16',
                '--oproj-dir', out / 'oproj', '--seed', 0, '--log-every', 25, '--resume']
        if init is not None:
            args += ['--init-from-dir', init]
        return cmd('compile_torch_v2.py', *args)
    for k in (4096, 8192):
        jobs.append((f'fit{k}', fit(out / 'traj', out / f'compiled{k}', k, 400, .001, inputs / 'joint/sampling.json')))
    def evaluate(name, compiled, probes, arms, tokens):
        return cmd('eval_agent_exl3.py', '--model', model, '--teacher', teacher,
            '--prompt-file', prompt, '--compiled', compiled, '--probeset', probes,
            '--arms', arms, '--max-tokens', tokens, '--out', out / (name + '.json'), '--resume')
    for suite, tokens in (('agent78', 64), ('stress197', 64), ('gate', 768)):
        for k in (4096, 8192):
            name = f'{suite}_{k}'
            jobs.append((name, evaluate(name, out / f'compiled{k}', inputs / 'joint' / (suite + '.json'),
                'teacher,none,compiled' if k == 4096 else 'compiled', tokens)))
    jobs += [('freeze_tasks', cmd('reproduce.py', 'freeze-tasks', '--out', out, '--model', model)),
             ('tasks', cmd('eval_tasks27b.py', '--frozen', out / 'tasks_frozen.json',
                '--out', out / 'tasks.json', '--split', 'test', '--arms', 'full,none,joint4k,joint8k'))]
    continuation = out / 'continuation'
    jobs += [('capture64', cmd('capture_agent_exl3.py', '--model', model,
        '--items', inputs / 'continuation/fresh.json', '--position-plan', inputs / 'continuation/positions.json',
        '--out', continuation / 'fresh_traj', '--prompt-file', prompt, '--teacher-in', teacher,
        '--verify-roundtrip', '--checkpoint-every', 5, '--resume')),
        ('merge64', cmd('prepare_policy_coverage_continue27b.py', '--root', continuation, '--reference', out))]
    for arm in ('control', 'candidate'):
        traj = out / 'traj' if arm == 'control' else continuation / 'traj'
        jobs.append((f'continue_{arm}', fit(traj, continuation / arm, 4096, 80, .00025,
                    continuation / f'{arm}_sampling.json', out / 'compiled4096')))
        name = f'continuation_{arm}'
        jobs.append((name, evaluate(name, continuation / arm, inputs / 'joint/gate.json', 'compiled', 768)))
    jobs.append(('summarize', cmd('reproduce.py', 'summarize', '--out', out, '--model', model)))
    return jobs


def check_runtime(model):
    config = json.loads((PROJECT / 'runtime.json').read_text())
    if platform.python_version() != config['python']:
        raise ValueError(f'expected Python{config["python"]}, found {platform.python_version()}')
    for package in ('torch', 'numpy', 'safetensors', 'tokenizers'):
        if importlib.metadata.version(package) != config[package]:
            raise ValueError(f'wrong runtime package: {package}')
    runtime = Path(os.environ['EXLLAMAV3_PATH']).resolve()
    commit = subprocess.check_output(['git', '-C', str(runtime), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != config['runtime_commit']:
        raise ValueError('wrong ExLlamaV3 runtime commit')
    dirty = subprocess.check_output(['git', '-C', str(runtime), 'diff', '--name-only', 'HEAD'], text=True)
    if dirty.strip():
        raise ValueError('runtime tracked source has local changes')
    for name, expected in config['weight_sha256'].items():
        print(f'{datetime.now(timezone.utc).isoformat()} hashing external weight {name}', flush=True)
        if digest(model / name) != expected:
            raise ValueError(f'model weight differs: {name}')
    for name, expected in config.get('metadata_sha256', {}).items():
        if digest(model / name) != expected:
            raise ValueError(f'model metadata differs: {name}')
    return {'python': platform.python_version(), 'runtime_commit': commit,
            'packages': {n: importlib.metadata.version(n) for n in ('torch', 'numpy', 'safetensors', 'tokenizers')}}


def freeze_tasks(out, model):
    frozen = json.loads((PROJECT / 'inputs/joint/tasks.json').read_text())
    frozen.update(n_sys=26341, prompt=str(PROJECT / 'inputs/joint/prompt.txt'),
                  teacher=str(out / 'teacher'), model=str(model),
                  arms={'full': str(out / 'teacher'), 'none': str(out / 'teacher'),
                        'joint4k': str(out / 'compiled4096'), 'joint8k': str(out / 'compiled8192')})
    paths = [PROJECT / 'inputs/joint/tasks.json', PROJECT / 'inputs/joint/prompt.txt',
             out / 'teacher/state.safetensors', out / 'teacher/state.json']
    for k in (4096, 8192):
        root = out / f'compiled{k}'
        manifest = json.loads((root / 'manifest.json').read_text())
        if not manifest['complete'] or len(manifest['layers']) != 16 or manifest['slots'] != k:
            raise ValueError('incomplete compiled cache')
        paths += [root / 'manifest.json', *sorted(root.glob('layer_*.safetensors'))]
    paths += list((PROJECT / 'scripts').glob('*.py')) + list((PROJECT / 'src').glob('*.py'))
    frozen['files'] = {str(p): digest(p) for p in sorted(paths)}
    path = out / 'tasks_frozen.json'
    if path.exists() and json.loads(path.read_text()) != frozen:
        raise ValueError('task freeze identity changed')
    atomic(path, frozen)


def summarize(out):
    result = {'complete': True, 'probes': {}, 'behavior_structure': {}, 'tasks': {}, 'continuation': {}}
    from task_eval27b import grade, schemas
    from review_long_policy27b import review
    schema = schemas((PROJECT / 'inputs/joint/prompt.txt').read_text())
    cases = json.loads((PROJECT / 'inputs/joint/gate.json').read_text())['probes']
    image = json.loads((PROJECT / 'runtime.json').read_text())['docker_code_check_image']
    for suite in ('agent78', 'stress197', 'gate'):
        for k in (4096, 8192):
            d = json.loads((out / f'{suite}_{k}.json').read_text())
            if not d['summary']['complete']:
                raise ValueError('incomplete generation output')
            if suite == 'gate':
                checked = {a: review(cases, rows, image) for a, rows in d['rows'].items()}
                atomic(out / f'gate_{k}_code.json', checked)
                result['behavior_structure'][str(k)] = {a: {
                    'refactor_structure': sum(r['behavior'] is True for r in rows),
                    'refactor_checks': sum(r['code_ok'] is True for r in rows),
                    'money_manual_review_required': 12} for a, rows in checked.items()}
            else:
                result['probes'][f'{suite}_{k}'] = {a: {'correct': sum(r['ok'] for r in rows),
                    'n': len(rows), 'caps': sum(r['stop'] == 'cap' for r in rows)} for a, rows in d['rows'].items()}
    tasks = json.loads((out / 'tasks.json').read_text())
    frozen = json.loads((out / 'tasks_frozen.json').read_text())
    if not tasks['complete']:
        raise ValueError('incomplete task outputs')
    for arm, rows in tasks['rows'].items():
        if len(rows) != len(frozen['test']):
            raise ValueError('incomplete tasks')
        for case, row in zip(frozen['test'], rows):
            assert row['id'] == case['id']
            for i, tr in enumerate(row['trace']):
                ok, reason = grade(tr['pred'], case['steps'][i], schema)
                assert tr['ok'] == (ok and tr['stop'] != 'cap')
                assert tr['reason'] == ('cap' if tr['stop'] == 'cap' else reason)
                assert i == len(row['trace'])-1 or tr['ok']
            assert row['ok'] == (len(row['trace']) == len(case['steps']) and all(t['ok'] for t in row['trace']))
        result['tasks'][arm] = {'correct': sum(r['ok'] for r in rows), 'n': len(rows)}
    for arm in ('control', 'candidate'):
        d = json.loads((out / f'continuation_{arm}.json').read_text())
        checked = review(cases, d['rows']['compiled'], image)
        atomic(out / f'continuation_{arm}_code.json', checked)
        result['continuation'][arm] = {'refactor_structure': sum(r['behavior'] is True for r in checked),
            'refactor_checks': sum(r['code_ok'] is True for r in checked), 'money_manual_review_required': 12}
    atomic(out / 'summary.json', result)
    print(json.dumps(result, indent=2), flush=True)


def phase_outputs(out, name):
    if name == 'capture812':
        paths = [out / 'traj/meta.json', out / 'teacher/state.json', out / 'teacher/state.safetensors',
                 *sorted((out / 'traj').glob('layer_*.pkl'))]
    elif name == 'projections':
        paths = sorted((out / 'oproj').glob('oproj_L*.pt'))
    elif name.startswith('fit'):
        root = out / ('compiled' + name[3:])
        paths = [root / 'manifest.json', *sorted(root.glob('layer_*.safetensors'))]
    elif name == 'capture64':
        root = out / 'continuation/fresh_traj'
        paths = [root / 'meta.json', *sorted(root.glob('layer_*.pkl'))]
    elif name == 'merge64':
        root = out / 'continuation'
        paths = [root / 'merge_result.json', root / 'traj/meta.json', root / 'questions.json',
                 root / 'control_sampling.json', root / 'candidate_sampling.json',
                 *sorted((root / 'traj').glob('layer_*.pkl'))]
    elif name.startswith('continue_'):
        root = out / 'continuation' / name.removeprefix('continue_')
        paths = [root / 'manifest.json', *sorted(root.glob('layer_*.safetensors'))]
    else:
        paths = [out / ({'freeze_tasks': 'tasks_frozen', 'summarize': 'summary'}.get(name, name) + '.json')]
    if not paths or not all(p.is_file() for p in paths):
        raise ValueError(f'missing phase outputs: {name}')
    return paths


def run(out, model):
    started = time.time()
    verify_inputs()
    release = json.loads((PROJECT / 'RELEASE.json').read_text())
    for name, expected in release.items():
        if digest(PROJECT / name) != expected:
            raise ValueError(f'release source changed: {name}')
    out.mkdir(parents=True, exist_ok=True)
    if PROJECT == out or PROJECT in out.parents:
        raise ValueError('output must be outside the source snapshot')
    identity = {'release_sha256': digest(PROJECT / 'RELEASE.json'), 'model': str(model), 'source': str(PROJECT)}
    config_path = out / 'run.json'
    if config_path.exists():
        state = json.loads(config_path.read_text())
        if state['identity'] != identity:
            raise ValueError('resume source/model identity differs')
    else:
        if any(out.iterdir()):
            raise ValueError('fresh output directory must be empty')
        state = {'identity': identity, 'complete': False, 'phases': {}}
    state['runtime'] = check_runtime(model)
    image = json.loads((PROJECT / 'runtime.json').read_text())['docker_code_check_image']
    state['code_check_image_id'] = subprocess.check_output(
        ['docker', 'image', 'inspect', '--format', '{{.Id}}', image], text=True).strip()
    atomic(config_path, state)
    # Preserve input bytes/relative layout for the existing merge helper.
    for src, dst in [(PROJECT / 'inputs/joint/questions.json', out / 'questions.json'),
                     (PROJECT / 'inputs/continuation/fresh.json', out / 'continuation/fresh.json'),
                     (PROJECT / 'inputs/continuation/positions.json', out / 'continuation/positions.json')]:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and digest(dst) != digest(src):
            raise ValueError(f'copied input changed: {dst}')
        shutil.copyfile(src, dst)
    jobs = phases(out, model)
    for i, (name, command) in enumerate(jobs, 1):
        if name in state['phases']:
            for path, expected in state['phases'][name]['outputs'].items():
                if digest(path) != expected:
                    raise ValueError(f'completed phase output changed: {path}')
            print(f'verified completed phase {name}; skip', flush=True)
            continue
        phase_start = time.time()
        print(f'{datetime.now(timezone.utc).isoformat()} phase={name} completed={i-1}/{len(jobs)} elapsed={time.time()-started:.1f}s', flush=True)
        process = subprocess.Popen(command, cwd=PROJECT)
        while True:
            try:
                returncode = process.wait(timeout=60)
                if returncode:
                    raise subprocess.CalledProcessError(returncode, command)
                break
            except subprocess.TimeoutExpired:
                print(f'{datetime.now(timezone.utc).isoformat()} phase={name} child_pid={process.pid} phase_elapsed={time.time()-phase_start:.1f}s completed={i-1}/{len(jobs)}', flush=True)
        # Hash each phase's durable outputs before allowing a later resume to skip it.
        outputs = phase_outputs(out, name)
        state['phases'][name] = {'elapsed_s': time.time()-phase_start, 'command': command,
            'outputs': {str(p): digest(p) for p in outputs}}
        atomic(config_path, state)
    state.update(complete=True, measured_phase_s=sum(p['elapsed_s'] for p in state['phases'].values()))
    atomic(config_path, state)
    print(f'DONE total_duration={time.time()-started:.3f}s artifact={out}', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=('plan', 'run', 'freeze-tasks', 'summarize'))
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    a = p.parse_args()
    out, model = a.out.resolve(), a.model.resolve()
    if a.phase == 'plan':
        verify_inputs()
        print(json.dumps(phases(out, model), indent=2))
    elif a.phase == 'freeze-tasks':
        freeze_tasks(out, model)
    elif a.phase == 'summarize':
        summarize(out)
    else:
        run(out, model)
