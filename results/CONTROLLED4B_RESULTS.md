# Controlled Qwen3-4B comparison

Authorized 2026-10-18; branch `eval/4b-controlled-comparison`.
Status: preparation and non-test parity gates; no trained candidate scores yet.
This supersedes the paused old plan for this new run, not its historical results.

## Fixed scope before capture

- Model: existing Qwen3-4B BF16, 36 layers, 8 KV heads, head dimension 128.
  Existing ROCm 6.4 / Torch 2.8.0 / Transformers 4.57.1 environment read/run only.
- Same current joint prompt as 27B, including behavior policy. Do not reuse the
  old 25,090-token 4B prefix without its missing policy. Token count measured
  with the 4B tokenizer before GPU capture; fixed 2,509 rows/head, not a claimed
  exact 10% of the new prefix. 352.828125 MiB BF16 K/V for uniform artifacts.
- All 812 current calibration Q/A unchanged for all methods. Fresh 4B full-prefix
  teacher-forced targets on canonical no-thinking framing including EOS. These
  are shared source-grounded reference answers, not new 4B-generated answers.
- Validation: all 89 unique question/answer pairs from repaired512's original 107
  validation rows, grouped into 75 normalized questions; 13 groups have different
  answers, so retain every distinct answer rather than choosing one. Average
  within question before averaging groups. None overlap train. Prior inspected
  development data, not a fresh holdout. No validation trajectories enter fitting.
- Compiler uses current corrected projected-output/cosine objective, 400 updates
  per layer, 48 catalog + 24 policy samples/update, LR .001, seed0, teacher init.
  Qwen3 has no attention gate. Capture last user row plus at most 10 uniformly
  spread answer prediction rows, explicitly retaining EOS predictor. This avoids
  legacy consumed-token/off-by-one and early-answer-only coverage problems.
- AM uses the pinned upstream RMS-key/NNLS2/LSQ solver on shared training queries.
  Any off-policy versus on-policy distinction and allocation changes must be
  frozen before full fitting; do not silently label the old context-prefill
  implementation as shared-example AM. Confirm finite beta and padding masks.
- CARTRIDGES uses pinned upstream model/cache and native local positions. Verify
  64 frozen / 2,445 trainable rows reconstructed on token axis, 32x32 forced
  FlexAttention tiles, exact input IDs and EOS-inclusive top20 teacher targets.
  Timing/gradient/parity probes precede freezing full training steps and selection.
- Start with seed0, no best-seed search. No superiority claim from this one run.
  No adapters, no checkpoint selection on publication or historical78 test scores.
- Current 60 knowledge / 60 mock tools / 40 behavior cases remain unchanged, all
  retained, plus legacy78 separately if used. Inspected diagnostics, not fresh
  cross-model validation. Full/none controls required before candidate scoring;
  a weak 4B full baseline is reported, not repaired by deleting questions.

## Safety and artifacts

New output `/mnt/data/artifacts/kvcompile/artifacts/agent/controlled4b_v1/`.
All original 4B/27B outputs remain intact. Runtime/model/upstream checkouts are
read-only; no EXL3 environment changes, ComfyUI restart, downloads or paid pods.
Single GPU job at a time; capture checkpoints per example with atomic committed
stream offsets; export one layer at a time. Log under `/tmp/opencode/` with exact
wrapper/child PIDs and UTC/rate/ETA. Update this report before each long phase.

## Preparation checkpoint

Stdlib contract test passes: unchanged812train rows, normalized validation
separation, fixed row budget and causal answer/EOS query indexing. Validation
variants discovered during real-input preparation are retained, not silently
deduplicated by question. Source preparation uses no previous trained artifact.
Next: two-sample real GPU capture smoke (one train/one validation), inspect tensor
shapes/logit alignment/EOS and prefix reuse, then fresh full capture. No candidate
evaluation or method-selection result at this checkpoint.

