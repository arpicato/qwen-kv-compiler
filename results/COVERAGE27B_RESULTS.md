# 27B broader calibration coverage

User authorized2026-10-14; reviewed2026-10-15. **Complete; no active job.**
Broader calibration improves tool selection at the same8192row budget, but not
all argument retrieval or policy/skill retention. Separate from partial
compression and paused4B three-way work. No extra run or deployment authorized.

## Final generation result

| Suite | Original71 control | Expanded476 | Full context | Informative control → expanded | Paired gains / losses | Caps control → expanded |
|---|---:|---:|---:|---:|---:|---:|
| Dev194 | 167/194 | **179/194** | 193/194 | 69/89 → 83/89 | 16 / 4 | 1 → 1 |
| Fixed78 | **75/78** | 73/78 | 76/78 | 44/45 → 42/45 | 1 / 3 | 1 → 3 |
| Stress197 | 165/197 | **173/197** | 197/197 | 80/107 → 89/107 | 13 / 5 | 1 → 1 |
| Strict diagnostic12 | 7/12 | **9/12** | 12/12 | 5/9 → 7/9 | 3 / 1 | 0 → 1 |

All frozen settings preserved; one fresh teacher/no-prefix informative mask
per suite, shared across baseline and candidate. No-prefix104/194,32/78,
90/197,3/12. All evaluations complete, no exceptions/interruption or evaluation-
selected checkpoint.12diagnostic is small and strict name-set graded, not
evidence for whole-agent reliability. Its separated6dev score4→5/6; reserved
6test3→4/6 (2gains/1loss). Original71contains none of its six tool names or
their source first-description queries; added405absence was established by
repaired512audit. These string checks do not certify semantic independence.

### What improved, what regressed

- Stress **tool selection47→57/62**. Argument lookup **118→116/135**. Therefore
  total173/197 is mainly better name selection, not solved argument binding.
- Dev tool selection51→57/62, argument lookup116→122/132.
- Fixed78 lookup27→27/28, style18→17/20, tool selection26→25/26, unrelated4/4
  both. Gain:create_issue required argument. Losses:Python package manager,
  incident-response skill selection, normal-answer length. Stored original71
  preservation did not preserve its previous sampling frequency.
- Historical shared20slice19→20/20; other58slice56→53/58. This split refers to
  the previously reported512tool overlap; it is not a new semantic holdout.
- Stress selection targets present in added selection supervision42→49/51;
  targets absent5→8/11. Some gains occur outside added target tools, but only11
  cases, and original71may cover some: not a pure untrained-transfer estimate.
- Stress argument targets whose tool has added required-argument supervision
  73→75/79; other tools45→41/56. Direct required-field bindings30→31/31;
  remaining104argument cases88→85/104. Dataset adds required-field questions,
  not every distinctive optional argument; these results do not establish the
  effect of comprehensive argument supervision.
- Corresponding dev required-field bindings27→31/31; remaining101cases89→91.
  Per-question gains/losses and by-kind scores:
  [COVERAGE27B_SUMMARY.json](COVERAGE27B_SUMMARY.json). Split/coverage counts and
  exact durations: [COVERAGE27B_DETAIL.json](COVERAGE27B_DETAIL.json).

**Verdict:** a real observed tool-selection gain, unlike the fixed-budget
mixed-prefix run. Not a uniformly better replacement: full context remains
197/197, arguments and three old policy/skill answers still regress. This
supports broader selection-query coverage as useful, without proving causal
attribution to coverage alone (answer distributions and sampling changed too).
Keep both artifacts; do not silently promote expanded476over original71.
No longer run, resampling, optional-argument synthesis, LoRA or hybrid started.

## Budget, runtime and artifacts

Same8192occupied attention rows/layer ×16layers:536870912bytes (512MiB),
unchanged teacher recurrent state. Full prompt26033tokens; no total-memory
increase. Harness still allocates32768paged capacity, so this is occupied-row
retention, not measured process-VRAM savings.

Capture1356.746s (22m37s); compiler2478.556s (41m19s); paired evaluations plus
fresh teacher/no-prefix controls1741.048s (29m1s). **Total5576.350s (~1h32m56s)**,
excluding setup/analysis and historical original71control compilation. Capture
time includes repeated checkpoint writes; no speculative runtime projection.

