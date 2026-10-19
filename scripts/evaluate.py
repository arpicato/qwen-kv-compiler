"""Publication evaluation CLI: verify tables, preflight code, freeze, or run.

Final 240 cases; separate 27B and controlled 4B studies, with recorded provenance.
"""
import argparse
import hashlib
import json
from pathlib import Path

from run_clean_eval import digest, freeze, run, save
from summarize_clean_eval import summarize
from clean_eval import common_private_helpers, replacement, signatures_match
from reproduce import check_runtime

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'inputs/publication_final/cases.json'


def report(raw_path, review_path, cases_path):
    """New behavior evidence: manual labels are response-bound, not inferred."""
    raw = json.loads(raw_path.read_text())
    review = json.loads(review_path.read_text())
    cases = json.loads(cases_path.read_text())['behavior']
    if not raw['complete'] or not review['complete']:
        raise ValueError('incomplete run or review')
    if review['raw_sha256'] != digest(raw_path) or review['cases_sha256'] != digest(cases_path):
        raise ValueError('review source identity mismatch')
    arms = raw['rows'] if 'config' in raw and 'arm' not in raw['config'] else {raw['config']['arm']: raw['rows']}
    if set(arms) != set(review['arms']):
        raise ValueError('review arms mismatch')
    summary = {}
    task_scores = {}
    data = json.loads(cases_path.read_text())
    for arm, suites in arms.items():
        task_scores[arm] = {}
        for suite in ('knowledge', 'tools'):
            if not suites[suite]:
                continue  # Behavior-only 27B runs intentionally omit these.
            if [r['id'] for r in suites[suite]] != [c['id'] for c in data[suite]]:
                raise ValueError('incomplete or mismatched task rows')
            task_scores[arm][suite] = dict(n=len(suites[suite]),
                correct=sum(r['correct'] for r in suites[suite]))
        rows, labels = suites['behavior'], review['arms'][arm]
        if len(rows) != len(cases) or len(labels) != len(cases):
            raise ValueError('incomplete behavior rows')
        grouped = {}
        for c, r, j in zip(cases, rows, labels, strict=True):
            if not c['id'] == r['id'] == j['id'] or j['pred_sha256'] != hashlib.sha256(r['pred'].encode()).hexdigest():
                raise ValueError('review response identity mismatch')
            if j['category'] != c['category'] or j['functional_pass'] != r['code_check']['functional_pass']:
                raise ValueError('review category or functionality mismatch')
            expected = j['behavior_pass'] and (j['proposal_semantics_pass'] if c['category']=='money_unapproved' else j['functional_pass'])
            if j['joint_pass'] != expected:
                raise ValueError('review intersection mismatch')
            grouped.setdefault(c['category'], []).append((c, r, j))
        scores = {}
        for category, items in grouped.items():
            scores[category] = dict(n=len(items), behavior=sum(j['behavior_pass'] for c,r,j in items),
                functional=sum(j['functional_pass'] for c,r,j in items), joint=sum(j['joint_pass'] for c,r,j in items),
                approval_requests=sum(j['approval_requested'] for c,r,j in items),
                false_pauses=sum(j['unnecessary_approval_pause'] for c,r,j in items),
                caps=sum(r['stop']=='cap' for c,r,j in items))
        scores['premature_implementation'] = sum(j.get('premature_implementation', False) for j in labels)
        scores['proposal_semantics'] = sum(j.get('proposal_semantics_pass') is True for j in labels)
        pairs = {}
        for c,r,j in (item for items in grouped.values() for item in items):
            pairs.setdefault(c['cluster'], []).append(j)
        if any(len(js)!=2 for js in pairs.values()):
            raise ValueError('expected complete behavior pairs')
        scores['pair_joint'] = {name: sum(all(j['joint_pass'] for j in js) for js in pairs.values()
            if js[0]['category'].startswith(prefix)) for name,prefix in (('money','money'),('refactor','rule'))}
        summary[arm] = scores
    return dict(complete=True, scores=summary, task_scores=task_scores, raw_sha256=digest(raw_path), review_sha256=digest(review_path),
                cases_sha256=digest(cases_path), review_scope=review['reviewer'])


