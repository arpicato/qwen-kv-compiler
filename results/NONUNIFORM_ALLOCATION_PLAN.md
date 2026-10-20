# Nonuniform cache allocation follow-up

Authorized 2026-10-19, branch `eval/nonuniform-allocation`. **GPU work reauthorized
by the user; sequential execution starting.** This is a quality/allocation experiment,
not authorization for a llama.cpp port or a production-performance claim.

## Question

At a fixed total cache budget, does assigning different numbers of prefix rows
to different layers/heads improve the compiler or Attention Matching (AM),
relative to their uniform-budget controls?

Uniform allocation fits the current inference layout but is not established as
quality-optimal for either method. Existing results do not answer this question.

## Order and boundaries

1. Finish and audit the public-clone reproduction, including its new evaluations
   and response-bound review. Track that work in `GITHUB_RECREATION.md`; an exited
   wrapper is not proof of success. Fresh27BAM/controlled4B reproduction remain
   ahead of this study in the existing sequence unless the user changes priority.
2. Check free disk and GPU availability, then freeze the precise allocation
   protocol, implementation gates and one budget before fitting or scoring.
3. Run the bounded allocation study sequentially; preserve failures and all
   uniform controls. No concurrent reproduction/allocation GPU jobs.

Do not edit the immutable reproduction clone or its live artifacts. New allocation
outputs need a separate source snapshot/output root. No public push authorized.

## Frozen design requirements

- Test **both compiler and AM**, each with uniform and allocated budgets. Choose
  one model and one total budget, not a sweep across models/budgets. Choose them
  for feasibility/protocol reasons, not by screening evaluation outcomes.
- Use the same calibration examples, source prompt and base-model identity.
  Select allocation using calibration and, where available, validation only.
  Do not allocate based on knowledge/tool/behavior test failures or published
  test-score improvements. These are already inspected development tests, not a
  new holdout; disclose that limitation.
- Freeze the allocation rule and its search/selection budget, per-head limits,
  rounding, exact total accounting, seed and validation criterion in a manifest
  before new evaluation outputs. Do not assume the best AM allocation is also
  the best compiler allocation. Use comparable allocation-selection effort and
  record method-specific objectives and extra calibration compute.
- Preserve the underlying fitting recipes. Allocation is the intended change;
  do not silently add on-policy recapture, new calibration data or alter losses.
  Record unavoidable changes separately, including any precision failure.
- Compare allocated vs uniform **within each method at fixed payload bytes**.
  Cross-method comparison must also account for K/V dtype, AM row bias and
  unchanged recurrent state; equal row sums alone are not equal memory.
- Verify each installed head length/mask, causal live-token handling and cache
  reload before quality generation. A padded/masked research implementation is
  allowed for quality measurement, but report padded allocation separately from
  useful payload. No measured memory/speed benefit without actual measurement.
- Use the same frozen evaluation cases/graders and controls, retaining every
  failure/cap and comparing paired outputs. New behavior responses require new
  manual labels with the existing AI-assistant/unblinded disclaimer.
- Report quality changes, total useful and allocated bytes, fit/allocation time,
  peak memory and backend restrictions. No best-seed/test-selected checkpoint,
  pooled winner, independent-review or production-readiness claim.

## Implementation ceiling

First answer the quality question with the smallest correct research path.
Variable lengths across heads need padding/masks or packed execution; standard
llama.cpp does not supply this as a drop-in cache configuration. Fixed offline
prefix allocation avoids dynamic prefix redistribution but does not remove the
attention-kernel/cache-layout work. A production backend is a separate decision
only if measured quality gains justify it.

## Current status

No allocation rule fitted, no new allocations/caches, and no quality results yet.
After the laptop restart, remote reproduction wrapper1849965/runner1849969 was
confirmed active at2026-10-19T09:42:14Z: capture, projections and both uniform fits
complete; historical stress evaluation active (6/19 phases completed). Local
monitor restored; remote job did not need restarting. No allocation GPU work.

