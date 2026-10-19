# qwen-kv-compiler

**Can a language model keep using a long system prompt without keeping its full
attention cache?** This project learns a smaller cache offline, then tests what
the model can still recall and which instructions it still follows.

The input is a fixed, roughly **26,000-token agent prompt** containing repository
instructions, tool descriptions, and policies. The output is a set of synthetic
key/value tensors—not a shorter text prompt or a new model. Model weights stay
unchanged. Changing the source prompt requires building a new cache.

This repository contains the method, two experiments, evaluation code, and saved
responses. It is research code tested on one **AMD RX 7900 XTX**, not a drop-in
compression library for arbitrary models.

> **Exploratory findings—not independently reviewed.** Behavior was judged by an
> AI assistant with method identities visible. Experiments use one seed and
> authored, previously inspected development cases, not a pristine holdout.
> Results do not establish general superiority, safety, or production readiness.

## How the compiler works

When a transformer reads a prompt, each attention layer stores **keys and values
(the KV cache)** that later tokens attend to. A long, repeated system prompt
therefore leaves a large prefix in that cache even before a user asks a question.
Ordinary prefix caching reuses that state; this project tries to make it smaller.

```text
OFFLINE
Fixed system prompt + calibration questions and reference answers
    → run the unchanged model with the full prompt
    → record attention queries and full-cache attention outputs
    → fit a smaller set of synthetic keys and values, layer by layer

INFERENCE
Load the fitted prefix cache + a new user question
    → generate with the unchanged model, without rereading the system text
```

The fitting procedure starts from sampled rows of the original cache. It updates
the synthetic keys and values so that attention at the recorded queries resembles
attention with the full prefix. The loss combines squared error and a
direction-matching term on attention outputs after the layer's output projection;
the 27B version also accounts for its attention gates. The first cache row stays
fixed. The reported compiler runs use **400 optimization steps per attention layer**.

Calibration uses **812 question/answer examples** about the prompt, including its
tools and policies. Reference answer tokens are supplied during capture
(“teacher forcing”); the compiler matches internal attention outputs, **not answer
cross-entropy**, and does not train on the evaluation questions. A lower fitting
loss alone is not evidence that free generation works—we test that separately.

Synthetic rows need not correspond to readable tokens. The user conversation
continues to accumulate its own live cache; the compressed prefix does not replace
that conversation. Original logical positions are preserved for the compiler.
On the hybrid 27B model, **all recurrent state is also retained unchanged**:
this compresses attention state, not the model's entire memory.

## What are the other methods?

These are three ways to construct a small prefix cache, not three different
language models. All keep the base model weights fixed.

| Method | What it fits | Implementation used here |
|---|---|---|
| **KV compiler** (this project) | Synthetic keys and values that reproduce internal attention outputs | Layer-by-layer gradient optimization on captured calibration queries |
| **Attention Matching (AM)** | A smaller cache that approximates the original attention behavior | Selects original keys using attention scores, fits a per-row attention bias, then solves for values using least squares |
| **CARTRIDGES** | A trainable prefix cache that makes the model's answer-token predictions resemble a full-context teacher's | Gradients through the frozen model; distillation from captured teacher token probabilities |

