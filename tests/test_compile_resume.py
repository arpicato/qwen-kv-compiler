"""Run with PyTorch installed; exercises CLI checkpoint/resume without training."""
import importlib.util
import json
import pickle
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import torch

spec = importlib.util.spec_from_file_location('compiler', Path(__file__).resolve().parents[1] / 'scripts/compile_torch_v2.py')
compiler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compiler)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    traj = root / 'traj'
    out = root / 'out'
    traj.mkdir()
    (traj / 'meta.json').write_text(json.dumps({'meta': {'layers': [0, 1], 'n_sys': 8}}))
    for layer in (0, 1):
        with (traj / f'layer_{layer:03d}.pkl').open('wb') as f:
            pickle.dump({'traj': [{'q_rot': torch.zeros(1, 1, 1, 4)}]}, f)
    calls = []

    def optimize(shard, slots, *args, **kwargs):
        layer = int(Path(shard).stem.split('_')[-1])
        calls.append(layer)
        if layer == 1 and calls == [0, 1]:
            raise RuntimeError('interrupted after layer 0')
        return torch.ones(1, 1, slots, 4), torch.ones(1, 1, slots, 4), [2.0, 1.0]

    argv = ['compiler', '--traj', str(traj), '--out', str(out), '--ratio', '.25', '--steps', '2', '--device', 'cpu', '--resume']
    with patch.object(sys, 'argv', argv), patch.object(compiler, 'optimize_layer', optimize):
        try:
            compiler.main()
        except RuntimeError as error:
            assert str(error) == 'interrupted after layer 0'
        else:
            raise AssertionError('expected interruption')
        partial = json.loads((out / 'manifest.json').read_text())
        assert not partial['complete'] and len(partial['layers']) == 1
        compiler.main()
        assert calls == [0, 1, 1], calls
        final = json.loads((out / 'manifest.json').read_text())
        assert final['complete'] and len(final['layers']) == 2
        compiler.main()
        assert calls == [0, 1, 1], 'completed layers retrained'
        with patch.object(sys, 'argv', argv + ['--seed', '1']):
            try:
                compiler.main()
            except SystemExit as error:
                assert 'resume configuration differs' in str(error)
            else:
                raise AssertionError('changed recipe accepted')
print('PASS: partial checkpoint, completed-layer resume, no retraining, changed recipe rejected')