CPU-only preparation: `scripts/head_allocation.py` chooses one measured row budget
per head with an exact total using dynamic programming. It minimizes the sum of
supplied head losses, including nonmonotone curves; it is not a claim of optimal
end-to-end quality or the upstream AM allocation implementation. Exhaustive tiny
fixtures verify the solver, deterministic ordering, and invalid/unreachable budget
rejection (`tests/test_head_allocation.py`). The failing test first confirmed the
helper was absent; all fixtures pass after implementation.

Still to freeze before any allocation measurement: model/budget, curve-generation
protocol and selection split, per-head candidate row counts, common comparison
criterion and selection compute. This utility alone does not select any of them.

## Execution protocol v1 — fixed before allocation measurements

The user's latest “do nonuniform” prioritizes this experiment ahead of further
AM/4B reproduction. GitHub27B completed19/19phases and final960responses;
all152phase-output hashes verified. Knowledge/tool totals match publication;
new behavior review remains pending and is not used to choose allocations.

- Model: same pinned27B, fresh812captures from
  `/mnt/data/artifacts/kvcompile/github-recreate-20261019/27b`, seed0.
- One mean budget:4096rows/head across16layers×4KVheads =262144head-rows.
  Candidate counts per head:2048,4096,6144. This fixed three-point grid limits
  search cost and padding; do not change it after inspecting results.
- Both methods obtain full fits at all three grid budgets. Compiler retains
 400steps/layer,LR.001,projected/cosine/gated loss,freeze-sink,72samples/update,
 original48+24sampling. Reuse verified fresh4096fit; other fits start from teacher.
 AM retains upstreamRMS/NNLS2/unregularizedLSQ,FP16K/V/beta,all812queries,seed0.
 Any overflow is a recorded failure, not permission to clamp or change precision.
- Measure curves on72calibration examples chosen once with original48+24sampling,
 NumPy RNGseed1729. These are training examples, NOT held-out validation.
 Evaluation questions/scores cannot enter allocation.
- Common cost proxy: replace one KVhead's attention output with that from its
 fitted prefix plus causal liveK/V, leaving other heads' outputs at teacher.
 Measure projectedMSE+cosine with original gates and equal example/query weights.
 The exact DP minimizes the sum of these isolated-head costs at262144rows.
 This ignores cross-head/layer interactions: it is proxy-optimal on this grid,
 NOT globally quality-optimal or upstream's perplexity-based allocator. Use the
 same proxy/data/grid for both methods; record their different fitting costs.
- Final compiler fits selected head lengths jointly perlayer from teacher for
 400steps; padded rows are masked during attention/fitting, keeping its original
 projected objective. Do not label spliced independently optimized heads a joint fit.
 AM reuses independent perhead grid solutions at the selected lengths.
- Uniform/allocated inference share a session-local SDPA padded/masked wrapper.
 Gate uniform compiler native parity, unequal-head explicit attention, causal
 live writes, recurrent injection and exact reload before scored generation.
- Useful compilerKVbudget256MiB;AM adds0.5MiBbeta. Each method's allocated/uniform
 payload is equal; cross-method bytes differ by beta. Report physical padding,
 cache capacity and temporaries separately; no memory/speed saving claim.
- Evaluate same240cases for all fourvariants, new manual behavior labels required.
 Reuse hash-identified freshfull/nonecontrols but rerun uniformcompiler via wrapper.
 No test-based changes, bestseed/checkpoint selection, or production-backend port.
- Resume gridfits/finalcompiler perlayer,AMperhead,curves perlayer,evaluationpercase.
 Separate source/output `nonuniform27b_v1`, oneGPUjobatime. No public push.

This is a bounded calibration-proxy allocation follow-up, not a reproduction of
AM's strongest allocator. A negative result cannot rule out better allocators.

