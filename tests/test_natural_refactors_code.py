"""Run authored reference/unchanged controls in Docker, never on the host."""
import argparse
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from clean_eval import code_check

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--cases', type=Path, default=root / 'inputs/natural_refactors_v3/cases.json')
    a = p.parse_args()
    cases = json.loads(a.cases.read_text())['cases']
    rows = []
    for c in cases:
        positive = code_check(c, '```python\n'+c['reference']+'```', 'eos', a.image)
        negative = code_check(c, '```python\n'+c['code']+'```', 'eos', a.image)
        assert positive['functional_pass'] and not negative['functional_pass'], (c['id'], positive, negative)
        rows.append(dict(id=c['id'], positive=positive, negative=negative))
        print('PASS reference/unchanged negative', c['id'], flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(dict(complete=True, rows=rows), indent=2)+'\n')
    print('DONE40reference+40negativechecks artifact='+str(a.out), flush=True)
