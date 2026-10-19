import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_long_policy27b import build

project=Path(__file__).resolve().parents[1]
body,gate,train=build(project)
original=(project/'prompts/agent_resident.txt').read_text()
assert body.endswith(original[original.index('## Build and test\n'):])
assert body.index('## Project behavior agreements')<body.index('## Build and test')
assert len(gate)==24 and len(train)==32
assert len({r['q'] for r in train+gate})==56
for c in train+gate:
    code=c['q'].split('\n\n',1)[1];compile(code,c.get('id','case'),'exec')
for c in train:
    if c['answer'].startswith('```python\n'):compile(c['answer'][10:-3],c['id'],'exec')
for path in project.glob('results/POLICY*CASES.json'):
    older=json.loads(path.read_text())
    assert not {r['q'] for r in gate}&{r['q'] for r in older}
print('PASS original catalog/prompt suffix preserved; policy inserted at project instructions; 24 fresh gate/32 separate calibration inputs; Python valid')