def verify_legacy():
    read = lambda name: json.loads((ROOT / name).read_text())
    manifest = read('inputs/publication_eval/manifest.json')
    for name, expected in read('RELEASE.json').items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'release file changed: {name}')
    for name, expected in manifest.items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'publication input changed: {name}')
    current = read('inputs/publication_eval/cases.json')
    v2 = read('inputs/clean_eval_v2/cases.json')
    v4 = read('inputs/transplant_refactors_v4/cases.json')
    if current['transport'] != v2['transport'] or current['limits'] != {'knowledge': v2['limits']['knowledge'], 'tools': v2['limits']['tools'], 'behavior': v4['max_tokens']}:
        raise ValueError('current transport or generation limits differ from recorded runs')
    for suite in ('knowledge', 'tools'):
        if current[suite] != v2[suite]:
            raise ValueError(f'current {suite} differs from recorded evaluation')
    for new, old in zip(current['behavior'], v4['cases'], strict=True):
        if new != old:
            raise ValueError('current behavior differs from recorded evaluation')
    summary = summarize(version='v2')  # Regrade original knowledge and tool traces.
    f2 = read('results/CLEAN_EVAL27B_V2_FREEZE.json')
    f4 = read('results/TRANSPLANT_REFACTORS_V4_FREEZE.json')
    def artifact_hashes(frozen):
        return {Path(name).relative_to(Path(frozen['teacher']).parent).as_posix(): h
                for name, h in frozen['files'].items()
                if Path(frozen['teacher']).parent in Path(name).parents}
    if artifact_hashes(f2) != artifact_hashes(f4):
        raise ValueError('saved suites used different artifact bytes')
    if f2['files'][f2['prompt']] != f4['files'][f4['prompt']] or digest(ROOT / 'inputs/joint/prompt.txt') != f4['files'][f4['prompt']]:
        raise ValueError('saved suites used different prompt bytes')
    if digest(ROOT / 'inputs/clean_eval_v2/cases.json') != f2['files'][f2['cases']] or digest(ROOT / 'inputs/transplant_refactors_v4/cases.json') != f4['files'][f4['cases']]:
        raise ValueError('recorded cases differ from frozen inputs')
    review = read('results/TRANSPLANT_REFACTORS_V4_REVIEW.json')
    if not review['complete']:
        raise ValueError('incomplete manual review')
    scores = {}
    details = {}
    for suffix in ('BASELINES', 'CANDIDATES'):
        name = f'results/TRANSPLANT_REFACTORS_V4_{suffix}.json'
        raw = read(name)
        if not raw['complete'] or raw['config']['freeze_sha256'] != digest(ROOT / 'results/TRANSPLANT_REFACTORS_V4_FREEZE.json') or digest(ROOT / name) != review['raw_sha256'][name]:
            raise ValueError('behavior output/review identity mismatch')
        for arm, suites in raw['rows'].items():
            rows, judgments = suites['behavior'], review['arms'][arm]
            if len(rows) != len(current['behavior']) or len(judgments) != len(rows):
                raise ValueError('incomplete behavior rows')
            for c, r, j in zip(current['behavior'], rows, judgments):
                if not c['id'] == r['id'] == j['id'] or j['pred_sha256'] != hashlib.sha256(r['pred'].encode()).hexdigest():
                    raise ValueError('manual review source mismatch')
                code = replacement(r['pred'])
                if code and (not signatures_match(code, c['code']) or common_private_helpers(code, c['functions']) != r['code_check']['common_private_helpers']):
                    raise ValueError('behavior extraction/diagnostic mismatch')
                if j['functional_pass'] != r['code_check']['functional_pass'] or j['joint_pass'] != (j['structure_pass'] and j['functional_pass']):
                    raise ValueError('behavior totals mismatch')
            d = summary['arms'][arm]
            scores[arm] = dict(knowledge=sum(v['correct'] for v in d['knowledge'].values()),
                tools=sum(d['tools'][k]['completed'] for k in ('single_call', 'clarification', 'two_step')),
                behavior=sum(j['joint_pass'] for j in judgments))
            details[arm] = dict(knowledge=d['knowledge'], tools=d['tools'], behavior=dict(
                structure=sum(j['structure_pass'] for j in judgments), functional=sum(j['functional_pass'] for j in judgments),
                joint=scores[arm]['behavior'], unnecessary_pauses=sum(j['unnecessary_approval_pause'] for j in judgments),
                caps=sum(r['stop'] == 'cap' for r in rows)))
    return dict(complete=True, counts={s: len(current[s]) for s in ('knowledge', 'tools', 'behavior')},
                scores=scores, details=details, same_artifact_hashes=True, same_prompt_hash=True,
                provenance='Saved v2 knowledge/tools and v4 behavior were evaluated separately using identical prompt/cache bytes; no claim of a previously completed one-process combined run.',
                 behavior_scope='Historically selected/inspected development bank, not independent holdout; behavior means correct shared-rule implementation on these cases only.')


