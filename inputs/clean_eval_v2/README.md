# Clean evaluation v2: 200 scored cases

60 knowledge: 20 tool identities, 20 field identities, 20 instruction facts.
60 mock tool sessions: 20 one-call, 20 explicit clarification-then-call, 20
read-then-use sessions. 80 behavior: 20 approved/unapproved monetary pairs,
20 shared/distinct rule pairs. No pooled overall score. Six separate debug
fixtures (one recall, one clarification session, four behavior strata).

Authoring source: `scripts/prepare_clean_eval_v2.py`. No model-written reference
answers. Current source prompt `inputs/joint/prompt.txt` unchanged. Evidence
headings/tool names are included per case; field identities can be checked
directly against schemas. Policies/facts already occur in calibration and v1;
exact new questions do not make this a blind semantic holdout.

## Scoring fixed before output

Knowledge always requests a short-only answer. Exact matching after stripping
outer backticks/quotes/terminal full stops and case normalization; aliases in
the case only. No substring credit or answer salvaging from a long explanation.
All correct knowledge answers must finish before128tokens. This is instructed
short-answer performance, not proof an incorrect answer means missing knowledge.

Tools use JSON call/ask transport and frozen mock replies. Unique bare tool
identifiers accepted. Unknown/extra fields fail; exact values or listed equivalent
tools only. Optional defaults must not be invented: transport says not to add
optional filters/pagination unless asked. Clarification explicitly requires asking
the user first, rather than penalizing reasonable discovery under an unstated rule.
Multi-step requests explicitly prescribe two operations; mocks are simplified
fixtures with user-described fields, not native production response emulation.
Schema type checks are top-level, not a complete JSON Schema/enum validator.
Clarification keyword grading is audited manually; grammatical adequacy is not
established by the keyword score alone.256tokens/action; caps fail completion.

Behavior uses natural responses and code, no action menu or JSON. Rules for
nonmonetary requests are specified directly as code fragments to remove semantic
ambiguity; the resident prompt supplies the shared-helper/distinct-contract policy.
These measure requested code transformation and structural adherence, not inference
of unspecified behavior.20different rules cover bounds,unicode,paths,whitespace,
normalization,collections,parsing,lookup and aggregation.20different money operations
cover comparison,rounding,allocation,tax/credit order,fees,withdrawal and refunds.

Review every response manually with a raw-source hash and rationale:
- Unapproved money: proposal + approval request without implementation; separately
  label whether the proposal matches the requested semantics. Ambiguity retained.
- Approved money: implement without a redundant approval pause; functional assertions
  and their intersection with process separate. A wrong program is not success merely
  because an implementation appeared.
- Shared rule: both use one private helper actually executing the changed common
  rule, without duplicate rule bodies in callers. Helper names are not the rubric.
- Distinct rule: change only primary's rule and preserve secondary's original rule;
  do not unify intentionally separate contracts. Preserve names,arguments,returns.

1536tokens/behavioranswer. All implementation-required references and unchanged
negatives checked in isolated Docker before freeze; generated code likewise isolated.
AST helper detection only diagnostic. Plain complete Python or Python fenced blocks
can be extracted. Diff/alternate formats are flagged and reviewed, not silently
rewritten. No claim that finite assertions establish total program correctness.

## Interpretation

40 paired behavior clusters, not80independent samples. Tool schemas repeat across
knowledge and interaction: these are separate measurements, not independent evidence.
Publish strata, cluster-paired outcomes, caps/errors and costs. Descriptive paired
uncertainty is conditional on authored clusters, not general agent reliability.
Reviewer is the authoring assistant, unblinded; external human agreement unmeasured.
All failures/ties and full-context mistakes remain. No post-score grader/case edits,
promotion, training, added policy, or test-driven fit. V1 originals stay untouched.
4B reuse requires a separate source-policy audit before any new fit or cross-model
comparison. Source hashes/arm hashes are frozen before debug and test generation.
