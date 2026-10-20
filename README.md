# qwen-kv-compiler

**Can a model use a long system prompt after most of its attention cache is
removed?** This project builds a smaller cache for a fixed, roughly 26,000-token
agent prompt, then tests what the model remembers and how it behaves. Model
weights stay unchanged. A different prompt needs a new cache.

These are **exploratory results**, from one seed on an AMD RX 7900 XTX. The
authors had inspected related evaluation cases. An AI assistant reviewed
behavior with method names visible; there was no independent review. The
results do not establish general superiority, safety, or production readiness.

## How it works

When a model reads a prompt, its attention layers keep keys and values (the
**KV cache**) for later tokens to use. A long system prompt leaves a large
cache before the first user question. This compiler runs the full prompt
offline, records attention on calibration examples, and fits fewer synthetic
cache entries to reproduce those attention outputs. At inference time, the
fitted cache stands in for the system prompt.

The compiler uses 812 question/answer examples about the prompt and fits each
attention layer for 400 steps. Reference answer tokens are supplied during
fitting, but the loss matches internal attention outputs, not answer-token
probabilities. We test free generation separately. The user's conversation
still builds its own cache. On the 27B model, recurrent state is kept unchanged:
only its attention state is compressed.

We compare two other ways to build a small cache:

| Method | How it works |
|---|---|
| **KV compiler** | Fits synthetic keys and values to match full-cache attention outputs. |
| **Attention Matching (AM)** | Selects original keys, fits an attention bias, and solves for values. |
| **CARTRIDGES** | Trains cache entries to match the full model's answer-token predictions. |

