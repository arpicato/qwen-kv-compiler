# Qwen3-4B: KV compiler vs CARTRIDGES vs Attention Matching

**Historical pilot, superseded for publication.** The later same-example,
2,509-row comparison and final240cases are in `CONTROLLED4B_RESULTS.md` and
`FINAL_EVAL_RESULTS.md`; 27B AM is separate. Do not use the older50/60/45/30
counts below as the current controlled comparison or method-superiority evidence.

**Verified through 2026-10-14. No experiments currently running.**

Follow-up dataset audit and frozen behavioral/LoRA protocol:
[FROZEN_AGENT_TEST_PLAN.md](FROZEN_AGENT_TEST_PLAN.md). The 512 rows pass
structural checks but contain duplicates, lack policy/skill cases and have a
teacher/native no-thinking framing difference; supervision parity and absence
of overfitting are not established. This does not retroactively change scores.

## Conclusion

Our existing compiler scored **50/78 at 10% KV retention** and **60/78 at 25%**.
The corrected native CARTRIDGES pilot scored **45/78 at 10%**. Corrected
Attention Matching (AM) scored **30/78 at 25% effective retention**.

These are artifact-level results, not proof of general method superiority.
Compiler and CARTRIDGES used different training examples. CARTRIDGES' published
held-out quality has not been reproduced, and some checkpoints were inspected
on the evaluation set. No valid three-way comparison at one budget was completed.

## Evaluation protocol

- Model: Qwen3-4B, BF16; 36 layers, 8 KV heads, head dimension 128.
- Hardware: RX 7900 XTX, 24 GB VRAM; approximately 7.2 GB host RAM.
- Resident agent system prefix: 25,090 tokens.
- Same 78 probes: lookup 28, policy/style 20, tool selection 26, unrelated 4.
- Greedy generation, thinking disabled, seed 0, maximum 64 new tokens.
- Errors count as misses; all completed evaluations below had zero exceptions.
  Zero exceptions does **not** mean acceptable output.
- Primary grading accepts bare and qualified tool names; it does not establish
  full tool-call execution or argument correctness.
- CARTRIDGES uses its native model/cache/generator with sequence-local positions
  plus cartridge length. Compiler/AM use their compacted-cache evaluator.
  Generation settings match, but attention implementations are not identical.
- Prefix SHA256:
  `260281d80bc9c370719a44d1d334e8e4c6b0e7598d817490736a0e89e6b2eab1`.
- Probeset ID: `2274bcd35bf7f7b51857c163`.

The probes were inspected in earlier experiments. They are a frozen comparison
set, not a pristine final held-out research test.

## Primary artifact results

| Artifact | Effective retention | Correct /78 | Lookup /28 | Policy/style /20 | Tool /26 | Unrelated /4 | Cap hits |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full manual | 100% | 64 | 23 | 12 | 25 | 4 | 5 |
| No manual | 0% | 15 | 6 | 5 | 0 | 4 | 73 |
| Compiler r10 | 2,509 rows/layer, 10% | **50** | 12 | 11 | **23** | 4 | **6** |
| CARTRIDGES v3 e96, native | 2,509 rows/layer, 10% | **45** | **21** | 10 | 11 | 3 | 30 |
| Compiler r25 | 6,272 rows/layer, 25% | **60** | 17 | 14 | 25 | 4 | 6 |
| AM corrected bounded | Mean 6,271.4 rows/head, 25% | **30** | 10 | 11 | 6 | 3 | 2 |

At 10%, compiler-only successes = 21, CARTRIDGES-only = 16 (exact two-sided
paired p = 0.511). CARTRIDGES retrieves more facts; compiler selects tools and
terminates more reliably. The five-question overall difference is inconclusive.
At 25%, compiler substantially outscored this corrected AM artifact.

### What “matched budget” means

Training dataset size and retained KV memory are separate quantities.
The original compiler and CARTRIDGES already had matched KV size; changing
training data was **not needed** to match memory.

