# Frozen-cache offline task evaluation

Authorized 2026-10-16. **Complete: 8k solves 30/40; 4k solves 21–22/40, full 40/40.**
Artifact: XTX `/mnt/data/artifacts/kvcompile/artifacts/agent/task27b_v1/`.
Log: `/tmp/opencode/task27b.log`. No training, cache changes, or live service calls.

## Results

| Frozen artifact | Single call | Clarification + call | Two steps | Rule advice | All tasks |
|---|---:|---:|---:|---:|---:|
| Full context | 20/20 | 8/8 | 6/6 | 6/6 | **40/40** |
| No context | 1/20 | 0/8 | 0/6 | 0/6 | **1/40** |
| Position8k | 13/20 | 5/8 | 6/6 | 6/6 | **30/40 (75%)** |
| Purpose4k | 9/20 | 3/8 | 3/6 | 6/6 | **21/40 (52.5%)** |
| Position4k | 10/20 | 3/8 | 3/6 | 6/6 | **22/40 (55%)** |

On the 39 tasks full context solved but no context did not, 8k solves30/39,
purpose4k21/39,position4k22/39. All arms ask for missing information on8/8 initial
clarification turns: the failures occur on the subsequent action, not the first
question. The task wording explicitly advertises missing information, so this is
not a hard test of discovering implicit omissions. No malformed JSON or cap hits.

Six tasks about three tools absent by name from calibration Q/A: full6/6,none1/6,
8k3/6,purpose4k2/6,position4k3/6. This is tiny, paired/repeated-tool evidence, not
an independent pristine holdout. 8k vs purpose4k has10gains/1loss; vs position4k
10gains/2losses. Extra budget helps overall here, but does not fix every4k success.

### Decisive trace checks

- Full and8k read each existing file's SHA and use that returned value on the
  update:3/3. Both4k candidates instead immediately attempt the update without
  reading or providing SHA:0/3. The fixture has three variants of one workflow,
  not three independent workflow families.
- All compressed artifacts pass the three thread-read/resolve workflows.
- 8k failures include an invented draft tool name, posting a new comment instead
  of editing an existing one, wrong tag/release tools, `ghsa_id` instead of `ghsaId`,
  `team` instead of `team_slug`, and `failed_job` instead of `failed_only` while
  also omitting requested `return_content`. These are not just JSON formatting.
- Both4k artifacts omit requested draft status when opening a PR and lose source
  branch information when creating a branch (omitted or invented`from_ref`).
- All compressed artifacts pass6/6 *keyword advice rubrics*, but free text still
  invents details: both4k migration answers change the~400-line guideline to~200
  and add unsupported requirements. 8k overgeneralizes generated-file wording
  to`infra/`. Thus6/6does not certify accurate policy summaries or compliance.

### Grading limitations, scores unchanged

Exact declared calls/arguments are intentionally strict, but are not a complete
semantic equivalence checker. For example, both4k outputs use`ref:"release"`
instead of requested`refs/heads/release`on the file-read task; this may resolve to
the same branch in a real server but was not an accepted alternative. Some methods
allow optional defaults/pagination that the frozen exact matcher would also reject.
We retain this scored failure and disclose it rather than revise scoring after
seeing generations. Bare tool names (most no-context failures) are rejected, so
the1/40no-context result partly measures catalog namespace recall, not total lack
of task understanding. The full40/40 demonstrates this runner is usable with the
source context; it does not validate every possible alternate action.

Verdict: the previous recall totals overstated practical task reliability. New8k
shows useful two-turn behavior but still fails10/40tasks;4kfails18–19/40. Neither
is ready for unattended use on this evidence. No artifact promotion, tuning, new
fit, or follow-up evaluation started. Small authored/correlated test, single greedy
run, no confidence claim about arbitrary agent tasks. Repository-rule advice is
not execution; native tool-call formatting, recovery and real services untested.

## Completion and artifacts

Scored run401.260s(6m41s),including hash checks/load;debug64.116s,combined465.377s
(7m45s),not counting CPU case construction/local checks. All200arm/task records
completed2026-10-16T04:04:22Z;wrapper1517377/python1517379exited. Source/compiler
artifacts unchanged; no live API calls or EXL3/environment modifications.

- `TASK27B_FROZEN.json`: pre-output cases, rules, overlap and file hashes.
- `TASK27B_OUTPUTS.json`: all200task records with actual action traces and reasons.
- `TASK27B_SUMMARY.json`: counts, categories, failureIDs, common informative slice.
- `TASK27B_DEBUG.json`: separate debug gate outputs.

XTX originals:`frozen.json`,`test.json`,`debug.json`under the artifact root above.
`scripts/summarize_tasks27b.py`regrades every action and asserts exact agreement
with all recorded scores without changing the frozen parser/grader. File identity
includes prompt, cache tensors/manifests, evaluator/helpers and model metadata;
model weight shard hashes were not newly computed. Inputs must remain immutable
for any resume; cache hashes were checked before generation.

