# Reports and supporting evidence

Start with the [project overview](../README.md) for the method, baselines and
evaluation design. All behavioral reviews are AI-assistant/unblinded; findings are
exploratory, not independently reviewed.

## Current studies

| Report | What it establishes |
|---|---|
| [Final 27B and 4B evaluation](FINAL_EVAL_RESULTS.md) | Frozen 240-case design, results, manual-review decisions, and grading limitations |
| [Controlled 4B protocol](CONTROLLED4B_RESULTS.md) | Shared training examples, capture checks, compiler/AM/CARTRIDGES training and selection; chronological checkpoints |
| [27B Attention Matching](AM27B_RESULTS.md) | AM 4k results and the original failed FP16 8k fit |
| [27B AM FP32-value follow-up](AM27B_FP32_RESULTS.md) | Separate successful 8k run, changed precision/memory, results and limitations |
| [Source reproduction](REPRODUCTION27B_RESULTS.md) | Completed 19-phase 27B reproduction on the original runtime, including numerical differences |
| [Release validation](RELEASE_VALIDATION.md) | Git-free CPU checks, Docker preflight, fresh dependency installation, and short inference/resume checks |

## Find the underlying data

- **Questions and rubric:** [`inputs/publication_final/`](../inputs/publication_final/).
- **27B full/no-prefix/compiler behavior:** `FINAL_EVAL27B_{RAW,REVIEW,SUMMARY}.json`.
  Knowledge/tool evidence is in `CLEAN_EVAL27B_V2_RAW.json`; identical prompt/cache
  hashes allow its reuse, not a claim that both suites were generated together.
- **27B AM:** `AM27B_4K_{RAW,REVIEW,SUMMARY}.json` and
  `AM27B_8K_FP32_{RAW,REVIEW,SUMMARY}.json`.
- **4B:** `FINAL_EVAL4B_{FULL,NONE,COMPILER,AM,CARTRIDGES}_{RAW,REVIEW,SUMMARY}.json`.
- **Run identities:** matching freeze/manifests record source, input, model and
  artifact hashes. Reviews bind labels to the exact response bytes.

`RAW` files contain generated responses and automatic checks; `REVIEW` files
contain manual behavior labels; `SUMMARY` files combine them into separate
measurements and paired counts. Schemas differ across historical experiments.
They are not all the same generic accuracy/retention format.

## Recheck or regenerate

From the repository root:

```sh
python3 scripts/evaluate.py verify
```

This verifies saved evidence, not a new model run. See the [evaluation guide](../EVALUATION.md)
for new responses and [reproduction guide](../REPRODUCE.md) for fresh capture/fitting.

## Historical material

Other files preserve earlier development, failed pilots and superseded case sets.
Do not substitute their scores for the current tables or pool them as independent
tests. Commands in old reports may require their original source revision;
historical revisions mentioned there are not shipped as public Git history.
Large models, captures and fitted cache tensors are not in this repository.
