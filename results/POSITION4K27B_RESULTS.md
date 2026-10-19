# Position-aware calibration at 4,096 KV rows

## Frozen protocol (authorized 2026-10-15)

**Complete: mixed changes, no overall improvement over the previous 4k artifact.**
Artifact root on XTX:
`/mnt/data/artifacts/kvcompile/artifacts/agent/position4k27b_v1/`.

| Evaluation | Previous purpose4k | Position-aware4k | Full context |
|---|---:|---:|---:|
| Development | 175/194 | **179/194** | 193/194 |
| Fixed probes | 69/78 | **71/78** | 76/78 |
| Stress | 164/197 | **163/197** | 197/197 |
| Stress tool selection | 47/62 | **49/62** | 62/62 |
| Stress arguments | 117/135 | **114/135** | 135/135 |
| Strict diagnostic | 8/12 | **7/12** | 12/12 |
| Reserved test | 3/6 | **2/6** | 6/6 |

Paired gains/losses: dev5/1, fixed78 2/0, stress3/4, strict12 0/1.
Development selection53→58/62, arguments122→121/132. Fixed78 gains are Sentry
project coverage and create_pull_request source-branch lookup; style20/20 and
selection23/26 unchanged. Caps dev1→0, fixed78 3→2, stress0→0, strict12 2→2.
Strict dev remains5/6; reserved mandatory-argument loss is update_pull_request_body.
All test questions/grades remain frozen despite known historical grading limits.

**Verdict:** fixing coverage of queries preceding tool-leaf tokens helps some
selection regressions but does not establish an overall 4k gain or explain all
errors. Argument quality fell despite better required-list coverage. No causal
claim about one token boundary alone: this selector also changes EOS, prose and
fragment row weights. No hard-capacity-limit claim, promotion, extra optimization,
new data, or generalization certification. These are inspected regression suites;
the six reserved tests remain a small diagnostic, not whole-agent evidence.

Fresh stress no-prefix90/197, versus91 in prior4k run; use **one common fresh
107-question informative mask**: previous4k79/107, new4k79/107. Do not compare
prior78/106 directly to new79/107. Fresh masks: dev76→79/89, fixed78 40→41/45,
strict5→4/9. Full-context results reproduced on all four suites.

Measured work: capture5769.057s, equality audit51.925s, compile6167.128s,
evaluation1657.384s; total**13645.494s (3h47m25s)** excluding launch/load gaps,
CPU plan preparation and postprocessing. Capture slowed under 7.2GiB host RAM
pressure with ~6GiB swap used; all checkpoints completed. Fit runtime versus
previous4k6148.368s is essentially unchanged. Same occupied attention KV
**268435456bytes (256MiB)**, full recurrent state158859264bytes (~151.5MiB),
same paged-capacity32768; no measured process-VRAM saving.

Saved [SUMMARY](POSITION4K27B_SUMMARY.json) uses generic `expanded` for new4k
and `control` for fresh original71 **8k**, not the matched4k comparator.
[DETAIL](POSITION4K27B_DETAIL.json) contains actual paired old4k/new4k changes,
per-question generations for changed cases, shared masks, hashes and runtime.
All eight complete per-question eval JSONs remain at the XTX artifact root.
Questions and sampling files are byte-equal to prior4k; compiler configuration
matches except trajectory path, layer measurements and elapsed time. Manifest
SHA256 `54fb4a37199de5f68b3ce48c9e0401dab307681f79f19bdf794c1466a3dd9ae8`.

All jobs finished. Pipeline summary initially failed because the control artifact
link was missing, **after all eight evaluations completed**. Preparation now creates
and validates the link (4582732); summary rerun succeeded, no generation rerun.
Original artifacts preserved. No further GPU work started.

Compare final artifact to purpose4k27b_v1 (dev175/194, fixed78 69/78,
stress164/197: arguments117/135, selection47/62; strict8/12, reserved3/6).
Only query selection in the 405 older tool examples changes. Original71 and new
purpose304 retain their exact old selected rows. All780 Q/A and sampling quotas
are identical; six reserved tools remain excluded from fitting. No new evaluation,
hidden-generalization claim, CE, backend rewrite, uneven allocation, or 8k teacher.

