# Frozen publication scope

## Current publication interface (2026-10-18)

This document retains the original scope/tables below as historical evidence.
The current report-facing evaluation is `inputs/publication_eval/cases.json` via
`scripts/evaluate.py`: v2 knowledge60/tool60 and recovered v4 behavior40. Recorded
scores were generated separately on identical prompt/cache bytes, not in an
unperformed combined run. Full/none/4k/8k: knowledge60/28/46/55,tools59/2/51/56,
correct shared-rule implementations33/0/18/36. No pooled overall score.

Behavior is an explicitly inspected, historically selected development bank;
full/none screening before latest candidate outputs is not independent holdout
validation. Approval cases and v1–v3 behavior pilots are historical only. The old
24casebehaviorand78/197/40suitesbelowarelegacyreproductionevidence,not competing
headline benchmark choices. Same artifacts trained jointly, no refit/eval tuning.

See EVALUATION.md, results/CLEAN_EVAL27B_V2_RESULTS.md and
results/TRANSPLANT_REFACTORS_V4.md. All prior raw outputs/failures remain intact.
The original19phasecapture/fittingreproduction and failedcoveragecontinuation
remain supported via reproduce.py. Current source/input identities in RELEASE.json;
recorded runs retain their original source hashes. No model weights in release.

Frozen 2026-10-17 after joint-cache tool evaluation (`938ce48`). No new training
or outcome-based recipe changes are part of this cleanup.

## Main table: the same joint artifacts on every suite

26,341-token combined prompt; 812 calibration examples (780 catalog + 32 policy).
4096/8192 rows, teacher initialization, 400 updates/layer, seed0, 48catalog+
24policy examples/update, projected/gated corrected attention objective, frozen
sink, BF16 export. Legacy query selector, not the earlier position-aware recipe.

| Metric | Full | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Fixed probes /78 | 76 | 32 | 62 | 72 |
| Stress selection /62 | 62 | 1 | 44 | 55 |
| Stress arguments /135 | 135 | 89 | 113 | 126 |
| Stress total /197 | 197 | 90 | 157 | 181 |
| Offline tasks /40 | 40 | 1 | 24 | 29 |
| Behavior /24 | 23 | 0 | 18 | 22–23 |
| Refactor patches passing supplied checks /12 | 10 | 12 | 5 | 12 |

Source: `JOINT_TOOLS27B_SUMMARY.json` plus raw probe/task files. Behavior sources:
`LONG_POLICY4K27B_SUMMARY.json`, `LONG_POLICY8K27B_SUMMARY.json` and original
full/none review. Behavior is reused from the same caches, not a new evaluation.
Coupon formula judgment gives8k22conservative/23sensitivity; insurance patch is
a clear approval leak. Supplied tests are finite checks, not proof of correctness.

Task breakdown (full/none/4k/8k): single call20/1/12/14 of20;
clarification8/0/4/6 of8;two-step6/0/3/3 of6;keyword advice6/0/5/6 of6.
Advice passes do not certify accuracy; calls are strict JSON with mock replies,
not native tool execution. Report caps alongside scores: fixed0/74/5/1;
stress0/159/4/0;tasks0all. Do not pool these suites or compute one overall score.

Occupied attentionKV:full1646.3125MiB,4k256MiB,8k512MiB;unchanged recurrent
151.5MiB. Combined state1797.8125/407.5/663.5MiB. No process-VRAM/speedup claim.
Measured joint tool evaluation phases1274.289s/wrapper1325.848s. Training/capture
costs remain separate in LONG_POLICY4K27B/LONG_POLICY8K27B reports.

## Supported negative result

Bounded4kcoveragecontinuation:original18/24,old-data80-updatecontrol17/24,
expanded-coverage80-updatecandidate15/24. Same initial saved4kstate, fresh Adam;
not a full retrain. Confirmed missing caller/EOS queries did not establish that
repairing coverage would recover generation. Keep audit,64newexamples,positions,
merge,matched sampling and fitting recipes. Source: POLICY_COVERAGE_CONTINUE27B*.

## Historical appendix only

Earlier catalog-only purpose/position variants, reread/recompression, short-policy
development and 4B CARTRIDGES/AM/LoRA comparisons remain in reports/raw evidence
and archived code. They are not supported reproduction targets for this release.
The selector comparison is historical context, not an ablation of the final joint
recipe. No method-superiority claim from the4Bcomparison. Broken evaluation
pilots are methodology history, not model-quality benchmarks.

No new joint-selector ablation,2kfit,seed sweep or full retrain for this cleanup.
All evaluations are inspected/authored regression cases; no broad generalization
or production-compliance claim. Frozen historical scores are never overwritten.

## Code boundary and remaining release gates

`scripts/README.md` defines the supported dependency closure. Tests live in
`tests/`. Code outside this scope lives at `archive/pre-unified-release`; all
reports and raw result files remain here. No deletions on XTX, no remote Git push.

Reproduction scope clarified2026-10-17: rerun from published tracked code and
published inputs on the same Qwen/EXL3/ROCm setup, with no reliance on private
experiment folders or preexisting untracked captures/checkpoints. Generated
outputs may be untracked. No other architecture/backend support is required.
Model weights/runtime are explicit external dependencies with pinned acquisition
instructions, not an implicit shared-environment dependency.

Pending: publish frozen input bundle, replace historical-folder dependencies with
explicit input/output/model paths, pin dependencies/model/runtime, choose license
and preserve third-party notices. Then perform a separately recorded full
capture/fit/evaluate reproduction from those published inputs in a new output
directory, never overwriting original results. Smoke/replay alone is not the
requested full reproduction. Existing scripts are not yet a turnkey release.

## Cleanup checkpoint

Later release preparation supersedes the packaging gaps below: MIT-0/notices,
tracked frozen `inputs/`, model/runtime pins, `reproduce.py` replacing3shellrecipes,
and tag-independent algorithm hash checks. See REPRODUCE.md and
REPRODUCTION27B_RESULTS.md for release validation and actual rerun status.

Scope/count verifier `test_script_layout.py` pins18scripts and byte-identical
compiler/capture/generation/task grading relative to the archive. Cleanup commit
`023a7a6`;about18,600lines removed from the active tree, historical evidence retained.
Six checks moved from scripts to tests. README now describes the joint ROCm path.

Verified2026-10-17:8dependency-free checks locally;5additionalCPU checks on XTX
in isolated `/tmp/opencode/unified-cleanup-check` using the existing environment:
compiler layer-resume,cosine normalization,grader parity,probe diversity,probe-set
loading. One old diversity test depended on unavailablepytest;removed its fixture
decorator and added direct invocation,all7assertion functions pass. No dependency
installation/environment mutation. All retained Python parses,3shellrecipes pass
`bash -n`,no imports of removed local modules.14test files total:13automated checks
verified;explicitDockercalibration-outputcheck not rerun. This is CPU cleanup
verification,NOT GPU replay or a clean-environment reproduction.
# Current release status — 2026-10-19

The original scope below has been extended by explicit user authorization to the
final240-case matrix, controlled4B comparison and27BAM4k/FP32V8kbaseline. Current
scope/claims are in README.md and PUBLICATION_READINESS.md. Older limits below
remain historical decisions, not a claim that completed4Bwork is paused.
