# Frozen compiler KV + joint late4 LoRA

2026-10-14: **training and frozen selected evaluation complete; no active job**.
Independent of the paused three-way comparison and completed local36 run.

Fixed original compiler r10:2509rows/layer, origin25090,36layers, all K/V/beta
frozen. Qwen3-4B BF16 on XTX24GB. Rank8 q/v LoRA layers32–35, alpha16,
dropout0, Adam0.001, clip1, three epochs, seed0. First32layers no backward
graph; **one answer-token CE loss backpropagates jointly through32–35**,
without detach between them. No hidden-state matching and no trainable K/V.
Frozen model norm/head transmit gradients into the suffix; their weights fixed.

Data: repaired512 SHA2563ca7fe9e13b05b5483ca2dc70f6d2ee40a0bda6a235d8183ee7b78fc72f43d80,
405train/107validation. Complete no-thinking answers including EOS. No new
synthesis/143 data/32-token truncation. This is hard-label CE on repaired
answers, not teacher top20 KL; no teacher capture needed for this objective.

Preflight: tiny actual joint_loss gradient test; GPU direct/manual CE parity;
finite gradients in all four suffix activations/adapters, none in base/KV;
prefix tensor digest unchanged. Representative35/median/p95 lengths measured
before optimization. Memory/alignment failure stops rather than changes data.

Epoch0–3 validation:107-row teacher-forced CE and free generation; six unseen-
tool dev questions. Select highest dev correct, then lowest dev decoded-text
cap proxy, then lowest validation CE, then earliest epoch. The installed helper
returns text, not token IDs; **dev cap counts are proxies**, not EOS certificates.
Same prefix-install path for baseline and candidate, greedy/no-thinking/cap64.
107 generation grading is required-field/tool-name diagnostic, not execution.
Save per-epoch outcomes and adapter/optimizer/RNG checkpoints each epoch or15min.

After selection: fresh compiler-only and unmerged compiler+adapter78-probe
evaluations, same install path; publish paired gains/losses and20shared-tool
slice. Six reserved test cases for compiler/candidate; full/no-prefix controls
already in local36 heldout_test.json and retained separately. No78/test recipe
or checkpoint selection. Unchanged78 and existing6test only.

Artifact root: `/mnt/data/artifacts/qwen3_agent/late4_kv_agent512_v1/`.
Log: `/tmp/opencode/late4-kv-agent512-*.log`. No27B transfer or comparison run.
Implementation `scripts/late4_kv.py`; regression `scripts/test_late4_kv.py`.
Final quality results below; implementation does not imply successful retention.

Implementation checkpoint4f32857. Actual joint_loss tiny-model test passes:
CE gradients reach all four suffix layers but not earlier layers/base weights.
GPU preflight direct/manual CE absolute difference0; all suffix activations and
adapter gradients finite; compiler K/V has no gradients and tensor digest
unchanged (`8159572093982f0e4f5738870eb720d0978728746cfd401a2b97d33fee1abdf8`).
35/75/167-token forward/backward timing0.537/0.104/0.112s, peaks8.548/8.657/
9.003GiB; first includes warmup, not a total-runtime estimate. Artifact
`preflight.json`. Training PID746745 finished. Training/validation total930.4s
(15m30s),1215updates, peak9.387GiB. Epoch2 selected by frozen dev/cap/CE rule.

| Epoch | Train CE | Validation CE | Correct /107 | Decoded cap proxies | Dev /6 | Dev cap proxies |
|---|---:|---:|---:|---:|---:|---:|
| 0 compiler-only | — | 1.973125 | 45 | 13 | 1 | 0 |
| 1 | 0.465838 | 0.391405 | 70 | 17 | 1 | 0 |
| **2 selected** | 0.300805 | 0.347577 | 71 | 15 | 1 | 0 |
| 3 | 0.235379 | 0.413116 | 78 | 24 | 1 | 1 |

Training CE continues falling, validation CE worsens at3, while tolerant
validation free-generation correctness rises. That is mixed generalization/
termination evidence, not a demonstrated converged optimum. No epoch chosen
from78 or reserved tests. Compiler prefix digest unchanged at each epoch.
Final paired baseline/candidate78 and six heldout tests completed below; no tuning.

## Final result — validation gain did not transfer

| Fixed configuration | Correct /78 | Lookup /28 | Style /20 | Tool /26 | Unrelated /4 | Cap hits |
|---|---:|---:|---:|---:|---:|---:|
| Original compiler-only, fresh rerun | **50** | 12 | 11 | 23 | 4 | 6 |
| Compiler + selected unmerged late4 epoch2 | **41** | 10 | 9 | 18 | 4 | 5 |

Same prefix, model, question/answer identities, seed0, cap64 and installed cache
generation path; zero exceptions. Baseline reproduces original50/78. Paired:
3gains,12losses,38both pass,25both fail. Shared-tool20 slice19→17; remaining58
31→24. Losses include skill selection, repo/policy/style facts and two GitHub
tool probes. Copilot canonical old answer is the nonpreferred tool, so this
specific old probe loss has a grading/ground-truth limitation; it does not
explain other regressions. Strict tool-ID fraction baseline
0.26923→0.15385 on26tool probes (7→4), reported separately from tolerant scores.

Six reserved unseen-tool tests: compiler0/6, compiler+late40/6 under strict
name-set grading; decoded cap proxies0for both. Earlier full/no-prefix controls
were3/6 and0/6 (local36 experiment, same frozen cases). Strict grading rejects
otherwise relevant prose: do not equate0/6 with all underlying facts absent.
No test outcome selected the adapter. No additional tuning or27B transfer.

**Verdict:** this fixed output-supervised suffix adapter improves the narrow
validation tool dataset (45→71/107 at selected epoch) but **regresses the broader
78-probe prompt retention (50→41)**. Keep compiler-only as the reference.
This is not proof all joint suffix training fails; task distribution, hard-label
CE, learning rate, rank and layer count were not isolated. It is not an
acceptable improvement and not evidence for deployment.

## Time, budget and artifacts

Train/validation930.4s (15m30s), fresh baseline78122.6s, candidate78144.3s,
reserved test73.3s including loading =**1270.7s (~21m11s)** recorded total.
No teacher capture required for hard-label CE. Peak train9.387GiB. Prefix
K/V369,967,104bytes (352.83MiB) unchanged; adapter adds1,312,840bytes on disk
(327680FP32 parameters plus metadata). Therefore not matched total storage
against compiler-only. Unmerged eval; no KV optimization.

Root: `/mnt/data/artifacts/qwen3_agent/late4_kv_agent512_v1/`.
Evidence: `preflight.json`, `train.json`, `validation_epoch{0..3}.json`,
`dev_epoch{0..3}.json`, `best_adapter/`, `latest.pt`, `baseline78.json`,
`candidate78.json`, `heldout_test.json`. Local report:
[LATE4_KV_TRAIN.json](LATE4_KV_TRAIN.json).
Adapter SHA256 `a0c51743061c9825e661149f964579dde3e182605081c351a65cbec013351685`.
Logs `/tmp/opencode/late4-kv-agent512-{train,eval}.log`.
Implementation4f32857, preflight1883002, training checkpoint457d611.
Training/eval PIDs746745/757664 finished. Comparison stays paused.
