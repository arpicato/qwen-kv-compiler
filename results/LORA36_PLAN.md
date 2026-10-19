# All36-layer local LoRA — active experiment plan

Authorized by user2026-10-14; execution complete. Failed-quality result:
[LORA36_RESULTS.md](LORA36_RESULTS.md). No further run currently active.
This is separate from the paused three-way comparison in
[FROZEN_AGENT_TEST_PLAN.md](FROZEN_AGENT_TEST_PLAN.md).
Use repaired512, **not the abandoned143-example dataset**. No new synthesis.
Repair implementation/provenance checkpoint: `c8714f8`.

## Fixed data and target

XTX input: `/mnt/data/artifacts/qwen3_agent/cartridges_out/agent512-repaired-v1.json`.
SHA256: `3ca7fe9e13b05b5483ca2dc70f6d2ee40a0bda6a235d8183ee7b78fc72f43d80`.
405train/107validation, duplicate questions grouped. Full fixed25,090-token
agent manual, Qwen3-4B BF16, XTX24GB VRAM/~7.2GB host RAM.
Repair details: [AGENT512_REPAIR.json](AGENT512_REPAIR.json).
All answer tokens including EOS; no32-token truncation. Exact no-thinking
student framing. Fresh full-manual teacher activations required; do not reuse
old chunk-teacher probabilities or targets from143 data.

## Run sequence

1. Capture teacher residual outputs for layers0–35 at shared suffix token
   positions. Verify exact input IDs, first answer prediction offset and EOS
   on two examples before full capture. Stream targets; resumable sample/layer
   writes. Record hashes, memory, UTC progress and total capture time.
2. Implement local36 rank8 q/v LoRA, alpha16, dropout0, Adam lr0.001,
   weight decay0, three epochs, seed0, clip norm1. Base weights frozen;
   no resident KV; student positions start at0. Each layer takes the preceding
   **student** output detached, not teacher input. Match full-manual teacher
   residual outputs by energy-normalized MSE. Each layer loss coefficient1/4
   preserves historical early4 scale; report mean loss across36 layers.
3. Backpropagate each local loss separately to release graphs; accumulate
   gradients, clip and step once per example. Check streamed/summed gradient
   equality and frozen-base/no-cross-layer gradients on a small test.
4. Time short/median/p95 repaired examples after warmup; check GPU/host memory
   and target I/O. Publish measured ETA before full training. No silent sample
   truncation or dataset shrink if it fails to fit.
5. Validate epoch0/1/2/3 on107 reserved rows: local MSE plus free-generation
   correctness/termination. Also run six held-out development questions from
   `AGENT512_HELDOUT.json`. Select highest six-dev correctness, then fewest
   unfinished dev cap hits, then lowest107-row MSE, then earliest epoch.
   Record the weakness of six-case selection;78 and six test cases never select.
6. Freeze selected unmerged adapter. Evaluate existing78 once with unchanged
   cap64/greedy/no-thinking/seed0; publish20 shared-tool probe slice separately.
   Evaluate six reserved test questions once with full/no-prefix controls.
   Save generations, token IDs, exceptions, repetitions, caps, category scores,
   peak memory, adapter bytes, durations and hashes. Update a separate LoRA
   result report before further experimentation.

Use installed unmerged LoRA modules; BF16 merging changed historical logits.
Checkpoint cache/optimizer/RNG/progress each epoch or15minutes and resume
deterministically. Proposed output root:
`/mnt/data/artifacts/qwen3_agent/lora36_agent512_v1/`.
Logs: `/tmp/opencode/lora36-agent512-*.log`. One GPU job at a time.

## Interpretation and timing

This seed0 run is exploratory. Falling hidden-state MSE does not establish
free-generation quality, absence of overfitting or whole-agent equivalence.
512 is tool-heavy and lacks policy/skill questions; keep that limitation.
No rank/lr/data/loss rescue sweep, hybrid or joint final-logit backprop in this
run. Those would be separately named protocols.

Historical early4:68.54s training/validation/loading/export;177.48s unmerged78
evaluation;18m10s shared teacher capture.2/78 with51cap hits. These used old
short143 examples, not this512. Nine-times training is arithmetic only;
all36/512 capture, train and validation duration is unmeasured. Do not quote
an ETA until step4 measures it.