## User pause — 2026-10-19T11:55:34Z

Grid wrapper1896783 and compiler child1896787 stopped by exact PID; both confirmed
exited, and the wrapper cannot launch6144next.2048fit was in its first layer
(layer3, last logged75/400steps); no completed layer/checkpoint was saved. Resume
must restart that layer.6144fit never started. Fresh4096/8192reproduction artifacts
remain unchanged. Wrapper trap printed status0 on termination: this is NOT a
successful gridfit; output directory contains no completed artifact.

CPU-only padded-head preparation `nonuniform_cache.py` plus tiny regression passed
in isolatedhf-env: explicit unequal-head GQA/causal reference, uniform objective/
initialization parity, zero gradients on padding, and invalid-length rejection.
No GPU parity gate or nonuniform quality result yet. Keep these code checkpoints;
do not resume GPU work automatically.

## CPU preparation checkpoint

User authorized finishing preparation only, stopping before GPU. Padded exports
now use atomic writes, canonical zero padding and FP16 finite/cast-overflow checks;
loader verifies all16layers, hashes, shapes, lengths and padding. Tiny CPU fixture
roundtrips and rejects tampered/incomplete exports. Tests run with GPU visibility
disabled; no model load or GPU call. This does not pass the future native gate.

### Prepared entry points (GPU remains paused)

`scripts/nonuniform27b.py` wires the fixed protocol to existing solvers/graders.
All GPU commands require explicit `--allow-gpu`; there is no automatic launcher.
Use immutable source and a new empty output root, not the interrupted grid folder.

CPU-only preparation after source export:

```sh
python scripts/nonuniform27b.py prepare --reference /path/to/fresh-27b-reproduction --out /path/to/new-nonuniform-output
```

This verifies152reproduction hashes, binds source/capture/teacher/projections and
calibration inputs, and selects the fixed72training indices. No fit or allocation
is performed. Full-artifact prepare was not run during the pause.

After separate GPU permission, in sequence (all commands need `--out`):

1. `compiler-grid --slots N` for2048/6144,400steps/layer/completed-layer resume;
   verified fresh4096fit reused.
2. `solver-gate --model MODEL` inhf-env, then `native-gate --model MODEL` inexl-env;
   `am-fit --slots N --model MODEL --gate OUT/am-gate/gate.json` inhf-env for all
   threebudgets. No FP32fallback.
3. `curves --method compiler|am` inexl-env, perlayer identity-bound resume;
   CPU-only `allocate --method METHOD` applies exactDP to frozen trainingproxy.
4. `compiler-fit` inexl-env jointly fits selectedheads, perlayer atomic/hashcheckpoint.
   CPU-only `export --method METHOD --variant uniform|allocated` for fourvariants;
   AMreuses independentgridheads. Exports report useful/paddedbytes, zero padding.
5. `smoke --model MODEL` inexl-env: fourvariant reload/recurrentchecks and uniform
   nativecompiler tokenparity/maxlogitdiff<=.25. No threshold relaxation.
6. CPU-only `freeze --model MODEL` requires accepted source/artifact-bound smoke;
   `evaluate` inexl-env uses existing240casegrader/percase resume. New manual
   labels use `evaluate.py report`, not inherited labels.

GPU commands also need `--allow-gpu`; environment variables point to isolated
pinned runtimes. Pickle captures are trusted local artifacts only. No source
export, full-artifact prepare, fitting, allocation measurement, native gate or
GPU job launched in this preparation turn. Real-shape/native/VRAMchecks remain.

Tiny CPU checks cover ragged/GQA/causalattention, uniformloss/initparity,
paddinggradients, export/reload/tamper/bytes, exactbudget/resumeidentity,
smokebinding/NaNrejection, independentprojectedcost, and actualgraderloop with
fakeCPUmodel/fourarm output and partial/completedresume. GPUvisibilitydisabled.
Compiler grid/final fits use the sameexl-env/Torch2.13as freshuniformcontrol;
AMsolving useshf-env/Torch2.8as before. No runtime-version change within compiler
uniform/allocated fitting. CPUtests usehf-env only and do not create study artifacts.

