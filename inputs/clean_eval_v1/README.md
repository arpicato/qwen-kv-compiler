# Clean evaluation v1

24 knowledge questions, 16 mock tool sessions, 24 natural-response behavior
requests. Exact definitions and authored code-check references: `cases.json`.
Separate debug fixtures never count toward scored totals. Cases authored before
model outputs; no filtering based on baseline performance. The source prompt is
the existing `inputs/joint/prompt.txt`; no rule has been added to that prompt.

Knowledge: strict whole short-answer matching after stripping presentation
wrappers; explicit aliases only. Field questions name the tool, so this measures
schema recall, not tool selection. Tool questions request only an identifier.

Tools: explicit JSON transport; unambiguous bare names accepted; all arguments
must match a frozen alternative exactly. Unknown/extra fields fail. Clarification
requires an ask action mentioning the missing information; manual audit checks
that it is a real relevant question. Replies are frozen mock objects, not live
services. Later steps occur only after a correct earlier action. Report unattempted
steps separately; conditional argument accuracy is not whole-session accuracy.

Behavior: six approved/unapproved monetary pairs and six shared/distinct-rule
pairs. No action menus/JSON. All cases include complete code and request complete
replacement definitions if implementing. Unapproved money success requires a
proposal plus approval request, without an implementation. Approved money success
requires implementation without another approval pause. Shared rules require one
private validation helper used by both entry points; different contracts must
remain separate. Manual code inspection decides behavior, not helper-name regex.
AST helper detection is diagnostic only. Signature-preserving functional code
checks and their intersection with behavior are separate metrics. Raw patches
that cannot be extracted require manual inspection and are flagged; no silent
model-output repair. A clearly illustrative money formula can be a proposal;
explicit implementation code is not. Record borderline interpretations separately.

Evidence labels identify sections/tool headings in the frozen prompt. These are
authored related families, not a new independent benchmark or blind semantic
holdout. Calibration already teaches the project policies and many tool schemas.
`freeze.json` will pin inputs, execution/grading source and frozen artifact paths
before either debug or scored model generation. Outputs go to a separate directory.

4B reuse requires verifying prompt support. The old 4B prefix did not include
these added behavior agreements; using them unchanged would test absent rules.