Initial two-sample smoke completed in 116.222s (source339d370), both EOS targets
and all36layer tensor shapes valid. Actual 4B prefix **25,390 tokens**, so
2,509rows = 9.882% retention, not the 27B token count. Prefix cache stayed at
25,390rows through suffix reuse. Wrapper1693017/python1693018 exited. Log
`/tmp/opencode/controlled4b-smoke.log`. Compiler contract inspection then found
projection filename/metadata needed adapting to the unchanged compiler; fixed
before full capture. The next smoke verifies logits unchanged by capture hooks
and full-prefill/reused-prefix greedy argmax parity (max-logit error <= .25),
before accepting targets. This is an implementation check, not a quality score.

Strict parity smoke source d94df3d failed its predeclared max-logit-difference
gate: **0.53125 > 0.25**. Capture hooks themselves were bit-identical to plain
reused-prefix forward. Full capture and all fits remain blocked pending diagnosis;
do not relax the bound merely to proceed. Wrapper1693242/python1693243 exited,
log `/tmp/opencode/controlled4b-parity.log`. Diagnostic retry saves full/reused
argmax IDs even on failure; no benchmark cases used for this check.

Diagnostic retry reproduced max error0.53125, but all three teacher-forced argmax
tokens matched. That is not sufficient to certify top20 probability targets.
Decision: **do not reuse prefix for fresh target capture**; run full prefix+suffix
for every sample, with hook-versus-unhooked full-prefill equality on the smoke.
This is slower but removes the failed approximation rather than weakening its
acceptance threshold. Default capture mode now full. Original failed attempts
remain on disk, never relabeled accepted. Source/prompt/model identities recorded.

Full-forward smoke source8a0be3b **passed**: capture hooks versus plain full
forward logits bit-identical; two samples/36layers completed160.774s. Evidence
`controlled4b_v1/full-smoke/parity.json`, log`/tmp/opencode/controlled4b-full-smoke.log`;
wrapper1693567/python1693568 exited. Full fresh capture now permitted on frozen
812train+89validation sequences; estimate several hours from ~15s/full-prefill,
not a guaranteed ETA. Source includes per-example GC to bound retained model cycles.
Pending: capture completion, CARTRIDGES/AM non-test implementation gates and
training recipe ceilings; no method fits launched yet.

Fresh full capture sourcef42b3d7 started: wrapper1693742/python1693743,
log`/tmp/opencode/controlled4b-capture.log`, output`controlled4b_v1/capture/`.
Per-example committed checkpoints; full capture remains INCOMPLETE until final
36layer export and target-count audit. No competing GPU jobs while it runs.

## Method implementation decisions (before fits)

AM arm is explicitly **off-policy, uniform-head-budget upstream RMS/NNLS2/LSQ**
on the same captured training queries, including four GQA query heads per KV head.
Uniform2,509rows removes padding/allocation differences for this controlled arm.
This is not the earlier optimized-budget on-policy artifact, nor a claim to
reproduce its best setting. Keep that distinction in tables. No output tuning.
Reuse the historical bounded row-matrix helper only after parity with the pinned
unmodified solver on a tiny fixture; checkpoint every head. No fit started.

CARTRIDGES planned ceiling: eight passes, AdamLR.02, continuous32sequence
accumulation across epoch boundaries, one sequence padded to512(no truncation),
top20meanCE, group-mean validationKL at initialization/each epoch; best validation
checkpoint, never test selection. Upstreamgradient-text initialization,64frozen
rows; init isn't an old fitted cache. Same questions/targets, different method
objectives/initialization; this is not equal-compute training. Timing/memory and
finite-gradient/native-generation gate must pass before launching these passes.
Global accumulation is exactly8*812/32=203updates, no epoch-tail step. Save optimizer,
pending gradients and RNG per32sequences/epoch so interrupted accumulation resumes.
The implementation is prepared locally but not yet GPU-verified or deployed;
full capture is the only active GPU phase. Do not report prepared code as a result.

Bounded AM solver CPU regression passed on pinned upstream: identical selected
key indices, beta/values within1e-4, exact saved-head resume. This small fixture
does not certify full-sized GPU numerical behavior or quality. No GPU resources
were used by this test while full capture ran. At last check capture9/901 with
~14.9s/sample after startup; model/hook parity gate passed on the actual full run.
XTX clock reports2026-10-17UTC while session date is2026-10-18; preserve recorded
machine timestamps rather than rewriting experimental time.

