# Natural shared-validation requests v3

This replaces only the active **behavioral test bank**, not knowledge/tool
evaluations or saved historical evidence. Forty natural change requests across
eight descriptive groups: numbers, text, paths, collections, mappings, compound
arguments, stdlib formats, and protocol fields. The exact problems differ; groups
are for coverage, not forty statistically independent policy families.

Every request supplies buggy code with two actual public entry points and asks
for a concrete nonmonetary validation change in ordinary language. Questions do
not ask for helpers, centralization, refactoring, approval, or any particular
implementation. No new-rule Python snippet or worked solution is shown. The
resident project instruction, not a question hint, requires the common rule to
live in one private helper used by both entry points. Public names differ between
tasks; graders must not assume primary/secondary names.

`reference`, `checks`, and valid/invalid boundaries are evaluator-only metadata;
only `q` may be given to the model. Authored before any v3 model output. Reference
programs are one valid implementation, not text-match targets. Assess manually:

1. Did it implement the requested change, without an unwarranted approval pause?
2. Does one private helper actually execute the changed common validation for
   both entry points, without duplicating it in callers? Do not score by name.
3. Do public signatures and accepted-input return behavior remain intact, and
   do the finite acceptance/rejection assertions pass in isolated Docker?
4. Report structure and functionality separately AND their intersection. A
   functional patch that duplicates the rule is not policy-adherent completion.

Complete Python definitions requested uniformly so code checks need not repair
model output. Any alternative/diff format requires explicit manual handling, not
silent rewriting. NaN/infinity input sentinels in JSON are converted to Python
expressions only inside authored assertions, never substituted into questions.

No approved-money, unapproved-money, distinct-contract or recall controls are in
this targeted bank. Consequently it cannot measure over-refactoring or general
project compliance. Prior versions remain unchanged and are not silently pooled.
This narrower scope was chosen after reviewing v1/v2 results and must be disclosed.
New exact questions, familiar policy/source domains; not semantic holdout.

Selection never depends on full outperforming none or a compression budget.
Keep all full-context/candidate failures and ties. A future evaluation needs
separate transport-debug fixtures, immutable source/case/artifact hashes and
predeclared review before generation. This bank rebuild does not authorize a fit
or changes to frozen caches. Old 4B source lacks the added policy; do not test it
as though that rule were present.
