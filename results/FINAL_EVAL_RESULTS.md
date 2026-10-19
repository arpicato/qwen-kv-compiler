# Final publication evaluation v1

> **Exploratory findings—not independently reviewed.** Behavioral judgments were
> made by an AI assistant with method identities visible (unblinded). Results use
> one seed and authored, previously inspected development cases, not a pristine
> holdout. They do not establish general method superiority, safety, or production
> readiness. Frozen code checks are limited tests, not semantic correctness
> certificates. Raw responses and response-bound reviews are retained for inspection.

**Current release note (2026-10-19):** Both final studies below are complete.
Subsequent27BAM4k andFP32V8k comparisons are in `AM27B_RESULTS.md` and
`AM27B_FP32_RESULTS.md`. Current checklist/installation evidence are
`PUBLICATION_READINESS.md` / `RELEASE_VALIDATION.md`; progress paragraphs below
are chronological records, not active job status.

Authorized2026-10-18:27Bchanged behavior sets FIRST, then4Bfull240cases/all5arms.
No27Bknowledge/tool rerun, no new training data. 4Bfits resume only after27Bphase.
Final240coverage matrix in FINAL_PUBLICATION_PLAN.md; case bytes in
inputs/publication_final/cases.json; frozen manual rubric in its README.

## Before output

60knowledge/60tools unchanged.120behavior=20moneyapprovalpairs+40contractpairs.
77model-visible behavior questions reused unchanged,40new distinct counterparts,
3wording corrections:page-sizeexplicitrejection and monetarytaxreturnincludesnet
principal+taxinbothconditions. No current outcome-driven selection/removal.
Historical source banks already inspected/selected; not a pristine holdout.
All references/buggy controls must pass/fail isolated checks before model launch.

27Bbehavior run retains all120cases on full/none/joint4k/joint8k, same26341token
prompt/currentreproductionartifacts and limits768EOS; manualreviewrequired.
Saved knowledge/tools remain separate verified component evidence. New freeze
records source/inputs/model/cache hashes; original freezes/raw remain intact.
No4Bmodel run/fit concurrently with27Bevaluation.

Status:definition/CPUchecks passed; Dockerpreflight and source freeze pending.

## Preflight accepted;27Blaunched

Source5c14ac6Git-freearchivefinal-eval-v1. Docker120referenceprograms passed and
all120unchangedbuggycontrols failed, reference tool schema calls valid. Exact
normalized overlap audit:77/120previous questions,0/120exact812calibrationquestions;
familiar templates/operations/policies remain and this is not independence.
Evidence`FINAL_EVAL_OVERLAP.json`; no output-based filtering.

27Bfreeze+behavior-onlyrun wrapper1719091, logs`/tmp/opencode/final-eval27b-freeze.log`
and`/tmp/opencode/final-eval27b-generation.log`; outputfinal_eval27b_v1. Freeze/runtime
checks precede generation. Run incomplete;4Bfit remains paused while27BoccupiesGPU.

Freeze acceptedSHA256c88bf64df88022a7faaf2a792ce5cc37548792ca9effa22b7b2f8287b3fae8eb;
generationchild1719169running. Separatefinal-4b-v1exportsourceaa62530plusversioned
runner2b912eewrapper1719197waitsexact27Bwrapper1719091andrequiresall4x120behavior
rowscompletebeforeGPUwork. Then resumescompilerfromlayer0checkpoint,AMfit,nontest
inferencesmokesandfull240x5evaluationviaevaluate.py--backendhf4b. Log
`/tmp/opencode/final-4b-sequence.log`. No27Bknowledge/toolsrequestedorrun.

Progress checkpoint:27B215/480responses atelapsed600.6s; no4BGPUwork started.
Manualreviewreadfull120andfirstnone101responses; source-hashedpartialannotations
in`FINAL_EVAL27B_REVIEW_PARTIAL.json`, explicitly incomplete. Fullunapprovedmoney
includes2prematurepatches despiteaskingapproval; approvedfunctionalerrorsand5
nonmonetaryfalsepausesretained. These are partial inspection findings, not final
tables or permission to change grading/cases. Floatprecisionlimitationsdocumented
separately from finite assertions. Final480response review still pending.

## Final27Bbehavior results

All480responses complete1136.772s (18m56.772s),allEOS,no caps. Manualunblinded
assistantreadall480responses; no independent second reviewer. Raw/freeze/review/
summary retained as `FINAL_EVAL27B_{RAW,FREEZE,REVIEW,SUMMARY}.json`. Earlier partial
review retained explicitly incomplete, not counted twice. No case/score tuning.

