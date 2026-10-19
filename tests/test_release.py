"""Small archive trust-boundary regression; no Git, dependencies or model needed."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_release import check

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    def manifest(data):
        (root/'file.txt').write_bytes(data)
        (root/'RELEASE.json').write_text(json.dumps({'file.txt':hashlib.sha256(data).hexdigest()}))
    manifest(b'safe research fixture')
    assert check(root)['complete']
    for data in (b'ghp_'+b'a'*36, b'hf_'+b'b'*30, b'-----BEGIN '+b'OPENSSH PRIVATE KEY-----'):
        manifest(data)
        try: check(root)
        except ValueError as e: assert 'credential' in str(e)
        else: raise AssertionError('credential accepted')
    manifest(b'safe')
    (root/'unknown.txt').write_text('not approved')
    try: check(root)
    except ValueError as e: assert 'inventory' in str(e)
    else: raise AssertionError('unlisted file accepted')
    (root/'unknown.txt').unlink()
    (root/'RELEASE.json').write_text(json.dumps({'../file.txt':'0'*64}))
    try: check(root)
    except ValueError: pass
    else: raise AssertionError('unsafe manifest accepted')
print('PASS exact release inventory and credential-signature rejection')

installer=Path(__file__).resolve().parents[1]/'scripts/install_release_runtime.sh'
with tempfile.TemporaryDirectory() as tmp:
    for args in ([tmp], [tmp,'--resume'], ['relative-root']):
        result=subprocess.run(['bash',str(installer),*args],capture_output=True,text=True,timeout=5)
        assert result.returncode != 0 and not list(Path(tmp).iterdir())
print('PASS installer rejects existing unmarked or relative roots before changes')
