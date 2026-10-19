import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from policy_coverage27b import training,positions

rows=training();assert len(rows)==64 and len({r['q'] for r in rows})==64
for r in rows:
    compile(r['q'].split('\n\n',1)[1],r['id'],'exec')
    if r['answer'].startswith('```python\n'):compile(r['answer'][10:-3],r['id'],'exec')
s='def _validated(x):\n    if x <= 0: raise ValueError()\n    return x\n\ndef encode(x):\n    return _validated(x)\n\ndef decode(x):\n    return _validated(x)\n<EOS>'
ids=list(range(len(s)));ids[-1]=248046
p=positions(ids,list(s),s)
assert len(p)<=10 and len(p)==len(set(p)) and len(s)-2 in p
for m in re.finditer(r'(?m)^def ',s):assert m.start()-1 in [-1]+p
for m in re.finditer('_validated\\(',s):assert m.start()-1 in p
print('PASS64separatetrainingexamples,validPython,10-rowcap,helper/bothcaller/EOSpredecessorcoverage')
