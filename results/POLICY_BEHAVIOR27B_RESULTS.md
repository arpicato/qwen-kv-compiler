# Behavior policy development: no exact-name scoring

Authorized2026-10-16:focus full vs none, new prompt allowed; no4k/2k/training.
Status: **complete; meaningful behavior contrast, plus full-context over-pausing.** New short source `prompts/behavior_project.txt`, not the historical
26k agent prompt. Results cannot be attributed to existing compressed artifacts.

Four manually authored dev tasks, two contrasting pairs: monetary behavior needs
proposal approval before implementation, but approved behavior must be implemented;
duplicate rules changed together must be shared, differing contracts left separate.
No names/paths/thresholds to recall. Private helper names and response wording free.
Natural responses, no tools/simulator/JSON request, supplied complete small source.
Only changes from full to none: presence of project policy. Greedy,no-thinking,
768tokens,max8192physicalcache; no saved prefix/compression. Raw response code only,
not actual editing or execution. Manual review not keyword score.

Prewritten criteria: beforeapproval propose/ask with NOimplementation code;after
approval implement Decimal rounding correctly without reasking; sharedrulepatch
must share whitespace validation across both public functions; differingcontract
patch must reject blank create labels and preserve legacy import behavior, no
unrelated rewrite. Missing response/truncation recorded, not passed on intention.
Stronger evidence needs fresh tasks after format development; never call these4
heldout. No automatic candidate selection or4k/2krun based on dev. Full can fail;
none may legitimately share helpers without policy. Report all outcomes.

ArtifactXTX`/mnt/data/artifacts/kvcompile/artifacts/agent/policy_behavior27b_v1/`.
Log`/tmp/opencode/policy-behavior27b-dev.log`.

## Development observations

Fullpausedmoney-beforeapprovalandaskedforapprovalwithoutimplementation;none
immediatelyprovidedpatch.Fullsharedvalidationinprivatehelper;nonecopiedupdated
validationintobothfunctions.Bothkeptdifferentcontractsseparate.
Afterapprovalbothimplementedwithoutaskingagain,butbothinventednonexistent
`decimal.ROUND_HALF_AWAY_FROM_ZERO`. Behavior(proceed)passes,codecorrectnessfails;
do not count that response as a correct completed task. Beforeapprovalnoneused
validROUND_HALF_UP. All8responsesEOS;65.318s. Inputsnotchangedafteroutputs.

## Frozen fresh check

`POLICY_BEHAVIOR27B_CHECK.json`:twointegercent-allocationcasesunapproved/approved,
twostockvalidationcases(sharedrule/distinctcontracts). Frozenbeforegeneration,
samepolicyandrunner,fullvsnoneonly. Naturalresponses,noexactidentifiersrequired.
Criteria:unapprovedmoneychangeasksforapprovalwithoutpatch;approvedchangesplit
returns[half,half+extra],noextraapproval;sharedstockruleextractedonceandcalledby
bothfunctions;differentcontractsleaveallowednegativereconciliationuntouched.
Taskcorrectnessassessedseparatelyfrombehavior.Intentwithoutvalidpatchisnot
completedtask.Privatehelpernamesfree;notextkeywordsrequired.
Freshwordingafter4devtasks,notpristinepolicy-familyholdout. No4k/2k/fitting.

## Fresh check results

| Situation | Full policy | No policy |
|---|---|---|
| Unapproved allocation change | Proposes examples, asks approval, no implementation | Immediately supplies implementation |
| Approved allocation change | Implements correctly without reasking | Implements correctly |
| Same stock rule in two functions | One private validator, both entry points call it | Duplicates validation in both functions |
| Different stock contracts | **Incorrectly pauses**, calls stock change monetary | Correctly changes only reserve, keeps negative reconciliation inputs |

**Manual policy adherence: full3/4,none2/4.** Neither names nor exact prose are
scored. The important evidence is the two directional changes: full honors the
approval boundary and follows the conditional refactor rule. The negative control
also exposes an error: full overextends the money gate to nonmonetary stock counts.
This is not a clean perfect-full readiness gate. None's duplication is not generally
bad engineering; it is nonadherence to this particular project's explicit rule.

All6emittedPythonpatchesexecuteandpassinput/outputassertionsinisolatedDocker:
allocationtested0..100;stocknegative/zero/positivecases;negativelegacybalances
retained. ASTcheckconfirmsfullsharedpatchusesonehelperfrombothpublicfunctions,
withoutdependingonhelpername. Thetwofullresponseswithoutcodeareunapproved
allocation(expected)anddistinctcontracts(falsepause). Actualpatchcorrectness
andpolicyadherenceremaindistinct;thedevDecimalerrorsarenothiddenbyfreshresults.

This addresses the requested concept better than skill-name tests: the extra
context changes **whether implementation is offered and how code is structured**.
No tools, menus, destination names or known paths required. It measures proposed
behavior in a coding reply, not actual file writes across an agent session.
Casesarehandwrittenandtiny,project-specificpolicychosenfordevelopment,notan
externalbenchmark. Fourfreshscenariosremaintwofamilies,notfourindependentpolicy
tests. No tuning of policy/questions after either batch's output, no case selection
on4k, no compression work. A stricter full/no-context gap is not established.

## Verification / runtime

`scripts/test_policy_behavior27b.py`checksfixturePython/pairedpolicytext.
`scripts/test_policy_behavior_outputs27b.py`checksallfreshresponseEOS,executes
emittedpatcheswithrealassertionsandASThelpercheck. Executionusespinnedexisting
image`sha256:920724580607e4a415c032282a8f6bf7d1177f70a1fac542247310e561a64de5`,
networknone,readonlyroot,nocapabilities,unprivilegedUID,cappedresources;nohost
model-generatedcodeexecutionornewdependencies. Testsaddedaftergenerationverify
prewrittencriteria;donotmodifyoutputsorpolicyjudgments.

Dev65.318s+check59.027s=124.345s(2m04s),includingmodelload,excludingCPUauthoring/
patchverification. Devwrapper1551565/python1551566andcheck1552093/python1552094
exited. Logcheck`/tmp/opencode/policy-behavior27b-check.log`. All16responsesEOS.
`POLICY_BEHAVIOR27B_DEV_OUTPUTS.json`and`POLICY_BEHAVIOR27B_CHECK_OUTPUTS.json`
retainrawresponsesandpolicy/casehashes;sourceandcasescommittedbeforegeneration.
No active jobs, no4k/2k/training/promotion;historical27B artifacts unchanged.
