# Coverage audit and bounded warm-start continuation, not full retraining

Authorized2026-10-16. **Complete: candidate15/24 vs control17/24, original18/24.** Reference long_policy4k27b_v1
unchanged26341prompt/teacher/4096KV/recurrentstate. No2k or new full initialization.

CPU audit verifies selected positions for all32 policy examples across16saved
layers, reports helper/caller/EOScoverage. No gate-question-derived calibration.
Fresh64train-only examples:32shared (16diverse rules,2entrypointlayouts),8distinct,
16ordinarynonmonetarychanges,4moneyapproved/unapprovedpairs. Coversstring/enum/
zero/lower/upper/prefix/suffix rules and imperative code answers. Original812Q/A
and captures reused unchanged, verified teacher K/V and identity. Fresh64only
capture with 10answerpositions prioritizing EOS/helper/callers/condition rather
thanprefix-only legacy hints; fixedrowcap,attentionfittingnotCE. This changes data
and query coverage together; cannot isolate either effect.

Before capture: use bounded writer from4b5e7cc(localbranchintegratione0882dc),
tiny old-vs-new capture array parity against saved teacher. Versioned remote script
copy avoids changing historical hashed capture scripts. No EXL3/envchanges.

If audit/parity pass: matched continuations from SAME saved4096KV,80updates/layer,
lr.00025,seed0,chunk4,freeze-sink,gate-weight,cosine1,BF16,72examples/update.
Control uses old812:48catalog+24oldpolicy. Coverage candidate876:48catalog+
8oldpolicy+16newpolicy. No reinitialization or original400update rerun; maximum
160updates total across two arms. Fresh optimizer state (saved KV only), not exact
Adam optimizer resume. Full recurrentstate/logicalpositionunchanged. Match compute
with control so ordinary continuation is not mislabeled a coverage gain.

Final artifacts only, no evaluation-based stopping/checkpoint choice. Same24frozen
inspected gate cases, compare saved18/24/reference23/24 and matched control; no
new test or heldoutgeneralizationclaim. No promotion/extension/2k. Pipeline must
checkpoint/resume and log time/count/rate/ETA. Jobs/artifacts logged below before
next long run. XTXroot`/mnt/data/artifacts/kvcompile/artifacts/agent/policy_coverage_continue27b_v1/`.

## Audit checkpoint

CPUaudit21.903s:all32policypositionsverifiedagainst16savedlayers,notjust
recomputedselection. Shared8answerscapturedqueriesonlyinthefirst20–22%:all8
includehelperqueries,noneincludeeitherpubliccallerbody. Acrossall32answers,
EOSprecedingquery0/32. `function_queries add8`intheauditisfromdistinctcases,
notsharedrefactorcallercoverage. Audit`POLICY_COVERAGE_CONTINUE27B_AUDIT.json`.
Missingcoverageisnotprovedcausal;fittingattentionoutputsisnotanswerCE.

64train-onlyexamples/policydiversityandfixed10-rowselectorpreparedwithoutgate
cases. Sourcecode/boundarytestsandnewwriterarray-paritygatebeforecontinuation.
Nooriginal812recaptureorfull400-stepfit. FreshGPUcapture64only;verificationprobe
1repeatedtrainitemnotincludedinnewdataset. Remoteversionedcapturecodekeepsold
artifactscriptidentitiesintact;srcsymlinkpointstounchangedprojecthelpers.

Implementation`aceb012`(writerintegratione0882dc). Authored40shared/distinctpatches
passedrealDockerboundary/outputchecks. Detachedpipeline started2026-10-16T11:20:37Z,
wrapper1572947,pipeline1572949. Newwriterparitycapture~109s,python1572950exited;
all16layersprefixandq_rot/q_logical/gate/k_live/v_live/k_logicalbit-exactversus
savedlegacyseed. Statebitexact/argmaxequalroundtrip(maxlogitdiff.015625).
Freshcapturepython1573502started,only64newexamples;old812remainuntouched.
Log`/tmp/opencode/policy-coverage-continue27b.log`. No competingGPUwork.

Fresh64capturecompleted~132s,boundedwriterexport16/16;newprefixroundtripagain
bitexact/argmaxequal(maxdiff.029296875). Merge53.319sverifiedold/freshteacherK/V
equalall16layers;old812objectsretainedunchangedexceptnew64globalitemoffsets.
Controlcompiler1574011running80updates/layerfromoriginal4096KV,6/16savedat
11:34Z,~80s/layer. Candidatecontinuesaftercontrol+frozencontrolgeneration.
Norecapture812,no400-updatefit. Final results follow.

## Final results

| Artifact | Money approval | Shared refactor | Total behavior | Correct refactor code |
|---|---:|---:|---:|---:|
| Full prompt | 12/12 | 11/12 | 23/24 | 10/12 |
| Original4k | 12/12 | 6/12 | 18/24 | 5/12 |
| Old-data80-updatecontrol | 12/12 | 5/12 | **17/24** | 4/12 |
| Coverage80-updatecandidate | 10/12 | 5/12 | **15/24** | 4/12 |

Candidate versus control:1gain(depth),3losses(membership/prepaidapproval and
priority-code refactor). The two money failures actually supply patches before
approval. Versus original: candidate1gain/4losses;control0gains/1loss(segment).
Both inherit the incorrect zero check; both over-pause on nonmonetary changes.
All48responsesEOS,nocaps. Placeholder keyword scores are ignored; manual policy
review plus real isolated code assertions are authoritative. Escrow proposal still
reverses recipient order: successful pauses do not certify correct proposals.

**Verdict:** confirmed missing caller/EOS coverage, but this bounded continuation
did not recover behavior. Expanded coverage regressed against the matched control.
Not proof coverage is irrelevant or4khas a hard capacity ceiling: data, query
selection and policy sampling changed together; only80updates with fresh Adam
state were tried. No automatic extension, promotion, new run,2kor full retraining.

## Verification and measured costs

All16layersnewwriterGPUparity passed bit-exact Q/gate/liveKV/prefix comparison.
Fresh64x16positions match plan; EOS predecessor64/64 vs original0/32. Old812x16
Q/gate/liveKV/positions remain bit-exact after merge. XTX retains
`final_capture_verification.json`. Both manifests complete16layers,80updates,
LR.00025,original4kinit,matching72quotas. Each occupies268435456bytes=256MiB
attentionKV,unchanged151.5MiBrecurrentstate/logical26341,no process-VRAM claim.

Parity108.814s,capture132.365s,merge53.319s,controlfit1287.331s/eval90.459s,
candidatefit1298.016s/eval115.834s. New pipeline stages sum3086.139s(51m26s),
withCPUaudit21.903s total3108.042s(51m48s). Wrapper3152s(52m32s)includesprocess
gaps,notCPUaudit. Capture64vs prior812 is not a matched speed comparison.

Wrapper1572947/pipeline1572949,control1574011/eval1574241,candidate1574672/
eval1574843all finished2026-10-16T12:13Z. Original artifacts intact, no active jobs.
`POLICY_COVERAGE_CONTINUE27B_CONTROL.json`/`_CANDIDATE.json`retain raw generations;
`_CONTROL_CODE.json`/`_CANDIDATE_CODE.json`code checks;`_SUMMARY.json`allmanual
rows,paired changes,manifestconfigs,hashes,memory,timing. Existing24areinspected
regression cases,not new generalization evidence. No scores/cases changed afterward.