AM comes from [Fast KV Compaction via Attention Matching](https://arxiv.org/abs/2602.16284)
([code](https://github.com/adamzweiger/compaction)). CARTRIDGES comes from
[Cartridges: Lightweight and general-purpose long context representations via self-study](https://arxiv.org/abs/2506.06266)
([code](https://github.com/HazyResearch/cartridges)).

**These are workload-specific comparisons, not reproductions of the papers'
headline benchmarks.** Here, AM fits queries captured with the original full
cache (“off-policy”) and gives each head the same row budget. Its pinned recipe
uses RMS attention scoring, two nonnegative least-squares iterations for row
weights, and an unregularized least-squares value solve. We do not test its
optimized allocation or on-policy settings. CARTRIDGES uses the same 812 examples
as the other methods, rather than a separately generated self-study dataset.

## What we tested

There are **two separate studies**:

- **27B:** a quantized Qwen3.8-27B model, using the ExLlamaV3 inference runtime,
  with a **26,341-token** prefix. Compare the compiler and AM at 4,096 and 8,192
  cache rows per key/value head. CARTRIDGES was not tested on this model.
- **4B:** Qwen3-4B in BF16, with the same prompt text (**25,390 tokens** under its
  tokenizer). Compare all three methods at **2,509 rows per head**, about 9.9%
  of the original prefix length. Each uses the same 812 training examples.
  CARTRIDGES chooses its checkpoint using 89 validation question/answer pairs
  grouped into 75 questions, not evaluation scores.

For 4B, CARTRIDGES trains for eight passes over the examples, matching the teacher's
top-20 token probabilities; validation selects epoch 7. Compiler uses 400 steps
per layer; AM solves from the captured training queries. These are different
training schedules, not equal-compute trials. The supplied calibration answers
are references, not a claim that either full-context model freely generates them.

A **row** is one key/value entry per head, not a model parameter or generated
token. “4k” and “8k” below refer to these row budgets, not the total context limit.
Same examples and row counts do **not** imply equal objectives, training exposure,
compute, or memory. The studies also differ in architecture and precision;
their differences cannot be attributed to model size alone.

### Controls and evaluation procedure

Each study includes the unchanged model with **Full prefix** (original system
prompt) and **No prefix** (system prompt removed, question/transport still present).
Compressed variants receive the fitted cache in place of the original prefix.
These controls show whether a question actually benefits from the prompt and
whether the full-context model can perform the requested behavior at all.

All variants use the same frozen **240-case evaluation bundle**:

| Cases | What is tested | How it is judged |
|---|---|---|
| **60 knowledge questions** | Recall of facts and instructions in the source prompt | Frozen accepted-answer matching |
| **60 mock-tool tasks** | Choosing tools, supplying arguments, and completing the specified sequence | Frozen schema, argument, and trace checks; tool replies are simulated |
| **20 approval pairs = 40 cases** | A monetary change requested without approval, and the corresponding already-approved request | Manual review of proposal correctness, asking before implementation, premature code, and unnecessary reapproval; separate code checks |
| **40 refactor pairs = 80 cases** | Two functions should share a changed validation rule, versus a matched request where their contracts must remain different | Manual review of sharing/contract preservation, plus separate executable code checks and unnecessary-approval labels |

For example, the monetary policy asks the model to propose a change and obtain
approval **before supplying a complete implementation**. Asking permission and
then providing the complete patch still fails. The paired approved request tests
the opposite error: asking again instead of doing approved work. Refactor pairs
similarly distinguish useful sharing from incorrectly merging different rules.
These are tests of **the supplied prompt's specific policies**, not a universal
definition of safe or correct coding behavior.

Cases, reference solutions, checks, and the manual rubric were fixed before the
final outputs. Generation is greedy with no sampling; token limits are 128 for
knowledge, 256 per tool action, and 768 for 27B behavior / 1,536 for 4B behavior.
Failures and token-limit hits stay in the results. Each manual decision is bound
to the exact response's hash. Paired cases are related, not independent replicates;
we report separate measurements, **not a pooled overall score**.

**Important limits:** authors had inspected earlier cases and related outputs, so
this is not an unseen policy-family benchmark. Tool calls are JSON text checked
against simulated services, not native tool execution. Code runs in isolated
Docker containers, but extraction rules and finite assertions can reject valid
alternatives or miss semantic errors. Passing those checks is not a correctness
certificate. See the [frozen rubric](inputs/publication_final/README.md) and
[detailed methodology and results](results/FINAL_EVAL_RESULTS.md).

## Results

Counts below are passes out of the denominator shown. **Higher is better except
rows marked ↓.** “+” means both requirements pass on the same case. “Code checks”
always means the limited, frozen tests described above.

### 27B: useful retention, with tradeoffs

| Measurement | Full prefix | No prefix | Compiler 4k | Compiler 8k | AM 4k | AM 8k FP32V |
|---|---:|---:|---:|---:|---:|---:|
| Knowledge /60 | 60 | 28 | 46 | 55 | 55 | 57 |
| Mock-tool tasks /60 | 59 | 2 | 51 | 56 | 52 | 54 |
| Approval gate + correct proposal /20 | 18 | 0 | 17 | 17 | 16 | 16 |
| Premature implementation /20 ↓ | 2 | 20 | 0 | 1 | 3 | 4 |
| Already-approved code checks /20 | 18 | 19 | 18 | 18 | 18 | 18 |
| Shared structure + code checks /40 | 33 | 0 | 19 | 37 | 23 | 29 |
| Distinct contract + code checks /40 | 39 | 39 | 39 | 39 | 39 | 38 |
| Unnecessary approval pauses on refactors /80 ↓ | 5 | 0 | 19 | 1 | 12 | 9 |

**Interpretation:** compiler 8k retains much of this prompt's knowledge/tool
performance and targeted behavior, but does not match full context on every
measurement. Against AM 8k, it has more correct tool tasks and shared refactors;
AM has more correct knowledge answers. No method wins across all measurements.
The 37/40 sharing count exceeding full's 33/40 is an observation on these cases,
not evidence that compression generally improves reasoning.

**Why “AM 8k FP32V”?** The original AM 8k fit produced a value too large for FP16
and failed. A separate follow-up stores fitted values in FP32 and computes
attention in FP32 before casting the output back. It does not clamp the solution,
change the fitting objective, or drop the failed head. The original failure is
retained; it is not a scored method variant.

This also means the comparison is **not memory-matched**:

| 27B state | Compiler 4k | Compiler 8k | AM 4k | AM 8k FP32V |
|---|---:|---:|---:|---:|
| Attention K/V payload | 256 MiB | 512 MiB | 256 MiB | 768 MiB |
| Additional AM row bias | — | — | 0.5 MiB | 1 MiB |
| Unchanged recurrent state | 151.5 MiB | 151.5 MiB | 151.5 MiB | 151.5 MiB |

These are state payloads, **not total GPU memory**. The prototype also allocates
cache capacity, placeholders, and temporaries. AM uses a PyTorch attention wrapper
(SDPA); compiler uses native ExLlamaV3 attention. We claim neither measured
process-VRAM savings nor inference speedups from these tables.

[27B results](results/FINAL_EVAL_RESULTS.md) ·
[AM 4k and original failure](results/AM27B_RESULTS.md) ·
[AM 8k FP32V](results/AM27B_FP32_RESULTS.md)

### 4B: different knowledge/tool tradeoffs; inconclusive behavior retention

| Measurement | Full prefix | No prefix | Compiler | AM | CARTRIDGES |
|---|---:|---:|---:|---:|---:|
| Knowledge /60 | 46 | 7 | 28 | 35 | 26 |
| Mock-tool tasks /60 | 28 | 0 | 19 | 17 | 5 |
| Approval gate + correct proposal /20 | 1 | 0 | 0 | 0 | 0 |
| Shared structure + code checks /40 | 0 | 0 | 0 | 0 | 0 |
| Distinct contract + code checks /40 | 28 | 37 | 13 | 25 | 23 |
| Unnecessary approval pauses on refactors /80 ↓ | 0 | 0 | 0 | 0 | 0 |

AM has the most knowledge passes among compressed variants; compiler has the most
mock-tool passes. CARTRIDGES does worse on these measures with this training recipe.
That is not a ranking of the methods in general or a reproduction of their papers.

**Full-context 4B itself fails the target behaviors.** We therefore cannot conclude
that a compressed method retained them—or that compression caused their loss.
Zero unnecessary pauses alone is not success: the model can act without pausing
while ignoring the required rule. [4B protocol, selection, and costs](results/CONTROLLED4B_RESULTS.md).

## Inspect, verify, or reproduce

**Inspect the evidence:** [results index](results/README.md). Original 27B
knowledge/tool scores reuse earlier runs with identical prompt/cache hashes;
the final behavior suite was run separately. AM and all five 4B variants ran all
240 cases. The final page-size wording requires rejection: its 37/40 compiler
sharing result must not be confused with the earlier suite's 36/40.

**Recheck saved scores** without a model, GPU, Docker, or Git history:

```sh
python3 scripts/evaluate.py verify
```

This regrades saved knowledge/tool traces and validates hashes/manual labels;
it **does not generate new responses, rerun code, or independently review behavior**.

**Run a fresh experiment:** follow [REPRODUCE.md](REPRODUCE.md) for pinned models,
dependencies, capture and fitting, then [EVALUATION.md](EVALUATION.md) for new
responses and reviews. This takes hours on the tested GPU, not just the command
above. Weights and fitted caches are not included. No other hardware/backend is
validated. [Validation record](results/RELEASE_VALIDATION.md) documents CPU tests,
Docker checks, fresh dependency installation and short generation/resume checks.
A separate 19-phase source reproduction took 5h 27m on the existing runtime;
numerical drift is disclosed. A new reproduction from the public clone is in
progress, not yet a completed result.

## Contents and license

- `scripts/`: capture, fit, evaluation, and verification code.
- `inputs/`: fixed prompt, calibration examples, evaluation cases, and rubric.
- `results/`: reports, raw responses, review labels, and historical failures.
- `tests/`: implementation and saved-evidence checks.
- `RELEASE.json`: hashes of the current published files; historical experiment
  identities are preserved separately.

Original code is **MIT-0**; embedded and external material retains its
[third-party terms](THIRD_PARTY_NOTICES.md). Cache tensors are not an anonymization
mechanism: they may retain information from the source prompt or model.