| Approval measurement | Full | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Correct pause/no premature implementation /20 |18|0|20|19|
| Premature complete implementation /20 (lower better) |2|20|0|1|
| Correct proposal semantics /20, separately |20|0|17|18|
| Gate AND correct proposal /20 |18|0|17|17|
| False repeated approval after explicit approval /20 (lower better) |0|0|0|0|
| Approved finite code assertions /20 |18|19|18|18|
| Both monetary pair members correct /20 |17|0|17|16|

Allfull/4k/8kaskapproval20/20unapproved,butfullodd-first+credit-firstand8kcredit-first
includecompleteimplementationbeforepermission. Askingaloneisnotgatecompliance.
4khalf-upformulaonlyincrementsatexact50;bankersopeningcontradictslatercorrect
examples;odd-firstformulaallocatestoSECOND.8kodd-firstandper-lineworkedexamples
wrong/contradictory. Theseproposalerrorsremainfailures,notrescuedbykeywordapproval.
Approvedties-evenandodd-firstcodefailfull/4k/8k;noneonlyodd-firstfails.
Floatdivisionprecisionlimitsremainbeyondfinitechecks,especiallyfee/truncation;
do not infer exactarbitraryintegermoneycorrectnessfromthetable.

| Refactor measurement | Full | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Shared-rule structure /40 |35|0|20|38|
| Shared-rule finite functionality /40 |33|40|20|38|
| Shared-rule BOTH /40 |33|0|19|37|
| Distinct-contract structure /40 |40|40|40|40|
| Distinct-contract finite functionality/BOTH /40 |39|39|39|39|
| Nonmonetary false approval pauses /80 (lower better) |5|0|19|1|
| Both contract pair members correct /40 |32|0|19|36|

Allnonmonetaryfalsepausesoccurinsharedcases;distinctcaseszeroallarms. Nonealways
proceeds/duplicates—zerofalsepausesdoesNOTmeanitobeysmonetarygatesorsharing.
Allarmsmake thesame distinctchannelerror:striponlyfailsinternalspaces. Shared
fulltimeout/downloadboundarybugsremain;4kdownloadbug+duplicatedbatch;8ktimeoutbug+
duplicatedsort. Correctedpage-sizewordingnowrejectsinallarms;do not silently
substitute37/40forhistorical8k36/40withoutnotingnewcaseversion.

Interpretation:8kretainsmoretargetedsharingthan4k,butallcompressedarmsstillhave
realapproval/proposal/codefailures. Balancedcontrolsnowshowbothgatingandfalse
pauses,notgeneralcomplianceorindependentholdoutproof.No pooled120score.

Source-bound report regeneration uses `evaluate.py report --raw --review --cases
--out`; this validates manual response hashes/intersections/pairs, not automatic
semantic grading. New review regression validates all480judgments/counts.

## 4Bfollow-on active

27Bwrapper1719091exited;4Bsequentialwrapper1719197startedcompilerchild1749760at
04:22:54Z,resumingverifiedlayer0andstartinglayer1. No competingGPUrun; AM/final
240x5results pending. Logs`controlled4b-compiler.log`and`final-4b-sequence.log`.

## 4Bcompiler complete;AM active

Compiler completedall36layers400updatesat07:09:00Z. Resumedphase9946.0s;
manifestcumulative10233.221s includes287.2sretainedlayer0fromearlierphase,not
discardedpartiallayer1orcapturecost. Evidence`CONTROLLED4B_COMPILER_MANIFEST.json`.
No model-quality claim from local loss. Compiler1749760exited cleanly.
AMchild1751965startednext,171/288headscheckpointedatlastcheckelapsed207.2s;
~2–3minutesremainingatcurrentrate.133GiBfree/~4GiBhostRAMavailable. Sequence1719197
stillactive; non-testsmokesandfull240x5evaluationsnext, no4Bqualityscoresyet.

## 4Bevaluation progress

AMcomplete338.191s/all288heads; manifest`CONTROLLED4B_AM_MANIFEST.json`.
All5non-testinferencesmokesfinished (full/compiler/AM/cartridgesEOS,none16tokencap;
smokecompletiondoesnotimplyqualityorEOSsuccess). Full240casesfinished5112.030s
(1h25m12s),notyetmanuallyreviewed. None229/240at1253.781s,remaining3compressed
armsnotstartedyet. Child1761145noneevaluationactive,sequence1719197healthy,
132GiBfree. No final4Bqualitytablesclaimedfrompartial/unreviewedoutputs.

## 4B generation complete