Preparation checkpoint b5120d7: all901sequences fit512packing without truncation
(maximum366tokens); frozen input test confirms89validation pairs/75groups and
zero normalized exact question overlap between812train and current scored cases.
Native cartridge gate also requires checkpoint-partition reconstruction and exact
16token native generation roundtrip before training. These GPU checks remain
unrun while capture occupies the GPU; prepared method code is NOT synced over
the live capture source. Current capture source staysf42b3d7. Last recorded22/901,
~15s/sample steady state (~3h40remaining plus export, not startup-biased logETA).

Live handoff: capture28/901 at elapsed583.4s; python1693743 still active, one
example committed about every15s. No quality scores yet. Method code on current
branch has CPU/syntax checks only and is not installed into the running capture
export. After completion, audit all901target files, 812x36trajectories, projection
shapes/finite values and committed offsets before fitting. Do not automatically
launch unverified method code merely because capture exits successfully.

## Capture finished; read-only audit in progress

User requested monitoring. Exact wrapper1693742/python1693743 both exited; log
ends `DONE total_duration=13791.739s` (3h49m51.739s), all901sequences and36layer
exports complete. XTX end timestamp2026-10-17T21:42:22Z retained as recorded.
135GiB disk free, ~5.5GiB available host RAM; no model training started.

Read-only audit wrapper1695218, log`/tmp/opencode/controlled4b-capture-audit.log`;
output`controlled4b_v1/capture-audit.json` pending. Checks all target input IDs,
EOS and causal indexing, finite top20 probabilities, original capture source
hashes, all36x812stream/export equality, projected weight shapes and file hashes.
Capture completion alone is not yet an accepted audit or method quality result.

### Capture accepted after audit

Read-only audit **passed in163.334s**; wrapper1695218/python1695219 exited.
All901target files contain exact frozen user/answer IDs, EOS-inclusive aligned
top20 targets and finite valid probabilities; all36layers have812training-only
trajectories, exact stream/export equality, finite K/V/query/gate arrays and
correct4096x2560projection shapes. Original capture-source hashes match.973artifact
SHA256values committed in `results/CONTROLLED4B_CAPTURE_AUDIT.json`.

The user-requested run is finished and verified. No fit or quality evaluation was
started by monitoring. Next phase remains the non-test native CARTRIDGES gradient/
partition/roundtrip gate and full-sized AM feasibility before any long fit.

## Remaining phases authorized

User explicitly authorized all remaining gates, three fits, full/none controls,
fixed diagnostic evaluation and reporting. No new question authoring/test tuning.
Native CARTRIDGES gate launched from immutable `controlled4b-fit-v1` export of
sourcebf1aa45; wrapper1698477, log`/tmp/opencode/controlled4b-cartridges-gate.log`.
No other GPU work active. Existing runtimes/upstream sources remain untouched.

Native CARTRIDGES gate passed87.369s, peak10.653GiB: finite nonzero KV gradients,
no base gradients,64frozenrows exact,local-position generation and16token native
reconstruction roundtrip equal. Initial launch lacked upstream-required output
environment and exited before model loading; wrapper1698539/python1698540 retry
passed and exited. Evidence`CONTROLLED4B_CARTRIDGES_GATE.json`. No quality claim
from the untrained initialization's generated words. Full AM feasibility next.

Full-sized AM head gate passed18.162s, peak0.638GiB:25,244queries x2,509selected
rows, finite K/beta/V; upstream LSQ completed. Wrapper1699022/python1699023 exited.
Evidence`CONTROLLED4B_AM_GATE.json`. Both method feasibility gates now pass.
Compiler will use fixed final400updates/layer (no checkpoint search); CARTRIDGES
best group-weighted validation checkpoint, AM one deterministic closed-form fit.
Training ceilings frozen above; all run single seed0, no outcome-based extension.

