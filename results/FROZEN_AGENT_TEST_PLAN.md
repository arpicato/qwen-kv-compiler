# Frozen three-way KV comparison — resumption plan

Updated2026-10-14. **Paused; no comparison training running.**
This file is exclusively for resuming compiler vs CARTRIDGES vs Attention
Matching. The separately authorized LoRA experiment is in
[LORA36_PLAN.md](LORA36_PLAN.md); it does not resume or replace this comparison.
Prior mixed revisions remain in Git, including repair checkpoint `c8714f8`.

## Goal and unchanged controls

Compare preservation of the resident agent system prompt on Qwen3-4B within
XTX24GB VRAM/~7.2GB host RAM. The fixed fixture is25,090 tokens, not exactly20k.
Prefix SHA256:
`260281d80bc9c370719a44d1d334e8e4c6b0e7598d817490736a0e89e6b2eab1`.
Keep original r10/r25 compiler, corrected AM and native e96 artifacts intact.
Historical results and limitations: [AGENT_KV_COMPARISON.md](AGENT_KV_COMPARISON.md).
This is not an upstream-scale quality reproduction or a whole-agent equivalence
claim. No new synthesis, dataset shrinking or27B transfer.

## Shared examples and completed repair

Original512 parquet SHA256:
`4cd423c83b657f1e35c28e1032fb86cde26c597da12a92a337a639b6dabb08d8`.
Repaired exact-token inputs on XTX:
`/mnt/data/artifacts/qwen3_agent/cartridges_out/agent512-repaired-v1.json`.
SHA256: `3ca7fe9e13b05b5483ca2dc70f6d2ee40a0bda6a235d8183ee7b78fc72f43d80`.
All512 original questions retained;405train/107validation, grouped by normalized
question so identical questions cannot cross splits. Similar templates still
overlap; this split is not an unseen-tool test.

Audit: [AGENT512_AUDIT.json](AGENT512_AUDIT.json).
Original source-answer checks: [AGENT512_HOLDOUT_CHECK.json](AGENT512_HOLDOUT_CHECK.json).
Repair provenance: [AGENT512_REPAIR.json](AGENT512_REPAIR.json).

- Original data:373 unique questions,77 duplicate Q/A excess rows, no policy/
  skill questions; relevant to tool knowledge, incomplete for the whole manual.
- Repaired13 answer rows: seven incomplete argument answers, one missing tool
  identifier, five answers ignoring the manual's preferred Copilot tool.
- Reviewed13 description ambiguity flags; longest matching descriptions and
  explicit tool preference resolve them without deleting examples.
- Removed88 closed thinking blocks for a consistent no-thinking protocol.
  Total100 distinct changed rows. Token IDs/answer offsets are explicit; EOS
  retained. Source parquet is unchanged.
- Old no-thinking teacher synthesis included four template tokens absent from
  native student conversion. Repaired inputs fix the framing contract, but
  **new teacher targets and CARTRIDGES-compatible packing remain pending**.
  The repaired JSON is not a ready-to-train upstream parquet. Do not use stale
  top20 probabilities after modifying answers or framing.
- Passing source-field/tool checks does not certify every conditional argument
  or every sentence, nor demonstrate absence of model overfitting.

## Frozen comparison recipe before resumption

1. Freeze exact shared input IDs, train/validation IDs, model/template/source
   hashes, code revisions, seeds and generation settings in a run manifest.
   Use the full manual teacher for new method-specific targets; this is an
   explicitly different protocol from the historical chunk-teacher e96.
2. Compiler: capture full-manual queries/live suffix K/V on shared sequences;
   preserve original all-question+sampled-answer query policy and fixed400-step
   recipe. Fit synthetic K/V to original-prefix attention outputs, not answer
   token CE. Validation trajectories never enter fitting.
3. CARTRIDGES: recapture teacher probabilities from the same exact sequences,
   including EOS; verify native message conversion reconstructs those inputs
   exactly. Use upstream loss/model/cache, corrected continuous accumulation,
   saved partition reconstruction and native local-position generation.
4. AM: extract task queries from the same sequences and use upstream fitting.
   Validate the chosen conversation/on-policy query configuration before using
   it; do not relabel old context-prefill AM as a shared-example result. Freeze
   query sampling, solver, head allocation and handling of query drift.
5. All arms retain2,509 effective rows/head averaged over36layers at10%.
   Report AM allocated padded memory separately. No adapters in these arms.
   Freeze training-time ceilings after representative timing/memory probes,
   before long runs. Different objectives need not have equal update counts.
6. Use validation/development only for checkpoint decisions; record the exact
   per-method selection rule before training. Do not use78 or reserved test
   outcomes to choose recipes, artifacts or seeds. Seeds0/1/2 are confirmation
   coverage if a superiority claim is pursued, not best-seed selection.
7. Close inference checks on non-test inputs: full-prefix reuse, AM nonzero
   beta/padding and CARTRIDGES native token/position alignment. Publish explicit
   numerical acceptance criteria before candidate scoring.

## Evaluation retained by user request

Keep existing78 unchanged: greedy/no-thinking/seed0/cap64. Zero exact questions
overlap source512, but20 probe tools appear in source supervised Q/A. Publish
that20-probe slice separately; the remaining58 are not thereby certified
semantically disjoint. Historical outcomes have been inspected;78 is regression
evaluation, not a pristine final test. Same grading/generation settings per arm.

[AGENT512_HELDOUT.json](AGENT512_HELDOUT.json) contains12 prospective diagnostic
questions across six tools absent by qualified/bare name and generation-description
checks from source/repaired Q/A, with answer evidence in the manual. Six dev
questions and six test questions use disjoint tools. Use dev for selection;
score test after artifact selection, with full/no-prefix controls. Facts being
in the source manual is required, not leakage into supervised calibration.
This small diagnostic cannot establish general absence of overfitting.

Report paired per-question results, category scores, EOS/cap hits, errors,
train/dev losses and free generation, runtime/memory and artifact hashes.
Claim only the measured workload/configuration result; require uncertainty
support and no hidden generation collapse before asserting superiority.
Actual tool execution, policy priority and multi-turn compliance need a future
separately frozen behavioral evaluation; they are not proven by these text probes.

## Execution discipline

Do not launch this comparison while the LoRA experiment is active. Keep tasks
and output roots separate. Long runs checkpoint each epoch or15minutes,
whichever is sooner, with deterministic resume and UTC elapsed/rate/ETA logs.
Stream targets under `/mnt/data/artifacts/qwen3_agent/`; logs under
`/tmp/opencode/`. No EXL3 modification, USB writes, paid pod or ComfyUI restart.
Update the comparison report after each verified experiment checkpoint.
