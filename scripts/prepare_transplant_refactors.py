"""Recover original working questions verbatim, not outcome-filtered v3 variants."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    sources = [('results/POLICY_TARGET_CASES.json', 'refactor'), ('inputs/joint/gate.json', 'refactor')]
    cases = []
    boundaries = {
        'usernames-shared': ['', ' ', 'a'], 'batch-size-shared': [-1, 0, 1],
        'timeouts-shared': [-1, 0, 1], 'page-size-shared': [0, 1, 100, 101],
        'project-slug-shared': ['', 'a', 'a/b'], 'retry-count-shared': [-1, 0, 5, 6],
        'tags-shared': ['', 'a', 'a'*20, 'a'*21], 'ports-shared': [0, 1, 65535, 65536],
    }
    for source, family in sources:
        obj = json.loads((ROOT / source).read_text())
        original = obj['probes'] if isinstance(obj, dict) else obj
        for c in original:
            if c['family'] != family:
                continue
            code = c['q'].split('\n\n', 1)[1]
            tree = ast.parse(code)
            old = ast.unparse(tree.body[0].body[0].test)
            new = c['new_condition']
            reference = 'def _validate('+c['argument']+'):\n    if '+new+':\n        raise ValueError("invalid")\n\n'
            for fn in tree.body:
                fn.body[0] = ast.Expr(value=ast.Call(func=ast.Name(id='_validate', ctx=ast.Load()), args=[ast.Name(id=c['argument'], ctx=ast.Load())], keywords=[]))
            reference += ast.unparse(ast.fix_missing_locations(tree))+'\n'
            values = c.get('values', boundaries.get(c['id']))
            assert values is not None
            # Newly invalid values must reject; accepted original values retain outputs.
            checks = 'original = {}\nexec('+repr(code)+', original)\n'
            checks += 'for value in '+repr(values)+':\n    '+c['argument']+' = value\n    invalid = bool('+new+')\n'
            checks += '    for name in ("primary", "secondary"):\n        try:\n            got = ("ok", globals()[name](value))\n        except ValueError:\n            got = ("error", None)\n        want = ("error", None) if invalid else ("ok", original[name](value))\n        assert got == want, (name, value, got, want)\n'
            cases.append(dict(id=c['id'], category='recovered_refactor', family='refactor', cluster=c.get('cluster', c['id']),
                q=c['q'], code=code, reference=reference, checks=checks, functions=['primary', 'secondary'],
                source=source, source_id=c['id'], new_condition=new, old_condition=old, values=values,
                rubric='One private helper executes the changed common rule in both callers; preserve public signatures and valid outputs. Functional assertions and structure judged separately and jointly.'))
    assert len(cases) == 40 and len({c['q'] for c in cases}) == 40
    return dict(version='transplant-refactors-v4', cases=cases, max_tokens=768)


if __name__ == '__main__':
    path = ROOT / 'inputs/transplant_refactors_v4/cases.json'
    if path.exists():
        raise SystemExit('refusing to overwrite recovered bank')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), indent=2)+'\n')
    print(path)
