"""AM baseline freeze rejects changed exports and mismatched teacher state."""
import json
from pathlib import Path
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
import run_clean_eval as runner

with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)
    artifacts=p/'reference'
    model=p/'model'
    am=p/'am'
    (artifacts/'teacher').mkdir(parents=True)
    (artifacts/'teacher/state.json').write_text('{}')
    (artifacts/'teacher/state.safetensors').write_text('state')
    for slots in (4096,8192):
        folder=artifacts/f'compiled{slots}'
        folder.mkdir()
        (folder/'manifest.json').write_text(json.dumps(dict(complete=True,layers=list(range(16)),slots=slots)))
    (am/'gate-v2').mkdir(parents=True)
    gate=am/'gate-v2/gate.json'
    gate.write_text(json.dumps(dict(complete=True,zero_beta_parity=True,nonzero_roundtrip_exact=True,
        identity=dict(teacher_sha256=runner.digest(artifacts/'teacher/state.safetensors')))))
    for slots in (4096,8192):
        folder=am/f'am{slots}'
        folder.mkdir()
        files={}
        for l in range(3,64,4):
            f=folder/f'layer_{l:03d}.safetensors'
            f.write_text('test-tensor')
            files[f.name]=runner.digest(f)
        (folder/'manifest.json').write_text(json.dumps(dict(complete=True,slots=slots,
            layers=list(range(3,64,4)),files=files,recipe=dict(gate_sha256=runner.digest(gate)))))
    runtime=json.loads((root/'runtime.json').read_text())
    # No external model hashes in this isolated orchestration fixture.
    from unittest.mock import patch
    original=runner.json.loads
    def loads(text):
        d=original(text)
        if d==runtime:
            d.update(weight_sha256={},metadata_sha256={})
        return d
    with patch.object(runner.json,'loads',side_effect=loads):
        runner.freeze(p/'freeze.json',artifacts,model,root/'inputs/publication_final/cases.json',am)
        frozen=original((p/'freeze.json').read_text())
        assert {'am4k','am8k'} <= frozen['arms'].keys()
        runner.freeze(p/'only4k.json',artifacts,model,root/'inputs/publication_final/cases.json',am,(4096,))
        assert 'am4k' in original((p/'only4k.json').read_text())['arms']
        assert 'am8k' not in original((p/'only4k.json').read_text())['arms']
        (am/'am4096/layer_003.safetensors').write_text('changed')
        try:
            runner.freeze(p/'bad.json',artifacts,model,root/'inputs/publication_final/cases.json',am)
        except ValueError as error:
            assert 'export changed' in str(error)
        else:
            raise AssertionError('accepted modified AM head')
        # FP32 variant needs both precision evidence and matching all-layer smoke.
        manifest_path=am/'am8192/manifest.json'
        m=original(manifest_path.read_text())
        precision=p/'precision.json'
        precision.write_text(json.dumps(dict(complete=True,promotion_ids_equal=True,
            nonzero_roundtrip_exact=True,max_logit_diff=.03125)))
        m['recipe'].update(values_dtype='float32',precision_gate=str(precision),precision_gate_sha256=runner.digest(precision))
        manifest_path.write_text(json.dumps(m))
        smoke=am/'smoke.json'
        smoke.write_text(json.dumps(dict(complete=True,recurrent_injection_exact=True,
            wrapper_sha256=runner.digest(root/'scripts/am27b_attention.py'),
            rows=[dict(slots=8192,roundtrip_exact=True,manifest_sha256=runner.digest(manifest_path))])))
        runner.freeze(p/'fp32.json',artifacts,model,root/'inputs/publication_final/cases.json',am,(8192,))
        assert 'am8k_fp32' in original((p/'fp32.json').read_text())['arms']
        smoke.write_text('{}')
        try:
            runner.freeze(p/'badfp32.json',artifacts,model,root/'inputs/publication_final/cases.json',am,(8192,))
        except (ValueError,KeyError):
            pass
        else:
            raise AssertionError('accepted missing FP32 smoke evidence')
print('PASS AM freeze inventories complete gated exports and rejects tampering')
