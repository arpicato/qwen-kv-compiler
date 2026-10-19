"""Clean evaluation v1 grading. Pure parsing except explicit isolated code checks."""
import ast
import json
from pathlib import Path
import re
import subprocess

from task_eval27b import grade, parse


def knowledge(text, answers, stop):
    # Strip presentation wrappers only, not explanatory prose or wrong alternatives.
    normalize = lambda s: s.strip().strip('`\"\' .\n').casefold()
    return {'correct': stop == 'eos' and normalize(text) in {normalize(a) for a in answers}}


def tool(text, expected, schema, stop):
    result = dict(format_valid=False, tool_correct=None, schema_valid=None, values_correct=None, correct=False)
    try:
        action = parse(text)
    except (ValueError, TypeError):
        return result
    result['format_valid'] = True
    if 'accept' not in expected:
        result['correct'] = grade(text, expected, schema)[0] and stop == 'eos'
        return result
    name, args = action.get('call'), action.get('arguments')
    if not isinstance(name, str):
        result['tool_correct'] = result['schema_valid'] = result['values_correct'] = False
        return result
    # Bare names are unambiguous only if exactly one schema has that suffix.
    if isinstance(name, str) and name not in schema:
        matches = [n for n in schema if n.rsplit('__', 1)[-1] == name]
        if len(matches) == 1:
            name = matches[0]
    result['tool_correct'] = name in {a['call'] for a in expected['accept']}
    if not isinstance(args, dict) or name not in schema:
        result['schema_valid'] = result['values_correct'] = False
        return result
    candidate = {'call': name, 'arguments': args}
    result['schema_valid'] = grade(json.dumps(candidate), {'accept': [candidate]}, schema)[0]
    result['values_correct'] = candidate in expected['accept']
    result['correct'] = result['schema_valid'] and result['values_correct'] and stop == 'eos'
    return result


def replacement(text):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', text, re.S)
    candidates = ['\n'.join(blocks)] if blocks else [text.strip()]
    for code in candidates:
        try:
            tree = ast.parse(code)
            if any(isinstance(n, ast.FunctionDef) for n in tree.body):
                return code
        except SyntaxError:
            pass
    return None


def signatures_match(code, original):
    try:
        definitions = lambda text: {n.name: ast.dump(n.args) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
        supplied, generated = definitions(original), definitions(code)
        return all(generated.get(name) == args for name, args in supplied.items())
    except SyntaxError:
        return False


def common_private_helpers(code, names=('primary', 'secondary')):
    tree = ast.parse(code)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    if not set(names) <= funcs.keys():
        return []
    calls = [{n.func.id for n in ast.walk(funcs[name]) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Name)} for name in names]
    return sorted(n for n in calls[0] & calls[1] & funcs.keys() if n.startswith('_'))


def code_check(case, text, stop, image):
    """Functional assertions only. Human review decides instruction following."""
    code = replacement(text)
    result = dict(code_extracted=code is not None, signatures_preserved=False,
                  functional_pass=False, common_private_helpers=[], manual_behavior_required=True)
    if code is None:
        return result
    result['signatures_preserved'] = signatures_match(code, case['code'])
    result['common_private_helpers'] = common_private_helpers(code, case.get('functions', ('primary', 'secondary')))
    # Proposed money code is still checked; passing is NOT a behavior pass.
    if not result['signatures_preserved'] or stop != 'eos':
        return result
    command = ['docker', 'run', '--rm', '-i', '--network', 'none', '--read-only',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '32',
               '--memory', '128m', '--cpus', '1', '--user', '65534:65534',
               '--entrypoint', '/usr/bin/python3', image, '-I', '-']
    try:
        run = subprocess.run(command, input=code+'\n'+case['checks'], capture_output=True, text=True, timeout=15)
        result['functional_pass'] = run.returncode == 0
        result['error'] = run.stderr[-2000:] if run.returncode else None
    except subprocess.TimeoutExpired:
        result['error'] = 'isolated code check timed out'
    return result
