# Wave-1 findings — calibration correctness, sink, and self-study

Compact, publishable summary of the first experiment wave from
`EXPERIMENT_PLAN.md`. Full per-run detail (including launch logs) lives in
`artifacts/tool/experiments/RUN_LEDGER.md`; the tracked result JSONs are in
`results/wave1_*.json`.

## Setup

- Model: frozen `jclyons52/Qwen3.8-27B-Unsloth-Dynamic-v3-mlx` (bf16).
- State: exact captured DeltaNet prefix + 16 compiled full-attention K/V layers,
  K=4738 slots (= round(18952 x 0.25), 4x compression), 400 Adam steps.
- Two evaluation suites:
  - **dev** (`src/dev_probes.py`): 52 probes (48 domain + 4 controls), authored
    independently of the 103-probe benchmark.
  - **benchmark** (`src/tool_probes.py`): the locked 103-probe set
    (70 informative), used only to confirm finalists.
- Protocol: greedy, full EOS set, max 64 tokens, graded with
  `eval.grade_instruction`. `--probeset` replaces the old invalid `--limit`.

## Arms

| arm | what changed |
|---|---|
| E0 | historical v1 calibration (baseline) |
| E1 | corrected objective: causal live-key masks, occupied-length live region, final-prompt query predicting the first answer token |
| E2 | E1 + frozen true first-token attention sink |
| E3 | E2 + natural verbose teacher answers, same 24 questions |
| E4 | E2 + 128 section-balanced self-study questions/answers (minibatch 24/update) |

## Results

Informative retention (teacher-correct retained), both suites:

| arm | dev (n=34) | benchmark (n=70) |
|---|---:|---:|
| E0 historical | 26/34 = 0.765 | 57/70 = 0.814 |
| E1 corrected | 29/34 = 0.853 | 55/70 = 0.786 |
| **E2 corrected + sink** | 30/34 = 0.882 | **60/70 = 0.857** |
| E3 teacher answers | 27/34 = 0.794 | not run (dev-negative) |
| **E4 self-study + sink** | **32/34 = 0.941** | 59/70 = 0.843 |

Median KL (benchmark): E0 0.305, E1 0.115, E2 0.180, E4 0.138.

## Conclusions

1. **The historical calibration had three real defects** (capacity padding in the
   live region, future answer keys visible in the fitted attention, and a missing
   final-prompt query). Fixing them is mandatory on correctness grounds; the
   corrected objective alone (E1) is a dev win but a small benchmark regression.
2. **Freezing the first-token attention sink (E2) is the change that converts the
   correction into a net win**: 60/70 vs 57/70 on the benchmark, +3, and 0.857 vs
   0.814. It is a one-slot change, near-zero cost.
3. **Broader self-study questions (E4) are a clear dev win (32/34 = 0.941) and
   benchmark-neutral vs E2** (59/70 vs 60/70). Recommend E4 for coverage,
   robustness, and KL; E2 is the leanest benchmark-maximal recipe.
4. **Verbose teacher answer text on few questions (E3) is negative.** Do not
   adopt; it dilutes retrieval signal on a small question set.

## Seed replicate (finalist decision)

E2 seed1 (same data, training seed 1 only) scores 31/34 = 0.912 on dev; the
seed-to-seed swing is ~1-2 probes on n=34 (gained 5, lost 2 vs seed 0). The
E2-vs-E4 difference (dev 30 vs 32, benchmark 60 vs 59) is inside that swing.

**E2 and E4 are therefore the same operating point within noise.** Prefer E4 for
broader question coverage and lower benchmark KL; prefer E2 as the leanest arm.
Both are clear wins over the historical baseline; do not claim E4 beats E2.

## Honesty notes

- The dev/benchmark disagreement on E1 is reported, not hidden; it is the reason
  the two suites exist. Selecting only on the dev suite would have over-claimed.
- `unrelated` controls are never counted as informative. All ratios are shown as
  numerator/denominator.
- The 103-probe benchmark is a locked regression set, not a pristine unseen set;
  it was inspected during earlier work.