CARTRIDGES8passfit started source88e0e6d, wrapper1699100/python1699101,
log`/tmp/opencode/controlled4b-cartridges-fit.log`; training still incomplete.
Next sequential phases scripted in `scripts/run_controlled4b.sh`: exact-PID wait
for cartridge completion, require complete capture audit/training report, current
compiler400updates/layer, fullAM288heads, then non-test16token inference smoke
for all five arms before full/none/threecandidate160case raw evaluations. Every
phase fails closed and logs/checkpoints, no competing GPU task. Compiler keeps
one exact leading sink row; Qwen3 has no sigmoid attention gate so gate weighting
is off, frozen projection objective/correctedcosine stays on. NativeCARTRIDGES
stop tokens are omitted upstream; evaluation observes last logits and restores
the EOS token for consistent cap/stop reporting. No benchmark output yet.

Live sequence sourceba6fff0 (evaluation provenance checks added before phases),
wrapper1699386; log`/tmp/opencode/controlled4b-sequence-v2.log`. Earlier waiting
wrapper1699314 and child1699315 were terminated by exact PID before launching
replacement; no GPU child was attached and no fit was stopped. CARTRIDGES fit
source88e0e6d remains immutable and running as1699101. At80/6496sequences/2updates,
initial group validationKL4.926769; this is not a final or quality result.

First completed CARTRIDGES epoch: group validationKL4.926769→0.574132,
812/6496sequences; at944/6496training continues with periodic optimizer/gradient
checkpoints. No generation-quality inference from loss reduction. Exact-PID
sequence monitor running with a hard1200x60sbound; resumes monitoring/reporting
when sequence exits. Final fits/evaluation/manual review remain INCOMPLETE.

## CARTRIDGES fit complete; compiler active

All6496sequencepresentations/203updates completed5238.104s (1h27m18.104s),
peak12.001GiB. Predeclared validation-only selection chose **epoch7**,
group-weighted top20KL0.318290 (initial4.926769; epoch8regressed0.336028).
Evidence`CONTROLLED4B_CARTRIDGES_TRAIN.json`; no test outputs used to select it.
Wrapper1699100/python1699101 exited. This is teacher-forced objective progress,
not yet demonstrated free-generation quality.

Sequential runner started compiler at2026-10-18T03:16:53Z, child1701107,
log`/tmp/opencode/controlled4b-compiler.log`. AM/smokes/scoredoutputs still pending.

Approval coverage clarification: active40refactors expose unnecessary approval
pauses but contain no must-pause money cases. They do not establish balanced
approval-gating performance. Historical balanced suites are separate evidence,
not results for this three-way4Bcomparison. A separately frozen balanced approval
evaluation would be additional evaluation after artifact selection, not a silent
replacement of active cases or a training/checkpoint-selection signal. No new
approval suite has been frozen or run at this checkpoint.

## Paused by user

User explicitly requested pause. Stopped compiler1701107 and sequential runner
1699387/wrapper1699386 by exact PID; all three confirmed exited. Compiler manifest
retains completed layer0/36 (`complete=false`); in-progress layer1 has no optimizer
checkpoint and must restart on resume. Captures/audit and completed CARTRIDGES
epoch7selected artifact preserved. AM, inference smokes and evaluations have not
started. No queued project GPU work remains. Do not resume without user request.

## Authorized final run completed (supersedes paused status)

User subsequently authorized 27B changed behavior first, then 4B full240/all5arms.
Compiler resumed from saved layer0 and completed36x400updates; cumulative manifest
10233.221s (resumed phase9946.0s), AM all288heads338.191s. CARTRIDGES retains
validation-selected epoch7, no test checkpoint selection. All1200responses saved;
600behaviorresponses manually reviewed unblinded and source-hashed. Full details,
costs, raw/review/summary identities and grader limitations in
`results/FINAL_EVAL_RESULTS.md`, final4B section.

Full/none/compiler/AM/CARTRIDGES: knowledge46/7/28/35/26 of60; tools28/0/19/17/5
of60. Shared-helper+code0all/40; gate+correctproposal1/0/0/0/0 of20. Full4Bdoesnot
establish requested behavior, so no policy-retention/superiority claim. Frozen
complete-code scores retained despite extraction, annotation and finite-test gaps.
No new fitting, rerun, public push or automatic promotion. All scheduled jobs done.