Implementing checkpoint `ce0bd15`: Git-free export passed all30small-dependency
CPUtestfiles, exact558file/557hash inventory and obvious-credential scan. Both
Torch CPU fixture files also passed in the isolatedhf-env with GPU visibility
disabled. Logs `/tmp/opencode/nonuniform-prep-cpu.log`; test scratch source
`/tmp/opencode/nonuniform-prep-verified`. No artifact protocol preparation or GPU
study step has been run. Pause boundary is the first real GPU gate/fit; permission
is still required before crossing it.

## GPU authorization and execution — 2026-10-19

User explicitly unblocked GPU. New output root
`/mnt/data/artifacts/kvcompile/nonuniform27b_v2`; the interrupted v1 directory
remains untouched.47GiB free at prelaunch; no competing model process observed.
Use an immutable source snapshot, existing isolated runtime and fresh27Bcapture.
First prepare exact input identities, solver/native AM gates, then three AMgrid
fits. Failure stops without precision fallback. Next compiler2048/6144fits,
method-specific curves/allocation, allocatedcompiler fit, four exports, train-only
smoke gates, freeze and final240×4generation. Completed stages validate their
durable outputs before skipping on resume. No new quality result claimed yet.
Logs `/tmp/opencode/nonuniform-v2-*.log`; manual review follows generation.

Launched at2026-10-19T15:52:48Z: immutable source checkpoint `eb3c402` exported to
`/mnt/data/artifacts/kvcompile/nonuniform-v2-source`; sequence wrapper PID1910308,
prepare child PID1910311. Initial input-hash audit is active, not yet a passed
gate or completed fit. Main log `/tmp/opencode/nonuniform-v2-sequence.log`;
stage receipts `/tmp/opencode/nonuniform-v2-stages`, current child PID recorded in
`/tmp/opencode/nonuniform-v2-child.pid`. Wrapper stops on any nonzero child exit;
completion/failure record `/tmp/opencode/nonuniform-v2.exit`. Old v1 untouched.

### First verified GPU checkpoint

Input audit passed in97.1s. AM solver gate passed (812 shared examples,4096rows,
Torch2.8/ROCm6.4): solver30.742s. Native gate passed in107.242s after runtime/model
verification: identical greedy tokens, maxlogitdifference0.0234375<=0.25,
nonzero-bias save/reload exact, recurrent injection exact, peak14.248GiB.
Evidence `nonuniform27b_v2/am-gate/{solver,gate}.json` and `head.safetensors`.
This establishes wrapper compatibility, not nonuniform quality or native ragged
kernel support. At15:58:06Z sequence started AM2048fit, child1910969; no completed
grid fit/allocation/evaluation result yet. Active source remains `eb3c402`, not
these later report-only updates. Failure still halts without precision fallback.

Direct PID/log polling requested by user (background notifications unreliable).
AM2048 completed all64heads/16layers, manifest `complete=true`, fit190.692s;
wrapper hashed82outputs and started AM4096 at16:01:54Z (child1911073).
At16:04:45Z AM4096 reached29/64heads; no allocation or quality claim. Data
storage remains47GiB free. Poll exact wrapper/current-child PIDs, not name matches.

### Halted on AM6144 nonfinite result — 2026-10-19T16:09:30Z

Direct polling caught sequence exit1 after1002.2s wall time. AM2048 and AM4096
completed64/64heads and16/16layers: fit190.692s and261.463s respectively. CPU-only
postfailure audit verified all32completed-layer hashes and finite tensors in all
128saved head files. These are fitting artifacts, not evaluation results.