XTX root `/mnt/data/artifacts/kvcompile/artifacts/agent/coverage27b_v1/`:
`questions.json`, `heldout_cases.json`, `diagnostic12.json`, `traj/`, `compiled/`,
`control` read-only-reference symlink to `../mixed27b_v1/control`,
`{dev,agent78,stress197,diagnostic12}_{baseline,candidate}.json`, `summary.json`.
Teacher state reused from `mixed27b_v1/teacher`; old artifacts untouched.
Provenance/tool coverage: [COVERAGE27B_AUDIT.json](COVERAGE27B_AUDIT.json).
Expanded manifest SHA256
`593649b6d7d565ddb1e2acecfe8ecfd3b6cd0a934c3709671933338a17ed00a2`.
Capture927194, compile942769, evaluation943380all finished. No remote push/merge.
Implementationaa53836; capture05bf8ff; audit5d4fa87; compile9c2c617;
dev checkpoint4bd2dff.

## Frozen protocol and earlier checkpoints

Frozen model/prompt/runtime: existing27B EXL33.5bpw, unchanged26033token manual,
same full recurrent teacher state, all8192attention rows synthetic except sink.
No exact-policy reservation, LoRA,512replacement, new synthesis or143data.

Calibration: original71 unchanged +all405train conversations from repaired512
(SHA2563ca7fe9e13b05b5483ca2dc70f6d2ee40a0bda6a235d8183ee7b78fc72f43d80).
Preserve duplicates, no val107 fitting. Copy question/answer text only; retokenize
and capture fresh27B attention inputs/targets. Repaired required-field answers
expand argument coverage but do not supervise every optional argument binding.
Exact normalized dev/197/78/val107/12question overlap checked before capture;
same-binding overlap counted separately, not a pristine generalization claim.

Fixed projected/gated corrected objective, seed0,400steps/layer, LR0.001,
24uniform examples/update, chunk4, cosine1, frozen sink, BF16 export. Baseline
fresh corrected original71 control from `mixed27b_v1/control/` retained unchanged.
Expected exposures/item change~135(original control)→~20(new476) under same
400×24budget. This tests broader calibration at fixed optimization budget;
retaining original rows does not retain their original sampling frequency.
No extended training or recipe sweep automatically after results.

Capture checkpoints5questions; compiler checkpoint each layer/resume. Capture
fresh expanded questions only, reuse original71captured trajectories and teacher
state after validating source identities; merge indices without stale4Btargets.
Frozen gen: greedy/no-thinking/full EOS/cap64; per-question checkpoints. Dev194
(4known dev/test duplicate questions excluded), unchanged78and197historically
inspected regression suites; frozen12tool diagnostic (6dev/6test) additionally.
No checkpoint or schema selection from evaluation. Same fresh teacher/no-prefix
informative mask for paired baseline/candidate. Report by-kind, gains/losses,
shared tool/binding slices, caps, durations, occupied KV bytes (not allocatedVRAM).

Artifact root `/mnt/data/artifacts/kvcompile/artifacts/agent/coverage27b_v1/`.
Scripts: `prepare_coverage27b.py`, `capture_agent_exl3.py`, `compile_torch_v2.py`.
Logs `/tmp/opencode/coverage27b-*.log`. No original artifact overwritten.

Preparation verified:476rows, added298unique questions;137argument rows and
268selection rows. Added coverage108selection tools,71required-argument tools,
120/131union. No normalized exact question overlap with dev198/stress197/78/
val107/12diagnostic. Same-binding overlap remains, and optional-argument coverage
is not established. Stdlib regression preserves all original71and405added rows,
rejects question leakage/missing required fields, omits4Btokens/targets.

Implementationaa53836. Capture PID927194 active: full teacher restore bit-exact,
first query argmax equal, logit max difference0.015625. Original71trajectories
reused only after source Q/A and every teacher KV tensor verified identical.
Fresh405capture underway; per-five-question checkpoints. No quality result.

Capture complete476×16trajectories,1356.746s (22m37s), index and every shard
count verified. Saved partials every5rows; heavy checkpoint writes included in
duration. Prefix prompt hash260281d80bc9c370 unchanged, calibration hash
a9948d1f2e60968a. No quality result; fixed400step compile next.

Compile Python942769 started with frozen recipe. Preparation provenance and
tool lists saved in [COVERAGE27B_AUDIT.json](COVERAGE27B_AUDIT.json). None of six
prospective diagnostic tools appears by qualified/bare name in original71Q/A;
absence from added405was established in repaired512audit. Description overlap
with original71not yet separately certified; do not claim pristine unseen tools.

Fixed400step compile complete16/16layers in2478.6s (~41m19s), no recipe/data
change. Evaluation wait wrapper943380 will run baseline/candidate paired suite
evaluations and strict12diagnostic. No generation quality result at this checkpoint.

Dev completed:control167→expanded179/194, paired16gains/4losses; common
informative89mask69→83/89; caps1both. Teacher193/194,no-prefix104/194.
Fixed78/stress197/12diagnostic pending; no recipe/partition selection from dev.
