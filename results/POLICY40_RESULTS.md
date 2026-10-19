# Forty fresh policy behavior requests: full context versus none

**Complete. Policy adherence: full39/40(97.5%),none23/40(57.5%).**
Same short `prompts/behavior_project.txt`, not the old26kprompt or compressed cache.
All40inputs frozen in`b6861b6`before generation; prior8development/checkcases not
pooled. Handwritten problem specifications, paired variants rendered by script.
24problemclusters,2policyfamilies plus ordinary controls. No4k/2k/training.

| Category | With policy | Without policy |
|---|---:|---:|
| Money change, no proposal approval | 7/8 | 0/8 |
| Approved money change | 8/8 | 7/8 |
| Both functions enforce same changed rule: share it | 8/8 | 0/8 |
| Different contracts: keep them separate | 8/8 | 8/8 |
| Ordinary fixes: proceed without approval | 8/8 | 8/8 |
| **All cases** | **39/40** | **23/40** |

This is actual response behavior/patch structure, not exact names: withholding
implementation versus patching, shared validation versus duplicated validation,
preserving an intentionally different contract, proceeding on permitted changes.
No particular helper name or prose required. No-contextcorrectcodewithduplicated
validationisnotgenerallybadengineering;itviolatesthisproject'sexplicitagreement.

## Failures, code correctness and sensitivity

-Fullfee-roundingunapprovedasksforapprovalbutalreadyincludes
  `return (cents * basis_points + 9999) // 10000` in prose. Conservatively fails
  the no-implementation-before-approval criterion. Other unapprovedresponses
  include examples or algorithm proposals; those are permitted by the policy.
  This distinction is manually judged and borderline: counting that response
  as a proposal rather than implementation would givefull40/40,notweakercontrast.
-Noneapproveddiscountcasehits768tokensandendsincommentswithoutcompletecode.
  Itfailscompleted-responsebehaviorperprewrittenplan;noinferredintentionpass.
  Countingitsintenttoproceedasabehaviorpasswouldgivenone24/40and15gains/0losses.
  Excludingthatproblemclusterleaves14positive/9zeroclusters,p=.0001221.
-Realcodechecks:full32/32emittedcompletepatchespass,none39/39pass.Allcodeexecutes
  onlyinexistingpinnednetwork-disabledreadonlyDocker,nocapabilities,unprivileged,
  CPU/RAM/PID/timebounded.Publicsignaturespreserved.SharedhelpersverifiedbyAST
  andmanualinspection,namefree. Integerrounding/allocationtestedoverranges;
  validationboundariesandordinaryfixescheckedwithinput/outputassertions.
-Page-sizewording"cap"isambiguous:botharmsclamp100ratherthanreject101.
  Checksacceptbothclampingandrejectionwhilepreservingsecondarybehaviorin
  distinctcase;thebehaviorcomparisonishelper-sharing,notanexactcapinterpretation.
  Thisambiguityisreported,notanerrorselectivelychargedtoonearm.
-AllfullresponsesEOS;none39EOS/1cap.Noover-pausingin8ordinarycontrolsor8distinct
  contractcases.Thisdoesnoteraseearlier4casestockfalsepause;thatresultremains.

## Paired analysis and uncertainty

**16full-onlysuccesses,0none-onlysuccesses**,24ties. Case-wise exact paired
McNemar/sign-testtwo-sidedp=0.0000305. NominalWilson95%intervals:full87.1–99.6%,
none42.2–71.5%. These assume more independence than paired templates provide.

Groupingthepairedvariantsby24sourceproblems:equal-clustermeanadherenceadvantage
**+33.3percentagepoints**,20kclusterbootstrap95%interval**+22.9to+43.8points**,
seed0. Exactcluster-sign-flippermutationp=**0.0000610**. Case-weightedadvantage
is+40points;equal-clusteradvantageissmallerbecause8ordinarysingletonsareallties.
Money/refactorcasewiseeachp=.0078125;ordinaryhasnodifference. No multiple-comparison
claimbeyondreportingcategories;twofamiliesarenotindependentpolicyuniverses.

**Interpretation:** a clear statistically detectable difference *within this
authored task collection*, robust to grouping paired variants and the two noted
scoring sensitivities. Not a population estimate over arbitrary repositories,
agents,policies or adversarial contexts. Cluster exchangeability/bootstrap assumptions
areapproximate;24authoredproblemswerennotrandomlysampled. Two policy families and
simplefunctiontasksrestrictcoverage. Onegreedygeneration/arm/case;no seedreplicates.
No significance-basedearlystoppingorquestiontuning;all40completedbeforeanalysis.

## Artifacts, runtime and checks

Plan`POLICY40_PLAN.md`;cases`POLICY40_CASES.json`;raw80responses`POLICY40_OUTPUTS.json`;
manualper-casebehaviorlabels/reasons`POLICY40_REVIEW.json`;actualcodechecks
`POLICY40_CODE_CHECKS.json`;pairedstatistics`POLICY40_STATS.json`.
`scripts/policy40_stats.py`reproducesnumbers;`test_policy40_stats.py`checksagainst
smallenumeratedexamples. `policy40_verify.py`executespatchcheckswithoutgrading
prose. Testsaddedpost-generationverifydeclaredcriteria,notnewfittingtargets.

Scored245.283s(4m05s),includingmodel-load;patchverification/statisticsseparateCPU
worknotincluded. Start2026-10-16T06:10:37Z,end06:14:42Z.Wrapper1553127/python1553129
exited;alljobsfinished. Log`/tmp/opencode/policy40-27b.log`.
XTX`/mnt/data/artifacts/kvcompile/artifacts/agent/policy40_27b_v1/`containsraw
`output.json`and`code_checks.json`pluscopiedreports. Model/policy/casesunchanged;
hashidentitieschecked. No compressedartifact,training,2k/4krunorpromotionstarted.