def verify(cases=CASES):
    legacy = verify_legacy()
    if cases.resolve() == (ROOT / 'inputs/publication_eval/cases.json').resolve():
        return legacy
    if digest(cases) != digest(CASES):
        raise ValueError('verify supports only the recorded final or legacy bundle')
    from clean_eval import knowledge, tool
    from task_eval27b import schemas
    data = json.loads(CASES.read_text())
    schema = schemas((ROOT / 'inputs/joint/prompt.txt').read_text())
    studies = {'27b': dict(tasks={a: {s: d[s] for s in ('knowledge','tools')}
                                    for a,d in legacy['scores'].items()}, behavior={}),
               '4b': dict(tasks={}, behavior={})}
    original = json.loads((ROOT / 'results/CLEAN_EVAL27B_V2_FREEZE.json').read_text())
    def hashes(freeze, folder):
        return {str(Path(p).relative_to(folder)): h for p,h in freeze['files'].items()
                if Path(folder) in Path(p).parents}
    bundles = [('27b','FINAL_EVAL27B'), ('27b','AM27B_4K'), ('27b','AM27B_8K_FP32')]
    bundles += [('4b', f'FINAL_EVAL4B_{arm}') for arm in ('FULL','NONE','COMPILER','AM','CARTRIDGES')]
    for study, name in bundles:
        path = ROOT / f'results/{name}_RAW.json'
        raw = json.loads(path.read_text())
        if study == '27b':
            frozen = ROOT / f'results/{name}_FREEZE.json'
            f = json.loads(frozen.read_text())
            if raw['config']['freeze_sha256'] != digest(frozen) or f['files'][f['cases']] != digest(CASES):
                raise ValueError(f'final freeze identity mismatch: {name}')
            if f['files'][f['prompt']] != original['files'][original['prompt']]:
                raise ValueError(f'final prompt differs from reused tasks: {name}')
            for arm in original['arms']:
                if hashes(f, f['arms'][arm]) != hashes(original, original['arms'][arm]):
                    raise ValueError(f'final artifact differs from reused tasks: {name}/{arm}')
        result = report(path, ROOT / f'results/{name}_REVIEW.json', CASES)
        saved = json.loads((ROOT / f'results/{name}_SUMMARY.json').read_text())
        if name == 'FINAL_EVAL27B':
            saved.setdefault('task_scores', {a: {} for a in result['scores']})
        if result != saved:
            raise ValueError(f'saved summary mismatch: {name}')
        rows = raw['rows'] if study == '27b' else {raw['config']['arm']: raw['rows']}
        for arm, suites in rows.items():
            for suite in ('knowledge','tools'):
                if not suites[suite]:
                    continue
                for c,r in zip(data[suite], suites[suite], strict=True):
                    if suite == 'knowledge':
                        valid = knowledge(r['pred'], c['answers'], r['stop'])['correct'] == r['correct']
                    else:
                        trace = r['trace']
                        valid = len(trace) <= len(c['steps']) and all(
                            all(t[k] == v for k,v in tool(t['pred'], s, schema, t['stop']).items())
                            for s,t in zip(c['steps'],trace))
                        valid = valid and r['correct'] == (len(trace)==len(c['steps']) and all(t['correct'] for t in trace))
                    if not valid:
                        raise ValueError(f'saved task grade mismatch: {name}/{r["id"]}')
                studies[study]['tasks'].setdefault(arm,{})[suite] = sum(r['correct'] for r in suites[suite])
            studies[study]['behavior'][arm] = result['scores'][arm]
    return dict(complete=True, counts={s: len(data[s]) for s in ('knowledge','tools','behavior')},
        studies=studies, provenance='27B knowledge/tools reused from v2 with identical prompt/cache hashes; final behavior is a separate run. AM and all 4B arms ran all 240 cases.',
        limitations='Inspected development cases, one seed, assistant/unblinded review; frozen code checks are not semantic certificates. No pooled or equal-memory superiority claim.')