Sequence1719197 exited after successful final phase at2026-10-18T09:57:35Z.
All5raw files have complete=true and60knowledge/60tools/120behavior rows each:
1200/1200responses saved. Evaluation durations:full5112.0s,none1351.7s,
compiler857.0s,AM769.2s,CARTRIDGES826.0s (sum8915.9s,2h28m35.9s;
excludes fits, smokes and orchestration).132GiBfree at completion check.
Artifacts remain controlled4b_v1/final-eval-{full,none,compiler,am,cartridges}.json.
Generation is complete, not final scientific review:600behavior responses still
require manual review and response-bound report regeneration. No4Bquality scores
or superiority claims from this completion check.

## Final 4B review and scores

All 600 behavior responses read by the assistant, unblinded; no independent
second reviewer. Raw bytes, response-hashed annotations and regenerated summaries
are `FINAL_EVAL4B_{FULL,NONE,COMPILER,AM,CARTRIDGES}_{RAW,REVIEW,SUMMARY}.json`.
No model rerun, case removal, grader repair, checkpoint reselection or refit.
All 300 knowledge answers and 300 tool traces regraded against frozen inputs.
`tests/test_final4b_results.py` checks identities, counts, task grades and summaries.

| Measurement | Full | None | Compiler | AM | CARTRIDGES |
|---|---:|---:|---:|---:|---:|
| Knowledge exact answers /60 |46|7|28|35|26|
| Mock-tool complete tasks /60 |28|0|19|17|5|
| Approval request with no premature code /20 |1|0|1|0|0|
| Approval gate AND correct proposal /20 |1|0|0|0|0|
| Premature function supplied /20 (lower better) |18|20|18|18|20|
| Repeated approval prerequisite after approval /20 (lower better) |0|0|0|0|0|
| Approved frozen code checks /20 |11|12|11|9|9|
| Shared-helper structure /40 |0|0|0|0|0|
| Shared-case frozen code checks /40 |32|40|35|27|17|
| Shared-helper AND frozen code checks /40 |0|0|0|0|0|
| Distinct-contract structure /40 |36|40|35|31|38|
| Distinct-contract AND frozen code checks /40 |28|37|13|25|23|
| Nonmonetary false approval pauses /80 (lower better) |0|0|0|0|0|
| Both monetary pair members correct /20 |1|0|0|0|0|
| Both refactor pair members correct /40 |0|0|0|0|0|

Full correctly gates only the withdrawal case. Compiler withholds the withdrawal
implementation and says approval is needed, but gives no concrete proposal. Its
tax response merely repeats that the change is unapproved and asks to resolve it;
that is not an explicit approval request with a proposal. AM claims existing
bankers/odd-first code needs no change; full makes that claim for signed truncation.
Withholding code alone is not a gate pass. Full often acknowledges approval is
needed yet immediately supplies code. All arms duplicate shared validation or
fail to supply a usable implementation; no shared-helper pass was found manually.
Missing code, fictitious tool-use placeholders and caps are not false pauses.
Behavior cap hits: full0, none0, compiler2, AM1, CARTRIDGES0; retained in denominator.

**Main interpretation:** full-context 4B itself fails these policy behaviors.
This does not establish compressed retention of approval/sharing, nor a
compression-caused loss for a behavior the full control did not demonstrate.
AM leads these compressed knowledge totals; compiler leads compressed tool totals;
there is no uniform winner. This is one seed, this authored/inspected workload,
and different objectives/exposure/compute, not broad baseline superiority or a
cross-model 27B comparison. The 27B demonstration remains separate evidence.

### Frozen grader limitations (scores unchanged)

The code column means the recorded parser/signature/finite-test result, not a
complete manual semantic certificate. `replacement()` concatenates all fenced
Python blocks and executes examples too; expected exceptions in examples cause
otherwise plausible replacements to fail (none upload-size/region distinct).
Unfenced code mixed with prose can be missed (CARTRIDGES sort/extension distinct,
region/segment/stream shared). Argument annotations are compared in the AST and
can fail signatures (CARTRIDGES approved qualifies/withdraw), even if argument
names are preserved. Some check-passing code is still wrong outside the finite
assertions: CARTRIDGES approved invoice uses ceiling, not half-up; shared email
validators impose extra constraints; distinct path rejects all dot-prefixed names.
Monetary floating-point and return-type limitations also remain. No post-output
parser/assertion fix or selective rescoring was used; these issues limit claims.

Regenerate each summary with the supported `scripts/evaluate.py report` command,
using its raw, review and `inputs/publication_final/cases.json` paths. Review hashes
validate annotation identity, not independent semantic agreement. No pooled score.
All scheduled fits/generation/review are complete. Independent review, fresh-runtime
installation and final privacy/license/release checks remain; no push authorized.
