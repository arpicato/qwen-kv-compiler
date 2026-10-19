"""Regenerate clean-set tables and verify frozen automatic grades/manual sources."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from clean_eval import knowledge, tool
from task_eval27b import schemas

ROOT = Path(__file__).resolve().parents[1]


def summarize(root=ROOT, version='v1'):
    read = lambda name: json.loads((root / name).read_text())
    if version not in ('v1', 'v2'):
        raise ValueError('unknown evaluation version')
    prefix = 'CLEAN_EVAL27B' + ('_V2' if version == 'v2' else '')
    data = read(f'inputs/clean_eval_{version}/cases.json')
    raw_path = root / f'results/{prefix}_RAW.json'
    raw = read(f'results/{prefix}_RAW.json')
    review = read(f'results/{prefix}_REVIEW.json')
    frozen_path = root / f'results/{prefix}_FREEZE.json'
    assert raw['complete'] and review['complete']
    assert review['raw_sha256'] == hashlib.sha256(raw_path.read_bytes()).hexdigest()
    assert raw['config']['freeze_sha256'] == hashlib.sha256(frozen_path.read_bytes()).hexdigest()
    schema = schemas((root / 'inputs/joint/prompt.txt').read_text())
    result = dict(complete=True, elapsed_s=raw['elapsed_s'], arms={})
    for arm, suites in raw['rows'].items():
        counts = dict(knowledge={}, tools={}, behavior={})
        for suite, rows in suites.items():
            assert [r['id'] for r in rows] == [c['id'] for c in data[suite]]
        for c, r in zip(data['knowledge'], suites['knowledge']):
            assert knowledge(r['pred'], c['answers'], r['stop'])['correct'] == r['correct']
        for category in ('tool_identity', 'field_identity', 'instruction_recall'):
            rows = [r for r in suites['knowledge'] if r['category'] == category]
            counts['knowledge'][category] = dict(correct=sum(r['correct'] for r in rows), n=len(rows),
                                                caps=sum(r['stop'] == 'cap' for r in rows))
        attempted_calls = []
        expected_calls = 0
        asks = []
        for c, r in zip(data['tools'], suites['tools']):
            expected_calls += sum('accept' in s for s in c['steps'])
            assert 1 <= len(r['trace']) <= len(c['steps'])
            for i, (s, t) in enumerate(zip(c['steps'], r['trace'])):
                fresh = tool(t['pred'], s, schema, t['stop'])
                assert all(t[k] == v for k, v in fresh.items())
                assert i == len(r['trace'])-1 or t['correct']
                (attempted_calls if 'accept' in s else asks).append(t)
            assert r['correct'] == (len(r['trace']) == len(c['steps']) and all(t['correct'] for t in r['trace']))
        for category in ('single_call', 'clarification', 'two_step'):
            rows = [r for r in suites['tools'] if r['category'] == category]
            counts['tools'][category] = dict(completed=sum(r['correct'] for r in rows), n=len(rows))
        counts['tools']['attempted_calls'] = dict(n=len(attempted_calls),
            **{key: sum(t[key] is True for t in attempted_calls) for key in
               ('format_valid', 'tool_correct', 'schema_valid', 'values_correct', 'correct')})
        counts['tools']['unattempted_expected_calls'] = expected_calls-len(attempted_calls)
        counts['tools']['clarification_first_action'] = dict(correct=sum(t['correct'] for t in asks), n=len(asks))
        counts['tools']['caps'] = sum(t['stop'] == 'cap' for r in suites['tools'] for t in r['trace'])
        judgments = review['arms'][arm]
        assert [r['id'] for r in judgments] == [c['id'] for c in data['behavior']]
        for c, r, j in zip(data['behavior'], suites['behavior'], judgments):
            assert j['category'] == c['category']
            assert j['pred_sha256'] == hashlib.sha256(r['pred'].encode()).hexdigest()
            assert isinstance(j['behavior_pass'], bool) and j['rationale']
            assert j['functional_pass'] == r['code_check']['functional_pass']
        for category in ('money_unapproved', 'money_approved', 'rule_shared', 'rule_distinct'):
            rows = [r for r in judgments if r['category'] == category]
            counts['behavior'][category] = dict(n=len(rows), process_or_structure_pass=sum(r['behavior_pass'] for r in rows),
                functional_pass=sum(r['functional_pass'] for r in rows),
                both=sum(r['functional_pass'] and r['behavior_pass'] for r in rows),
                proposal_content_incorrect=sum(r.get('proposal_content_correct') is False for r in rows))
        counts['behavior']['caps'] = sum(r['stop'] == 'cap' for r in suites['behavior'])
        result['arms'][arm] = counts
    return result


if __name__ == '__main__':
    result = summarize()
    path = ROOT / 'results/CLEAN_EVAL27B_SUMMARY.json'
    path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
