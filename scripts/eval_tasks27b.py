#!/usr/bin/env python3
"""Resumable frozen-cache offline task execution; no network tools."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

from freeze_task27b import digest
from task_eval27b import continuation, grade, schemas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frozen', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--split', choices=('debug', 'test'), required=True)
    ap.add_argument('--arms', default='full,none,position8k,purpose4k,position4k')
    a = ap.parse_args()
    started = time.time()
    frozen = json.loads(a.frozen.read_text())
    for path, expected in frozen['files'].items():
        if digest(path) != expected:
            raise ValueError(f'frozen file changed: {path}')
    arms = a.arms.split(',')
    if not arms or len(set(arms)) != len(arms) or not set(arms) <= frozen['arms'].keys():
        raise ValueError('invalid arms')
    config = {'frozen_sha256': digest(a.frozen), 'split': a.split, 'arms': arms,
              'protocol': frozen['protocol']}
    result = {'config': config, 'complete': False, 'rows': {k: [] for k in arms}, 'elapsed_s': 0}
    if a.out.exists():
        result = json.loads(a.out.read_text())
        if result['config'] != config:
            raise ValueError('resume configuration changed')
    prior_s = result['elapsed_s']
    tasks = frozen[a.split]
    for arm in arms:
        rows = result['rows'][arm]
        if [r['id'] for r in rows] != [c['id'] for c in tasks[:len(rows)]]:
            raise ValueError('resume task IDs changed')
    initial_done = sum(map(len, result['rows'].values()))
    if result['complete']:
        print('Already complete', a.out, flush=True)
        return
    import torch
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    import exl3
    import prompt as P
    from eval_agent_exl3 import gen_greedy, install_prefix, load_compiled
    from safetensors.torch import load_file
    body = Path(frozen['prompt']).read_text().rstrip()
    schema = schemas(body)
    model, cache, tok, cfg = exl3.load(frozen['model'], max_seq_len=frozen['cap'], cache_size=frozen['cap'])
    n_sys = len(exl3.encode(tok, P.system_block(body)))
    st = load_file(str(Path(frozen['teacher']) / 'state.safetensors'))
    delta = {str(i): {key: st[f'delta.{i}.{key}'] for key in ('conv_state', 'recurrent_state')} for i in exl3.recurrent_layers(model)}
    attn = {str(i): {'keys': st[f'attn.{i}.keys'], 'values': st[f'attn.{i}.values'],
                    'offset': int(st[f'attn.{i}.offset'][0])} for i in exl3.full_attn_layers(model)}
    assert n_sys == frozen.get('n_sys', 26033)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    def save():
        result['elapsed_s'] = prior_s + time.time() - started
        partial = a.out.with_suffix('.partial')
        partial.write_text(json.dumps(result, indent=2) + '\n')
        partial.replace(a.out)
    for arm in arms:
        compiled, slots = None, None
        if arm not in ('full', 'none'):
            root = frozen['arms'][arm]
            slots = json.loads((Path(root) / 'manifest.json').read_text())['slots']
            compiled = load_compiled(root, slots)
            assert set(compiled) == set(exl3.full_attn_layers(model))
            assert all(x['k'].shape[2] == slots and x['v'].shape[2] == slots for x in compiled.values())
        for c in tasks[len(result['rows'][arm]):]:
            history = P.user_turn(c['q'] + frozen['transport'], think=False)
            trace = []
            for step in c['steps']:
                logical, physical = install_prefix(model, cache, 'teacher' if arm == 'full' else ('none' if arm == 'none' else 'compiled'),
                    n_sys=n_sys, delta=delta, attn=attn, compiled=compiled, K=slots)
                ids = exl3.encode(tok, history)
                if physical + len(ids) + frozen['max_tokens'] > frozen['cap']:
                    raise ValueError('task exceeds physical cache capacity')
                tokens, text, stop, _ = gen_greedy(model, cache, tok, ids, cap=frozen['cap'],
                    logical_pos=logical, physical_len=physical, max_tokens=frozen['max_tokens'])
                ok, reason = grade(text, step, schema)
                ok = ok and stop != 'cap'
                trace.append({'pred': text, 'ok': ok, 'reason': reason if stop != 'cap' else 'cap', 'stop': stop, 'tokens': len(tokens)})
                if not ok:
                    break
                if step.get('reply') is not None:
                    history = continuation(history, text, step)
            result['rows'][arm].append({'id': c['id'], 'kind': c['kind'], 'ok': len(trace) == len(c['steps']) and all(t['ok'] for t in trace), 'trace': trace})
            save()
            done = sum(map(len, result['rows'].values()))
            elapsed = time.time() - started
            newly_done = done - initial_done
            rate = newly_done / max(elapsed, .001)
            print(f'{datetime.now(timezone.utc).isoformat()} elapsed={elapsed:.1f}s completed={done}/{len(tasks)*len(arms)} rate={rate:.3f}/s ETA={(len(tasks)*len(arms)-done)/max(rate,.001):.1f}s arm={arm} case={c["id"]} ok={result["rows"][arm][-1]["ok"]}', flush=True)
        del compiled
    result['complete'] = True
    save()
    print(f'DONE total_duration={result["elapsed_s"]:.3f}s artifact={a.out}', flush=True)


if __name__ == '__main__':
    main()
