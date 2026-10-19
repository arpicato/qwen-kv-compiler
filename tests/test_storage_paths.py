"""Run with python3 tests/test_storage_paths.py; no GPU required."""
from pathlib import Path

scripts = Path(__file__).resolve().parents[1] / 'scripts'
for path in scripts.iterdir():
    if path.suffix in {'.py', '.sh'}:
        text = path.read_text()
        assert '/mnt/kvbench' not in text, path
        assert '/mnt/sandisk/kvbench' not in text, path
        assert '/mnt/sandisk/kvcompile' not in text, path
print('PASS: live scripts do not depend on the old SSD mount or USB project paths')
