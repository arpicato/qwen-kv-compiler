# Targeted bank: removed non-discriminating cases, added forty fresh tasks

**Fresh batch: full38/40,none0/40. Active bank now53selected cases.**

The active bank is `POLICY_TARGET_CASES.json`. Approved-money, ordinary-fix and
different-contract cases were removed completely, not moved into a controls set.
The old all-category generator was deleted. The one old pause case where both
arms failed, plus the two new ties, are also removed from the active bank.

Final active53=15previous discriminators+38new discriminators. This is an explicitly
retrospectively selected diagnostic bank, **not a holdout and not a100%accuracy
claim**. Historical cases/rawoutputs remain as audit evidence only. The entire
fresh40wasfrozenbeforegenerationandisreportedbelowwithoutpost-outputfiltering.
`POLICY_TARGET_FRESH.json`isthatimmutablecompleted-runmanifest,notacontrolsuite.

## Fresh40results — no old selected cases pooled

| Selected behavior | Full policy | No policy |
|---|---:|---:|
| Ask approval before supplying monetary-change implementation | 18/20 | 0/20 |
| Extract one changed rule and use it from both public entries | 20/20 | 0/20 |
| **All fresh cases** | **38/40** | **0/40** |

Full failures: `new-revenue-split` supplies a complete function and then asks for
approval; `new-tax-surcharge` reaches768tokens while listing examples before its
approval request. Both count as failures, even though its intended policy is clear.
None supplies implementations for all20moneycases and duplicates validation in
all20refactorcases. No exact wording/helper names required. Nomoneycodeexecution
isrequiredforbehaviorjudgment;proposalformulas/examplesareallowed,nofunctionpatch.

Shared-refactor patches: **20/20full and20/20none pass actual input/output tests**,
but onlyfullputsvalidationinonehelperusedbybothpublicfunctions. Publicsignatures
kept. Full'soneunapprovedmoneypatchandnone's20moneypatcheswereparsed/compiled
andrun,butmoneycheckingwas**syntax/smokeonly**,notfinancial-correctnesscertification.
`POLICY_TARGET_CODE_CHECKS.json`field`code_ok`forrefactorincludesrealboundary/
outputtests;formoneyitdoesnot. Thisdistinctionmustsurviveanysummary.

Onefullcap,none0caps;allotherresponsesEOS. Codesmoke/assertionsrunonlyinthe
existingnetwork-disabledreadonlyDockerwithunprivilegedUIDandresourcecaps.
No model code executes on host, no live APIs, no model/env modifications.

## Interpretation/statistics

38full-onlysuccesses,0none-onlysuccesses,2tiesonthefreshbatch. Nominalexactpaired
two-sidedp=7.28e-12;casewiseWilson95%full83.5–98.6%,none0–8.8%(floating-point
epsilonnegativezeroinrawstatsisnumericalonly).40authoredproblemclustersherehave
onecaseeach;clusterbootstrapdifference95%87.5–100points,seed0/20kdraws.

These are **targeted, selected policy behaviors**, not broad compliance. Categories
werechosenfromtheearlier40results,taskformsremaincloselyrelated,andtwofamilies
arenot40independentrules. Significanceisconditionalontheauthoredquestionsand
exchangeabilityassumptions;cannotcertifyunseenpolicygeneralization. No questions
werechangedortossedfromthefreshreporteddenominatorafteroutputs. Removalsapply
onlytotheactivebankandareexplicitlypost-hoc. Donotcalculatevalidationp-values
onthatselected53casebank.

Peruserinstructionnondiscriminatingcontrolsaregone.Thismeanswecannotmeasure
falsepauses,always-pausebehavior,overrefactoring,orcorrecthandlingofalreadyapproved
workwiththisbankalone. Do not infer these from38/40. The previous40-case report
withitscontrolsremainsunchangedasahistoricalresult,nottheactiveevaluation.

## Artifacts and execution

Policyunchanged:`prompts/behavior_project.txt`. Source specification/script
`scripts/policy_target_cases.py`;active53`POLICY_TARGET_CASES.json`;frozenfresh40
`POLICY_TARGET_FRESH.json`;raw80responses`POLICY_TARGET_OUTPUTS.json`;manual
behaviorlabels`POLICY_TARGET_REVIEW.json`;codechecks`POLICY_TARGET_CODE_CHECKS.json`;
fresh-onlystats`POLICY_TARGET_STATS.json`. Initialfreshbankfrozencommit`5e3a891`.
Helper/validationstructureandallmoneyresponsesmanuallyreviewed;ASTsupports
namefreehelperchecks. Statsreuse`policy40_stats.py`withoutchangingoldresults.

XTX `/mnt/data/artifacts/kvcompile/artifacts/agent/policy_target27b_v1/`.
Log `/tmp/opencode/policy-target27b.log`. Wrapper1559133/python1559134exited.
Generation273.976s(4m34s),start2026-10-16T06:27:19Z,end06:31:53Z;includesload,
notCPUcodeverification/statistics. Alljobsfinished,no4k/2k/training/promotion.
