"""Check a Git-free release's exact file inventory and obvious secret signatures.

Not a legal, semantic privacy, or Git-history audit. Invoke on exported source.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SECRETS = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|hf_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')


def check(root):
    manifest = json.loads((root / 'RELEASE.json').read_text())
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if actual != set(manifest) | {'RELEASE.json'}:
        raise ValueError(f'archive inventory mismatch: {sorted(actual ^ (set(manifest) | {"RELEASE.json"}))}')
    for name, expected in manifest.items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('unsafe archive manifest path')
        path = root / name
        if path.is_symlink() or path.suffix in {'.safetensors','.pt','.pkl','.pem','.key'} or path.name.startswith('.env'):
            raise ValueError(f'forbidden archive entry: {name}')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'archive hash mismatch: {name}')
        if SECRETS.search(data):
            raise ValueError(f'possible credential in {name}; value withheld')
    return dict(complete=True, files=len(actual), hashed_files=len(manifest),
        credential_signature_hits=0, scope='Exact Git-free source inventory; not Git history or legal clearance')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    a = p.parse_args()
    print(json.dumps(check(a.root), indent=2))