AM follows [Fast KV Compaction via Attention Matching](https://arxiv.org/abs/2602.16284);
CARTRIDGES follows [Cartridges](https://arxiv.org/abs/2506.06266). These are
comparisons on *our* prompt, not reproductions of those papers' benchmarks.
The methods use different objectives, compute, and inference implementations.
AM here uses queries captured with the full cache. See the
[reproduction guide](REPRODUCE.md) for exact recipes.

## What we tested

We used a quantized **Qwen3.8-27B** with a 26,341-token prompt and **Qwen3-4B**
in BF16 with the same text (25,390 tokens under its tokenizer). A cache
**row** is one key/value entry per attention head. The 27B study uses 4,096
or 8,192 rows per head; the 4B study uses 2,509. The models also differ in
architecture and precision, so their results are not a model-size comparison.

Each model was tested with the full prompt, no system prompt, and compressed
variants. The fixed **240-case** evaluation has 60 prompt-knowledge questions,
60 simulated tool tasks, 40 approval cases, and 80 code-refactor cases. The
approval cases test asking before an unapproved change and proceeding when
approval is already given. The refactor cases test when code should share a
changed rule and when two contracts should stay distinct. Tool replies are
simulated; code checks use finite, frozen assertions. The
[case design and rubric](inputs/publication_final/README.md) give examples.

Counts below are passes out of the shown denominator. Higher is better except
for rows marked ↓. A combined measure requires both named checks on one case.

### 27B results

| Measurement | Full | None | Compiler 4k | Compiler 8k | AM 4k | AM 8k |
|---|---:|---:|---:|---:|---:|---:|
| Knowledge /60 | 60 | 28 | 46 | 55 | 55 | 57 |
| Tool tasks /60 | 59 | 2 | 51 | 56 | 52 | 54 |
| Approval gate + correct proposal /20 | 18 | 0 | 17 | 17 | 16 | 16 |
| Premature implementation /20 ↓ | 2 | 20 | 0 | 1 | 3 | 4 |
| Shared refactor + code checks /40 | 33 | 0 | 19 | 37 | 23 | 29 |
| Distinct contract + code checks /40 | 39 | 39 | 39 | 39 | 39 | 38 |

Compiler 8k retains much of the tested prompt's knowledge, tool use, and
targeted behavior, but does not match the full prompt on every measure. AM 8k
answers more knowledge questions; compiler 8k passes more tool and shared
refactor cases. There is no overall winner. A compressed score above the full
prompt on one measure does not show a general improvement in reasoning.

**AM 8k is a separate FP32-value follow-up.** Its original FP16 fit failed
because a fitted value exceeded FP16 range. At 8k, the compiler's useful
attention keys/values occupy **512 MiB**; AM's occupy **768 MiB**, plus 1 MiB
of row biases. At 4k, both use 256 MiB of keys/values, with another 0.5 MiB
of biases for AM. All variants retain another 151.5 MiB of recurrent state.
These are state payloads, not total GPU memory or measured speedups. AM and
compiler also use different attention backends. See the
[full 27B report](results/FINAL_EVAL_RESULTS.md),
[AM report](results/AM27B_RESULTS.md), and
[FP32 follow-up](results/AM27B_FP32_RESULTS.md).

### 27B follow-ups: different row counts for each head

We used a fixed measure of training attention to give some heads more rows
than others. Evaluation scores did not select the allocations. The
[equal-row study](results/NONUNIFORM_RESULTS.md) keeps a mean of 4,096
rows/head: compiler uses 256 MiB and FP32-value AM uses 384.5 MiB. With
allocation, compiler knowledge changes **46→53/60** and tool tasks **51→48/60**;
AM changes **55→53/60** and **52→52/60**. These comparisons have equal rows,
not equal bytes.

The [byte-capped study](results/EQUAL_MEMORY_RESULTS.md) instead caps useful
cache payload at **256 MiB**, including AM's row biases. Compiler keeps 4,096
mean rows/head; AM gets 2,727. Allocated compiler scores **53/60** knowledge,
**48/60** tools and **23/40** shared refactors; allocated AM scores **56/60**,
**54/60** and **20/40**. Compiler does better on the reported approval and
sharing checks; AM does better on knowledge and tools. Compiler responses
here are **reused** from the equal-row study; the two smaller AM variants
have 480 new responses and 240 new behavior reviews.

The useful-byte cap counts AM's FP32 values but excludes padding,
placeholders, workspaces, and recurrent state; it is not a total VRAM cap.
The smaller allocated AM cache scores better on knowledge and tools than the
larger one, but worse on shared refactors. This one-seed result does not
explain why or establish a general size trend.

In this implementation, AM fits faster and compiler evaluates faster. The
equal-row uniform AM fit took 4.5 minutes versus 107.5 minutes for the
compiler's historical fit. Evaluating 240 cases took 30.8 versus 10.0
minutes. Precision, backend, and response lengths differ, so these are not
isolated algorithm or token-throughput comparisons. The linked reports
contain complete behavior metrics and timings.

### 4B results

| Measurement | Full | None | Compiler | AM | CARTRIDGES |
|---|---:|---:|---:|---:|---:|
| Knowledge /60 | 46 | 7 | 28 | 35 | 26 |
| Tool tasks /60 | 28 | 0 | 19 | 17 | 5 |
| Approval gate + correct proposal /20 | 1 | 0 | 0 | 0 | 0 |
| Shared refactor + code checks /40 | 0 | 0 | 0 | 0 | 0 |

AM has the most knowledge passes among compressed variants; compiler has the
most tool passes. The **full-prompt 4B model itself fails the target behavior
tests**, so these data cannot show that a compressed variant retained those
behaviors or that compression caused their loss. All methods used the same
812 training examples, but different schedules and objectives. See the
[4B report](results/CONTROLLED4B_RESULTS.md).

## Check the evidence

The [results index](results/README.md) links reports, raw responses, review
labels, timings, failed fits, and run identities. Reviews are bound to exact
response bytes. Cases are related in pairs, so we report separate measurements
rather than a pooled score. The benchmark is authored and previously inspected,
not a fresh holdout; finite code checks can miss errors or reject valid code.

Recheck saved scores and hashes **without a model or GPU**:

```sh
python3 scripts/evaluate.py verify
python3 tests/test_nonuniform_results.py
python3 tests/test_equal_memory_results.py
```

These commands regrade saved tasks and check response-bound reviews. They do
not generate responses, rerun code assertions, or independently review
behavior. For a fresh run, follow [REPRODUCE.md](REPRODUCE.md) and
[EVALUATION.md](EVALUATION.md). Weights and fitted caches are not included.
A public-clone 27B reproduction completed its 19-phase fit, generation, and
artifact-hash audit; its separate behavior review remains pending. Fresh AM
and 4B public-clone reproductions remain deferred. See the
[reproduction status](results/GITHUB_RECREATION.md).

The code is licensed under **[MIT-0](LICENSE)**. Embedded and external
material has [separate notices](THIRD_PARTY_NOTICES.md). Cache tensors may
retain information from the source prompt or model.
