"""Read-only audit of completed 4B targets, streams, exports and source identities."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import pickle
import sys
import time

import numpy as np
import torch
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))
from capture_store import CaptureStore
from compare4b import positions, target_indices
from run_clean_eval import digest, save
import prompt as P

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--capture', type=Path, required=True)
p.add_argument('--data', type=Path, required=True)
p.add_argument('--source', type=Path, required=True, help='immutable source used by capture')
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
started = time.monotonic()
m = json.loads((a.capture / 'meta.json').read_text())
d = json.loads(a.data.read_text())
assert m['complete'] and m['completed'] == m['total'] == 901 and m['train_completed'] == 812
assert m['identity']['data_sha256'] == digest(a.data)
assert m['identity']['teacher_forward'] == 'full'
assert m['meta']['layers'] == list(range(36)) and m['meta']['n_sys'] == 25390
for name, expected in m['identity']['source_sha256'].items():
    assert digest(a.source / name) == expected, name
parity = json.loads((a.capture / 'parity.json').read_text())
assert parity == dict(hook_logits_exact=True, teacher_forward='full', prefix_reuse=False, passed=True)
tok = AutoTokenizer.from_pretrained(m['identity']['model'], local_files_only=True)
hashes, sequences = {}, []
for split in ('train', 'validation'):
    for i, row in enumerate(d[split]):
        path = a.capture / f'{split}_{i:04d}.pt'
        s = torch.load(path, weights_only=True)
        user = tok(P.user_turn(row['q'], think=False), add_special_tokens=False)['input_ids']
        answer = tok(row.get('answer_text', row['answer'])+'<|im_end|>', add_special_tokens=False)['input_ids']
        assert s['ids'].tolist() == user + answer and s['answer_ids'].tolist() == answer
        assert answer[-1] == 151645 and 151645 not in answer[:-1]
        assert len(user+answer) <= 512
        assert s['target_indices'].tolist() == target_indices(len(user), len(answer), 0)
        assert s['top_ids'].shape == s['top_logp'].shape == (len(answer), 20)
        assert torch.isfinite(s['top_logp']).all() and (s['top_logp'] <= 0).all()
        assert (s['top_ids'] >= 0).all() and (s['top_ids'] < len(tok)).all()
        assert (s['top_logp'].exp().sum(-1) <= 1.00001).all()
        hashes[path.name] = digest(path)
        if split == 'train':
            sequences.append((len(user), len(answer), row['q']))
print(f'{datetime.now(timezone.utc).isoformat()} targets=901/901 elapsed={time.monotonic()-started:.1f}s', flush=True)
store = CaptureStore(a.capture, range(36), 'v2-causal-occupied', m['storage'])
for j in range(36):
    path = a.capture / f'layer_{j:03d}.pkl'
    with path.open('rb') as f:
        shard = pickle.load(f)
    assert shard['schema'] == 'v2-causal-occupied' and len(shard['traj']) == 812
    for key in ('k_sys', 'v_sys'):
        assert shard[key].shape == (1, 8, 25390, 128) and np.isfinite(shard[key]).all()
    stream = (r for batch in store.batches(j) for r in batch)
    for i, (r, streamed, seq) in enumerate(zip(shard['traj'], stream, sequences, strict=True)):
        n_user, n_answer, question = seq
        idx = positions(n_user, n_answer)
        assert r['item'] == i and r['q'] == question and r['n_user'] == n_user
        assert r['q_rot'].shape == (1, 32, len(idx), 128)
        assert r['q_logical'].tolist() == [25390+x for x in idx]
        assert r['k_logical'].tolist() == list(range(25390, 25390+n_user+n_answer))
        for key in ('k_live', 'v_live'):
            assert r[key].shape == (1, 8, n_user+n_answer, 128)
        assert r.keys() == streamed.keys()
        for key, value in r.items():
            if isinstance(value, np.ndarray):
                assert np.isfinite(value).all() and np.array_equal(value, streamed[key]), (j, i, key)
            else:
                assert value == streamed[key], (j, i, key)
    op = a.capture / f'oproj_L{j}.pt'
    w = torch.load(op, weights_only=True)['weight']
    assert w.shape == (4096, 2560) and torch.isfinite(w).all()
    hashes[path.name], hashes[op.name] = digest(path), digest(op)
    del shard, w
    print(f'{datetime.now(timezone.utc).isoformat()} layers={j+1}/36 elapsed={time.monotonic()-started:.1f}s', flush=True)
assert len(list(a.capture.glob('train_*.pt'))) == 812
assert len(list(a.capture.glob('validation_*.pt'))) == 89
assert len(list(a.capture.glob('layer_*.pkl'))) == 36
save(a.out, dict(complete=True, targets=901, train=812, validation=89, layers=36,
    stream_export_exact=True, eos_inclusive=True, finite=True, identity=m['identity'],
    parity=parity, sha256=hashes, elapsed_s=time.monotonic()-started))
print(f'DONE total_duration={time.monotonic()-started:.3f}s artifact={a.out}', flush=True)
