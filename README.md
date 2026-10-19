# qwen-kv-compiler

Replace a long, fixed system prompt’s attention cache with smaller synthetic
key/value (K/V) tensors—without changing model weights.

Tested on an **RX 7900 XTX** with Qwen3.8-27B EXL3 and Qwen3-4B. The hybrid 27B
model keeps its full DeltaNet recurrent state; only its attention cache is compressed.

> **Exploratory research—not independently reviewed.** Behavioral responses were
> manually judged by an AI assistant with method identities visible (unblinded).
> Results use one seed and authored, previously inspected development cases—not
> a pristine holdout. Treat them as observations on this workload, not proof of
> general superiority, safety, or production readiness. Raw responses and review
> records are included for inspection.

## At a glance

- **27B:** compiler 8k does better than Attention Matching (AM) 8k on mock tools
  and targeted sharing/approval behavior here; AM does better on knowledge.
- **4B:** AM leads compressed knowledge; compiler leads compressed tools.
  Full-context 4B itself fails the target behaviors, so their compressed
  retention cannot be established.
- **No overall winner:** methods differ in memory, numerical path, and training
  cost. We do not claim process-VRAM savings or inference speedups.

## Results

The frozen **240-case** bundle contains 60 knowledge questions, 60 mock-tool
tasks, 20 monetary approval pairs (40 cases), and 40 shared/distinct refactor
pairs (80 cases). Each measurement is reported separately; there is no pooled score.

### 27B: compiler vs. Attention Matching

“4k” and “8k” mean 4,096 and 8,192 attention-cache rows per head.
Full uses the original prefix; no prefix removes it. Higher is better unless marked ↓.

| Measurement | Full | No prefix | Compiler 4k | Compiler 8k | AM 4k | AM 8k FP32V |
|---|---:|---:|---:|---:|---:|---:|
| Knowledge /60 | 60 | 28 | 46 | 55 | 55 | 57 |
| Mock-tool tasks /60 | 59 | 2 | 51 | 56 | 52 | 54 |
| Approval gate + correct proposal /20 | 18 | 0 | 17 | 17 | 16 | 16 |
| Premature implementation /20 ↓ | 2 | 20 | 0 | 1 | 3 | 4 |
| Approved code checks /20 | 18 | 19 | 18 | 18 | 18 | 18 |
| Shared structure + code checks /40 | 33 | 0 | 19 | 37 | 23 | 29 |
| Distinct contract + code checks /40 | 39 | 39 | 39 | 39 | 39 | 38 |
| Unnecessary approval pauses /80 ↓ | 5 | 0 | 19 | 1 | 12 | 9 |

**Memory and backend differ.** Compiler 8k uses **512 MiB** of attention K/V;
AM 8k FP32V uses **768 MiB + 1 MiB bias**. Both keep 151.5 MiB of recurrent state.
AM uses a session-local SDPA attention wrapper; compiler uses native EXL3.
Equal row counts do not mean equal memory or execution paths.

The original FP16 AM 8k fit overflowed. Its separate **FP32V** follow-up retains
values in FP32 and computes attention in FP32, without clamping or changing the
fitting objective. AM here is the upstream off-policy, uniform-budget
RMS/NNLS2/LSQ recipe—not optimized-budget or on-policy AM.

[Full results and provenance](results/FINAL_EVAL_RESULTS.md) ·
[AM 4k and FP16 failure](results/AM27B_RESULTS.md) ·
[AM 8k FP32V](results/AM27B_FP32_RESULTS.md)

### Controlled 4B comparison

All three compressed methods use the **same 812 training examples and 2,509
rows per head**, with full/no-prefix controls. Training objectives, exposure,
and compute differ. CARTRIDGES uses native generation, 64 frozen tokens, and
validation-only epoch selection.

| Measurement | Full | No prefix | Compiler | AM | CARTRIDGES |
|---|---:|---:|---:|---:|---:|
| Knowledge /60 | 46 | 7 | 28 | 35 | 26 |
| Mock-tool tasks /60 | 28 | 0 | 19 | 17 | 5 |
| Approval gate + correct proposal /20 | 1 | 0 | 0 | 0 | 0 |
| Shared structure + code checks /40 | 0 | 0 | 0 | 0 | 0 |
| Distinct contract + code checks /40 | 28 | 37 | 13 | 25 | 23 |
| Unnecessary approval pauses /80 ↓ | 0 | 0 | 0 | 0 | 0 |

**Full-context 4B itself fails the target behaviors.** These results cannot show
compressed retention or compression-caused loss of those behaviors. The 4B and
27B studies are separate, not an isolated model-size comparison.
[4B protocol and costs](results/CONTROLLED4B_RESULTS.md).

### How to read these numbers

- **Code checks are not correctness certificates.** Frozen extraction/signature
  rules can reject plausible answers, and finite assertions miss semantic errors.
- **Mock tools are not live tools.** Tasks use JSON transport and authored replies,
  not native tool calls or real services.
- **Unnecessary approval pauses** are measured on the same 80 nonmonetary refactor
  cases; approval gates and premature implementation are reported separately.
- **Provenance matters.** Original 27B knowledge/tool scores reuse v2 runs with
  identical prompt/cache hashes; final behavior was run separately. AM and all
  4B arms ran all 240 cases. The final page-size case requires rejection; its
  37/40 sharing result is not the older 36/40 result. Failures and caps are retained.

## Verify or reproduce

Verify saved results without a model, GPU, Docker, or Git history:

```sh
python3 scripts/evaluate.py verify
```

- [Evaluation guide](EVALUATION.md): run cases, resume, and report new reviews.
- [Reproduction guide](REPRODUCE.md): dependencies, fresh capture/fitting, and costs.
- [Validation record](results/RELEASE_VALIDATION.md): 29 CPU test files,
  120 reference/120 negative Docker checks, and fresh-install inference/resume
  checks passed. The separate 19-phase 27B source reproduction took 5h 27m on
  the existing pinned runtime; numerical drift is disclosed.
- [Release status](results/PUBLICATION_READINESS.md): current scope and approvals.

## Package and license

The source package includes code, frozen inputs, raw responses, and review records.
`RELEASE.json` hashes current files; historical outputs and freezes are preserved.
Weights and fitted cache tensors are **not included**. Caches do not anonymize
prompt or model information. Failed historical pilots remain evidence, not
alternative headline scores.

Original code is **MIT-0**. Embedded and external material retains its
[third-party terms](THIRD_PARTY_NOTICES.md).
