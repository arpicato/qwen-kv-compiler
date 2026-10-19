# Independent behavior-review packet

Status: **not performed**. All existing judgments are assistant/unblinded.
This packet is a handoff, not an independent endorsement or a new score.

On 2026-10-19 the user chose to publish with an explicit exploratory disclaimer
instead of waiting for independent review. This packet remains optional future
work; review is still absent, not completed or implied by that decision.

Read `inputs/publication_final/README.md` first. Use exactly its frozen rubric,
questions/references and limits. Evaluate all responses, including failures/caps;
do not pick examples or repair the code/parser. Keep semantic concerns outside
finite assertions in a separate field, leaving frozen functional labels unchanged.

Scope: **1,320 behavior responses**: 27B full/none/compiler4k/compiler8k (480),
AM4k (120), AM8kFP32V (120), 4B five arms (600). Sources:

- `FINAL_EVAL27B_RAW.json` and matching `REVIEW.json`.
- `AM27B_4K_RAW.json` and matching `REVIEW.json`.
- `AM27B_8K_FP32_RAW.json` and matching `REVIEW.json`.
- `FINAL_EVAL4B_{FULL,NONE,COMPILER,AM,CARTRIDGES}_RAW.json` and matching reviews.

Files are in `results/`. The 60knowledge/60tool traces per arm are automatically
regraded by `evaluate.py verify`; this review concerns behavioral interpretation.

Reviewer should not have authored the cases, models' outputs, or existing labels.
First read outputs without existing decisions or aggregate scores. Ideally have a
coordinator replace arm names with opaque IDs and shuffle order, keeping a private
mapping; don't call review blinded if the reviewer saw names/previous decisions.
Record reviewer identity/role, conflicts, blinding and actual start/finish dates.
No reviewer solicitation or raw-data upload is authorized here.

For each case: record explicit approval request, complete premature implementation,
concrete proposal correctness, unnecessary approval prerequisite, helper execution
through both callers or preservation of distinct contracts, and rationale. Keep
behavior, code checks and intersections separate; don't equate an approval keyword
with compliance. Note contradictory examples, output truncation, missing code and
finite-check blind spots. Preserve both member labels in every money/refactor pair.

Write a separate review file with existing schema plus per-label rationale and
source hashes. Validate using `evaluate.py report --raw ... --review ... --out ...`.
Never overwrite original reviews. Compare independent vs original decisions:
counts/disagreements per rubric/condition and pair, raw agreement and adjudication
notes. Resolve disagreements explicitly, retaining both original decisions, rather
than replacing inconvenient labels. No score change without a versioned report.

Until complete: all public claims remain exploratory, single-seed, inspected-case
evidence with assistant review disclosed. No independent agreement claim.