For each 2,509-row BF16 artifact:

`36 layers × 8 heads × 2,509 rows × 128 dimensions × 2 (K,V) × 2 bytes`

= **369,967,104 bytes = 352.828125 MiB of K/V**, excluding model weights and
live generation cache. CARTRIDGES exports also store 1,445,184 bytes of zero
beta values; native generation does not use them. Compiler stores no beta.
The adapter hybrid adds 2,621,440 bytes (2.5 MiB) of adapter tensors, so it is
not matched in total artifact storage.

AM is nonuniform across heads. Its matched budget is **effective retained rows**;
the install path pads to a mean 16,041.1 rows/layer. Do not call its allocated
KV memory equal to compiler r25's uniform 6,272-row allocation.

### Training provenance

- Compiler: original calibration questions/teacher answers captured into
  per-layer attention trajectories; layer-local synthetic K/V optimization,
  400 steps/layer. Existing r10 and r25 artifacts were not overwritten.
- CARTRIDGES v3: separate 512-conversation self-study dataset, mostly GitHub
  tools/arguments, with incomplete policy/skill coverage; 96 epochs/updates in
  the historical pilot, upstream-pinned learning rate 0.02, 64 frozen rows.
  Model weights frozen; final loss backpropagates through the transformer to K/V.
  It is not upstream-scale synthesis/training reproduction.
- AM: corrected bounded implementation of the pinned attention-matching method;
  use `agent4b_am_r25_bounded.json`, not the older result file.

Different training targets do not require different questions/answers.
A shared-example comparison could have reused CARTRIDGES' existing dataset,
captured compiler targets from it, and trained only the compiler. That comparison
has **not** been performed.

## Invalid or superseded results

| Historical result | Reason not to use as a valid comparison |
|---|---|
| AM 17/78 | Older run; corrected bounded result is 30/78. |
| CARTRIDGES v1 25/78 | Incorrect conversation/data construction. |
| CARTRIDGES v2 40/78 | Targets included truncated thinking preambles. |
| CARTRIDGES v3 e4/e32/e96: 47/52/53 | Wrong installed position origin: 25,090 instead of 2,509. |

Only v3 e96 was rerun with native generation, giving **45/78**. Do not use the
old scores to infer a training-step trend. Earlier “60 vs 53 at matched budget”
and “all runs valid / ours wins overall” verdicts were incorrect and withdrawn.

## Implementation validation, not upstream quality reproduction

The actual upstream/local training blocks were compared on identical saved
initialization and six packed batches: three Adam steps, 2,509 rows, 64 frozen.
All six losses, cache gradients, and post-update cache parameters matched
exactly; native 16-token generation matched. Peak 12.47 GiB, final run 140.8 s.

Corrections and limitations:

- Fixed local epoch-end accumulation to follow upstream's continuous schedule.
  Historical e96 used partly filled epoch-end steps; it was not retroactively
  retrained. Sampler order still differs; parity imposed identical batches.
- Pinned upstream checkpoint loader mistakes axis 1 (8 heads) for frozen-token
  axis 2 (64 tokens). Explicit reconstruction preserves the saved partition.
- Exported e96 K/V equal the checkpoint. Three audit inputs agree in top1 with
  native logits at origin 2,509, but not at 25,090. Numerical attention-path
  differences remain; exact export-install generation parity is not claimed.
- ROCm native generation needed verified 32×32 FlexAttention tiles, one stage,
  forced FlexAttention, to avoid shared-memory/decoding-kernel failures.

Reduced upstream MTOB held-out check, 50 Kalamang→English questions per arm:

| Arm | chrF | Cap hits |
|---|---:|---:|
| Trained cache | 15.4355 | 0 |
| Untrained gradient-text initialization | 14.0904 | 0 |
| No cache | 14.1974 | 0 |