Post-run verification: every frozen file hash and case/transport still matches.
Re-running the freeze command against the existing file reported a mismatch because
it compares serialized text and builds file entries from a set (key order varies).
A separately generated manifest under `/tmp/opencode/task27b-verify/` is identical
as parsed data. Original frozen bytes/hash remain untouched; no generation rerun.
This is a freeze-command repeatability defect, not changed experiment inputs.
The evaluator's hash-based resume is unaffected. Do not overwrite the frozen file
or modify its hashed scripts to repair this completed run; fix canonical ordering
and add a cross-process regression check before reusing the freezer for a new run.

## Protocol frozen before scored generation

40 synthetic tasks from the exact resident prompt: 20 single calls, 8 missing-input
clarification conversations, 6 two-step tasks (3 file SHA retrieval/update, 3 review
thread retrieval/resolution), 6 advice-only repository-rule cases. Two separate debug
cases exercise transport/continuations before scored tasks. No scored outputs used
to fix the runner, change cases/accepted answers, select artifacts, or train caches.

Compare full context, no context, position8k, purpose4k, position4k. Fixed existing
artifacts; include both 4k candidates because their previous scores traded off.
Source prompt 26033 tokens; original full recurrent state retained in compressed
arms, logical position 26033. Occupied attention KV: full 1627.1 MiB, 8k 512 MiB,
4k 256 MiB; recurrent state 151.5 MiB unchanged. No process-memory savings claim.

Greedy no-thinking, EOS {248044,248046}, max 256 tokens/action (not the old recall
test's 64), physical cache capacity 32768. All arms receive identical extra user
instructions specifying a JSON call/ask/answer transport. The transport supplies
no catalog or required field list. Fake results enter as tool-role messages;
clarification replies enter as user messages. Every continuation replays its actual
transcript from the frozen prefix; it never inserts expected calls or corrects a
failed output. Stop task at first failed action; success requires every step.

No model action reaches any API/shell dispatcher. Exact tool+argument values against
predeclared equivalent tools; reject extra fields (unrequested changes), missing
required fields, bad types, malformed/duplicate JSON, cap hits. Advice and question
text uses explicit keyword groups, not a semantic judge; preserve raw output for
review without changing frozen scores. Formatting/action success is separate from
native tool-calling compatibility. Report failure reasons and categories alongside
whole-task success. No-final-acknowledgement requirement: completion is the last
correct mock call. Reads are validated against expected local fixtures, writes
are accepted only for matching expected values; never execute arbitrary names.

`freeze_task27b.py` records immutable input hashes, source/schema validity, and
tool-name (qualified/bare) calibration mentions per case. This is new task wording,
not universally unseen tool knowledge; six two-step tasks span only two workflow
families. Existing untrained tools may occur here but have been evaluated before.
Policy advice is not behavioral execution. Authoring is source-grounded, not based
on candidate failures, but follows prior inspected experiments. 40 tasks are small,
correlated, not a public benchmark or production certification. Freeze hashes before
any scored model output; record debug gate and overlap before test execution.

Save every completed task atomically and resume only with identical frozen identity.
Runtime/progress include UTC time, elapsed, count, rate, ETA; complete status only
after all arms/cases finish. Report overall and full-correct/no-context-wrong paired
results; exclude full-context failures only in that separately labelled slice,
never from overall counts. No automatic promotion, further fit, or new evaluation.

## Verification

`python3 scripts/test_task_eval27b.py` passes all accepted-call source schemas,
parser rejection, required fields/types, unrequested writes, and continuation tests.
Python syntax and remote hash checks passed; final trace regrade passed200/200.

Implementation `1593171`, equivalent source-defined calls added `c454389`, all
before scored generation. Remote schema checks passed. Frozen manifest SHA256
`d3bbef9c795fad7279127c62a59206ca139f7487a16bc4024a22ed836b10b9d2`.
`TASK27B_FROZEN.json` retains cases/rubrics, all file hashes and overlap audit.
No exact task question occurs in calibration. Six tasks concern tools without
qualified/bare name mentions in 780 calibration Q/A: tag/gist/advisory and their
clarification versions. These are only three previously inspected tool families,
not a fresh pristine tool holdout. All other tool tasks share practised knowledge;
policy cases also share original calibration facts. Report these slices separately.

Full-context debug passed 2/2 (direct call + missing-ID clarification and later
call), 64.116s including load/hash checks. Detached wrapper1516824/python1516825
exited cleanly. `TASK27B_DEBUG.json` retains actual outputs. At this gate no scored
output had been generated; no changes from debug outputs. Other arms are not required
to pass the debug cases (that would select artifacts by task performance).

Scored run started2026-10-16T03:57:41Z,detachedwrapper1517377/python1517379.
Per-taskcheckpoint/progressverified; allfivearmsnowcomplete. Frozen grading/cases
unchanged after outputs. Original runs remain references; comparison still paused.
