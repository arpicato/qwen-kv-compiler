# Existing guidance: frozen-cache behavior decisions

Authorized 2026-10-16. **Complete: full/8k/position4k26/26,purpose4k25/26,none22/26.**
XTX artifact `/mnt/data/artifacts/kvcompile/artifacts/agent/behavior27b_v1/`.
Log `/tmp/opencode/behavior27b.log`. No new prompt, compression, or fitting.

## Results

| Existing artifact | Paired cases | Both sides correct | Two-stage cases | All cases |
|---|---:|---:|---:|---:|
| Full context | 24/24 | 12/12 | 2/2 | **26/26** |
| No context | 21/24 | 9/12 | 1/2 | **22/26** |
| Position8k | 24/24 | 12/12 | 2/2 | **26/26** |
| Purpose4k | 24/24 | 12/12 | 1/2 | **25/26** |
| Position4k | 24/24 | 12/12 | 2/2 | **26/26** |

Every action parsed, zero cap hits. All130arm/case traces regraded against the
original frozen rules with identical scores. The paired cases require actual
proceed/read/edit/commit/query choices, not merely advice text. All compressed
arms correctly distinguish permitted edits/commits from cases requiring a stop,
report, source change or prerequisite check within these supplied action menus.

The four full-correct/no-context-wrong cases are only **three distinct situations**:

- Advice-only request: no context edits immediately; all compressed arms answer
  the approach without editing.
- Connected read-only database: no context selects DROP TABLE; all compressed
  arms pause instead of attempting DDL.
-1001-rowquery: no context runs it without EXPLAIN. All compressed arms explain
  first. This initial decision is repeated in the two-stage query case.

Purpose4k's sole failure is the second stage: after EXPLAIN succeeds, it refuses
to retrieve the rows. Full,8k,position4k proceed with the requested SELECT.
No-context fails that same case at the first stage, so its second-stage choice
is unmeasured. Informative slice:8k4/4,purpose4k3/4,position4k4/4; denominator4
includes the repeated EXPLAIN situation. No extra hidden validation set implied.

### Interpretation

These behavior decisions survived compression much better than the prior exact
tool/argument task test (8k30/40,4k21–22/40). **This does not isolate inherent
compressibility:** the tests differ in format/difficulty and the menus supply
candidate actions. No-context22/26shows most choices can be made from base-model
knowledge or scenario cues. Only3distinct situations discriminate retained prompt
guidance here. No matched calibration comparison, smaller budget run, or separate
behavior-only prompt was performed. Do not claim general agent compliance from26/26.

Case scope is limited: choices rather than executed diffs/commands, short contexts,
one greedy run and fixed menu order, no adversarial distractor study. The paired
migration variants share the same invariant rather than truly contrast old-vs-new
editing; likewise generated/source variants require source edits in both cases.
An agent can recognize sensible-looking choices without retaining every source
detail. Nominal case-wise Wilson intervals in the summary (26/26~87–100%,25/26
~81–99%) assume independent cases and are not generalization confidence bounds
for these correlated authored scenarios. Existing guidance/calibration facts have
been inspected before. No score revision or case changes after model output.

**Verdict:** encouraging bounded behavior retention, including at4k, with weak
evidence on novel or difficult guidance. It supports separating behavior from exact
catalog recall; it does not establish safe unattended implementation. No new fit,
prompt, promotion or follow-up evaluation started.

## Completion

Scored180.256s(3m00s),debug76.037s,total256.293s(4m16s),including load/hash checks,
excluding CPU authoring/local checks. Scored wrapper1518896/python1518897 finished
2026-10-16T04:55:35Z. Per-case atomic checkpoints/progress verified. No live service
calls, real file edits or real database queries; compiler tensors/prompt/EXL3 env
unchanged. Canonical freeze repeated identically before execution and after
completion; all recorded file identities and cases match the original frozen hash.

