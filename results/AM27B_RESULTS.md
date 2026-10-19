# AM on the hybrid 27B model

Authorized2026-10-19: compatibility gate, then fixed4k/8k AM fits and final240case
evaluation if gates pass. No runtime edits, budget/config search or new cases.
Branch eval/am27b-baseline. Original27B/4B artifacts remain immutable.

## Frozen method before fitting

Off-policy uniform4096/8192 rows per KV head; upstream RMS-key/NNLS2/LSQ solver
commit2020f6d37940fe013e7e7f1ebf409e5d107c5670, beta bounds exp(-3)..exp(3),
seed0. Reuse reproduction27b_v1 812 captured examples/queries only after source
identity checks; 16 full-attention layers,4KVheads/layer,6GQAqueries/KVhead,dim256.
No recurrent compression: original full recurrent state/logical26341 retained.
Compiler artifacts not refit. Query weighting is uniform captured rows, not the
compiler48+24 update sampling; objectives/compute differ. Not optimized/on-policy
AM or equal-compute comparison. No output-based configuration changes.

## Compatibility concern and gate

Pinned EXL3 dispatcher has no additive per-row attention bias argument. Dropping
AM beta would change method. New session-local dispatcher uses PyTorch SDPA with
prefix-only beta, live causal mask, native Q/K norm/RoPE/gates/output projection
and native cache/recurrent path. Shared EXL3 files/environment untouched.
Batch1/contiguous pages only, fail closed on unsupported modes. CPU explicit
GQA reference required. GPU zero-beta native-vs-wrapper gate on a training-only
question:16greedytokens equal, finite logits/maxdiff<=.25; preserve failures.
Nonzero beta installation/reconstruction roundtrip and exact recurrent state
injection required before scored generation. One real4096head solver gate first.

Artifacts: /mnt/data/artifacts/kvcompile/artifacts/agent/am27b_v1/.
Status: source audit and wrapper preparation; no quality scores or full fits yet.

## Gate launched

Source f1c033f exported to releases/am27b-v1. CPU explicit GQA/causal/prefix-bias
test passed in the existing remote Python environment (local Python lacks Torch;
no packages installed). GPU was idle,132GiB free before launch. Wrapper1796711,
Python1796712; log `/tmp/opencode/am27b-gate.log`. Runtime weight hash verification
precedes one4096head fit and train-only native/zero-bias/nonzero roundtrip checks.
Status incomplete; no full fit or scored outputs launched. Remote machine still
reports2026-10-18UTC despite session date2026-10-19; keep raw timestamps unchanged.

First attempt1796712 exited atNNLS shape39630x4096 without checkpoint. Kernel
recorded libhsa-runtime64 segfaults at17:23:16Z; no Python exception/result.
EXL3 environment uses Torch2.13.0+rocm7.2; successful4BAM uses2.8.0+rocm6.4.
Separate solver-only process will use existing kvbench environment, save hashed
head/recipe, then EXL3 process validates handoff and runs compatibility checks.
No environment replacement or method/query change. Failed log remains intact.

## Compatibility accepted

Separated solver passed28.261s under Torch2.8/ROCm6.4. EXL3 native gate142.675s,
peak14.248GiB:zero-beta16token native IDs equal,logitmaxdiff0.03515625<=0.25;
nonzero4096head serialization/injection generation+logits exact; recurrentstate
injection exact. Evidence`AM27B_GATE.json`and`AM27B_SOLVER_GATE.json`.
Wrapper1796894 exited; no active projectGPUjob at acceptance check.
Proceed fixed4096then8192 fits,64heads each,per-head solver/RNG checkpoints and
per-layer atomic exports; verify all16teacher/capture KV arrays before solving.
Original812queries, no gating/weighting changes or test-based selection.

## Fixed fits active

Source3c02710exportam27b-fit-v1; wrapper1797492,4096child1797493, log
`/tmp/opencode/am27b-fit.log`. Runs4096then8192 sequentially in kvbench Python;
no model loaded during solver. Outputam27b_v1/am4096andam8192. Complete per-head
checkpoints carry RNG and recipe; all layer exports finite/hashed. No quality
score from a completed solver head. Fit source must stay immutable mid-run.
Evaluation integration is prepared separately:publicevaluate.pyfreeze accepts
--am-artifacts;run uses am4k/am8k with prefix beta and same final240/graders/limits.
Existingfull/none/joint4k/joint8ksavedresultsevidence reused,not silently rerun.

Evaluation exportsource51c616cplusrunner4a88ae5;sequentialwrapper1797576waits
exactfitwrapper1797492. Requiresbothmanifestscomplete,thenall-layer16token
nativebiasedgeneration/reloadsmokesforbothbudgets,hashfreeze,and480responses
(240cases xam4k/am8k)throughpublicevaluate.py. Logs`am27b-sequence.log`,
`am27b-smoke.log`,`am27b-freeze.log`,`am27b-generation.log`inremote/tmp/opencode.
Atfitcheck16/64heads4096saved;8192notstartedyet. No scored outputs yet.

