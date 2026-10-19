# All36 local LoRA on repaired512 — execution record

2026-10-14: **capture, training and selected artifact evaluation complete**.
Protocol: [LORA36_PLAN.md](LORA36_PLAN.md). Three-way comparison remains paused.
Data fixed SHA256 `3ca7fe9e13b05b5483ca2dc70f6d2ee40a0bda6a235d8183ee7b78fc72f43d80`;
405train/107validation, all512 rows retained, repaired no-thinking/EOS sequences.
Model Qwen3-4B BF16, XTX24GB. No143 data, new synthesis or answer truncation.

Implementation: `scripts/lora36.py`; regression `scripts/test_lora36.py`.
CPU numerical regression passes for the actual36-layer streamed local forward:
summed/streamed gradients exactly equal, frozen embedding receives no gradient,
final local loss cannot reach preceding layers. GPU preflight also passed.

Capture writes full-manual teacher residual targets for all36 layers per sample
as atomic safetensors; the answer-offset/EOS and final residual normalization
checks run on the first two samples. Train rank8 q/v, alpha16, Adam0.001,
three epochs, frozen base, no prefix, coefficient0.25 per local layer, clip1.
107-row MSE/free generation plus6 dev questions;6 reserved test questions and78
regression probes never select checkpoints. Adapters evaluated unmerged.

Artifact root: `/mnt/data/artifacts/qwen3_agent/lora36_agent512_v1/`.
Logs: XTX `/tmp/opencode/lora36-agent512-*.log`.
Teacher capture complete512/512,36layers/sample,328.3s (5m28s), peak18.037GiB.
First two exact answer-offset/EOS and residual-normalization checks pass;
all saved layer tensors checked for shape/finiteness. Artifact `capture.json`;
log `/tmp/opencode/lora36-agent512-capture.log`. Implementation `27a2e75`;
selected heldout test runner `7462267`.
GPU preflight passes direct/local loss equality (absolute difference0), all
2949120 adapter gradients finite, frozen base has no gradients.35/75/167token
sample forward/backward timings0.614/0.387/0.316s including target I/O, peaks
7.636/7.644/7.663GiB. Crude three-step projection533.6s for1215training steps
excludes generation validation/startup and is not a total-runtime promise.
Artifact `preflight.json`. Capture PID711266 and training PID715405 finished;
log `/tmp/opencode/lora36-agent512-train.log`. Training finished1593.9s
(26m34s),1215updates, peak7.724GiB. All36 q/v adapters trained, no base gradients.

| Epoch | Validation local MSE | Validation correct /107 | Cap hits | Dev correct /6 | Dev cap hits |
|---|---:|---:|---:|---:|---:|
| 0 | 946.46249 | 0 | 74 | 0 | 3 |
| 1 | 0.186927 | 0 | 104 | 0 | 6 |
| **2 selected** | 0.172630 | 0 | 41 | 0 | 2 |
| 3 | 0.151273 | 2 | 102 | 0 | 6 |

Selection used frozen dev score/cap/MSE ordering; all dev correctness scores0,
so fewer cap hits selected epoch2. This is **failed-quality validation**,
not acceptable compressed-prompt behavior. Outputs include repetition and
irrelevant text; local MSE reduction did not establish generation fidelity.
Strict dev name-set grading also rejects explanatory prose, as predeclared.
No benchmark or reserved-test outcome selected the adapter. Final78 and six
test controls completed below; no recipe change/rescue tuning.

## Final frozen evaluation

Selected epoch2, installed **unmerged** q/v rank8 LoRA in all36layers. No prefix
KV. Existing78 greedy/no-thinking/cap64/seed0: **9/78**, zero exceptions,
**31cap hits**. Categories: lookup4/28, style2/20, tool0/26, unrelated3/4.
Source-shared20 tool probes2/20; other58 probes7/58. Strict tool ID accuracy0.
Runtime188.6s (3m09s). Original no-manual15/78 and early4 unmerged2/78 are
historical references with different training data; **9 vs2 is not an isolated
layer-count gain**. Selected output still repeats/ignores manual-specific tools.

Six reserved unseen-tool questions, strict frozen name-set grader:
full-manual3/6 (0cap), no-manual0/6 (3cap), selected local360/6 (2cap).
Teacher is not perfect under this strict grader; report all6, do not remove its
misses. Test runner total96.5s including model loading/full-prefix prefill;
generation times11.15/10.40/10.22s. These12 dev/test questions were not fitted;
test never selected the adapter. No claim of general absence of overfitting.

**Verdict: failed-quality exploratory local36 run.** All-layer local residual
matching reduced teacher-forced error but did not preserve agentic prompt
behavior. It is worse than the historical no-manual baseline on78 and retains
none of the26 tool-selection successes. This is not evidence against every
LoRA approach; joint output supervision and other objectives were not tested.
No further experiment launched and no rescue tuning performed.

## Actual time and evidence

Capture328.3s + train1593.9s + regression188.6s + test/controls96.5s =
**2207.3s (~36m47s)** of recorded runtime; detached-wrapper startup overhead
can differ. Train total includes107-row MSE/validation generation and6dev
generation at epochs0–3, loading, preflight and exports. Validation generation
alone1078.3s; dev generation56.8s. The remainder458.8s includes optimization,
MSE checks, loading/preflight/I/O, not pure training time.1215updates complete.
Peak capture18.037GiB; train7.724GiB. Targets occupy7.7GiB SSD. Adapter file
11,815,504bytes (~11.27MiB including safetensors metadata), no runtime prefix KV.

Artifacts under `/mnt/data/artifacts/qwen3_agent/lora36_agent512_v1/`:
`capture.json`, `preflight.json`, `train.json`, `validation_epoch{0..3}.json`,
`dev_epoch{0..3}.json`, `best_adapter/`, `latest.pt`, `regression78.json`,
`heldout_test.json`, and512 targets. Local training report:
[LORA36_TRAIN.json](LORA36_TRAIN.json).

Selected adapter SHA256:
`512741961d34785a498c0aabfe2bda3f98747b8e57e2fe0eec58c2cc87e18fbb`.
Regression JSON SHA256:
`753808f2bb9beec9b8c3f05c2ab2fe2331fe342dcd1f6f201117fb5cc6407e23`.
Reserved-test JSON SHA256:
`edb65b0c5497bcacca7fc7456bb7c328b633b03f783e69243605a35ed97d95a3`.
Implementation27a2e75, test runner7462267, capturebd034b2, train checkpointd759242.
Capture/training/evaluation PIDs711266/715405/732332 finished; no active job.
Three-way comparison is still paused; original artifacts/data unchanged.
