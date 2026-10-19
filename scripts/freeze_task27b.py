"""Freeze tasks, source/calibration overlap and artifact file hashes before evaluation."""
import argparse
import hashlib
import json
from pathlib import Path
from task_cases27b import TRANSPORT, cases, debug_cases
from task_eval27b import schemas


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--artifacts', type=Path, default=Path('/mnt/data/artifacts/kvcompile/artifacts/agent'))
    a = p.parse_args()
    project = Path(__file__).resolve().parents[1]
    prompt = project / 'prompts/agent_resident.txt'
    schema = schemas(prompt.read_text())
    base = a.artifacts
    teacher = base / 'mixed27b_v1/teacher'
    calibration = base / 'position8k27b_v1/questions.json'
    items = json.loads(calibration.read_text())['items']
    texts = [str(i.get('q', i.get('question', ''))) + '\n' + str(i.get('answer_text', i.get('answer', ''))) for i in items]
    assert len(items) == 780 and all(t.strip() for t in texts)
    arms = {'full': teacher, 'none': teacher,
            'position8k': base / 'position8k27b_v1/compiled',
            'purpose4k': base / 'purpose4k27b_v1/compiled',
            'position4k': base / 'position4k27b_v1/compiled'}
    files = {str(prompt): digest(prompt), str(calibration): digest(calibration),
             str(teacher / 'state.json'): digest(teacher / 'state.json')}
    for root in set(arms.values()):
        paths = [root / 'state.safetensors'] if root == teacher else [root / 'manifest.json', *sorted(root.glob('layer_*.safetensors'))]
        if root != teacher:
            mf = json.loads(paths[0].read_text())
            assert mf['complete'] and len(paths) == 17 and mf['slots'] == (8192 if root.name == 'compiled' and root.parent.name == 'position8k27b_v1' else 4096)
        for path in paths:
            files[str(path)] = digest(path)
    for name in ('task_cases27b.py', 'task_eval27b.py', 'eval_tasks27b.py', 'freeze_task27b.py'):
        path = project / 'scripts' / name
        files[str(path)] = digest(path)
    for path in [project / 'scripts/eval_agent_exl3.py', project / 'src/exl3.py', project / 'src/prompt.py']:
        files[str(path)] = digest(path)
    model = Path('/home/arpin/exllamav3-rocm/models/Qwen3.8-27B-EXL3-3.5bpw')
    for name in ('config.json', 'quantization_config.json', 'tokenizer.json', 'tokenizer_config.json', 'model.safetensors.index.json'):
        files[str(model / name)] = digest(model / name)
    all_cases = cases()
    overlap = {}
    for c in all_cases:
        names = sorted({x['call'] for s in c['steps'] for x in s.get('accept', [])})
        overlap[c['id']] = {'tools': names, 'tool_mentions': {n: sum(n in t or n.removeprefix('mcp__github__') in t for t in texts) for n in names},
                             'exact_question_in_calibration': any(c['q'] in t for t in texts)}
        for n in names:
            assert n in schema
    payload = {'protocol': 'offline-json-tasks27b-v1', 'transport': TRANSPORT,
               'debug': debug_cases(), 'test': all_cases, 'overlap': overlap,
               'arms': {k: str(v) for k,v in arms.items()}, 'teacher': str(teacher),
               'prompt': str(prompt), 'files': files, 'max_tokens': 256, 'cap': 32768,
               'model': '/home/arpin/exllamav3-rocm/models/Qwen3.8-27B-EXL3-3.5bpw',
               'grader': 'exact accepted JSON calls/values; no extra fields; all steps; advice keyword rubric',
               'limits': '40 cases, 6 templated two-step cases; new task format, not 40 independent tool families; no native tool tokens, live services or end-to-end coding'}
    a.root.mkdir(parents=True, exist_ok=True)
    dest = a.root / 'frozen.json'
    text = json.dumps(payload, indent=2) + '\n'
    if dest.exists():
        assert dest.read_text() == text, 'frozen inputs changed; do not overwrite'
    else:
        dest.write_text(text)
    print(f'FROZEN tasks=40 arms=5 sha256={digest(dest)} artifact={dest}', flush=True)


if __name__ == '__main__':
    main()
