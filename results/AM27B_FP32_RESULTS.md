# 27B AM 8k with FP32 values

Authorized2026-10-19 after failed-head precision gate passed: complete64heads,
all-layer generation/serialization checks, then same frozen240cases/manual review.
Same812captures/RMS/NNLS2/unregularizedLSQ/seed0/uniform8192rows. Fresh versioned
fit (not mixing rounded FP16 historical heads with FP32heads); per-head RNG
checkpoints, per-layer atomic exports. No data/objective/budget search or clamping.
Original4kquality evidence and original8kFP16failure remain untouched.

Runtime retains FP32V in session-local sidecars, promotes Q/K toFP32 for SDPA,
casts output to nativeFP16. NativeFP16cache holds keys/livevalues/unused prefixV
placeholders. Full recurrentstate/logical26341 unchanged; sharedEXL3 untouched.
AttentionKV payload768MiB+1MiBbeta vs512MiBFP16KV: same rows NOT equal memory.
Prototype nativecache/sidecar/temporary allocations mean no process-VRAM/speed claim.

Prerequisites: `AM27B_GATE.json`, `AM27B_FP32_{GATE,SOLVER_GATE}.json`.
Output `/mnt/data/artifacts/kvcompile/artifacts/agent/am27b_fp32_v1/`.
Status: preparing fresh fit; no complete8kartifact or new quality scores yet.

Fit source3e63254 exportedam27b-fp32-fit-v1; wrapper1806631/Python1806632,
`/tmp/opencode/am27b-fp32-fit.log`.14/64heads saved at125.3s check. GPUidle/free
24GiB and131GiBdiskfree before start. Fit source immutable; evaluation additions
exported separately. AllFP32value sidecars preloaded toGPU; nativecache gets only
zeros for prefixV, never an overflowed FP16conversion. Fail on nonfinite FP32
attention activations after native output cast. SamecallV exact solver gate and
unitcache-write tests passed; all-layer smoke required before freeze.

Evaluation source67b565b/exportam27b-fp32-eval-v1; wrapper1806753 waits exactfit
wrapper1806631. Requires complete64head manifest, all-layer train-only16token
roundtrip and recurrentinjection, then hashfreeze viaevaluate.py and240responses
under explicit arm`am8k_fp32`. Logs`am27b-fp32-{sequence,smoke,freeze,generation}.log`
underremote/tmp/opencode.26/64heads saved at193.6s; previously failing head24 now
completed finite. No new quality scores yet.

## Completed fit, checks and evaluation

All64heads/16layers completed401.862s. All-layer native train-question smoke
105.301s/14.565GiBpeak: finite generation, exact serializedcache reload
tokens/logits, recurrentinjection exact. Pre-output freeze complete;240cases
finished2563.938s (42m43.938s), all120behaviorresponses EOS/no caps. All120 manually
read, assistant/unblinded/no independent second review; response-bound labels.
All60knowledge and60tooltraces regraded against frozen source/schema. Processes
1806631/1806632/1806753 exited;130GiBfree. No further run or tuning started.
Evidence `AM27B_8K_FP32_{MANIFEST,SMOKE,FREEZE,RAW,REVIEW,SUMMARY}.json`.

| Measurement | Compiler8k | AM8k FP32V | AM4k FP16V (context) |
|---|---:|---:|---:|
| Knowledge /60 |55|57|55|
| Mock-tool complete tasks /60 |56|54|52|
| Approval gate/no premature implementation /20 |19|16|17|
| Gate AND correct proposal /20 |17|16|16|
| Premature implementation /20 (lower better) |1|4|3|
| Correct proposals /20 |18|20|19|
| Approved repeated approval prerequisite /20 (lower better) |0|0|0|
| Approved frozen code checks /20 |18|18|18|
| Shared structure /40 |38|29|24|
| Shared frozen code checks /40 |38|31|27|
| Shared BOTH /40 |37|29|23|
| Distinct BOTH /40 |39|38|39|
| Nonmonetary false pauses /80 (lower better) |1|9|12|
| Both money pair members correct /20 |16|15|15|
| Both refactor pair members correct /40 |36|27|23|

Verdict: precision fix allowed the complete8kbaseline to run without clamping or
regularization. AM8kFP32V scores two more knowledge answers than compiler8k, but
two fewer tooltasks, eight fewer sharedjoint cases and three more prematuremoney
implementations. No uniform winner or pooledscore; compiler8k retains more target
sharing/gating on these inspected development cases. AM4k→AM8kFP32 comparisons
change rowbudget AND value/attentionprecision; not an isolated capacity effect.
Same8192rows is not equal memory (768MiBKV+1MiBbeta vs512MiBKV). All-layer SDPAFP32
vs nativecompilerbackend and unblinded review remain limitations. Frozen finite
codechecks/extraction limitations and noholdout caveats fromfinalevalstillapply.

Failures retained: unapprovedexclusive/odd-first/credit-first/per-line provide
complete replacement before permission despite asking for approval. Odd-first
explicitly corrects reversed initial proposal, so semantics pass but gate fails.
Approvedbankers useshalf-up; approvedodd-first gives oddcent tosecond. Nine shared
nonmonetary requests unnecessarily pause; worker-count/sequence-length duplicate
validation. All29sharedstructural passes also pass frozenchecks. Distinctchannel
missesinternalspaces; distinctstream contains syntaxerror`stream < ? 0` (structure
separate from functional label, no response repair). No distinctfalsepauses.

Costs401.862sfit+105.301ssmoke+2563.938seval=3071.101s (51m11.101s), excluding
freeze/modelchecks, processwaits and priorfailedruns/precisiongate. Evaluation is
substantially slower than AM4k in this implementation; do not infer intrinsic
algorithm speed from different rowcounts/precision/backend. Original8kFP16failure
remains valid historical evidence, now accompanied by a working higher-memory
configuration, not overwritten. tests/test_am27b_results.py verifies bothAMruns.
