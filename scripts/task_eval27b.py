"""Pure offline action parsing/grading; never executes a model-supplied tool."""
import json
import re


def schemas(body):
    out = {}
    for m in re.finditer(r'(?ms)^### `([^`]+)`\n(.*?)(?=^### `|\Z)', body):
        out[m[1]] = {name: (kind, bool(required)) for name, kind, required in
                     re.findall(r'^- `([^`]+)` \[([^]]+)\]( \(required\))?:', m[2], re.M)}
    return out


def parse(text):
    text = text.strip()
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError('duplicate JSON key')
            d[k] = v
        return d
    action = json.loads(text, object_pairs_hook=unique,
                        parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    if not isinstance(action, dict) or set(action) not in ({'call', 'arguments'}, {'ask'}, {'answer'}):
        raise ValueError('expected one call, ask or answer object')
    return action


def grade(text, expected, schema):
    try:
        a = parse(text)
        if 'accept' in expected:
            name, args = a.get('call'), a.get('arguments')
            if not isinstance(name, str) or name not in schema or not isinstance(args, dict):
                return False, 'unknown tool or invalid arguments'
            fields = schema[name]
            if set(args) - fields.keys() or any(required and key not in args for key, (_, required) in fields.items()):
                return False, 'unknown or missing required field'
            types = {'string': str, 'boolean': bool, 'number': (int, float), 'integer': int, 'array': list, 'object': dict}
            for k, v in args.items():
                kind = fields[k][0]
                if kind in types and (not isinstance(v, types[kind]) or kind in ('number', 'integer') and isinstance(v, bool)):
                    return False, 'wrong field type'
            return (True, 'accepted call') if a in expected['accept'] else (False, 'wrong tool or values/extra fields')
        key = 'ask' if 'ask_any' in expected else 'answer'
        if set(a) != {key} or not isinstance(a[key], str) or not a[key].strip():
            return False, 'wrong action kind'
        value = a[key].lower()
        groups = [expected['ask_any']] if key == 'ask' else expected['answer_all']
        ok = all(any(s.lower() in value for s in group) for group in groups)
        ok = ok and not any(s.lower() in value for s in expected.get('forbidden', []))
        return ok, 'text rubric passed' if ok else 'text rubric failed'
    except (ValueError, TypeError):
        return False, 'invalid action JSON'


def continuation(history, text, step):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    import prompt as P
    # ponytail: explicit JSON transport, not native tool-call tokens; replay the
    # transcript from the frozen prefix each turn to avoid recurrent rollback.
    history += P.assistant_turn(text)
    if 'ask_any' in step:
        return history + P.user_turn(step['reply'], think=False)
    result = json.dumps(step['reply'], ensure_ascii=False)
    return history + f'{P.IM_START}tool\n{result}{P.IM_END}{P.IM_START}assistant\n{P.NO_THINK}'
