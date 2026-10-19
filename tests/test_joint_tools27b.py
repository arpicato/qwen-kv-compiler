"""Dependency-free check of configurable prompt length in the actual task runner."""
import ast
from pathlib import Path

source = ast.parse((Path(__file__).resolve().parents[1] / 'scripts/eval_tasks27b.py').read_text())
check = next(n for n in ast.walk(source) if isinstance(n, ast.Assert)
             and ast.unparse(n.test).startswith('n_sys =='))
code = compile(ast.Module(body=[check], type_ignores=[]), 'prompt-length-check', 'exec')
exec(code, {'n_sys': 26033, 'frozen': {}})
exec(code, {'n_sys': 26341, 'frozen': {'n_sys': 26341}})
try:
    exec(code, {'n_sys': 26033, 'frozen': {'n_sys': 26341}})
except AssertionError:
    pass
else:
    raise AssertionError('wrong prefix accepted')
print('PASS original and joint prompt lengths; mismatched prefix rejected')
