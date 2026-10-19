# Joint catalog/behavior caches: frozen tool evaluation

Authorized 2026-10-17. **Complete: joint4k24/40tasks, joint8k29/40.**

Evaluate existing long_policy4k27b_v1 and long_policy8k27b_v1 caches on the
unchanged 78 regression probes, 197 stress probes, and 40 offline tasks.
Both caches already fit the combined 26,341-token prompt and 812 examples
(780 catalog + 32 policy). No fitting, recapture, selector change or new questions.
These use the legacy query selector, not the position8k catalog-only selector.

Fresh combined-prompt full/none controls on both probe suites and all tasks;
do not substitute original-prompt baseline outputs. Greedy no-thinking generation,
64 tokens for probes, 256 per task action, unchanged task JSON transport/grader.
Existing 24 behavior results are reused, not rerun or pooled as fresh validation.
All suites have been inspected; regression evidence, not a pristine holdout.

Freeze cases, artifacts, calibration overlap and code hashes before generation.
Versioned evaluator copy keeps historical remote scripts/hash identities intact.
Task runner accepts explicit n_sys=26341, retaining historical 26033 default;
no other generation/grading changes. Task strict-equivalence/namespace and
keyword-advice limitations remain. No tuning, retrain, automatic promotion.

XTX artifact: `/mnt/data/artifacts/kvcompile/artifacts/agent/joint_tools27b_v1/`.
Log: `/tmp/opencode/joint-tools27b.log`. Record jobs before long execution;
no competing GPU work while active. Per-question/task resume and atomic output.

Implementation `66dd167`; task length regression fails against the old runner,
passes for original26033/joint26341 and rejects mismatch. Existing40task parser/
expectation tests pass. Freeze uses original probe definitions (including topic
metadata), checks ordered Q/A/kind equality against saved suites, not reconstructed
answer-only metadata. Frozen40task cases/transport/acceptance remain unchanged.

Started2026-10-17T01:58:57Z; wrapper1582909, orchestrator1582910,
first evaluator1582929. Fresh full-context78probe evaluation progressing at
logical26341, no errors. Versioned runtime copies are the actual existing XTX
helpers, not replacements from unrelated local changes. Hashes include teacher,
both16-layercompiledartifacts, input/code/modelmetadata;modelweightshardsnot
newlyhashed. Existing GPU otherwise idle,223GiB free. No fit or recapture launched.

## Unified artifact results

| Metric | Full combined prompt | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Fixed probes | 76/78 | 32/78 | 62/78 | 72/78 |
| Stress tool selection | 62/62 | 1/62 | 44/62 | 55/62 |
| Stress arguments | 135/135 | 89/135 | 113/135 | 126/135 |
| Stress total | 197/197 | 90/197 | 157/197 | 181/197 |
| Offline tasks | 40/40 | 1/40 | 24/40 | 29/40 |
| Behavior, previously measured | 23/24 | 0/24 | 18/24 | 22–23/24 |
| Refactor patches passing supplied checks, previously measured | 10/12 | 12/12 | 5/12 | 12/12 |

Behavior is reused from LONG_POLICY4K27B/LONG_POLICY8K27B, not regenerated in
this evaluation. Joint8k money approval10/12 conservative or11/12 if the coupon
expression is treated as a permitted proposal; insurance full-patch leak remains.
These are the same joint caches across both evaluations, not spliced scores
from catalog-only and behavior-only artifacts. AttentionKV256/512MiB plus
unchanged151.5MiBrecurrentstate; logical26341. No measured process-VRAM claim.

| Task category | Full | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Single call | 20/20 | 1/20 | 12/20 | 14/20 |
| Clarification + call | 8/8 | 0/8 | 4/8 | 6/8 |
| Two steps | 6/6 | 0/6 | 3/6 | 3/6 |
| Keyword advice rubric | 6/6 | 0/6 | 5/6 | 6/6 |

Advice keyword passes do not certify policy accuracy. Task runner uses explicit
JSON transport and mocked replies, not native calls or live services. Strict
namespace/argument matching can reject equivalent alternatives; original grading
unchanged. Inspected authored/correlated cases, no population-generalization claim.

Joint8k vs joint4k: fixed10gains/0losses;stress32gains/8losses. More slots improve
aggregate retention, not every answer. Task file-update:both budgets read SHA3/3;
4k completes3/3,8k2/3 because one update uses `ref` instead of `branch` despite
correct returned SHA. Review-thread workflows:4k0/3(invented read tool),8k1/3
(two invented resolution calls). No task cap hits. Fixed probe caps4k5/8k1;
stress caps4k4/8k0. None caps74/78 and159/197; containment grades can still pass
capped output, so cap counts must accompany accuracy.

## Compared with original-prompt tool-only artifacts

| Metric | Position4k | Joint4k | Position8k | Joint8k |
|---|---:|---:|---:|---:|
| Fixed probes | 71/78 | 62/78 | 76/78 | 72/78 |
| Stress | 163/197 | 157/197 | 188/197 | 181/197 |
| Tasks | 22/40 | 24/40 | 30/40 | 29/40 |

This is NOT an isolated cost of behavior training. Prompt, recurrent state,
calibration812vs780,48+24vs24+24+24sampling, and legacy vs position-aware query
selection differ. No causal conclusion about behavior guidance alone. Main
release can report the coherent joint artifacts with these lower tool scores;
do not relabel earlier best catalog scores as joint-cache results. No new fitting,
selector rescue, checkpoint selection or promotion authorized by these outcomes.

## Verification and costs

Post-run all frozen hashes match. Original40tasks/debug/transport/tokenlimits/
grader unchanged. Regraded1100probe outputs and160task records against original
rules, including reasons/stops and all recorded action traces. Test cases remain
outside exact calibration questions; semantic/topic sharing remains. No model
weights rehashed or fresh-environment reproduction claimed.

Probe/task phase times sum1274.289s(21m14s);orchestrator1325.848s(22m06s),
including process startup gaps, excluding earlier training/capture and reused
behavior evaluation. Completed2026-10-17T02:21:10Z. Wrapper1582909,
orchestrator1582910 and all5evaluators exited; no active experiment jobs.
Verification log `/tmp/opencode/joint-tools27b-verification.log`.

Local `_AGENT78_4K.json`, `_AGENT78_8K.json`, `_STRESS197_4K.json`,
`_STRESS197_8K.json`, `_TASKS.json` retain raw generations; `_SUMMARY.json` counts.
XTX `frozen.json` retains file identities and overlap; versioned `code/` retains
the exact evaluator/runtime copies. Historical artifact files unchanged.
