"""Authoring/preflight checks: no model outputs or original fixture changes."""
import ast
from collections import Counter
import copy
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from clean_eval import common_private_helpers, knowledge, signatures_match, tool
from prepare_clean_eval_v2 import build
from task_eval27b import schemas

data = build()
assert [len(data[k]) for k in ('knowledge', 'tools', 'behavior')] == [60, 60, 80]
assert Counter(c['category'] for c in data['behavior']) == dict.fromkeys(
    ('money_unapproved', 'money_approved', 'rule_shared', 'rule_distinct'), 20)
assert all(n == 2 for n in Counter(c['cluster'] for c in data['behavior']).values())
assert len({c['id'] for k in ('knowledge', 'tools', 'behavior') for c in data[k]}) == 200
assert len({c['q'] for k in ('knowledge', 'tools', 'behavior') for c in data[k]}) == 200
assert Counter(c['kind'] for c in data['tools']) == dict.fromkeys(('single_call', 'clarification', 'two_step'), 20)
assert len({c['cluster'] for c in data['behavior']}) == 40
schema = schemas((root / 'inputs/joint/prompt.txt').read_text())
for c in data['knowledge']:
    assert 'Return only' in c['q']
    for a in c['answers']:
        assert knowledge('`'+a+'`', c['answers'], 'eos')['correct']
        assert not knowledge(a, c['answers'], 'cap')['correct']
for c in data['tools'] + data['debug']['tools']:
    for step in c['steps']:
        for action in step.get('accept', []):
            assert tool(json.dumps(action), step, schema, 'eos')['correct'], c['id']
            bad = copy.deepcopy(action)
            bad['arguments']['not_a_real_field'] = 7
            assert not tool(json.dumps(bad), step, schema, 'eos')['correct']
            assert not tool(json.dumps(action), step, schema, 'cap')['correct']
        if 'ask_any' in step:
            assert 'First ask' in c['q'] or 'First ask' in c['q'].capitalize()
            assert tool(json.dumps({'ask': 'Which '+step['ask_any'][0]+'?'}), step, schema, 'eos')['correct']
for c in data['behavior'] + data['debug']['behavior']:
    ast.parse(c['code'])
    ast.parse(c['reference']+'\n'+c['checks'])
    assert signatures_match(c['reference'], c['code'])
    if c['category'] == 'rule_shared':
        assert common_private_helpers(c['reference'])
    if c['category'] == 'rule_distinct':
        assert not common_private_helpers(c['reference'])
prior = []
for directory in ('inputs/joint', 'inputs/clean_eval_v1'):
    for path in (root / directory).glob('*.json'):
        obj = json.loads(path.read_text())
        if isinstance(obj, dict):
            for key in ('items', 'probes', 'test', 'knowledge', 'tools', 'behavior'):
                prior += [r['q'] for r in obj.get(key, []) if isinstance(r, dict) and 'q' in r]
assert not set(prior) & {c['q'] for k in ('knowledge', 'tools', 'behavior') for c in data[k]}
path = root / 'inputs/clean_eval_v2/cases.json'
if path.exists():
    assert json.loads(path.read_text()) == data
print('PASS 200cases,40pairedclusters,60referencecallgraphs,exact-format instructions,negative graders,prior exact-question separation')
