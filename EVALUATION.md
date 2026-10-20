# Final evaluation interface

This guide assumes caches have already been fitted. For an explanation of the
compiler, Attention Matching (AM), CARTRIDGES, and the testing design, start with
[README.md](README.md). To build caches from scratch, use [REPRODUCE.md](REPRODUCE.md).
An **arm** below means one experimental variant, such as full prefix or compiler8k.
**Freeze** records the exact inputs and artifact hashes before generation; it does
not train anything. **Preflight** tests reference solutions and deliberately buggy
controls to check the evaluation harness, not the language model.

Use `scripts/evaluate.py` for both studies. Default cases:
`inputs/publication_final/cases.json` (60 knowledge, 60 tools, 120 behavior).
The frozen rubric is its README. References/checks are evaluator-only; model input
is the question and, for tools, transport text. Never regenerate cases after scores.

## Verify saved evidence (no model, Docker or Git needed)

```sh
python3 scripts/evaluate.py verify
python3 scripts/evaluate.py verify --out /path/to/final-summary.json
```

Checks current release hashes, regrades knowledge/tool traces, validates
response-bound manual reviews, intersections and paired denominators, and compares
saved summaries. 27B original knowledge/tools are separate v2 runs with identical
prompt/cache hashes; final behavior is a new version. AM and 4B ran all 240 cases.
This does not execute generated code or turn manual labels into independent review.
The main verifier covers the original 27B/4B/AM tables. For the separately recorded
allocation follow-ups, also run these stdlib-only saved-evidence checks:

```sh
python3 tests/test_nonuniform_results.py
python3 tests/test_equal_memory_results.py
```

They verify task grades, response-bound reviews, exact allocations, smoke/timing
identities and compiler reuse. They do not rerun model generation or Docker
assertions. The byte-capped raw file contains only the 480 new AM responses;
compiler results are referenced from the equal-row study, not relabeled as fresh.

The older 160-case verifier remains available explicitly for historical provenance:

```sh
python3 scripts/evaluate.py verify --cases inputs/publication_eval/cases.json
```

## Preflight and 27B generation

Acquire runtimes/artifacts using [REPRODUCE.md](REPRODUCE.md). Output directories
must be new and outside the immutable source export. Build `Dockerfile.checks`.

```sh
python3 scripts/evaluate.py preflight --out /path/to/preflight.json
export EXLLAMAV3_PATH=/path/to/exllamav3-rocm
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 scripts/evaluate.py freeze --artifacts /path/to/reproduction --model /path/to/model --freeze /path/to/eval/freeze.json
python3 scripts/evaluate.py run --freeze /path/to/eval/freeze.json --out /path/to/eval/raw.json
```

Preflight requires 120 positive/120 negative code checks and valid reference tool
calls. Freeze hashes source/inputs/model/caches and enforces runtime pins. Run
validates those hashes and resumes per case; `--arms full,none` or `--suites behavior`
select explicit subsets. Completed resumes must contain every expected case.
27B limits: knowledge 128, tools 256/action, behavior 768 tokens. Greedy/no-thinking.
Run detached with bounded exact-PID monitoring; never edit a frozen source export.

Optional AM baseline: add `--am-artifacts /path/to/am-root --am-slots 4096` to freeze
for `am4k`, or `--am-slots 8192` for the separate FP32V root/`am8k_fp32`. Include the
matching `gate-v2/gate.json`. FP32V requires its precision gate and matching
all-layer `smoke.json` before freezing. Select the matching `--arms` on run.
The original incomplete FP16 8k fit must not be scored. Details in REPRODUCE.md.

## 4B generation

Use the separate pinned Torch 2.8/ROCm 6.4 runtime, shared 4B capture, and method
artifacts. No 27B tensor or recurrent state is installed in 4B.

```sh
python3 scripts/evaluate.py run --backend hf4b --model /path/to/Qwen3-4B --capture /path/to/4b/capture --arm compiler --artifact /path/to/4b/compiler --out /path/to/eval/compiler.json
```

Arms: `full`, `none` (omit `--artifact`), `compiler`, `am`, `cartridges`.
Use `--smoke` with a separate output for 16-token **training-question** inference,
not a score. Full evaluation uses all 240 cases; behavior limit is 1,536 tokens,
not the 27B 768. Model hashes must match capture provenance; runtime commits and
artifact shapes/finiteness are checked. Resume requires identical identities.

## New manual reviews

Read every new behavior response against the frozen rubric. Separate approval
sequence, proposal semantics, sharing/distinct structure, and frozen code checks;
include caps/missing code and false pauses. Do not copy labels to changed answers.
The review JSON schema/examples are `results/FINAL_EVAL27B_REVIEW.json` and
`results/FINAL_EVAL4B_FULL_REVIEW.json`: complete flag, reviewer description, raw
and cases SHA256, arm lists with each response SHA256 and rubric labels.

```sh
python3 scripts/evaluate.py report --raw /path/to/raw.json --review /path/to/review.json --out /path/to/summary.json
```

Report refuses mismatched response hashes, labels, intersections or pairs. It
does not independently infer semantics. [Review packet](results/INDEPENDENT_REVIEW.md)
is available for optional future independent review. Current publication uses
the explicit exploratory disclaimer; no independent review has been performed.
No pooled overall score, pristine
holdout, equal-compute or general safety/method-superiority claim. Full 4B fails
the target policy behaviors, so do not claim their compressed retention.
