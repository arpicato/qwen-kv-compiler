"""Freeze/run three disjointly reported evaluations on unchanged 27B caches."""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

from clean_eval import code_check, knowledge, tool
from task_eval27b import continuation, schemas

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'inputs/clean_eval_v1/cases.json'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix('.partial')
    partial.write_text(json.dumps(data, indent=2)+'\n')
    partial.replace(path)


def freeze(path, artifacts, model, cases=CASES, am_artifacts=None, am_slots=(4096,8192)):
    if path.exists():
        raise ValueError('refusing to overwrite existing freeze')
    data = json.loads(cases.read_text())
    files = [cases, ROOT / 'inputs/joint/prompt.txt', ROOT / 'runtime.json',
             artifacts / 'teacher/state.json', artifacts / 'teacher/state.safetensors']
    files += sorted((ROOT / 'scripts').glob('*.py')) + sorted((ROOT / 'src').glob('*.py'))
    arms = {'full': str(artifacts / 'teacher'), 'none': str(artifacts / 'teacher')}
    for k in (4096, 8192):
        folder = artifacts / f'compiled{k}'
        m = json.loads((folder / 'manifest.json').read_text())
        if not m['complete'] or len(m['layers']) != 16 or m['slots'] != k:
            raise ValueError('incomplete or wrong cache')
        files += [folder / 'manifest.json', *sorted(folder.glob('layer_*.safetensors'))]
        arms['joint4k' if k == 4096 else 'joint8k'] = str(folder)
    if am_artifacts is not None:
        gate = am_artifacts/'gate-v2/gate.json'
        g = json.loads(gate.read_text())
        if not g['complete'] or not g['zero_beta_parity'] or not g['nonzero_roundtrip_exact']:
            raise ValueError('AM compatibility gate incomplete')
        if digest(artifacts/'teacher/state.safetensors') != g['identity']['teacher_sha256']:
            raise ValueError('AM recurrent/teacher state differs')
        files.append(gate)
        if not am_slots or len(set(am_slots)) != len(am_slots) or not set(am_slots) <= {4096,8192}:
            raise ValueError('invalid AM budgets')
        for k in am_slots:
            folder = am_artifacts/f'am{k}'
            m = json.loads((folder/'manifest.json').read_text())
            if not m['complete'] or m['slots'] != k or m['layers'] != list(range(3,64,4)):
                raise ValueError('AM fit incomplete or wrong budget/layers')
            if m['recipe']['gate_sha256'] != digest(gate):
                raise ValueError('AM fit/gate mismatch')
            fp32 = m['recipe'].get('values_dtype') == 'float32'
            if fp32:
                precision_gate=Path(m['recipe']['precision_gate'])
                if digest(precision_gate) != m['recipe']['precision_gate_sha256']:
                    raise ValueError('AM precision gate changed')
                pg=json.loads(precision_gate.read_text())
                if not pg['complete'] or not pg['nonzero_roundtrip_exact'] or not pg['promotion_ids_equal'] or pg['max_logit_diff'] > .25:
                    raise ValueError('AM precision gate incomplete')
                smoke_path=am_artifacts/'smoke.json'
                smoke=json.loads(smoke_path.read_text())
                if not smoke['complete'] or not smoke['recurrent_injection_exact'] or smoke['wrapper_sha256'] != digest(ROOT/'scripts/am27b_attention.py') or not any(r['slots']==k and r['roundtrip_exact'] and r['manifest_sha256']==digest(folder/'manifest.json') for r in smoke['rows']):
                    raise ValueError('AM FP32 all-layer smoke not accepted')
                files += [precision_gate,smoke_path]
            if set(m['files']) != {f'layer_{l:03d}.safetensors' for l in range(3,64,4)}:
                raise ValueError('AM export inventory incomplete')
            for name,h in m['files'].items():
                if digest(folder/name) != h:
                    raise ValueError('AM export changed')
            files += [folder/'manifest.json',*sorted(folder.glob('layer_*.safetensors'))]
            arms['am8k_fp32' if fp32 else 'am4k' if k==4096 else 'am8k'] = str(folder)
    runtime = json.loads((ROOT / 'runtime.json').read_text())
    for name, expected in {**runtime['weight_sha256'], **runtime['metadata_sha256']}.items():
        if digest(model / name) != expected:
            raise ValueError(f'model mismatch: {name}')
    save(path, dict(protocol=data['version'], frozen_utc=datetime.now(timezone.utc).isoformat(),
        source=str(ROOT), cases=str(cases), prompt=str(ROOT / 'inputs/joint/prompt.txt'),
        teacher=str(artifacts / 'teacher'), model=str(model), arms=arms,
        files={str(p): digest(p) for p in files}, code_image=runtime['docker_code_check_image']))
    print('DONE freeze', path, digest(path), flush=True)


