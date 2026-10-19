# 27B AM failed-head FP32 gate

Authorized 2026-10-19: try higher-precision integration, first on the failed 8k
layer23/head3. No full refit or scored evaluation started by this gate.
Original `am27b_v1` fit, failure and final4k results stay untouched.

Same upstream RMS/NNLS2/unregularized LSQ, same812 captured queries and saved
head22 RNG. Only retain LSQ V in FP32 instead of converting it to FP16. Capture
the same-run LSQ solution and require bit-exact retention/save/reload.

Runtime: session-local FP32 prefix-value sidecar for layer23, native FP16 live
cache updates, FP32 Q/K/V SDPA at that layer, output cast to native activation
dtype. No fitted V passes through native FP16 cache. Other heads/layers use
leading original8192rows, so this is a feasibility test, NOT an 8k AM quality run.
Native recurrent state/logical26341 retained. No shared runtime/environment edits.

Gates: existing representable-cache promotion control16tokens equal/maxlogitdiff
<=.25; real failed-head FP32 sidecar finite generation; reconstructed sidecar and
16token generation/logits exact; recurrent injection exact. Solver and native
EXL3 use their existing separate environments. Initial mixed-dtype regression
failed as expected (SDPA requires equal Q/K/V dtype); promotion fix required.
Artifact root: `/mnt/data/artifacts/kvcompile/artifacts/agent/am27b_fp32_gate_v1/`.

Sourcebebd4ed first attempt stopped on an overly strict cross-process maxabs
identity assertion before generation. Diagnostic8d28960 measured67690.96875 vs
earlier67691.234375 (difference0.265625, about0.00039%), still one FP16 infinity.
Same RNG/environment is not proof of bit-identical GPU least-squares results.
Do not call this bit-exact reproduction of the historical fit. Correct gate
captures the SAME solver call's FP32 solution and requires exact retained tensor
equality, overflow under the original cast, and exact save/reload. No tolerance
relaxation for generation parity or changes to solver/data. New attempt uses
`am27b_fp32_gate_v3/`; failed logs/artifacts retained.

## Gate passed

Sourceafca128, process1806003 exited. Solver18.616s: retained FP32solution exact
to same LSQcall, one FP16cast infinity, maxabs67690.875. Head file roundtrip exact.
Native gate95.200s, peak14.096GiB: representable-cache promotion produced equal
tokens/maxlogitdiff0.03125<=.25. Failed-head FP32sidecar generated finite logits,
stopped at EOS after4tokens under16token limit; reconstruction produced exact
tokens/logits. Recurrentstate injection exact. Evidence:
`AM27B_FP32_SOLVER_GATE.json` and `AM27B_FP32_GATE.json`.

Verdict: the specific overflow is avoidable without clamping or changing AM's
fitting objective. The failed head can execute with FP32values outside EXL3's
FP16cache. This does NOT show that every8khead fits/executes or that an8kAMcache
is accurate. Remaining work, not started: complete versioned64head FP32Vfit,
all-layer finite/roundtrip gates, then frozen240case evaluation/manual review.
No regularization, budget/data change or scored-output selection.

Precision is a changed inference configuration: all-FP32V plus FP16K at8k would
occupy768MiB of attentionKV vs512MiB with bothFP16 (plus1MiB FP16beta). Current
prototype also retains nativeFP16cache placeholders and sidecar/SDPA temporaries;
it is not a memory-saving or performance implementation. A complete variant must
report its true allocation and backend/precision differences, not equal-memory
comparison. No shared runtime/environment edits, original artifacts untouched.

Regression: mixed-dtype attention matches explicitFP32reference/nativeoutputcast;
nativecache stub verifies FP32prefix override, liveFP16writes, dispatcher restore.
ExistingAM4kresult/freeze/publicCLI/source-layout checks pass unchanged. Initial
v1traceback retained; successfulv3launcher accidentally redirected console output
to/dev/null, so JSON evidence is authoritative and no console log is claimed.