AM6144 failed the finite-result assertion in `am_block_scores.py:61` while fitting
layer19/head1 (zero-based):17heads saved, fourcompletedlayers (3,7,11,15), nexthead
not saved. All17saved heads are finite. Manifest remains `complete=false` and its
118.273s is only the last completed-layer checkpoint, not total failed fit time.
The log shows the failed head reached value LSQ; the nonfinite component and
whether this is FP16 cast overflow are **not yet isolated**. Do not infer the cause
from the historical8k failure alone.

Wrapper1910308 and child1911177 are confirmed exited; no compiler directory,
curves, allocation, export, smoke or evaluation was produced.46GiB data space
remains. Failure evidence and all partial outputs preserved in the v2 root;
log `/tmp/opencode/nonuniform-v2-am6144.log`, exit record1. No precision fallback,
budget alteration, dropped head, retry or continuation launched. Fixed FP16 study
is blocked pending a separately authorized next step.

### Authorized failed-head diagnostic — 2026-10-20

User approved exact failed-head replay only. Generalized the existing
`am27b_diagnose.py` to select6144rows/layer19/head1, restore RNG from savedhead16,
validate capture/recipe/wrapper/upstream/runtime identity, and inspect the same
LSQ solution before/after FP16 casting. No solver/precision/objective change,
fit continuation, or writes to failed-fit outputs. CPU classification check
passed for finite output, finite-FP32/cast-overflow and nonfinite solver output.
Diagnostic is separate from immutable `eb3c402` study source; results pending.

### Diagnostic result: confirmed FP16 value overflow

Diagnostic checkpoint `145fdbd` completed successfully in19.571s, wrapper1911573 /
child1911575 confirmed exited, diagnostic exit0. Exact failed-head RNG restored
from `am6144/heads/head_016.safetensors`; capture/recipe/runtime/upstream/wrapper
identities validated. Same-call LSQ interception left solver results untouched.
The6144×256 FP32 value solution is entirely finite, maxabsolute71021.34375;
casting to FP16 creates exactly one nonfinite value (FP16maximum65504).
Returned K and beta remain finite; returned V does not. The preceding NNLS
least-squares call is also finite. Thus the replay reproduces the failure and
isolates it to value casting, not nonfinite FP32 LSQ output.

Evidence `results/NONUNIFORM_AM6144_FAILURE_DIAGNOSTIC.json`, mirrored from
`nonuniform27b_v2/am6144_failure_diagnostic.json`; log
`/tmp/opencode/nonuniform-am6144-diagnostic.log`. XTX log UTC18:18:13 onOct19
(host date differs from sessionOct20). No failed-fit file or immutable study
source changed. No FP32V artifact was fitted/exported, no full fit/evaluation
resumed, no clamp/ridge/head removal/budget change applied.

Original fixed-FP16 allocation study remains blocked. A separate FP32V extension
would require explicit approval, matched precision across AMuniform/allocated
arms, new byte accounting and gates; it is not an automatic repair or equal-memory
comparison with FP16compiler. No such extension launched.

## Authorized FP32V extension — 2026-10-20

User approved reusing existing FP32V code to continue. Separate output
`/mnt/data/artifacts/kvcompile/nonuniform27b_fp32v_v1`; original failed FP16v2
and its saved2048/4096/partial6144artifacts remain unchanged. Same model,
captures, grid2048/4096/6144, mean4096rows/head, calibration72/seed1729,
exactDP, compilerobjective/400steps/seed0, and final240cases. Only AM value
retention/storage uses FP32, for **all grid heads and both AM variants**;
K/beta remain FP16. Refit AMgrid from seed0, never upcast completed FP16values
and pretend their lost precision is recovered. Compiler remains unchanged FP16
inference with BF16export intermediate, same isolatedTorch2.13fit runtime.

