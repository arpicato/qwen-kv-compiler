# Clean evaluation v1 — prospective protocol

Authorized 2026-10-17. 4B method-comparison training is paused. No training,
recapture, selector changes or cache selection are part of this evaluation.

## Questions and reporting

Three separate sets, with no pooled score:

1. Prompt knowledge: 24 short-answer items, eight tool identities, eight field
   identities, eight project-instruction facts. Exact normalized identifiers or
   explicitly frozen aliases, not substring credit. This is recall, not behavior.
2. Mock tool interaction: 16 sessions (eight single calls, four clarification,
   four two-step). Explicit JSON transport, schema validation, frozen mock replies.
   Report tool identity, argument validity, accepted values and session completion
   separately. No advice-keyword cases. Not native tool execution.
3. Project instruction following: 24 natural-response cases in 12 paired clusters:
   six monetary changes with/without explicit behavior approval, and six pairs
   of shared-rule versus intentionally distinct contracts. Score each stratum
   separately. Manual behavior decisions and functional code assertions remain
   separate; report their intersection for cases requiring implementation.

Small authored diagnostic sets, not independent population samples. Contrast
pairs are related and must not be counted as independent discoveries. Families
and tool schemas have appeared in development/training; new wording alone is
not semantic holdout. No broad compliance/safety claim. No filtering by full/none
gap, no dropping ties, no tuning after scored output. Full-context failures stay.

## Freeze and execution

Before scored model outputs: publish exact questions, evidence references,
expected calls/answers, behavior rubrics, code assertions, debug cases and source
hashes. Validate positive AND negative scripted responses on distinct debug cases;
check all reference calls against the prompt schemas and all code assertions on
authored reference implementations in isolated Docker. Verify exact question
separation from calibration and prior evaluation inputs; disclose source/template
relationships rather than claiming no leakage from zero exact overlap.

Use full/none/joint4k/joint8k from the completed publication-source reproduction,
26341-token prompt and original recurrent states. Greedy unchanged EOS protocol;
knowledge128,tool256/action,behavior1024 tokens. Caps reported, never silently
accepted as completed code/calls. Checkpoint after every case and freeze identity
on resume. No edits to historical cases/graders/source snapshot.

Run separate debug cases through full context first to check transport only;
these outputs cannot justify changing scored cases or project policy. If harness
is materially invalid, preserve outputs, mark the run invalid, and obtain a new
version rather than silently repair completed scores. No quality gate requiring
full context to beat none. Manual review retains raw output and rationale,
including ambiguous approval formulas and alternative valid refactoring styles.

## 4B boundary

Freeze this structure before new 4B fits, not contingent on 27B success. Reuse
cases only where the frozen 4B source prompt supports them. Original 4B prompt
does not automatically include the added 27B behavioral policy: audit that before
claiming the same behavior test applies. Any prompt/data change needs a new
explicit 4B protocol and fresh targets for all methods. Test answers never enter
calibration or checkpoint selection. No 4B GPU work launched here.
