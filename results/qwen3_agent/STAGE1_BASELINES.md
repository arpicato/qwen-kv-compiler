# Stage 1 — Qwen3-4B agent-prompt baselines (full vs none)

Started 2026-10-12. Model `/mnt/sandisk/kvbench/models/Qwen3-4B` (BF16, ROCm
gfx1100). Protocol: `agent` suite (78 probes, id `2274bcd35bf7f7b51857c163`),
greedy, thinking disabled, `max_tokens=64`, native Qwen3 system role via
`src/prompt.py`. Evaluator `scripts/eval_agent_hf.py`; install path is the pinned
upstream `CompactedPrefixCache` (commit `ef34ba9` upstream checkout).

## Full-prefix baseline (control)

| | value |
|---|---:|
| accuracy | **0.821 (64/78)** |
| errors | 0 |
| cap hits | 5 / 78 (6.4%) |
| n_sys | 25,090 tokens |
| wall time | 1302 s |

By kind:

| kind | n | correct |
|---|---:|---:|
| tool_select | 26 | **25 (96%)** |
| lookup | 28 | 23 (82%) |
| style | 20 | 12 (60%) |
| unrelated | 4 | 4 (100%) |

`strict_tool_id_acc` (whole-qualified-identifier diagnostic) = 0.462, i.e. the
tolerant grader credits 25/26 but only ~12/26 reproduce the full
`mcp__server__tool` form. This is the plan's expected gap, not a regression.

## Go-gate assessment — **PASS**

| criterion | required | actual | verdict |
|---|---|---:|---|
| informative probes (full right, none wrong) | ≥ 50 | **51** | pass |
| informative tool_select | ≥ 20 | **25** | pass |
| full-prefix tool_select accuracy | ≥ 70% | **96%** (25/26) | pass |

`none` accuracy = **0.192 (15/78)**, and **0/26 on tool_select** — the model
cannot name the tools without the prefix at all, so tool-selection ability comes
entirely from the compressed cache. That is exactly the signal the experiment
needs. Informative breakdown: tool_select 25, lookup 18, style 8.

Gate note: 25,090 tokens is long enough that the ~0.3-logit ROCm noise floor
(S0.6) can flip a low-margin answer, so informative IDs must be recomputed under
whichever mechanism the compared arms use. The 51 figure here is from the slow
per-probe-prefill `full` run; it is stable enough to proceed (see below).

## Baseline stability under the noise floor — **resolved: reuse is safe**

Ran the `full` control twice at the same settings: slow (re-prefill every probe)
and fast (prefill once, clone per probe).

| | slow | fast |
|---|---:|---:|
| accuracy | 0.821 (64/78) | **0.821 (64/78)** |
| wall time | 1302 s | **260 s (5.0x faster)** |
| errors | 0 | 0 |
| cap hits | 5 | 5 |

**Per-probe correctness flips: 0.** Text differs on 11/78 probes (the S0.6
~0.3-logit noise), but not one flip changes `ok`. The two runs also agree on the
same 5 cap hits. The 5x speedup is what makes the multi-arm sweep affordable.

Decision: the fast prefix-reuse path becomes the standard mechanism for every
arm, and the informative set (51 probes: 25 tool_select, 18 lookup, 8 style) is
confirmed stable under it.

## Grader-tolerance hazard, observed live

One `lookup` probe (gold `#platform`) was answered by the slow run with a
**verbatim quote of the passage** ("...Cross-service breakage is owned by the
#platform channel.") rather than an answer, and the tolerant containment grader
awarded it. The fast run answered `#platform channel` directly and also passed.
So both were "correct", but one for the wrong reason. This is the audit's
finding #4 in practice: the primary metric can be satisfied by quoting the
prompt. It does not invalidate the comparison (both arms face the same effect)
but it means small score differences should be read with this in mind, and the
`strict_tool_id` diagnostic plus per-probe text inspection matter.

The historical 27B run on this suite (`results/agent_k4738.json`) had teacher
0.974 / none 0.321 / **52 informative** (24 tool_select). 4B full-prefix 0.821 is
lower than 27B teacher 0.974, as expected — the 4B is a weaker but still usable
model for this comparison.

## Style failures are genuine recall errors, not a token cap

Investigated using the baseline only (as the plan requires). Of 20 `style`
probes, 12 pass. The 8 failures are **not** mostly cap-driven:

* **nearby-number confusion:** "How many logical changes belong in one pull
  request?" → `4` (gold `one`); "How long should a normal answer be, in lines?"
  → `1-2 lines` (gold `4`). The model retrieves a different number from the
  same manual.
* **wrong exact term:** "What prefix does a maintenance commit use?" → `maint`
  (gold `chore`).
* **polarity error:** two questions whose gold is `no` were answered `Yes` about
  editability of migrations/ADRs — the tolerant grader still marks these wrong,
  so they are real.
* **tool misuse:** one probe emitted a `git log --grep` command instead of
  answering.

Conclusion: the weak `style` score is a real model limitation on exact recall
from a long prompt, which is precisely the behaviour a compressed prefix risks
degrading further. It is the right thing to measure, not a harness artifact.
Cap hits (5) are below the plan's 5% investigate threshold (6.4% is marginally
above, but each cap-hit probe was inspected and none failed *because* of the cap
— the failing style probes produced complete short answers, and the two cap-hit
style probes are answered correctly or fail for content reasons).
