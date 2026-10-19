# Expanded clean evaluation v2

Status: complete; all800records regraded, all320behaviorresponses manually reviewed.
Protocol `CLEAN_EVAL27B_V2_PLAN.md`, inputs `inputs/clean_eval_v2/`.
Source checkpoint `87b17a8`, tracked archive on XTX at
`/mnt/data/artifacts/kvcompile/releases/clean-eval-v2/`.

## Frozen intent

200cases ×4arms:60knowledge(20tool/20field/20fact),60mocktools(20single/
20clarification/20twostep),80behavior(20eachunapproved/approved/shared/distinct).
40pairedbehaviorclusters. Same original26341tokenprompt and publication-source
reproduction caches, no training/recapture/new policy. Fullcontext failures and
ties stay. V1 preserved; no pooling across suites/versions/models. Semantic family
novelty not claimed. See input README for scoring/format/conditional-step limits.

## Preflight checkpoint

No-model tests pass counts,pairedclusters,referencecallgraphs,uniformshortanswer
instructions,positive/negativegrading,source-field/signaturechecks and exact
question separation from joint calibration/old suites/v1. Domain content remains
related. V1 automatic-grading regression and original algorithm hashes still pass.

XTX isolated Docker executed84referenceimplementations(80scored+4debug) and
84unchanged-code negatives:allpositivespass,allnegativesfail. This includes
boundary rounding,tax/creditorder,allocation,unicode,parsing,normalization and
separate-rule requirements. No code/model/environment changes to historical
artifacts. Preflight log `/tmp/opencode/clean-eval-v2-preflight.log`.
Freeze/source hashes and model-debug outcomes will be recorded before scoring.
4B training remains paused pending prompt-policy/method implementation audit.

## Frozen debug checkpoint

FreezeSHA256d2235716a4cd5060d4122d04095d22e0641fc71ced12d4155af5d591e3f9fd13.
Allmodelweight/metadata hashes verified and cache/source hashes frozen before
model outputs. Debug6records93.139s,wrapper1627300exited. Recall/clarification
transport works;approved/unapprovedmoneyactionsanddistinctcontractcorrect.
Fullcontextdebugsharednormalizationduplicatesabsratherthanusingprivatehelper:
behaviorfailure,nottransportfailure. Functionalassertionspass. Preservefailure,
do not alter scored questions to force full-contextsuccess. All200casesunchanged.
Rawdebug/freeze/preflightareCLEAN_EVAL27B_V2_{DEBUG,FREEZE,PREFLIGHT}.json.

## Generation complete checkpoint

ScoredPID1628096completed2026-10-17T15:09:13Z,total1248.461s(20m48s),all800rows
checkpointed. Knowledgefull60/none28/4k46/8k55of60;tools59/2/51/56of60.
No generation caps in any arm/suite. All40refactorprogramspassfunctionalchecks
inallarms;sharedstructure/proposalsemanticsneedseparatemanualreview. No4Bfits,
newcache,recapture or edits to frozen cases/scoring. Rawoutputsretainedbefore
reviewinCLEAN_EVAL27B_V2_RAW.json. Fullcontext failures remain.

## Knowledge: instructed exact short answers

| Category | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Tool identity /20 | 20 | 7 | 18 | 20 |
| Argument identity /20 | 20 | 15 | 18 | 19 |
| Instruction facts /20 | 20 | 6 | 10 | 16 |
| Total /60 | 60 | 28 | 46 | 55 |

All questions explicitly request short answers; zero caps. Strict matching can
still reject recognizable wrong namespaces or incomplete commands. These are
catalog/instruction recall, not execution or policy compliance. All14/5compressed
misses respectively are full-context passes, no gains over full in this set.

## Mock tool interactions

| Sessions completed | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Single-call /20 | 20 | 2 | 16 | 20 |
| Explicit clarification then call /20 | 20 | 0 | 16 | 19 |
| Two calls using mock replies /20 | 19 | 0 | 19 | 17 |
| Total /60 | 59 | 2 | 51 | 56 |

| Attempted scored call steps (not clarification asks) | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Attempted calls | 80 | 61 | 80 | 80 |
| Correct tool identity | 79 | 26 | 75 | 79 |
| Schema-valid arguments | 80 | 5 | 75 | 78 |
| Exact accepted tool+values, and schema-valid | 79 | 4 | 71 | 76 |
| Expected calls not reached | 0 | 19 | 0 | 0 |
| First clarification action accepted /20 | 20 | 19 | 20 | 20 |

All attempted call JSON formats valid; none'soneclarificationask has an extra
argumentsobject and fails transport. Manual inspection confirms all80clarification
questions request the relevant missing information, including that malformed ask.
The19/20noneaskscoredoesnotestablishfailuretoask;0/20sessioncompletioncomes
fromtransportandtool-schemaerrors. No tool caps. Session scoring requires every
step; attempted-call scores have conditional denominators and are not comparable
as independent full sessions. No native/live service execution.

Full/4k/8kallrepeatget_release_by_taginsteadofupdatingPRtitleint-release-name;
keep all three failures.4kalsoomitsourcebranch/endtimestamporusesbase_ref,
wrongtagtoolorlist_issues.8kusesmethodgetinsteadofget_diffafterclarification,
andtag_nameinsteadoftagintwotagdetailcalls. Differences are inspected diagnoses,
not demonstrated latent causal mechanisms. All cases fixed before scored outputs.

