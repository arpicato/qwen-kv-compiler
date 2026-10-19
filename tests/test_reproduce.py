"""No-model command-plan checks: fresh inputs, recipe parity, no private artifact dependencies."""
import importlib.util
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
import reproduce as r

r.verify_inputs()
out, model = Path('/reproduction/output'), Path('/external/model')
jobs = dict(r.phases(out, model))
for k in (4096, 8192):
    cmd = jobs[f'fit{k}']
    def arg(flag): return cmd[cmd.index(flag)+1]
    assert arg('--steps') == '400' and arg('--slots') == str(k)
    assert arg('--lr') == '0.001' and arg('--examples-per-update') == '72'
    assert '--init-from-dir' not in cmd
capture = jobs['capture812']
assert '--seed-traj' not in capture and '--teacher-in' not in capture
assert '--teacher-out' in capture and '--verify-roundtrip' in capture
for arm in ('control', 'candidate'):
    cmd = jobs[f'continue_{arm}']
    assert cmd[cmd.index('--steps')+1] == '80'
    assert cmd[cmd.index('--init-from-dir')+1] == str(out / 'compiled4096')
for name, cmd in jobs.items():
    # Absolute source/interpreter paths come from this checkout, not private inputs.
    arguments = cmd[3:]
    for value in arguments:
        if value.startswith('/'):
            assert any(value == str(base) or value.startswith(str(base) + '/')
                       for base in (root, out, model)), (name, value)
assert len(jobs) == len(set(jobs)) == 19
print('PASS published input hashes; fresh812 capture; teacher-initialized4k/8k; bounded80controls; explicit paths')
