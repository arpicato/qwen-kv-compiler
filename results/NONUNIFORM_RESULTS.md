# Uniform versus nonuniform prefix allocation — 27B

**Completed exploratory, single-seed development study.** Allocation improved
some observed behavior outcomes but not all knowledge/tool outcomes. No overall
winner, independent holdout, equal-byte cross-method comparison, production
memory saving, or speed improvement is established. All480behavior responses
were read by the AI assistant, unblinded; no independent review occurred.

## Method and testing

Compare uniform4096rows per KVhead against calibration-selected2048/4096/6144
lengths across64heads. Each arm has262144useful head-rows. Exact dynamic
programming minimizes summed isolated-head projected attention-output MSE+cosine
on72fixed training examples (seed1729; original48catalog+24policy sampling).
This proxy is not downstream test quality or upstream perplexity allocation.
No evaluation outcome selected head budgets or final checkpoints.

Compiler fits synthetic K/V to attention outputs, jointly perlayer for400steps;
allocated heads are trained jointly after lengths are fixed, not assembled from
independent head fits. AM uses pinned upstream RMS-key selection, NNLS2 weights
and unregularized LSQ values, off-policy on shared812captures. AMallocated can
reuse independent gridhead solutions. Same fresh public-clone27Bcaptures,
projections, prompt and original recurrentstate; no on-policy/data/loss changes.
Both variants use the same padded/masked SDPA inference path within each method.
Compiler's uniform wrapper matched native tokens, maxlogitdiff.03515625<=.25.

The original FP16AM6144 fit failed: one value overflowed after a finite FP32 LSQ
solution. Exact diagnostic and all failed/partial artifacts remain preserved.
User authorized a separate extension retaining FP32V for **all** AMgridheads and
both AMarms; FP16K/beta unchanged. This reuses the earlier FP32sidecar code,
not clamping, regularization, dropping a head, or upcasting oldFP16 solutions.
Same-call LSQ retention, promotioncontrol, finite generation and exact reload
passed before full fits. See `NONUNIFORM_ALLOCATION_PLAN.md` for protocol/history.

Final evaluation uses the unchanged240case bundle:60knowledge,60mocktooltasks,
20unapproved/approved monetary pairs and40shared/distinct refactor pairs.
Knowledge/tool scoring is frozen automatic grading; code runs in isolated Docker;
manual behavior labels distinguish approval compliance, proposal correctness,
shared execution structure, functional tests and false pauses. All cases retained,
no pooled score. Full/no-prefix controls are the earlier same-prompt frozen27B
controls (`FINAL_EVAL_RESULTS.md`), **not freshly rerun as part of this four-arm
study**. This bank is historically inspected, not independent validation.

## Outcomes

Counts below are uniform→allocated; knowledge/tools each outof60, approval
conditions each outof20, shared/distinct each outof40. False pauses cover the
same80nonmonetary refactor cases, not an additional test bank.

| Outcome | Compiler | AM, FP32V |
|---|---:|---:|
| Knowledge correct |46→53|55→53|
| Mocktool tasks correct |51→48|52→52|
| Unapproved money: gate obeyed |20→19|17→20|
| Unapproved money: correct proposal |17→19|19→19|
| Unapproved money: gate **and** correct proposal |17→18|16→19|
| Premature implementations |0→1|3→0|
| Approved money: no new approval prerequisite |20→20|20→20|
| Approved money: functional |18→18|18→19|
| Shared refactor: structure |20→24|23→32|
| Shared refactor: functional |21→30|29→29|
| Shared refactor: structure **and** functional |19→23|22→29|
| Distinct refactor: structure **and** functional |39→39|39→39|
| False approval pauses /80 |18→9|10→7|
| Both monetary pair members joint /20 |17→16|15→18|
| Both refactor pair members joint /40 |19→23|22→29|

Compiler knowledge has9gains/2losses, tools7gains/10losses. AMknowledge has
1gain/3losses, tools2gains/2losses: unchanged aggregate tools is not percase parity.
The compiler loses a monetary pair despite a higher unapproved gate+proposal
total. AMshared functional total stays29while structure improves; allocation is
not a universal correctness fix. All480behavior outputs ended EOS, zero caps.

Failures retained include incorrect half-up/tie-even proposals, already-approved
banker's-rounding bugs, wrong first-recipient allocation, zero-boundary mistakes,
internal-space validation failure and one malformed AMallocated patch. Working
code followed by a confirmation request is not a withheld-implementation pause.
Shared helper execution can pass structure while enforcing the old numeric bound;
functional failure is separate. Finite assertions and float-based monetary
formulas do not certify arbitrary-precision money correctness. Frozen extraction
rules and all previous study results are unchanged.

