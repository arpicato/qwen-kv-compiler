# Final publication plan: one coverage matrix

**2026-10-19 status:** This proposal was approved and executed. Both final studies
and the later27BAMbaseline are complete. Current checklist:
[PUBLICATION_READINESS.md](PUBLICATION_READINESS.md); validation:
[RELEASE_VALIDATION.md](RELEASE_VALIDATION.md). The proposal text below is retained
as chronology, not the current run status or a request for more experiments.

2026-10-18. **Proposal for approval, not a frozen test set. GPU work stays paused.**
This replaces the additive “160 current +60 approval, maybe more controls” plan.
No new cases, fits or evaluations are authorized by writing this document.

## 1. Scope and final test matrix

Two separate studies, one evaluation definition:

- 27B hybrid model: full / none / existing joint4k / existing joint8k.
- 4B: full / none / compiler / native CARTRIDGES / specified off-policy uniform AM,
  at2,509effective rows/head. Completed captures/cartridge fit stay preserved.

**Proposed final bundle:240cases, reported in separate strata, no pooled score.**

| Measurement | Conditions | Cases | Required result |
|---|---|---:|---|
| Knowledge | Tool identity / field identity / instruction recall |20each=60|Correct instructed answer|
| Mock tools | Single call / clarification / two-step session |20each=60|All required steps, names, argument types and values correct|
| Approval |20monetary operations, each unapproved and explicitly approved|40|Pause before implementation only when approval is absent|
| Refactoring |40operations, each shared-rule and distinct-contract|80|Share changed validation when common; preserve separate contracts when distinct|

Thus behavior is **120cases across60paired operation families**. Counts preserve
all40existing shared-rule cases and recover the20existing monetary pairs; they
are a bounded coverage choice, not a statistical power claim. Paired variants are
not independent examples. Some operations/policies may also relate across families.

### No duplicate “ordinary changes” suite

All80refactor cases are nonmonetary implementation requests and should proceed
without monetary approval. They provide the ordinary-change false-pause slice.
The40approval cases provide must-pause and already-approved contrasts. A case can
have multiple diagnostic labels, but appears only once in the bundle and is never
counted twice in an overall total. No separate proposed60approval suite.

## 2. Exact source policy: reuse first, edit only for a defined defect

| Final component | Starting source | Action before freeze |
|---|---|---|
|60knowledge+60tools|`inputs/clean_eval_v2/cases.json`|Keep verbatim unless a documented validity defect requires a new version|
|20monetary approval pairs|All20`money_unapproved`/`money_approved`pairs in that same file|Audit all40, reuse valid cases; repair only documented ambiguity/approval-context defects|
|40shared-rule cases|All40`inputs/transplant_refactors_v4/cases.json`cases|Retain every operation, audit wording/tests; version any necessary correction|
|40distinct-contract counterparts|One counterpart per retained shared-rule case|Change only which contracts should change; preserve comparable domain, complexity and formatting|

The old v2 shared/distinct cases supplied the new rule's Python implementation.
They are provenance/debug material, not replacements for natural refactor tasks.
Do not restore those solution-supplied tasks merely because their scores were good.

The known page-size “cap” ambiguity must have an explicit semantic contract in
the final version (reject versus clamp), fixed BEFORE new output. Preserve its
original case, score and reason for change. Apply the same clarity requirement
to every case, not just recorded failures. No culling questions based on outcomes.

For approval, the paired monetary operation and expected implementation semantics
must match exactly. The approved variant must unambiguously establish approval of
that behavior, not approval of an unrelated proposal. A request to fix something
is not itself approval. Natural response/code, no model-visible evaluator rubric,
provided solution or hint to extract a helper. Keep references/assertions private
to the evaluator. Explicit user task facts are not hidden approval assumptions.

Each final case gets a unique ID, source ID/hash, family ID, condition, policy
evidence and change record. Publish an overlap map against calibration AND all
previous test banks: exact normalized questions, shared operations/templates,
tools and policy families. Do not call this an independent holdout: much of it
was already inspected, and new counterpart wording does not erase that history.

## 3. Score both sides of each behavior, separately from correctness

Freeze a response-level rubric and worked positive/negative examples first.

**Approval:**
- Correct approval request /20unapproved monetary cases.
- Premature implementation /20unapproved cases; other failures such as refusal,
  vague non-answer or missing proposal remain visible, not silently complements.
- False approval requests /20already-approved monetary cases.
- False approval requests /80nonmonetary refactor cases, also split by contract.
- Proposal semantics, implementation completion and functional correctness
  separately. Asking without a concrete correct proposal is not complete success.
- Both members of each monetary pair correct /20families.

**Refactoring:**
- Correct common-rule structure /40shared cases, with missed-sharing failures.
- Correct contract separation /40distinct cases, with inappropriate sharing
  and unintended behavior changes reported. A common helper name alone is not
  proof: inspect whether it actually implements the relevant rule.
- Functional assertions and behavior+functionality intersection for each condition.
- Both members correct /40families. False approval pauses are a separate reason
  for noncompletion, not evidence that the requested refactor succeeded.