## Natural instruction following: process, content, code kept separate

| Process / structure | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| No monetary implementation before approval /20 | 18 | 0 | 20 | 19 |
| Approved change supplied without another pause /20 | 20 | 20 | 20 | 20 |
| Shared rule executes through one private helper /20 | 20 | 0 | 15 | 16 |
| Intentionally distinct contracts remain separate /20 | 20 | 20 | 20 | 20 |

Fullsuppliescompleteimplementationsforodd-firstandcredit-firstbeforeapproval;
8kleakscredit-first. Calling a full usable replacement a proposal does not pass.
4khasnogateleaksherebutthatdoesnotmeanallitsproposalsarecorrect.

| Semantic / functional checks | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Unapproved proposal consistent with requested in-domain rule /20 | 20 | — | 17 | 18 |
| Gate compliance AND consistent proposal /20 | 18 | 0 | 17 | 17 |
| Approved implementation passing finite assertions /20 | 17 | 19 | 17 | 17 |
| Shared-rule implementation passing assertions /20 | 20 | 20 | 20 | 20 |
| Shared-rule structure AND assertions /20 | 20 | 0 | 15 | 16 |
| Distinct-contract structure AND assertions /20 | 20 | 20 | 20 | 20 |

Proposals are manual consistency judgments within supplied input domains, not
executed programs or proof of arbitrary-integer exactness. None provides
implementations rather than approval-stage proposals; don't silently substitute
its19/20functionalpassesforproposal/gatecompliance.4kproposalerrors:half-up
remainderlogic,internallycontradictoryties-evenclaim,odd-firstallocation.8k:
odd-firstallocationandcontradictoryper-lineexample. Fullodd-firstopeningerror
is explicitly corrected in final proposal/code, but its gate failure remains.
Floating-pointmath.ceil/round/intformulasareflaggedwherepresent:smallinput
tests do not certify arbitrary-large-integer monetary precision.

Approvedmoneyfull/4k/8kallfailties-even,odd-firstandtax-order;nonefailsonly
odd-firstontheassertions. Tax failures return the tax without principal. These
are actual code errors, not missing approval pauses. Existing resident instructions
also constrain response length/comments, but those are not scored here; don't
claimthefourstratatestallprojectinstructionsorwhole-answercorrectness.

4kduplicatescommonrulesforstrip/casefold/sort/slashes/nonnegative-sum;8kfor
strip/casefold/sort/slashes. All80distinct-ruleprogramsandall80shared-rule
programspassfunctionalassertions;onlystructuraladherencevaries. Manual inspection
confirms common helpers execute the changed rule, not merely similarly named calls.

## Paired clusters and uncertainty

20moneyoperationshaveapproved/unapprovedpartners;20ruleshaveshared/distinct
partners. Both sides of each pair must pass to count a fully retained pair:

| Both conditions in a pair | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Money: process only /20 | 18 | 0 | 20 | 19 |
| Money: process plus proposal consistency / approved code checks /20 | 16 | 0 | 16 | 15 |
| Rule: structure plus code checks /20 | 20 | 0 | 15 | 16 |

Machine-readable summary includes paired gains/losses and seeded10000draw
cluster-bootstrap descriptive intervals, computed after scoring without changing
any labels. Knowledge grouped by tool/source heading; sessions by operation/tool
pair; behavior by authored operation, never treating contrast partners as independent.
These pragmatic groups still share schemas and policy families. Intervals are
conditional descriptive variability of these authored clusters, not calibrated
confidence about future tasks or certified method superiority. Degenerate[0,0]
for matching outcomes does not imply zero real-world uncertainty. Multiple
contrasts uncorrected; no claim from crossing a nominal threshold.

No pooled overall score and no v1/v2 pooling.80behaviorcasesstillspanonlytwo
policyfamilies;increasingcountdoesnotmanufacturebroadpolicycoverage. Rules are
explicit code fragments and tasks constrained; successful program transformation
does not prove realistic end-to-end agent behavior. No human-blinded second reviewer.

## Reproducibility and handoff

Raw800records,320source-hashedmanualjudgments,freeze,debug,preflightandregenerable
summaryarecommittedseparately. No post-outputcase/gradeedit,scoredrerun,fit,
promotionortraining. Originalv1andpublication-sourceartifactsunchanged.4B
trainingstillpaused;reuseoftaxonomydoesnotauthorizetestingrulesabsentfrom4B
prefixortrainingonthesetestanswers. Source87b17a8,freeze d2235716... unchanged.
Logs`/tmp/opencode/clean-eval-v2-{preflight,debug,test}.log`;newartifactsunder
`/mnt/data/artifacts/kvcompile/artifacts/agent/clean_eval27b_v2/`.
Final verification: nine targeted regression files pass, including v1/historical
result retention. All800automaticrecords regraded; manual judgments bound to
response hashes; all84positive/negative preflight records verified. Completed-run
resume checked every frozen source/artifact hash and returned Already complete
without model loading/generation. Both recorded job PIDs exited. No active jobs.
