"""V2 tables plus descriptive cluster-bootstrap contrasts; never changes grades."""
from collections import defaultdict
import json
from pathlib import Path
import random

from summarize_clean_eval import summarize

ROOT = Path(__file__).resolve().parents[1]


def contrast(left, right, clusters):
    grouped = defaultdict(list)
    for a, b, cluster in zip(left, right, clusters):
        grouped[cluster].append(int(a)-int(b))
    means = [sum(v)/len(v) for v in grouped.values()]
    rng = random.Random(0)
    samples = sorted(sum(rng.choices(means, k=len(means)))/len(means) for _ in range(10000))
    return dict(n=len(left), clusters=len(means), gains=sum(a and not b for a, b in zip(left, right)),
                losses=sum(b and not a for a, b in zip(left, right)),
                equal_cluster_difference_pp=100*sum(means)/len(means),
                descriptive_cluster_bootstrap95_pp=[100*samples[249], 100*samples[9749]])


def build():
    summary = summarize(version='v2')
    data = json.loads((ROOT / 'inputs/clean_eval_v2/cases.json').read_text())
    raw = json.loads((ROOT / 'results/CLEAN_EVAL27B_V2_RAW.json').read_text())
    review = json.loads((ROOT / 'results/CLEAN_EVAL27B_V2_REVIEW.json').read_text())
    summary['uncertainty_scope'] = 'Descriptive bootstrap of authored clusters, seed0/10000 draws; not population generalization, no multiple-testing correction or superiority certification.'
    summary['paired_contrasts'] = {}
    for arm in ('joint4k', 'joint8k'):
        paired = {}
        for suite in ('knowledge', 'tools'):
            a = raw['rows'][arm][suite]
            b = raw['rows']['full'][suite]
            paired[suite+'_vs_full'] = contrast([r['correct'] for r in a], [r['correct'] for r in b], [c['cluster'] for c in data[suite]])
        for category in ('money_unapproved', 'money_approved', 'rule_shared', 'rule_distinct'):
            a = [r for r in review['arms'][arm] if r['category'] == category]
            b = [r for r in review['arms']['full'] if r['category'] == category]
            clusters = [c['cluster'] for c in data['behavior'] if c['category'] == category]
            paired[category+'_vs_full'] = contrast([r['behavior_pass'] for r in a], [r['behavior_pass'] for r in b], clusters)
        summary['paired_contrasts'][arm] = paired
    summary['behavior_pair_completion'] = {}
    for arm, rows in review['arms'].items():
        by_id = {r['id']: r for r in rows}
        groups = defaultdict(list)
        for c in data['behavior']:
            groups[c['cluster']].append(by_id[c['id']])
        summary['behavior_pair_completion'][arm] = {}
        for prefix in ('money-', 'rule-'):
            pairs = [v for k, v in groups.items() if k.startswith(prefix)]
            def strict(r):
                return r['behavior_pass'] and (r['proposal_content_correct'] is True if r['category'] == 'money_unapproved' else r['functional_pass'])
            summary['behavior_pair_completion'][arm][prefix[:-1]] = dict(n=len(pairs),
                both_process_or_structure=sum(all(r['behavior_pass'] for r in pair) for pair in pairs),
                both_process_and_content_or_function=sum(all(strict(r) for r in pair) for pair in pairs))
    return summary


if __name__ == '__main__':
    path = ROOT / 'results/CLEAN_EVAL27B_V2_SUMMARY.json'
    path.write_text(json.dumps(build(), indent=2)+'\n')
    print('DONE separate v2 tables, paired clusters and descriptive uncertainty', path)