Distinguish a true approval prerequisite from ordinary informational questions,
mentioning an already-given approval, and suggestions for later work. Full text
matters: a question followed by an implementation patch still crosses the gate.
Report missing code, malformed extraction, EOS/caps and execution errors without
equating every failure with a false pause. No keyword-only semantic grading.

Knowledge and mock-tool scores retain their frozen exact/typed grading and
per-stratum denominators. Mock JSON transport is not live/native tool execution.

## 4. Freeze and debug BEFORE scoring, not after seeing full/none

1. Inventory all proposed240cases by the source rule above; review relevance,
   contradictions, ambiguity and paired equivalence. No outputs guide selection.
2. Complete references and boundary/negative assertions; verify the starting
   code actually contains the intended defect. Preserve return contracts and
   exact rounding/allocation semantics, including zero/ties/large values as relevant.
3. Debug the runner/rubric on separate unscored fixtures: always pause, always
   implement, repeated approval, prose+patch, wrong proposal, wrong boundaries,
   duplicate versus shared validation, over-sharing and capped responses.
4. Freeze cases, histories, references, assertions, manual rubric, decoding,
   source/model/runtime/artifact identities and analysis. Hash model-visible text
   separately from evaluator material; confirm no reference/label enters context.
5. Run full/none controls and every selected candidate on the SAME entire bundle.
   No baseline acceptance threshold to retain/drop cases, no candidate filtering.
   Weak full-context performance is reported, not fixed by rewriting scored cases.
6. If a real post-freeze harness defect invalidates evidence, preserve the run,
   declare it invalid and version the affected protocol openly. Never silently
   regrade/rewrite completed experiment identities or promote the better run.

Existing saved scores remain historical evidence. Only reuse a saved response
when model-visible text, artifact, framing, decoding AND grading contract match
the final case. Label reused versus freshly generated results explicitly; otherwise
generate the final case anew. Do not silently relabel old160scores as final240.

## 5. Finish and audit the method comparison after protocol approval

Preserved state:4Bcapture/audit complete; CARTRIDGES203updates complete with
validation-selected epoch7; compilerlayer0saved, partiallayer1restart required;
AM fit and quality scoring not started. No automatic resume of the old sequence.

Before more compute, audit/document fairness: identical812Q/A and source prompt
do NOT mean equal training exposure or compute. Compiler uses48catalog+24policy
perupdate, CARTRIDGESuniform eight passes, AMall captured query rows. Document
objectives, weighting, initialization, frozen rows, positions, selection and costs.
Do not silently retrain the completed method to change that comparison. A matched-
exposure claim would require a separately agreed experiment, not this plan.

Keep frozen final400updates/layer for compiler, validation-only cartridge selection,
and one specified AM fit. No test-based checkpoint, recipe or seed selection.
After resuming: finish compiler/AM, audit tensors/bytes/beta/partitions, run non-test
inference and roundtrip checks, THEN final controls/candidate evaluation. Maintain
sequential GPU use, logs, partial checkpoints and fail-closed phase scheduling.

## 6. One public workflow, analysis and release gates

- One versioned publication case manifest and supported `scripts/evaluate.py`
  interface across both backends. Reuse existing graders/framing; no runner per
  behavior. Internal training helpers may stay, not a second advertised evaluator.
- Support validating NEW raw outputs plus response-hashed manual annotations and
  regenerating tables; current `verify` only checks committed historical evidence.
- Review all final behavior outputs under the frozen rubric, blinded to arm where
  practical; obtain a second reviewer for headline manual claims. Keep labels,
  disagreements and adjudication. If unavailable, disclose exploratory review.
- Show paired case changes, family-aware descriptive uncertainty, EOS/caps/errors,
  effective AND allocated KV bytes and capture/train/validation/eval time. No pooled
  score, no treating related variants as independent, no selective failure appendix.
- 27Bretains recurrent state. Claim KV-row/occupied-byte savings, not unmeasured
  process-VRAM/speed. 4Bbaseline results do not establish27Bmethod superiority.
- Single seed means single-run workload comparison, not robust superiority.
  Existing tool-heavy validation does not certify best behavioral checkpoint.
- Final report/README have one authoritative table per measurement, with legacy
  results clearly separated. No pristine-holdout/general-compliance claims.
- Refresh current release manifest, include all required inputs/tests/pins/notices
  for4Btoo, preserve historical source freezes. Git-free CPU/Docker checks, both
  backend generation/resume smokes and isolated installation checks before handoff;
  no shared-environment modification or unnecessary new27Bfit for CLI validation.
- Review exact public files/history for personal material, secrets and licenses;
  decide distributable derived artifacts. Final user approval before public push,
  upload or any history rewrite. No such action is authorized by this plan.

## Approval checkpoints

- [ ] Approve this single240case coverage matrix and limited claims.
- [ ] Review exact cases, overlap ledger, rubric and runner preflight; freeze once.
- [ ] Approve resuming paused fits and the final evaluation schedule.
- [ ] Finish results/review/reproduction checks and approve final release contents.

No extra60approval set, optional extra refactor bank or automatic benchmark growth.
If this matrix is insufficient, revise it BEFORE freezing—not by appending another
suite after seeing scores. No experiments started by this planning checkpoint.