## 8k fit failed closed

4k all64heads/16layers completed266.049s. 8k saved23/64heads and5complete layers,
then layer23/KVhead3 returned nonfinite output at17:37:08Z. Finite assertion stopped
fit before writing failed head; sequential wrapper1797576 refused incomplete8k
manifest. Both wrappers exited, no smokes/freeze/scoredresponses started.
This is not a quality result or permission to omit the failed head.
Next: exact failed-head replay with RNG restored from head22; log FP32least-squares
solution and FP16cast finiteness without solver/regularization/query changes.

Diagnostic687760d passed17.968s:FP32Vfinite,maxabs67691.234375; FP16cast has1nonfinite
entry. NNLSinitialsolutionfinite,absmax226.870. Not a general AM impossibility:
this fixed8k recipe cannot represent this head in the current FP16EXL3prefix.
No clamping, ridge, precision change, query reduction or failed-head exclusion.
Evaluate the completed finite4k artifact only with explicit --am-slots4096;
8k remains recorded failed/incomplete, not presented as an evaluated comparison.
Independent8k higher-precision integration would be a versioned follow-up.

4k-onlysource9bc62bfexportam27b-eval-4k-v1,wrapper1797842log
`/tmp/opencode/am27b-eval4k.log`;train-onlyfull4kcache16tokenroundtripthenfreeze4k
and240caseevaluation.8kfit/failureleftintact;no8kqualityscorewillbeinvented.

## Final 4k evaluation and review complete

Follow-up2026-10-19: higher-precision failed-head feasibility gate passed; see
`AM27B_FP32_GATE.md`. This fixes that head's representation failure with FP32V,
not the original8kfit. Subsequent separate full8kFP32Vfit/evaluation completed;
see`AM27B_FP32_RESULTS.md`:knowledge57/tools54,sharedjoint29/40,gate+proposal16/20,
fourprematurepatches. Same8192rowsbut768MiBKVvs512MiB,notmemoryfair. Original
failure/4kscoresremainunchanged; originalFP16recipeisstillfailed.

All240cases completed567.463s (9m27.463s); wrapper1797842 exited. All120behavior
responses EOS/no caps and manually read, assistant/unblinded/no independent second
review. Evidence`AM27B_4K_{RAW,FREEZE,SMOKE,REVIEW,SUMMARY}.json`. All60knowledge and
60tooltraces regraded against frozen inputs/schema. No post-output tuning/rerun.

| Measurement | Compiler4k | AM4k | Compiler8k (context only) |
|---|---:|---:|---:|
| Knowledge /60 |46|55|55|
| Mock-tool complete tasks /60 |51|52|56|
| Approval gate/no premature code /20 |20|17|19|
| Gate AND correct proposal /20 |17|16|17|
| Premature code /20 (lower better) |0|3|1|
| Approved false approval prerequisite /20 (lower better) |0|0|0|
| Approved frozen code checks /20 |18|18|18|
| Shared structure /40 |20|24|38|
| Shared frozen code checks /40 |20|27|38|
| Shared BOTH /40 |19|23|37|
| Distinct BOTH /40 |39|39|39|
| Nonmonetary false pauses /80 (lower better) |19|12|1|
| Both money pair members correct /20 |17|15|16|
| Both refactor pair members correct /40 |19|23|36|

AM4k leads compiler4k in knowledge and sharing on this workload; tools differ by
one case, while AM has three premature monetary patches versus compiler4k zero.
No overall winner, pooledscore, newholdout or broad superiority claim. AM4k shares
the same16attentionlayers x4heads x4096rows x256dim,FP16K/V=256MiB plus0.5MiB
FP16beta; full recurrentstate151.5MiBunchanged. CompilerBF16exports/nativeFP16
installation differ numerically from selected-original AMFP16keys/fittedvalues.
No measured process-VRAM or speedup claim: evaluation uses session-local SDPA,
not the compiler's native dispatcher, after one train-question zero-bias parity
gate. Thus backend numerical differences remain a comparison limitation.

All AM unapproved responses ask approval; inclusive/exclusive/odd-first also supply
complete code and fail the gate. Tax formula is right but closing prose reverses
rebate order: conservative inconsistent-proposal failure. Odd-first explicitly
corrects its initial reversed split, so proposal semantics pass but gate fails.
Approvedbankers/odd-first code fail. Shared12falsepauses retained; four other
shared cases duplicate instead of sharing; shared download helper still accepts
zero and fails functionally. Distinctchannelstripbugmatchesallother27Barms.
Finiteassertion/parser/monetaryprecisionlimitsfromfinalevalremainapplicable.

Costs:4kfit266.049s,4ksmoke98.602s,4keval567.463s,plus compatibility/initialfailed
attempt/failed8kcosts separately above. Do not present4kfitcost as totalexperiment
cost. 8k remains infeasible under this recipe's FP16representation; no replacement
precision/regularization/run authorized automatically. All project jobs finished.