`BEHAVIOR27B_FROZEN.json` contains frozen choices/source evidence/expected actions;
evidence is audit-only and was not sent to the model. `BEHAVIOR27B_OUTPUTS.json`
retains all130rawcase traces. `BEHAVIOR27B_SUMMARY.json` records pair/informative
counts and failed actions; `BEHAVIOR27B_DEBUG.json` retains separate debug output.
XTX originals are`frozen.json`,`test.json`,`debug.json`under the artifact root.
`scripts/summarize_behavior27b.py` reproduces scores without modifying the grader.

## Frozen protocol

Compare existing full, none, position8k, purpose4k, position4k artifacts. Unchanged
26033-token system prompt and full recurrent state in compressed arms. Attention
KV512MiB/256MiB at8k/4k, unchanged151.5MiBrecurrentstate; no process-VRAM claim.
Reuse verified task27b artifact/model identities, hash every relevant input before
generation. New freezer uses canonical JSON and a cross-process repeatability test;
completed task27b manifest/scripts stay untouched.

26 cases across12 guidance families:24paired next-action decisions plus2two-stage
sequences (run missing lint then commit, explain large query then retrieve it).
Families: advice vs implementation, generated source, append-only reversible
migrations, untouched vs own test failure, commit permission, force push, protected
branch, read-only DDL restriction, >1000-row explain boundary, comment permission,
dependency inspection, both linters before commit. Exact source-rule quotes are
stored for audit but NOT shown in evaluation questions. No invented refactoring
threshold or general requirement-conflict pause rule.

All arms receive the same available mock action menu and neutral opaque action
IDs, returned as JSON. Menu actions specify concrete read/edit/query/commit/report
operations; they contain no labels like 'correct' or rule quotes. This removes
tool-name spelling as a barrier, but turns the test into *action selection*, not
free-form editing or full sandbox execution. No real commands, edits or service
calls. Selected actions are recorded, no keyword advice scoring. Incorrect first
action fails a case; a later correct answer cannot undo a prohibited action.
Two-stage mock results are appended only after the model selects the right first
action. Both stages must pass, no expected answer inserted into assistant history.

Paired contexts mostly change whether proceeding is allowed. Generated/source and
migration variants deliberately retain the same invariant rather than reverse it;
an all-pause agent cannot pass the positive-action cases. At the1000-rowboundary,
extra EXPLAIN is accepted as harmless; at1001it is required. No explicit commit
request accepts either reporting completion without commit or asking permission;
explicit authorized commit requires committing after all checks. Action choices
are restrictive: not all alternative real-world valid workflows represented.

Greedy, no-thinking, EOS248044/248046,128tokens/action,capacity32768,independent
frozen-prefix reset between cases, transcript replay within two-stage cases.
Single separate debug read-vs-edit case checks menu transport before scored run.
Freeze cases/grader/hash identities before model output. No changing grading,
selecting caches, fitting or promoting artifacts based on results. Save each case
atomically; resume only identical identities. Include full/no-context controls,
overall cases, both-members-correct pairs and full-correct/none-wrong slice.

Limits: deliberately small authored test, short supplied scenarios, choices cue
plausible behaviors, many rules likely known without this prompt. Original71
calibration and earlier probes include policy facts; this is not a fresh policy
family holdout. The two extra sequences repeat conditions from paired cases;
not26independent facts. Passing would demonstrate bounded decision retention,
not reliable arbitrary implementation or prove guidance easier at equal training
coverage than tool names. No separate behavior-only prompt in this experiment.

## Verification / execution

Implementation `05ebd46`. Local/remote source evidence, grading and canonical
cross-process freeze checks passed. Remote freeze repeated byte-identically:
`79f700faffec42edc600bf55bc29243d2cc47b9cbb1bff203551157de859a399`.
`BEHAVIOR27B_FROZEN.json` stores all cases/menus/expected actions and file hashes.
Full-context separate debug passed1/1,76.037s including load/identity checks.
Wrapper1518310/python1518312exited;outputs in `BEHAVIOR27B_DEBUG.json`.
At this gate no scored output had been generated; no changes based on debug.
Scored run started2026-10-16T04:52:35Z,wrapper1518896/python1518897; alljobsnowfinished.
