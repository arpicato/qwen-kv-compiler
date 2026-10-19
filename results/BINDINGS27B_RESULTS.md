# 27B targeted argument bindings + protected original sampling

Authorized2026-10-15. **Complete; no active job.** Small stress-suite gain over
expanded476, fixed78recovers, strict reserved-tool diagnostic regresses.
Not the paused4B three-way work. No further experiment/deployment started.

## Final generation results

| Suite | Fresh original71 control | Previous476 | Bindings780 | Full context | Caps control → bindings |
|---|---:|---:|---:|---:|---:|
| Dev194 | 169/194 | 179/194 | 176/194 | 193/194 | 1 → 0 |
| Fixed78 | 75/78 | 73/78 | **75/78** | 76/78 | 1 → 1 |
| Stress197 | 165/197 | 173/197 | **175/197** | 197/197 | 1 → 0 |
| Strict diagnostic12 | 7/12 | 9/12 | **7/12** | 12/12 | 0 → 0 |

Previous476column is the saved earlier invocation, not a fresh matched compute
control. Fresh original71dev169vs earlier167demonstrates runtime variability.
No selection/tuning based on any of these scores. Same fresh teacher/no-prefix
informative masks for paired original71/bindings:dev70→80/89,78:44→43/45,
stress80→89/107,diagnostic5→6/9. No-prefix104/194,32/78,90/197,3/12.

Paired original71→bindings gains/losses:dev12/5,78:1/1,stress16/6,diagnostic2/2.
Compared with previous476outputs:dev4gains/7losses,78:3/1,stress4/2,
diagnostic0/2. Historical evaluations are not pristine heldout; no significance
or whole-agent reliability claim from small differences or strict12diagnostic.

- Stress selection **47→56/62** (previous476:57). Arguments **118→119/135**
  (previous476:116). Candidate175still22below full197/197.
- New binding pairs directly target101stress arguments:original86/101,
  previous47683/101,candidate86/101. Other34arguments32→33/34. On dev directly
  targeted98arguments original88,previous88,candidate87. Thus reverse-direction
  source reconstruction did **not** demonstrate robust new argument recall.
- Fixed78by-kind matches original control:lookup27/28,style18/20,tools26/26,
  unrelated4/4. Against original, gains create_issue required field; loses
  WebFetch for questions about opencode. Against previous476, recovers Python
  package manager,incident-response skill,normal-answer length, but adds that
  WebFetch loss. Historical shared20:19→20;other58:56→55.
- Strict diagnostic6dev4→4/6, reserved6test3→3/6, versus previous4765/6and4/6.
  No cap hits. Reserved-tool result did not improve.

**Verdict:** original sampling exposure was restored and three earlier policy/
skill errors recovered, but this does not isolate sampling as the cause: data,
batch size and total example work also changed. Stress175vs173is only2more
correct at~3.06×compiler duration, with worse dev/strict12scores. Not a clear
overall successor to expanded476; preserve all references and do not promote
or automatically extend this recipe. No evidence that simply adding more of
these reverse-direction bindings solves argument retrieval.

## Cost and artifacts

Same8192occupied attention rows/layer,16layers,512MiB attention KV; unchanged
teacher recurrent state. No measured allocated-VRAM saving (paged capacity32768).
Capture1690.169s +compile7593.103s +evaluations1735.570s =**11018.843s
(3h3m39s)** recorded total, excluding preparation/analysis and historical runs.
Compile2h6m33s vs prior coverage41m19s. Each of400updates/layer samples72rows,
3×previous24sample budget; no matched-compute causal claim.

Root `/mnt/data/artifacts/kvcompile/artifacts/agent/bindings27b_v1/` contains
questions/sampling JSON,`traj/`,`compiled/`,original control reference symlink,
heldout cases/diagnostic JSON,`{dev,agent78,stress197,diagnostic12}_{baseline,candidate}.json`,
`summary.json`. All per-question generations retained. Local machine-readable
[BINDINGS27B_SUMMARY.json](BINDINGS27B_SUMMARY.json) (generic arm label `expanded`
means bindings780),[BINDINGS27B_DETAIL.json](BINDINGS27B_DETAIL.json).
Expanded artifact manifest SHA256
`794ef6d981371d599ae297a7052ba73b158e710060b38dd58b9e6124c50b524d`.
Logs `/tmp/opencode/bindings27b-{capture,compile,eval}.log` on XTX.
Capture1273606,compile1292320,evaluation1292585finished. Original artifacts intact.
Implementation9549b31,audit13fdd01,capture30dea4b,compile786d965,devd8e2b7f.

