from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from task_cases27b import cases, debug_cases
from task_eval27b import continuation, grade, schemas
import json

schema = schemas((Path(__file__).resolve().parents[1] / 'prompts/agent_resident.txt').read_text())
for case in cases() + debug_cases():
    for step in case['steps']:
        for action in step.get('accept', []):
            assert grade(json.dumps(action), step, schema)[0], (case['id'], action)
        if 'ask_any' in step:
            assert grade(json.dumps({'ask': step['ask_any'][0] + '?'}), step, schema)[0]
        if 'answer_all' in step:
            assert grade(json.dumps({'answer': ' '.join(g[0] for g in step['answer_all'])}), step, schema)[0]
s = cases()[0]['steps'][0]
assert not grade('{"call":"shell","arguments":{"command":"rm -rf /"}}', s, schema)[0]
a = dict(s['accept'][0]); a['arguments'] = dict(a['arguments'], title='unrequested')
assert not grade(json.dumps(a), s, schema)[0]
a['arguments'].pop('title'); a['arguments']['pullNumber'] = True
assert not grade(json.dumps(a), s, schema)[0]
assert not grade('{"ask":"repo?","ask":"ID?"}', {'ask_any':['repo']}, schema)[0]
assert not grade('{"answer":"done"} trailing', s, schema)[0]
assert not grade('{"call":[],"arguments":{}}', s, schema)[0]
assert not grade('{"answer":"I need the repository"}', {'ask_any':['repo']}, schema)[0]
h = continuation('history', '{"ask":"repo?"}', {'ask_any':['repo'], 'reply':'widget'})
assert 'history' in h and '<|im_start|>user\nwidget' in h
h = continuation('history', '{}', {'reply':{'sha':'abc'}})
assert '<|im_start|>tool\n{"sha": "abc"}' in h
print('PASS 40 task expectations, schema types, side effects, parser, clarification and tool-result replay')
