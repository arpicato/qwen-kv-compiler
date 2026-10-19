# 27B development answer diagnostic

Authorized 2026-10-15; **complete**. No training or budget change.

## Result

| Cache | Fresh dev correct | Full-teacher-correct failures | Mean reference token NLL per question |
|---|---:|---:|---:|
| Full teacher | 193/194 | 0/193 | 0.0561 |
| Original71 | 168/194 | 26/193 | 0.2315 |
| Coverage476 | 179/194 | 14/193 | 0.1649 |
| Bindings780 | 176/194 | 17/193 | 0.1725 |

Full teacher replays its own reference argmax at **every token on194/194**
questions. Scoring alignment and reset/position path are consistent with free
generation. Original71dev varies167/169/168across invocations; do not read
single-point changes as an intervention. Dev includes previously inspected
questions and shared source bindings; not an untouched holdout.

**The main observed problem is output ranking of exact names, not long rollout
collapse.** Of17latest-cache failures where teacher is correct:

- **13 share the exact teacher prefix until a wrong tool/field token**;10have
  the correct next token rank2, the other3rank3/5/6. No previous wrong token
  caused those first errors. Under a forced-correct prefix, all remaining
  tokens match the teacher argmax in these13cases (including termination).
- **4 differ first in formatting** (`The argument is` vs backticks). Do not
  mislabel that harmless first difference as a binding error. Even forcing
  teacher formatting leaves a wrong semantic token: `resource_id` drops `_id`
  (correct suffix deficit4.078logits), `organization` loses to another token
  (6.375), `affects` loses at its first content token (5.281), `field_filters`
  loses its suffix (4.547). Those four each have one later non-argmax target.
- Concrete shared-prefix errors: `base_branch` vs `base_ref`, `commitSHA` vs
  `commitID`, `failed_jobs` vs `failed_only`, `commit_title` vs `commit_message`.
  The last two correct suffixes lose by4.977and3.188logits. Some mistakes are
  nearly tied (`base_ref` deficit0.031), others are not.
- Across all17failures,43/47tokens after first divergence are teacher argmax
  when given the reference prefix. This includes easy wrappers/EOS and is not
  an independent measure of semantic recovery. Full-answer NLL also includes
  common wrappers/tool namespaces; it is not an accuracy surrogate.

Coverage476has13shared-prefix failures out of14teacher-correct failures; the
other starts with different wording and still favors `org` over `organization`.
The pattern is not unique to the latest bindings run.

**Next direction:** output-supervised KV is better motivated than another bulk
data/local-loss run. First verify a finite, nonzero gradient to a tiny synthetic
KV slice through the frozen27B final logits, with forward parity against the
installed artifact; then define a bounded train-only CE/KL pilot and evaluate
free generation independently. Do not train on these194diagnostic questions.
EXL3 inference kernels are not demonstrated to support this gradient; no new
backend/dependency, full training run, or budget sweep has been started here.
This diagnostic does not prove the information absent, or establish that CE
training will improve generation; output ranking, representation and capacity
remain possible interacting causes.

## Cost and artifacts

**708.374s (11m48s)** total measured diagnostic, including model load, eight
reset passes/question (free+forced for four caches), per-question checkpoints.
No training, no test-suite reruns, no model/shared-environment modifications.
Raw per-token probabilities/ranks/margins and all generations at XTX
`/mnt/data/artifacts/kvcompile/artifacts/agent/answer27b_v1/diagnostic.json`.
Local [ANSWER27B_SUMMARY.json](ANSWER27B_SUMMARY.json) contains failure details.
Manifest/teacher/prompt hashes and configuration are in raw artifact `config`.
Implementation `ce78512`, offline summary `52d9c82`. Job1404436finished;
log `/tmp/opencode/answer27b.log`. Original artifacts unchanged.

## Frozen protocol

Run all frozen 194 development questions, no fixed78/stress197/reserved test.
Compare full teacher and saved original71/coverage476/bindings780 caches.
Each compiled cache retains 8192 rows/layer and the unchanged recurrent state.
Fresh greedy generation: no-thinking, cap64, full EOS set, original framing.

For each question, use the full teacher's fresh generated token sequence plus
its observed EOS as a common reference. Score every reference token in a
separate reset pass under each cache, feeding the reference prefix, not the
candidate's wrong output. Record log probability, vocabulary rank, argmax and
margin to best token, along with fresh free generation and grading. Include
teacher self-consistency and known teacher-wrong cases as controls. EOS is
scored, not consumed again. Raw answer labels are not forced as bare strings:
they often omit wrappers/qualified tool names and are not canonical responses.

Inspect errors at the first differing token and under later forced-correct
prefixes. Disagreement can be formatting or a valid alternative; semantic
failure is determined by the unchanged grader, not token equality. A low
teacher-answer rank is evidence of output distribution error, not proof that
the information is absent from KV. Recovery under forced prefixes suggests
prefix sensitivity, not a proven independent rollout mechanism. No causal
claim from teacher forcing alone; do not confuse falling CE with generation.

No output-supervised KV training started. Its feasibility/recipe depends on
this diagnostic; the EXL3 checkout/shared environment remain read/run only.
Three-way comparison remains paused. Resume checkpoints after every question.
Root `/mnt/data/artifacts/kvcompile/artifacts/agent/answer27b_v1/`;
log `/tmp/opencode/answer27b.log`. CPU test:
`scripts/test_diagnose_answers27b.py` covers scorer alignment, ranks, divergence,
split positions, and no extra EOS forward.

Implementation `ce78512`; CPU scorer test passed. Checkpoint
after each complete question. First22 questions passed live reference-token
count and teacher replay argmax checks (22/22 self-consistent; teacher21/22
graded correct). This checks mechanics, not final quality or a causal verdict.