Reuse existing `block_scores(values_dtype=torch.float32)` and `prefix_bias`
FP32value sidecar. Generalized existing solver/native gates to read the failed
head identity from diagnostic, not hardcoded8k/layer23/head3. Require same-call
exact LSQ retention, reload, finite failed-head generation, promotioncontrol and
original recurrent state. Gates run before fullgrid; no clamp/ridge/drophead.
New padded loader/export/curves/evaluator preserve FP32V and reject mismatched
precision, lengths, hashes and bytes. Explicit zero-valued native FP16V
placeholders avoid casting overflowing V into nativecache.

At fixed262144head-rows, useful compilerKV256MiB versus AMFP16K/FP32V384MiB
plus0.5MiBbeta; equal row count, **not equal bytes across methods**. Each method
uniform/allocated has equal useful bytes internally. Max6144padding adds
storage, FP32sidecars coexist with nativeFP16placeholders, original151.5MiB
recurrentstate remains; no processVRAM/speed-saving claim. Export manifests
report useful/padded tensors and native prefixVplaceholder bytes separately.

CPU ragged export/sidecar test first failed for missing FP32support, then passed:
71021.34375retained exactly, nativeplaceholders zero, maskedpadding, precision/bytes
rejection. Shared runner fixture verifies FP32sidecar reaches existing attention
context, including interrupted/completedresume. No shared runtime source or
dependencies changed; no public push. Sequential execution/directPIDpolling;
failurehalts. Real FP32gates/grid/allocation/evaluation pending at this checkpoint.

### FP32V gates accepted; grid active

Immutable source `115cd1d` exported to
`/mnt/data/artifacts/kvcompile/nonuniform-fp32v-source`. Git-free560file/559hash
inventory and30small-dependencyCPUfiles passed; Torch fixtures passed separately.
Wrapper1912061 launched18:25:22Z(XTXOct19), mainlog
`/tmp/opencode/nonuniform-fp32v-sequence.log`, currentchild
`/tmp/opencode/nonuniform-fp32v-child.pid`, receipts
`/tmp/opencode/nonuniform-fp32v-stages`, terminalrecord
`/tmp/opencode/nonuniform-fp32v.exit`. Each verified stage appends a checkpoint to
output `execution.md` before the next stage, without editing immutable source.

Input audit96.0s; baseAMgates passed. FP32failed-head solver gate27.108s:
same-call LSQVretention exact, allfinite, max71021.53125, oneInfifFP16cast.
Previous diagnostic max71021.34375 differs slightly across solves; no cross-run
bit-determinism claim. Nativegate78.759s, promotiongreedyexact/maxdiff.0234375,
finitefailed-headEOS, save/reload exact, recurrentinjectionexact, peak13.971GiB.
Evidence `NONUNIFORM_FP32V_{SOLVER,NATIVE}_GATE.json` mirrors outputfp32-gate.
At18:33:25Z AM2048FP32Vfreshfit started child1913120;46GiBfree. AllthreeAMgrid
fits must finish before compilergrid, curvesDP and finaljointfit/exports/smokes/
freeze/240×4eval. No allocation or qualityresult yet. OldFP16v2 unchanged.

### AM FP32V grid complete; compiler grid started

Direct polling confirmed allthreegrid fits exited0 and completed64heads/16layers:
2048rows192.702s;4096rows268.482s;6144rows346.988s. CPU-only postfit audit
verified51manifest/layer hashes, all48layersfinite, allVFP32 and K/betaFP16;
the failedFP16layer19/head1 is now retained without overflow. Mirrored manifests
`results/NONUNIFORM_FP32V_AM{2048,4096,6144}_MANIFEST.json`. No inference quality
or allocation claim follows merely from finite fits.

At18:48:50Z(XTXOct19) sequential launcher started compiler2048: CLIparent1913477,
optimizer1913486, wrapper1912061 still active. Fresh firstlayer3 loggedstep0/400;
no completed compilerlayer yet.44GiBfree. Compiler6144/curvesDP/jointallocatedfit/
exports/smoke/freeze/eval remain queued sequentially, failurehalts. Active source
`115cd1d` is unchanged; local report/evidence updates are not deployed into it.