This used only 512 training conversations, 2,048 cache rows, four epochs;
trained/init generation was native, no-cache control used HF SDPA. Gain over
no cache was 1.2381 chrF. **Published quality was not reproduced.** Falling
training loss alone never established that reproduction.

## Separate 114-example same-data run — failed quality

The agent unnecessarily reused the layer experiment's smaller dataset:
114 training / 29 validation questions, one broad question per tool/section,
at most 32 teacher-forced answer tokens, often excluding EOS. This reduction
was **not a hardware or CARTRIDGES requirement**; 512 conversations already fit.

Compiler captured all student input token query rows rather than the older
question-plus-sampled-answer policy, then used 400 steps/layer. CARTRIDGES
used native full-model backprop, mean top-20 CE, Adam lr 0.02, one sample/step,
342 updates; validation selected epoch 3 from epochs 0–3. Both retained 2,509 rows.

| New artifact | Correct /78 | Lookup | Policy/style | Tool | Unrelated | Cap hits |
|---|---:|---:|---:|---:|---:|---:|
| Compiler, small shared data | 35 | 8 | 10 | 13 | 4 | 8 |
| CARTRIDGES, small shared data | 12 | 7 | 2 | 3 | 0 | **78** |

Paired: both 9, compiler-only 26, CARTRIDGES-only 3, neither 40. CARTRIDGES
produced repetitive/irrelevant responses. No exceptions, but unacceptable output.
Compiler capture 647.9 s; compilation 6,890.5 s; cart training 390.5 s,
peak 11.42 GiB; evaluations 139 s / 365 s. Validation cart KL 1.8658 → 0.5541
did not predict acceptable free generation.

This is a completed failed-quality experiment, **not** proof against well-trained
CARTRIDGES and not a replacement for the original 50/45 artifact comparison.
No single cause of compiler's 50→35 drop was isolated: examples, answer length
and capture-row weighting all changed. No rescue tuning was performed.

## Layer experiments — separate from the pure-method comparison

Rank-8 LoRA in q/v projections; original model weights frozen. Same 114/29 split;
Adam lr 0.001, norm clipping 1, three epochs; checkpoint selection on validation
loss only. These are small adapter variants, not full-weight layer training.

### Early layers

Layers **0–3**, 327,680 adapter parameters. Student sees no manual; teacher sees
the full manual. Match residual outputs at the same question/answer token
positions using teacher-energy-normalized squared error, averaged over layers.
Each layer receives the **preceding student's output**, detached—not teacher
hidden input. Each local loss updates only that layer's adapters. Later layers
are frozen; no final-output loss trains the early adapters. Answer tokens are
teacher-forced, not free-running student answers.

Validation error 1.2871 → 0.0114; epoch 3 selected; peak 7.71 GiB, 68.6 s.
Local matching improved while downstream generation collapsed.

### Last layers

Layers **32–35**, 327,680 adapter parameters. First 32 layers run without a
backward graph; detached output enters the final four. Top-20 teacher logit
distillation trains all four adapters jointly, without gradients reaching
earlier layers. Validation loss 2.9711 → 0.5688; epoch 2 selected; peak 7.78 GiB,
102.9 s.

**Why four?** A conservative feasibility choice, not an optimum or GPU limit.
No layer-count sweep or largest-fitting suffix was tested. Measured memory
left substantial headroom, so “as many last layers as fit” remains untested.

### Hybrid and ablations

Both adapter groups plus existing compiler r10 KV; last-four-layer K/V also
trainable, earlier K/V and beta fixed. Local early losses do not receive the
final-layer objective through the detached middle. 655,360 adapter parameters,
21,209,088 total trainable parameters including KV. Validation combined loss
0.7420 → 0.3441; epoch 1 selected; peak 9.32 GiB, 137.9 s.

| Unmerged inference configuration | Correct /78 | Cap hits |
|---|---:|---:|
| Early-only, no KV | 2 | 51 |
| Late-only, no KV | 22 | 73 |
| Both + KV | 50 | 16 |
| Hybrid without early adapters | 51 | 16 |
| Hybrid without late adapters | 51 | 6 |
| Hybrid trained KV alone | 50 | 7 |

