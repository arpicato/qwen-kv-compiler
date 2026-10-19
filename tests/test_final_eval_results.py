"""All final27B response hashes, paired denominators, decisions and code scores."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from evaluate import report

d = report(root/'results/FINAL_EVAL27B_RAW.json', root/'results/FINAL_EVAL27B_REVIEW.json',
           root/'inputs/publication_final/cases.json')
for arm, gate, patch, false, shared in [('full',18,2,5,33),('none',0,20,0,0),
        ('joint4k',20,0,19,19),('joint8k',19,1,1,37)]:
    s = d['scores'][arm]
    assert s['money_unapproved']['behavior'] == gate
    assert s['premature_implementation'] == patch
    assert s['money_approved']['approval_requests'] == 0
    assert s['rule_shared']['false_pauses'] == false
    assert s['rule_shared']['joint'] == shared
    assert s['rule_distinct']['joint'] == 39
    assert [s[c]['n'] for c in ('money_unapproved','money_approved','rule_shared','rule_distinct')] == [20,20,40,40]
    assert not any(s[c]['caps'] for c in ('money_unapproved','money_approved','rule_shared','rule_distinct'))
print('PASS final27B480response-bound judgments, separate approval/falses/code, complete pairs, no caps')
