# Clean evaluation v2 — prospective expansion

Authorized 2026-10-17 following v1's small sample and rubric limitations.
No training, recapture, cache selection, or changes to prior results.

200 scored cases × full/none/joint4k/joint8k = 800 case/arm records:
- Knowledge60:20toolidentities,20fieldidentities,20instructionfacts.
- Mock tool sessions60:20singlecall,20clarification,20two-step sessions.
- Natural behavior80:20unapprovedmoney,20approvedmoney,20sharedrule,
  20distinctcontracts.40pairedclusters, not80independent experiments.

Knowledge always requests an identifier/short answer, not prose. Tool sessions
use explicit JSON transport. Clarification tasks explicitly require asking for
missing user input rather than discovery/listing; no hidden ask-first rule.
Multi-step tasks explicitly request particular operations and use frozen returned
data. Equivalent tools accepted where supported by the frozen schema, unique
bare names accepted. No advice-keyword tasks. Session, tool identity, schema,
argument values, format, unattempted actions and caps reported separately.

Behavior spans20monetaryoperations and20nonmonetaryrules, with varied arithmetic,
boundary, collection, parsing, normalization and exception cases. Not a renamed
copy of one template. Both process/structure and semantic correctness matter:
money proposals reviewed for content separately from approval gating; approved
implementations and refactors tested with isolated functional assertions.
Shared helpers inspected for actual common-rule execution, not just name match.
Distinct contracts and approved changes remain in the scored denominator.

Use the same immutable publication-source27B caches/prompt/runtime as v1.
Fresh questions/references/debug fixtures authored before model outputs. Related
domains/families already appeared in training/v1; exact novelty does not establish
semantic holdout. Report cluster-aware paired differences/descriptive uncertainty,
not population generalization from authored fixtures. No score pooling, ties
removal, favorable-seed selection, or post-output case/rubric repair. Full-context
failures stay. Manual review is unblinded assistant review, not independent human
adjudication. Freeze all source/inputs/artifacts before generating even debug.

Preflight: all reference calls schema-valid; positive and negative graders on
distinct fixtures; all authored reference programs pass Docker and original-code
negatives fail. At least one model-debug case per suite and contrasting behavior
cases before scored run; debug validates transport, not full-vs-none quality.
Checkpoint each record, source-bound resume, UTC progress/rate/ETA. Keep original
v1 immutable; expanded source/output under clean_eval_v2/clean_eval27b_v2.
Knowledge128tokens,tools256/action,behavior1536tokens,greedyEOS protocol unchanged.
4B comparison training remains paused pending prompt support/method parity audit;
these test answers cannot enter fitting. No public push/upload authorized.
