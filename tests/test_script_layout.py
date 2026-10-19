"""Release checks work from a source archive without Git or historical tags."""
import ast
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
hashes = json.loads((root / 'tests/algorithm_hashes.json').read_text())
for name, expected in hashes.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
for folder in ('src', 'scripts', 'tests'):
    for path in (root / folder).glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
assert not list((root / 'scripts').glob('test_*.py'))
print('PASS source archive syntax, tests separated, frozen algorithm hashes')
