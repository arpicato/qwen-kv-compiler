# KV-compiler external benchmark — frozen protocol (QuALITY / Qwen3-4B)

Created 2026-10-12. Purpose: benchmark our existing cheap KV compiler against
published Cartridges (self-study) and Compaction (attention matching / AM)
results, **without changing our method**.

## Pinned references

| Item | Value |
|---|---|
| Compaction repo | `https://github.com/adamzweiger/compaction` @ `2020f6d37940fe013e7e7f1ebf409e5d107c5670` |
| Cartridges repo | `https://github.com/HazyResearch/cartridges` @ `ef34ba97a06049c34820506e2c283746284ae5f0` |
| Model (primary) | `Qwen/Qwen3-4B` (original, **not** Instruct-2507), BF16, revision pinned at download |
| Dataset | QuALITY v1.0.1 dev, **bundled in compaction repo** (`data/QuALITY.v1.0.1.htmlstripped.dev`), no download |
| Article ordering | upstream merged order: unique `(article_id, article_text)`, first-seen; questions concatenated |
| QuALITY sizes | 115 unique articles, 2086 questions total; **first 20 = 357 questions**, **first 50 = 894 questions** |

Verified locally on XTX: first-3 question counts `[14, 19, 18]`; sum first-20 = 357; sum first-50 = 894.

## Published reference numbers (do not tune to these)

Cartridges final ICLR 2026 paper, Appendix A.2 Table 2 (Qwen3-4B):

| Cache | LongHealth acc | MTOB KE chrF |
|---|---:|---:|
| Full ICL | 51.2% | 25.8 |
| K=4096 | 56.0% | 32.43 |
| K=2048 | 55.5% | 33.27 |
| K=1024 | 54.0% | 32.30 |

Note: paper prose says "+3.8 at 106.4x" but the table implies 54.0-51.2 = +2.8. Use the table.

Compaction paper (QuALITY, Qwen3-4B):

| Setting | Value |
|---|---|
| Full context | 71.1% (50 articles, 894 q) |
| Cartridges comparison subset | first 20 articles / 357 q, full-context 75.0% |
| AM-HighestAttnKeys @ 1/2/5/10/20% | 60.4 / 65.0 / 70.1 / 71.3 / 71.0 |

## Two budget tracks

1. **Published-ratio track** — retained article-token fractions `.01 .02 .05 .10 .20`
   (article tokens only; system/template tokens preserved). Matches Compaction curves.
2. **Absolute-K track** — K = 1024 / 2048 / 4096. Matches Cartridges budgets.

For ratio runs, derive per-article K with upstream accounting. For nonuniform AM,
match **total KV entries across layers and heads**, and report actual bytes/padding.

## Our method (frozen — no changes during benchmark)

`scripts/compile_torch_v2.py`, projected recipe:

- per-layer synthetic K/V optimization, uniform K
- output-projected MSE + cosine objective (`--oproj-dir`)
- gate weighting OFF for Qwen3 (original Qwen3 has no attention output gate)
- frozen attention sink (`--freeze-sink`)
- stratified original-KV initialization
- **400 steps, LR 1e-3, 24 examples per update** (batch chunk 4)
- BF16 saved cache
- no paired refinement, no key selection, no attention-bias, no value fitting

Later warm-start/lr variants are **not** part of this benchmark.

## Training data (separate from evaluation)

- Context-only self-study conversations, generated from the article (never benchmark Q/A).
- Initial budget: **71 synthetic conversations per article**, distributed across chunks.
- Deterministic selection; record source spans, token coverage, captured query rows.
- Capture: original prefill K/V + continuation queries/live K/V + per-layer output projections.
- Cartridges/AM run their own published query generation; report data usage separately.

## Subset ladder (nested; reuse captures and training across stages)

| Stage | Articles | Questions | Methods / budgets |
|---|---|---|---|
| A correctness | 0 (1) | first 5 | full context, original-KV reload, AM-HighestAttnKeys 2%, our compiler 2% |
| B early | 0–2 (3) | all (~51) | full, no-context, AM-HighestAttnKeys 2%, our compiler 2% |
| C budget | 0–2 (3) | all | add K=2048 (ours + AM), add AM-OMP-fast 2% |
| D confirm | 0–19 (20) | 357 | predeclared methods/budgets |
| E expand | 0–49 (50) | 894 | add ratio sweep `.01/.05/.10/.20` if justified |

## Hard rules

- Benchmark questions never enter capture/training/cache fitting.
- Report per-question predictions and parsed answers, not just aggregates.
- Record effective K, actual tensor bytes, padding/bias overhead, and **allocated GPU memory** separately.
- Greedy diagnostics labelled separately from paper-compatible sampling.
- Tags for partial runs: `budget-limited` (Cartridges) vs `reproduced`.
- No method changes between stages; no article cherry-picking.

## Notes / open items

- Compaction evaluator forces `SDPBackend.EFFICIENT_ATTENTION` with no fallback → ROCm risk.
- vLLM path is CUDA-oriented; sleep/wake support unverified on ROCm.
- XTX Python is 3.14 → dedicated **3.12** venv (`uv`) for the pinned stack.
- Compaction pins torch 2.8.0 CUDA; we install the ROCm wheel instead (backend deviation, documented).
- LongHealth uses a *different* checkpoint (Instruct-2507) and grouping → run as a separate labelled protocol later.
- Cartridges QuALITY direct reproduction (~5 H100-h/article) is gated behind a training feasibility pilot.
