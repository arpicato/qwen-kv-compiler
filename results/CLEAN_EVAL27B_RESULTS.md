# Clean evaluation v1

Status: all256case/armrecords complete; manual review complete. No fitting.
Source checkpoint `b14aed5`, branch `eval/clean-suites-v1`.

## Protocol

See `CLEAN_EVAL27B_PLAN.md` and `inputs/clean_eval_v1/README.md`. Separate totals:
24 knowledge (8 tool / 8 field / 8 instruction recall), 16 mock tool sessions
(8 single / 4 clarification / 4 two-step), 24 natural behavior requests (6 each
unapproved money / approved money / shared rule / distinct contracts). The behavior
set has 12 paired clusters. Cases authored before scored output, not selected for
full-context advantage. Neither exact-question novelty nor pairing establishes
semantic independence from calibration or previous research.

Frozen publication-reproduction teacher and 4k/8k caches, same26341tokenprompt.
No fit/recapture/architecture change. 4B fits remain paused; its original prompt
needs a policy-support audit before reuse of the behavioral cases.

## Preflight

No-model tests pass exact short-answer grading, unambiguous bare-tool aliases,
schema/value/identity separation, malformed JSON, wrong-tool/wrong-value/extra-field
negatives, cap handling, reference signatures and shared-helper diagnostics.
All reference calls validated against actual prompt schema. Source review corrected
a draft base64 assumption before freezing: this tool server expects literal content.
Two-step cases read mock data and use the returned values in a later call.

On XTX, isolated Docker tests passed all25authoredreference implementations and
rejected unchanged-code negatives for all25, including the separate debug case.
Inputs exactly match the authoring script; no exact question overlap with joint
calibration or previous joint evaluation inputs. No knowledge/tool/behavior score
is pooled. Manual behavior and functional assertions remain separate.

Execution source is a tracked `git archive` at
`/mnt/data/artifacts/kvcompile/releases/clean-eval-v1/`. New outputs under
`/mnt/data/artifacts/kvcompile/artifacts/agent/clean_eval27b_v1/`.
Preflight local log `/tmp/opencode/clean-eval-preflight.log`.
Freeze, separate debug outputs, scored outputs and review to be recorded next.

## Freeze and model-debug checkpoint

All scored inputs and execution/grading source frozen before any model output.
Freeze SHA256 `a16431db3b47c3c8d246de9bacd426231a766dbe7bbf9f0cc7813ab994808e3f`;
model weights/metadata and all four arm artifact identities checked. Stored in
`CLEAN_EVAL27B_FREEZE.json`. Frozen source checkpoint `b14aed5` unchanged.

Separate full-context debug: recall exact command correct, typed JSON tool call
correct, approved monetary implementation correct and functional assertions pass.
3/3debugfixtures,79.197s,raw`CLEAN_EVAL27B_DEBUG.json`. This is a transport check,
not a score gate or permission to alter scored requests. Wrapper1607237 exited.
All scored cases unchanged. No model training. Scripted preflight outputs retained
in`CLEAN_EVAL27B_PREFLIGHT.json`. Next:256scoredcase-armrecords,manualbehaviorreview.

## Results — three separate questions, no pooled score

| Knowledge: exact short-answer recall | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Tool identity /8 | 8 | 0 | 8 | 8 |
| Field identity /8 | 8 | 3 | 7 | 8 |
| Project instruction facts /8 | 8 | 3 | 5 | 6 |
| Total /24 | 24 | 6 | 20 | 22 |

Eight no-prefix knowledge responses hit128tokens; other arms no caps. Some
identifier questions did not explicitly request a short-only answer, although
the frozen scorer requires one. No-prefix often returned general GitHub CLI/API
advice rather than this prompt's tool identifiers. This mixes response format and
catalog recall; not eight proven missing facts. Scores remain frozen.
The field question about literal content explicitly supplies the no-base64 fact;
it tests the field identifier only, not independent recall of encoding semantics.

| Mock tool sessions completed | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Single call /8 | 8 | 1 | 7 | 8 |
| Clarification then call /4 | 3 | 0 | 2 | 3 |
| Two calls with mock reply /4 | 4 | 1 | 4 | 3 |
| Total /16 | 15 | 2 | 13 | 14 |