def check_code(data, image, output):
    checked = []
    for c in data['behavior'] + data['debug']['behavior']:
        positive = code_check(c, '```python\n'+c['reference']+'```', 'eos', image)
        negative = code_check(c, '```python\n'+c['code']+'```', 'eos', image)
        if not positive['functional_pass'] or negative['functional_pass']:
            raise ValueError((c['id'], positive, negative))
        checked.append(dict(id=c['id'], positive=positive, negative=negative))
        print('PASS reference and unchanged-code negative', c['id'], flush=True)
    save(output, dict(complete=True, rows=checked))


def run(frozen_path, out, split, arms, selected_suites=None):
    started = time.time()
    f = json.loads(frozen_path.read_text())
    for name, expected in f['files'].items():
        if digest(name) != expected:
            raise ValueError(f'frozen file changed: {name}')
    if len(set(arms)) != len(arms) or not set(arms) <= f['arms'].keys():
        raise ValueError('invalid arms')
    data = json.loads(Path(f['cases']).read_text())
    if data['version'] in ('natural-refactors-v3', 'transplant-refactors-v4'):
        data = dict(data, knowledge=[], tools=[], behavior=data['cases'],
                    cap=32768, n_sys=26341, limits={'behavior': data['max_tokens']})
        if split != 'test':
            raise ValueError('targeted refactor banks have no model-debug split')
    suites = data['debug'] if split == 'debug' else data
    if selected_suites is not None:
        if not selected_suites or not set(selected_suites) <= {'knowledge', 'tools', 'behavior'}:
            raise ValueError('invalid selected suites')
        suites = {s: rows if s in selected_suites else [] for s, rows in suites.items()}
    config = dict(freeze_sha256=digest(frozen_path), split=split, arms=arms)
    if selected_suites is not None:
        config['suites'] = selected_suites
    result = dict(config=config, complete=False, elapsed_s=0,
                  rows={a: {s: [] for s in ('knowledge', 'tools', 'behavior')} for a in arms})
    if out.exists():
        result = json.loads(out.read_text())
        if result['config'] != config:
            raise ValueError('resume identity mismatch')
    for arm in arms:
        if set(result['rows'][arm]) != {'knowledge', 'tools', 'behavior'}:
            raise ValueError('resume suites mismatch')
        for suite, rows in result['rows'][arm].items():
            if [r['id'] for r in rows] != [c['id'] for c in suites[suite][:len(rows)]]:
                raise ValueError('resume case IDs mismatch')
            if result['complete'] and len(rows) != len(suites[suite]):
                raise ValueError('completed result has incomplete cases')
    if result['complete']:
        print('Already complete', out, flush=True)
        return
    import torch
    from safetensors.torch import load_file
    sys.path.insert(0, str(ROOT / 'src'))
    import exl3
    import prompt as P
    from eval_agent_exl3 import gen_greedy, install_prefix, load_compiled
    model, cache, tok, _ = exl3.load(f['model'], max_seq_len=data['cap'], cache_size=data['cap'])
    body = Path(f['prompt']).read_text().rstrip()
    n_sys = len(exl3.encode(tok, P.system_block(body)))
    if n_sys != data['n_sys']:
        raise ValueError('prefix token mismatch')
    schema = schemas(body)
    st = load_file(str(Path(f['teacher']) / 'state.safetensors'))
    delta = {str(i): {k: st[f'delta.{i}.{k}'] for k in ('conv_state', 'recurrent_state')} for i in exl3.recurrent_layers(model)}
    attn = {str(i): {'keys': st[f'attn.{i}.keys'], 'values': st[f'attn.{i}.values'],
            'offset': int(st[f'attn.{i}.offset'][0])} for i in exl3.full_attn_layers(model)}
    prior = result['elapsed_s']
    total = len(arms)*sum(len(suites[s]) for s in ('knowledge', 'tools', 'behavior'))
    initial = sum(len(rows) for by_suite in result['rows'].values() for rows in by_suite.values())
    done = initial
    for arm in arms:
        compiled, slots = None, None
        biases = None
        values = None
        if arm not in ('full', 'none'):
            folder = Path(f['arms'][arm])
            slots = json.loads((folder / 'manifest.json').read_text())['slots']
            if arm == 'am8k_fp32':
                from am27b_attention import load_fp32_prefix
                compiled,biases,values=load_fp32_prefix(folder,slots)
            else:
                compiled = load_compiled(folder, slots)
            if set(compiled) != set(exl3.full_attn_layers(model)):
                raise ValueError('wrong compiled layers')
            if arm in ('am4k','am8k'):
                biases = {l:load_file(str(folder/f'layer_{l:03d}.safetensors'))['beta'][0] for l in compiled}
                if any(b.shape != (4,slots) or not torch.isfinite(b).all() for b in biases.values()):
                    raise ValueError('invalid AM beta')
        def generate(history, limit):
            logical, physical = install_prefix(model, cache,
                'teacher' if arm == 'full' else 'none' if arm == 'none' else 'compiled',
                n_sys=n_sys, delta=delta, attn=attn, compiled=compiled, K=slots)
            ids = exl3.encode(tok, history)
            if physical + len(ids) + limit > data['cap']:
                raise ValueError('physical cache capacity exceeded')
            from am27b_attention import prefix_bias
            with prefix_bias(biases,values) if biases is not None else nullcontext():
                ids, text, stop, _ = gen_greedy(model, cache, tok, ids, cap=data['cap'],
                    logical_pos=logical, physical_len=physical, max_tokens=limit)
            return dict(pred=text, stop=stop, tokens=len(ids))
        for suite in ('knowledge', 'tools', 'behavior'):
            for c in suites[suite][len(result['rows'][arm][suite]):]:
                history = P.user_turn(c['q']+(data['transport'] if suite == 'tools' else ''), think=False)
                row = dict(id=c['id'], category=c.get('category', c.get('kind')))
                if suite == 'tools':
                    trace = []
                    for expected in c['steps']:
                        generated = generate(history, data['limits'][suite])
                        generated.update(tool(generated['pred'], expected, schema, generated['stop']))
                        trace.append(generated)
                        if not generated['correct']:
                            break
                        if expected.get('reply') is not None:
                            history = continuation(history, generated['pred'], expected)
                    row.update(trace=trace, correct=len(trace)==len(c['steps']) and all(t['correct'] for t in trace),
                               expected_steps=len(c['steps']))
                else:
                    row.update(generate(history, data['limits'][suite]))
                    if suite == 'knowledge':
                        row.update(knowledge(row['pred'], c['answers'], row['stop']))
                    else:
                        row['code_check'] = code_check(c, row['pred'], row['stop'], f['code_image'])
                result['rows'][arm][suite].append(row)
                result['elapsed_s'] = prior + time.time()-started
                save(out, result)
                done += 1
                elapsed = time.time()-started
                rate = (done-initial)/max(elapsed, .001)
                print(f'{datetime.now(timezone.utc).isoformat()} elapsed={elapsed:.1f}s completed={done}/{total} rate={rate:.3f}/s ETA={(total-done)/max(rate,.001):.1f}s arm={arm} suite={suite} id={c["id"]}', flush=True)
        del compiled
    result['complete'] = True
    save(out, result)
    print(f'DONE total_duration={result["elapsed_s"]:.3f}s artifact={out}', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('freeze', 'check-code', 'run'))
    p.add_argument('--freeze', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--artifacts', type=Path)
    p.add_argument('--model', type=Path)
    p.add_argument('--image', default='kvcompile-checks:repro')
    p.add_argument('--cases', type=Path, default=CASES)
    p.add_argument('--split', choices=('debug', 'test'), default='debug')
    p.add_argument('--arms', default='full,none,joint4k,joint8k')
    a = p.parse_args()
    if a.command == 'freeze':
        if not all((a.freeze, a.artifacts, a.model)):
            p.error('freeze needs --freeze --artifacts --model')
        freeze(a.freeze, a.artifacts.resolve(), a.model.resolve(), a.cases.resolve())
    elif a.command == 'check-code':
        if a.out is None:
            p.error('check-code needs --out')
        check_code(json.loads(a.cases.read_text()), a.image, a.out)
    else:
        if a.freeze is None or a.out is None:
            p.error('run needs --freeze --out')
        run(a.freeze, a.out, a.split, a.arms.split(','))