## Allocation and bytes

| Method | Heads at2k/4k/6k | Useful K/V+beta | Uniform padded tensors | Allocated padded tensors |
|---|---|---:|---:|---:|
| Compiler |21/22/21|256MiB|256.5MiB|384.75MiB|
| AM FP32V |19/26/19|384.5MiB|384.5MiB|576.75MiB|

Compiler's zero beta is wrapper overhead, not useful fitted payload. AMFP32V
also has native FP16Vprefix placeholders:128MiB uniform,192MiB allocated, on top
of sidecar storage; full native paged allocation/live capacity is additional.
Original recurrentstate151.5MiB remains. These are useful/export/prefix-overhead
counts, **not measured processVRAM savings**. Equal useful bytes within a method;
AM versus compiler is not bytefair. Padded allocated paths occupy more storage.

Selection proxy totals: compiler1.766169→1.461528, AM.268019→.178801. These are
calibrationproxy improvements by construction, not comparable cross-method
quality scores or proof of global optimality for joint downstream behavior.

## Execution, validation and evidence

Immutable source `115cd1d` at
`/mnt/data/artifacts/kvcompile/nonuniform-fp32v-source`; outputs
`/mnt/data/artifacts/kvcompile/nonuniform27b_fp32v_v1`. Shared runtimes untouched.
AMsolver Torch2.8/ROCm6.4; compilerfits Torch2.13/ROCm7.2, matching uniformfit.
Sequential wrapper1912061 exited0 at2026-10-20T02:04:09Z; allGPUchildren exited.
Wall27526.5s (7h38m46s); generation5581.138s; audit127.168s. Costs include
repeated identity/model hashing, reused4096fit/captures are not new fit cost.

AMgridfit192.702/268.482/346.988s for2k/4k/6k; compiler2k5831.685s,
6k6856.530s; jointallocatedcompiler6899.247s; finalsmoke67.394s/14.037GiB
peak in that smoke only. Backend/padding/precision differ; no fair speed ranking.

### Observed wall-clock costs

| Fitting work | Compiler | AM FP32V |
|---|---:|---:|
| 2k grid fit, internal timer |5831.7s (97.2min)|192.7s (3.2min)|
| 4k uniform fit, internal timer |6451.3s (107.5min), reused|268.5s (4.5min)|
| 6k grid fit, internal timer |6856.5s (114.3min)|347.0s (5.8min)|
| Final allocated fit |6899.2s (115.0min)|No additional fit; selected gridheads reused|

AM fitting was substantially faster in this implementation. Compiler fitting
cost is part of the result, not excused by downstream tradeoffs. Different
Torch/solver implementations prevent isolating an intrinsic algorithmic speedup.
Reused compiler4k time is historical measured cost, excluded from this new run's
7h38m46s total; common capture/projection costs are also reused and excluded.

| 240-case evaluation interval | Uniform | Allocated |
|---|---:|---:|
| Compiler |599.9s (10.0min)|593.6s (9.9min)|
| AM FP32V |1849.9s (30.8min)|2537.7s (42.3min)|

Intervals are reconstructed from successive240response completion logs, not
isolated inference microbenchmarks. First interval includes sharedrunner setup;
all include prefixloading, generation, Dockerchecks and saving. AM promotes
attention toFP32 and uses sidecars; larger padded allocatedprefix also costs
time. This observed path is slower to evaluate despite much faster fitting.
It does not establish general inference throughput, latency, or upstreamAMspeed.

`NONUNIFORM_TIMING.json` retains all22stage START/DONE lines, UTCboundaries and
elapsedintervals. End-to-end stagewall includes repeated sourcehashing/imports/
teardown/outputhashing: compiler2k5874.2s,6k6899.6s,allocated6936.0s versus
AM2k232.8s,4k305.9s,6k386.3s. Entireevaluationstage5652.7s versus runner5581.1s;
audit127.2s and manualreview are outside the7h38m46s automatedsequence. Failed
FP16attempts/diagnostics/earliercapture/controlfits are not hidden inside it.

Postrun audit validated179frozenfiles,22stage receipts/380outputhashchecks,
allfour240case inventories, grids/export finiteness/precision/lengths, accepted
smoke identities and completed resume without regeneration. Mirrored evidence:
`NONUNIFORM_{RAW,FREEZE,REVIEW,SUMMARY,AUDIT,SMOKE}.json`, both curve/allocation
files, grid manifests and `NONUNIFORM_COMPILER_ALLOCATED_FIT.json`.
`tests/test_nonuniform_results.py` regrades knowledge/tool traces, checks response
hash-bound review and extraction diagnostics, re-solves exactDP and rejects
tampered review bindings. No refit/case filtering/publicpush after evaluation.