No tool caps. The PR clarification fixture assumes asking first; full/4k/8k
instead list PRs, potentially a reasonable preparatory action. The harness has
no list-first continuation. Retain the miss but don't describe it as unsafe or
unequivocally incorrect. No posthoc repaired score. Other observed compressed
errors:4komits from_branch or invents base_ref;8kuses tag_name instead of tag.
Detailed attempted-call format/tool/schema/value counts, clarification and
unattempted steps are in CLEAN_EVAL27B_SUMMARY.json. Conditional call accuracy
does not equal session success; later steps only run after earlier success.

| Natural-response behavior (manual) | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Approval gate: no implementation before approval /6 | 6 | 0 | 6 | 6 |
| Approved change: implements without another pause /6 | 6 | 6 | 6 | 6 |
| Shared validation: one private helper used by both /6 | 6 | 0 | 3 | 2 |
| Distinct validation contracts remain separate /6 | 6 | 6 | 6 | 6 |

These are process/structure judgments, NOT whole-response correctness. In the
unapproved split case,4kand8kask for approval but propose a formula giving the
extra cent to the wrong recipient;8k'sexample contradicts its formula. We retain
the gate pass and explicitly mark proposal content incorrect. Full/no-prefix/8k
also implement that approved split incorrectly;4kgets it right. No unsafe formula
is promoted as a correct proposal merely because approval was requested.

| Functional assertions on implementation-required cases | Full | None | 4k | 8k |
|---|---:|---:|---:|---:|
| Approved monetary implementation /6 | 5 | 5 | 6 | 5 |
| Shared-rule implementation /6 | 6 | 6 | 6 | 6 |
| Distinct-contract implementation /6 | 6 | 6 | 6 | 6 |
| Shared-rule behavior AND functional assertions /6 | 6 | 0 | 3 | 2 |

Unapproved-money code assertion results are diagnostic only: supplying a correct
patch before approval still fails the gate. AST common-helper detection agrees
with manual inspection here, but is not the behavioral authority. All generated
shared/distinct code was manually read for duplicate validation and unrelated
changes. No hidden grader repair or answer extraction repair was needed.

## Interpretation and remaining limits

The clearer sets distinguish recall, mock transport/calls, process constraints,
and functional correctness. Full context does not have perfect code correctness;
4kand8kdo not uniformly rank by budget on these few shared-rule examples. Do not
average the three sets, infer8kisgenerallyworsefrom2vs3,orpool the12paired
clusters as24independent discoveries. Same two authored policy families and
familiar schema domains, not broad generalization or production safety evidence.

The PR fixture and short-answer-format limitation show why a preflight/debug
pass is not proof every scored task is unambiguous. Preserve them as disclosed
v1limitations;don'tkeep rewriting and rerunning until the table looks clean.
Use this taxonomy in the report, alongside the frozen construction history.

## Execution and 4B handoff

Source`b14aed5`,freezea16431db...,scoredPID1607874;completed2026-10-17T13:48:28Z
in393.032s(6m33s),plus79.197sseparatedebug and preflight. Per-case checkpoints;
all256rows saved under clean_eval27b_v1/test.json and CLEAN_EVAL27B_RAW.json.
All model jobs finished. Original release artifacts/runtime unchanged. No public
push or upload. Manual review retains source hashes and per-case rationale in
CLEAN_EVAL27B_REVIEW.json. Summary regeneration and grading checks are automated.
Final verification regraded all256records and matched every automatic decision;
manual judgments match raw-response SHA256. Completed-run resume verified every
frozen source/artifact hash and returned Already complete without model loading
or generation. Seven targeted local regression checks passed; no job remains.
Review was performed by the authoring assistant with arm labels visible, not
blinded independent human adjudication. Any later external review should retain
these original judgments and document disagreements separately.

4B comparison remains paused at protocol/implementation audit, not training.
New4Bfitsmustnotconsume these answers. Reuse the evaluation structure; reuse
exact cases only if the4Bprompt contains their required facts/policies. Adding
the27Bbehaviorpolicyto4Bwouldrequireexplicitlyfreezinganewcommonpromptand
freshtrainingtargetsforallmethods. No claim that old4Bartifactsfailed absent rules.