Direct poll18:55:35Z confirmed compiler2048firstlayer3 checkpoint saved after
400steps/364.6s; layer7 now active. Logged calibration minibatchloss.1600→.004428,
not a qualitymetric. Compiler reports roughly91minutes remaining at firstlayer
rate;6144grid and finalallocatedfit are additional work, so no fullstudyETA yet.
Exact optimizer1913486/wrapper1912061 alive, no failure record at latest poll.

UserAFKfollowup: continue direct polling to completion or concrete failure;
then start existing boxminer only after allGPUresearch/checks/evaluation finish
and noGPUprocess remains. Do not change mining configuration or enable bootstart.
Latest directpoll20:05:59Z(XTXOct19): compiler2048saved12/16layers, layer51active;
no failure, wrapper1912061 and optimizer1913486alive. Both miner.service and
miner-guard.service are inactive; existingmanualminer config/temperatureguards
will be reused only after completion. Failure is not successful completion.

### Grids, curves and exact allocation complete

Compiler2048completed16layers5831.685s,6144completed16layers6856.530s;
reference4096unchanged. Both16layercurve files and exactDP allocations completed
before allocated fitting. Compiler headcounts:21×2048,22×4096,21×6144; AM:
19×2048,26×4096,19×6144. Each262144head-rows, fixed before finalfit/evaluation.
Compiler isolated proxy summedcost uniform1.766169→selected1.461528; AM
.268019→.178801. These calibrationobjective reductions are selection metrics,
not testquality, jointloss guarantees, or comparable cross-method scores.
Mirrored `NONUNIFORM_{COMPILER,AM}_{CURVES,ALLOCATION}.json` and compilergrid
manifests. Wrapper stagehashreceipts validated durableoutputs before nextstage.

Joint allocatedcompilerfit started22:27:01Z(XTXOct19), child1915325; at22:44Z
twoof16layers saved, thirdactive. Wrapper1912061 alive, no failure. Miner off.

### Final fit and native smoke complete; evaluation active

Allocatedcompilerfit completed16/16layers in6899.247s, fixed400steps each.
Allfour exports passed identity/shape/precision/padding/hashchecks. Train-only
smoke67.394s/14.037GiB: fourvariants exactsave/reload and recurrentinjection,
uniformcompiler nativegreedytokensequal/maxlogitdiff.03515625<=.25. Mirrored
`NONUNIFORM_COMPILER_ALLOCATED_FIT.json` and `NONUNIFORM_SMOKE.json`.
Final240×4freeze accepted; evaluation child1916784 under wrapper1912061.
Directpoll02:01:41ZOct20 reached950/960responses with no failure. GPUwork still
active, mineroff, semanticreview/audit pending; do not call this completedquality.

## Completed — 2026-10-20T02:04:09Z

All22stages exited0,960responses generated in5581.138s; wrapperwall27526.5s.
179frozenfiles/380stageoutputhashes and four240case inventories audited in127.168s;
completedresume skipped generation. All480behavior responses read assistant/
unblinded and newresponsehash-bound labels recorded. Results, failures, useful/
paddedbytes and methodlimitations in `results/NONUNIFORM_RESULTS.md`; no overall
winner/generalization/equalmemoryclaim. OldFP16failure/source/artifacts untouched.
AllGPUresearch processes exited; minerhandoff pending idlecheck and savedsetupstart.

Miner handoff: after review/report checkpoint `6d308d0`, verified zero activeAI
services and zeroGPUdeviceholders; idleVRAM26.7MiB. Started existing
`~/mining/mine start` unchanged. `miner.service` active/running, mainPID1944527;
bootenablement remains disabled. Hashrate/share verification is backgrounded and
pending, not a confirmed hashing/payout result. No further GPUresearch queued.
