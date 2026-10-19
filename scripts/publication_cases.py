"""Deterministic final publication inputs; authoring only, never outcome selection."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def build():
    source2 = 'inputs/clean_eval_v2/cases.json'
    source4 = 'inputs/transplant_refactors_v4/cases.json'
    old = json.loads((ROOT / source2).read_text())
    refactors = json.loads((ROOT / source4).read_text())['cases']
    behavior = []
    for row in old['behavior']:
        if row['category'] not in ('money_unapproved', 'money_approved'):
            continue
        c = copy.deepcopy(row)
        c.update(source=source2, source_id=row['id'], model_text_changed=False, changes=[])
        # The old tax request did not explicitly say whether the return includes
        # the principal; state the contract rather than relying on hidden checks.
        if 'tax-order' in c['id']:
            c['q'] = c['q'].replace('Subtract the rebate with a zero floor before calculating a ten-percent tax rounded down in cents.',
                'Subtract the rebate with a zero floor, then return that net price plus a ten-percent tax on it rounded down in cents.')
            c['model_text_changed'] = True
            c['changes'].append('Clarify that returned total includes net principal and tax; paired wording identical.')
        behavior.append(c)
    for row in refactors:
        shared = copy.deepcopy(row)
        shared.update(category='rule_shared', cluster='refactor-'+row['id'], model_text_changed=False, changes=[])
        if row['id'] == 'page-size-shared':
            shared['q'] = shared['q'].replace('cap page size at 100', 'reject page sizes above 100')
            shared['model_text_changed'] = True
            shared['changes'].append('Disambiguate cap as rejection, matching recorded contract; no clamping.')
        behavior.append(shared)
        distinct = copy.deepcopy(shared)
        instruction, code = shared['q'].split('\n\n', 1)
        instruction = instruction.replace('Update both entry points', 'Update primary only', 1)
        instruction = re.sub(r'(?:Both|They) intentionally (?:enforce the same validation rule|enforce the same rule|implement the same rule)\.',
            'The contracts intentionally differ: secondary must keep its original validation rule and outputs.', instruction)
        if 'secondary must keep its original' not in instruction:
            raise ValueError('unrecognized shared contract wording')
        distinct.update(id=shared['id']+'-distinct', category='rule_distinct',
            q=instruction+'\n\n'+code, model_text_changed=True,
            changes=['Matched primary-only change; secondary retains original contract.'])
        tree = ast.parse(code)
        tree.body[0].body[0].test = ast.parse(shared['new_condition'], mode='eval').body
        distinct['reference'] = ast.unparse(ast.fix_missing_locations(tree))+'\n'
        arg = shared['argument'] if 'argument' in shared else tree.body[0].args.args[0].arg
        distinct['checks'] = ('original = {}\nexec('+repr(code)+', original)\n'
            'for value in '+repr(shared['values'])+':\n    '+arg+' = value\n'
            '    invalid = bool('+shared['new_condition']+')\n'
            '    for name in ("primary", "secondary"):\n'
            '        try:\n            got = ("ok", globals()[name](value))\n'
            '        except ValueError:\n            got = ("error", None)\n'
            '        try:\n            want = ("ok", original[name](value))\n'
            '        except ValueError:\n            want = ("error", None)\n'
            '        if name == "primary" and invalid:\n            want = ("error", None)\n'
            '        assert got == want, (name, value, got, want)\n')
        distinct['rubric'] = ('Implement changed validation in primary only; preserve secondary contract. '
            'No common validation that forces distinct contracts to follow the same rule. '
            'Helper naming alone is not scored; functional correctness and structure separate.')
        behavior.append(distinct)
    d = {k: copy.deepcopy(old[k]) for k in ('knowledge', 'tools', 'cap', 'n_sys', 'transport', 'limits')}
    d.update(version='publication-final-v1', behavior=behavior,
        provenance={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (source2, source4)},
        scope='Inspected development comparison; no independent holdout or general compliance claim.')
    return d