KV-only had identical per-question pass/fail to the original compiler r10.
Full hybrid lost seven and gained seven compared with that reference. Ablation
one-question gains do not establish improvement; configurations were not selected
for deployment from benchmark results. Pure adapter outputs are unacceptable.

BF16 adapter merging changed logits; unmerged reruns preserve training-path
precision and still scored 2/22/50. Manual versus built-in forward losses
matched; selected gradients were finite; frozen base received no gradients.
Limits include truncated/EOS-poor supervision and teacher-forced-only validation.
Low matching loss does not establish free-generation quality or overfitting.

## Evidence and retained artifacts

XTX results: `/home/arpin/kvbench/results/qwen3_agent/`.

| Result | JSON file |
|---|---|
| Full / none | `agent4b_full.json`, `agent4b_none.json` |
| Original compiler | `agent4b_ours_r10.json`, `agent4b_ours_r25.json` |
| Corrected AM | `agent4b_am_r25_bounded.json` |
| Native original CARTRIDGES | `agent4b_cart_v3_e96_native.json` |
| Failed same-data run | `agent4b_samedata_ours.json`, `agent4b_samedata_cartridges.json` |
| Layer arms | `agent4b_layer_{early,late,hybrid}_unmerged.json` |
| Fixed hybrid ablations | `agent4b_layer_hybrid_{noearly,nolate,kvonly}.json` |

Artifact root: `/mnt/data/artifacts/qwen3_agent/`.
Original `compiled_r10/`, `compiled_r25/`, `am_r25_bounded/`, and
`cartridges_out/cart_v3_r10_e96/` are retained. The v3 dataset and original
calibration inputs are retained. Failed-run result JSONs, reports, selected
artifacts, and logs are retained as evidence, not recommended models.

Native parity report: `cartridges_out/train_parity_20261014_final/report.json`.
MTOB report/checkpoint: `cartridges_out/mtob_test_source/reduced_eval.json`,
`cartridges_out/repro_mtob_qwen3_4b_toks2048/cache-step16.pt`.
Separate failed-run root: `kv_vs_cart_20261014/`; layer root:
`layer_distill_20261014/`. Logs remain under XTX `/tmp/opencode/`.

Implementing checkpoints: evaluator correction `9d290e4`; trainer parity and
accumulation correction `5998e61`, final parity `5ec1064`; layer protocol
`bd8be5e`, unmerged evaluator `cad81e1`; same-data runner `0b92671`, fixed
packing `9bcc4f0`. Git retains historical code/reports; this file supersedes
the contradictory append-only `SMALL_MODEL_AGENT_PLAN.md`.

## Cleanup and unresolved work

Cleanup removed the broken original generator and contradictory report text,
duplicate completed failed-run capture tensors, parity reference tensors,
invalid/superseded pilot KV tensors, nonselected MTOB checkpoints, finished
optimizer-resume files and disposable ablation adapter copies. **446 files,
38,168,020,554 bytes (35.55 GiB)** removed on XTX; SSD now has approximately
305 GB available. Evidence and
selected original artifacts are preserved. Exact deletions and byte counts
are recorded in `cleanup_20261014.json` under the artifact root.

The retained pilot trainer's periodic-save bug was also fixed: saves now occur
at completed optimizer-step intervals, independent of sparse batch logging.
A regression check first failed for the old nesting, then passed after the fix.
This does not alter historical training results or make the pilot an upstream
quality reproduction. Source scripts for failed experiments remain explicitly
experimental for reproducibility; keeping them is not a recommendation to rerun.

No new experiments are authorized by this report. Still unresolved: strong
CARTRIDGES training compared against the fixed original compiler; compiler
training on the existing v3 CARTRIDGES examples; upstream-scale held-out
reproduction; full-weight or larger-layer distillation. No 27B transfer ran.
