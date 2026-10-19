"""Small no-model regression checks for the new evaluation, not old graders."""
import ast
import copy
from collections import Counter
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
import clean_eval as e
from prepare_clean_eval import build
from task_eval27b import schemas

data = build()
assert json.loads((root / 'inputs/clean_eval_v1/cases.json').read_text()) == data
schema = schemas((root / 'inputs/joint/prompt.txt').read_text())
assert [len(data[k]) for k in ('knowledge', 'tools', 'behavior')] == [24, 16, 24]
assert len({c['id'] for k in ('knowledge', 'tools', 'behavior') for c in data[k]}) == 64
assert all(n == 2 for n in Counter(c['cluster'] for c in data['behavior']).values())
old = []
for path in (root / 'inputs/joint').glob('*.json'):
    obj = json.loads(path.read_text())
    if isinstance(obj, dict):
        for key in ('items', 'probes', 'test', 'debug'):
            old += [r['q'] for r in obj.get(key, []) if isinstance(r, dict) and 'q' in r]
assert not set(old) & {c['q'] for k in ('knowledge', 'tools', 'behavior') for c in data[k]}
assert e.knowledge('`pnpm`', ['pnpm'], 'eos')['correct']
assert not e.knowledge('Use pnpm or npm', ['pnpm'], 'eos')['correct']
assert not e.knowledge('pnpm', ['pnpm'], 'cap')['correct']
assert not e.knowledge('not_pnpm', ['pnpm'], 'eos')['correct']
for case in data['tools'] + data['debug']['tools']:
    for step in case['steps']:
        for action in step.get('accept', []):
            r = e.tool(json.dumps(action), step, schema, 'eos')
            assert r['correct'] and r['schema_valid'] and r['tool_correct'], (case['id'], r)
            bare = copy.deepcopy(action)
            bare['call'] = bare['call'].removeprefix('mcp__github__')
            assert e.tool(json.dumps(bare), step, schema, 'eos')['correct']
            assert not e.tool(json.dumps(action), step, schema, 'cap')['correct']
            broken = copy.deepcopy(action)
            broken['arguments']['imaginary_extra'] = 1
            r = e.tool(json.dumps(broken), step, schema, 'eos')
            assert r['tool_correct'] and not r['schema_valid'] and not r['correct']
        if 'ask_any' in step:
            assert e.tool(json.dumps({'ask': 'Which '+step['ask_any'][0]+'?'}), step, schema, 'eos')['correct']
            assert not e.tool('{"ask":"okay"}', step, schema, 'eos')['correct']
assert not e.tool('{"call":"x","call":"y","arguments":{}}', data['tools'][0]['steps'][0], schema, 'eos')['format_valid']
assert not e.tool('{"call":[],"arguments":{}}', data['tools'][0]['steps'][0], schema, 'eos')['correct']
good = data['debug']['tools'][0]['steps'][0]['accept'][0]
wrong_value = copy.deepcopy(good)
wrong_value['arguments']['page'] = 99
r = e.tool(json.dumps(wrong_value), {'accept': [good]}, schema, 'eos')
assert r['tool_correct'] and r['schema_valid'] and not r['values_correct']
wrong_tool = copy.deepcopy(good)
wrong_tool['call'] = 'mcp__github__list_tags'
r = e.tool(json.dumps(wrong_tool), {'accept': [good]}, schema, 'eos')
assert not r['tool_correct'] and r['schema_valid'] and not r['correct']
assert e.replacement('```python\ndef a():\n    return 1\n```') == 'def a():\n    return 1\n'
assert e.replacement('def a():\n    return 1\n') == 'def a():\n    return 1'
assert e.replacement('Here is a description without code.') is None
for case in data['behavior'] + data['debug']['behavior']:
    compile(case['reference']+'\n'+case['checks'], '<reference>', 'exec')
    assert e.signatures_match(case['reference'], case['code'])
    original_name = next(n.name for n in ast.parse(case['code']).body if isinstance(n, ast.FunctionDef))
    assert not e.signatures_match(case['reference'].replace('def '+original_name+'(', 'def changed_(', 1), case['code'])
    good = e.common_private_helpers(case['reference'])
    if case['category'] == 'rule_shared':
        assert good
    if case['category'] == 'rule_distinct':
        assert not good
print('PASS exact recall; schema/tool/value separation; malformed/capped negatives; all reference calls/signatures')