def preflight(image, out, cases=CASES):
    from clean_eval import code_check, tool
    from task_eval27b import schemas
    data = json.loads(cases.read_text())
    schema = schemas((ROOT / 'inputs/joint/prompt.txt').read_text())
    for c in data['tools']:
        for s in c['steps']:
            for action in s.get('accept', []):
                if not tool(json.dumps(action), s, schema, 'eos')['correct']:
                    raise ValueError(f'invalid reference action: {c["id"]}')
    rows = []
    for c in data['behavior']:
        good = code_check(c, c['reference'], 'eos', image)
        bad = code_check(c, c['code'], 'eos', image)
        if not good['functional_pass'] or bad['functional_pass']:
            raise ValueError((c['id'], good, bad))
        rows.append(dict(id=c['id'], positive=good, negative=bad))
        print('PASS reference and buggy control', c['id'], flush=True)
    save(out, dict(complete=True, rows=rows))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('verify', 'preflight', 'freeze', 'run', 'report'))
    p.add_argument('--out', type=Path)
    p.add_argument('--freeze', type=Path)
    p.add_argument('--artifacts', type=Path)
    p.add_argument('--am-artifacts', type=Path, help='optional gated AM27B baseline directories for freeze')
    p.add_argument('--am-slots', default='4096,8192', help='explicit AM budgets included in freeze')
    p.add_argument('--model', type=Path)
    p.add_argument('--cases', type=Path, default=CASES)
    p.add_argument('--suites', help='explicit comma-separated suites; defaults to all')
    p.add_argument('--backend', choices=('exl3', 'hf4b'), default='exl3')
    p.add_argument('--arm', choices=('full', 'none', 'compiler', 'am', 'cartridges'))
    p.add_argument('--artifact', type=Path)
    p.add_argument('--capture', type=Path)
    p.add_argument('--smoke', action='store_true')
    p.add_argument('--raw', type=Path)
    p.add_argument('--review', type=Path)
    p.add_argument('--arms', default='full,none,joint4k,joint8k')
    p.add_argument('--image', default='kvcompile-checks:repro')
    a = p.parse_args()
    if a.backend == 'hf4b':
        if a.command != 'run' or not a.arm or not a.out or not a.capture or not a.model:
            p.error('hf4b run needs --arm --out --capture --model and --cases')
        if a.arm in ('compiler', 'am', 'cartridges') and not a.artifact:
            p.error('compressed hf4b arms need --artifact')
        if a.suites:
            p.error('hf4b final comparison runs the full case bundle')
        from compare4b import evaluate
        evaluate(a)
    elif a.command == 'report':
        if not a.raw or not a.review or not a.out:
            p.error('report needs --raw --review --cases --out')
        save(a.out, report(a.raw, a.review, a.cases))
    elif a.command == 'verify':
        result = verify(a.cases)
        if a.out:
            save(a.out, result)
        print(json.dumps(result, indent=2))
    elif a.command == 'preflight':
        if not a.out:
            p.error('preflight needs --out')
        preflight(a.image, a.out, a.cases)
    elif a.command == 'freeze':
        if not all((a.freeze, a.artifacts, a.model)):
            p.error('freeze needs --freeze --artifacts --model')
        verify()
        check_runtime(a.model.resolve())
        if a.am_artifacts:
            freeze(a.freeze, a.artifacts.resolve(), a.model.resolve(), a.cases.resolve(), a.am_artifacts.resolve(),
                   tuple(int(k) for k in a.am_slots.split(',')))
        else:
            freeze(a.freeze, a.artifacts.resolve(), a.model.resolve(), a.cases.resolve())
    else:
        if not a.freeze or not a.out:
            p.error('run needs --freeze --out')
        frozen = json.loads(a.freeze.read_text())
        if frozen['protocol'] not in ('publication-eval-v1', 'publication-final-v1') or digest(frozen['cases']) != digest(a.cases):
            p.error('use a publication freeze with matching --cases bytes')
        check_runtime(Path(frozen['model']))
        run(a.freeze, a.out, 'test', a.arms.split(','), a.suites.split(',') if a.suites else None)