## Frozen protocol and chronological checkpoints

Audit all702argument fields of unchanged manual, not evaluation failures:
214required bindings already supervised,162shared owner/repo/pagination fields
skipped,22fields excluded because on six reserved diagnostic tools. Add304gaps:
247optional/conditional +57required. Preserve original71and repaired405train;
total780. No val107 fitting, no153/143data, no model-generated paraphrases.

Questions reverse direction from stress suite: name field+tool, ask purpose,
conditions and distinctions; answer exact source field description. This is
source-grounded calibration, **not an independent paraphrase benchmark**.
Source conditions include paired/confusable fields when schema describes them;
no invented conditional semantics. Evaluation question overlap checked, not used
to choose fields. Keep all6diagnostic tools absent from additions.

Model27B EXL33.5bpw, original26033token prompt, original teacher recurrent state,
8192synthetic KV rows/layer, frozen sink; corrected projected/gated objective,
LR0.001,400updates/layer,cosine1,seed0,chunk4,BF16export. Each update has disjoint
24original71 +24existing405 +24new304 samples. Original expected exposure135.2
is preserved rather than diluted to20.2.72examples/update vs24before: **3×sample
budget**, not same compute or an isolated data effect. Each group's objective
weight1/3. Chunked backward keeps activation memory bounded. Same400updates;
not an optimizer-step extension. No warm-start, no checkpoint selection.

Original476captured trajectories and teacher reused only if Q/A and KV hashes/
tensors match; fresh capture304only. Capture checkpoint every25questions with
progress5questions; max interval25, compiler checkpoints each layer. Frozen
generation greedy/no-thinking/fullEOS/cap64; dev194 then fixed78/stress197 and
strict12diagnostic. Same fresh teacher/no-prefix masks for paired original71
control; expanded476artifact remains secondary comparison. No new test cases.
Report policy/skill retention, argument/tool scores, caps and cost. Existing
evaluations historically inspected, not pristine heldout or agent execution.

Root `/mnt/data/artifacts/kvcompile/artifacts/agent/bindings27b_v1/`.
Logs `/tmp/opencode/bindings27b-{capture,compile,eval}.log`.
Tests `scripts/test_bindings27b.py`: source gap selection, reserved exclusion,
exact deterministic sampling quotas, invalid pool rejection and actual tiny
production optimizer with pooled/chunked backward. No results yet.

Implementation9549b31. Stdlib preparation audit stored in
[BINDINGS27B_AUDIT.json](BINDINGS27B_AUDIT.json); CPU production sampler/optimizer
test passed. Capture1273606active: full teacher state restore bit-exact, first
query argmax equal, logit max difference0.03125. Reused476trajectory Q/A and
all teacher K/V match exactly. Fresh304capture underway; no quality result.

Capture complete780×16,1690.169s (28m10s), all shard/index counts verified.
Full checkpoint writes dominate stalls, included in measured duration. Original
prefix hash260281d80bc9c370; calibration hash920bd8291aaef106. No quality result.
Fixed400step72-example/update compile next; no change to frozen sampler quotas.

Compile1292320active; eval wait wrapper1292585queued behind it. First layer
completed473.654s (7m54s), manifest verifies pools71/405/304with quotas24each.
Measured first-layer extrapolation~2h6m for16layers, not a guaranteed ETA.
No quality results. Original71exposure preserved, objective weight1/3not1.

Compile complete16/16layers,7593.1s (2h6m33s), manifest complete with all three
sampling quotas frozen. Evaluation1292585active, dev first. No quality result
yet; do not infer outcome from training-loss decline.

Dev complete: fresh original71control169/194, bindings176/194,caps1→0;
candidate informative80/89. Earlier control167/194 and coverage179/194 are
different invocations: runtime non-determinism affects borderline grades.
Do not attribute every cross-run difference to data. Final78/stress/12pending.