For each changed example preserve **exactly its old number of answer query rows**
(at most10), plus the unchanged final-user query. Priority: query before EOS;
first occurrence of each tool-leaf/field name in answer order; remaining name
fragments in answer order; legacy fallback until full. Exclude namespace fragments
from tool-leaf priority; punctuation predecessors are allowed. A name at answer
token0 is already preceded by the final-user query. Oversubscribed lists can lose
later names/fragments, explicitly counted in preflight; no all-token expansion.
Names come from train answers and scoped source schema, not evaluation failures.

CPU preflight freezes positions.json and reports old/new train coverage. Capture
reuses only verified original71 trajectories from the identical full teacher;
fresh capture for709 examples (405 changed +304 unchanged purpose rows). Mandatory
post-capture audit checks all780×16 position arrays, unchanged teacher prefix and
live K/V, plus equality of shared Q/gate rows against purpose780 before fitting.
Capture checkpoints every5 examples; fitting checkpoints each completed layer;
evaluation resumes per question. Failure of any gate stops the pipeline.

Fit:4096rows/layer,16 attention layers,400updates,24original+24existing+24binding
perupdate,seed0,LR0.001,chunk4,standardteacherinitialization,frozen sink,corrected
projected/gated cosine objective,BF16export. Same256MiB occupied attention KV and
151.5MiB recurrent state,logical26033. No measured process-VRAM saving claimed.

Frozen eval:dev194,fixed78,stress197,strict12(dev6/test6),greedy no-thinking cap64,
unchanged grading. Evaluate final400-update artifact only; no test-based checkpoint
selection, extension, or automatic promotion. Retain all per-question outputs and
paired outcomes vs saved purpose4k outputs; use common full/none mask when scoring
informative retention. These are inspected regressions, not a fresh generalization
test. Source Q/A equality and compiler-config comparison required in final report.

## Execution

Implementation:901ba15. Preflight:all780plans,identical per-example row counts;
404/405olderexampleschange(actualonealreadyhadthesameselection). Original71 and
purpose304remainunchanged. Selection tool-leafstarts0→268/268,EOS63→268/268;
requiredlistsleafstarts0→131/136,EOS7→137/137. Requiredlistname-token coverage
722→1159/2309;selection484→1311/2415(includesnamespace);notalllonglistsfit.
See [POSITION4K27B_PREFLIGHT.json](POSITION4K27B_PREFLIGHT.json).

Expected capture + compilation + eval is several hours; runtime will
be measured, not inferred from training loss. Log on XTX:
`/tmp/opencode/position4k27b.log`.

Started2026-10-15T16:42:04Z,detachedwrapper1503762,capturepython1503766.
At16:43:41Z:80/780total(71verifiedreused+9fresh),elapsed93.4s;
prefixroundtripstatebit-exact,argmaxequal,maxlogitdiff0.03125. Reused71teacherKV
bit-exact. Pipeline schedulespostcaptureequalityaudit→400-stepfit→frozeneval,
stoppingonfailure. Theseareprogresschecks,notqualityresults. Originalreferences
remainuntouched. No competingGPUworkwhilethissessionisactive.

Capturecompleted18:18:17Z(5769srounded;exactmetadataretainedonXTX),all780rows.
Host7.2GiBRAM/swapcausedsubstantialcheckpointslowdown;notGPUfailure.
Postcaptureaudit51.925s:all780×16querypositionsverified;teacherprefix,liveK/V,
commonQ/gatebit-exactagainstpurpose780. See
[POSITION4K27B_CAPTURE_AUDIT.json](POSITION4K27B_CAPTURE_AUDIT.json).
Compilationstarted18:19:27Z,python1506118;layer3step25at18:20Z.
At this checkpoint no quality result existed; frozen eval followed all16layers.

Compilecomplete20:02:23Z:6167.128s,16/16layers,400updates/layer. Manifestconfig
equalspriorpurpose4kexactlyexcepttrajectorypathandmeasuredlayerresults/timing.
Exactcapture5769.057s. Evaluationwrapper1507161subsequentlyfinished;freshoriginal71control
dev167/194,notcandidatequality. Candidatefull/none/compileddevcompleted. Noextra
trainingorcheckpointselection.

Implementation checks: runnable `scripts/test_decision_positions.py` and existing
`scripts/test_query_positions27b.py`; Python syntax and shell syntax checks.
