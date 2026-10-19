# 27B mixed exact/compressed prefix

2026-10-14: **completed; no active job. Fixed-budget mixed prefix is not an
overall improvement.** User authorized returning to existing27B and testing
partial compression. Separate from paused
4B compiler/CARTRIDGES/AM comparison. Branch `experiment/27b-mixed-prefix`.

## Frozen experiment

- Existing Qwen 27B EXL3 3.5bpw runtime on XTX, no model/environment changes.
- Original `prompts/agent_resident.txt` unchanged. Keep leading system policy,
  repo rules, MCP access rules and all skill routing through the boundary before
  `# Connected MCP tools` exact in full-attention KV. Remaining catalog and
  end-of-system delimiter represented by synthetic KV. No duplicated rows.
- Total **8192 rows per full-attention layer**, including exact rows; compression
  slots are 8192 minus measured exact-token count. Original RoPE positions and
  logical continuation at original full prefix length. Full teacher recurrent
  states retained, as in original compiler. This is mixed *KV*, not prompt
  reordering or concatenating separately-prefilled text. Exact rows remain
  teacher FP16 on export/install; synthetic tail BF16-rounded then stored FP16
  (same rounding as baseline BF16 artifacts installed into FP16 runtime cache).
- Same original 71 calibration questions/answers, unchanged policy/skill/tool
  distribution. No repaired512 addition or LoRA; isolate the structural choice.
  Source files/derived calibration hashes recorded. Source tool facts remain
  available in the teacher; dev/test questions do not become fitting queries.
- Same projected, gated compiler objective:400steps/layer, LR0.001, cosine
  coefficient1, seed0,24examples/update, chunk4. Exact leading rows zero-gradient;
  no optimizer momentum there. Tail initialization samples only tool rows.
- Recompile compressed-only8192 control and mixed8192 with the same current
  corrected projected-cosine normalization (`79eedbf`); original projected8192
  predates this fix and remains a historical reference, not the matched control.
  Recapture removed disposable teacher/trajectory state from unchanged source;
  preserve original artifact. No objective sweep: both arms use the corrected
  projected/gated objective, not the historical normalization defect.
- Use generated dev suite with four known dev/heldout exact duplicates excluded
  from dev. Structural choice frozen before scoring. No schema-group search,
  test-driven restoration or checkpoint sweep in this experiment. Score fixed78
  and existing197 stress probes only after dev; these are historically inspected
  regressions, not pristine heldout. Report paired changes, by-kind scores,
  EOS/caps, same teacher/no-prefix informative mask and actual retained bytes.
- CPU test: production optimizer keeps exact rows bit-identical, updates only
  tail, enforces total budget and causal live-token mask. GPU: full-prefix state
  restore and first-query greedy agreement; mixed export exact rows verified
  against teacher before generation. Stops on failed parity, no recipe changes.
- Capture checkpoints every5questions; compiler checkpoints each layer with
  resume. Detached jobs and UTC progress. Evaluation per-question checkpoints.

Artifact root: `/mnt/data/artifacts/kvcompile/artifacts/agent/mixed27b_v1/`.
Logs: `/tmp/opencode/mixed27b-*.log`. No transfer/deploy or 4B comparison resume.

## Final generation result

| Suite | Compressed-only control | Mixed exact + compressed | Informative control → mixed | Paired gains / losses | Cap control → mixed |
|---|---:|---:|---:|---:|---:|
| Dev194 | 167/194 | 174/194 | 69/89 → 79/89 | 16 / 9 | 1 → 3 |
| Fixed78 | 75/78 | 75/78 | 44/45 → 45/45 | 2 / 2 | 1 → 1 |
| Stress197 | **165/197** | **159/197** | 80/107 → 78/107 | 16 / 22 | 1 → 7 |

One fresh teacher/no-prefix informative mask per suite, identical across arms.
Teacher193/194,76/78,197/197; no-prefix104/194,32/78,90/197. Greedy, full EOS
set,64-token cap, same runtime/source prompt. Per-question outputs saved; zero
evaluation interruptions/exceptions. Neither eval questions nor answers added
to calibration. No selection or recipe modification after dev.

Fixed78 by-kind (control→mixed): lookup27→25/28, style18→20/20, tools26→26/26,
unrelated4→4/4. Gains: ADR append-only and reversible migration answers.
Losses: fork_repository owner argument and create_pull_request source branch.
Stress tool selection47→44/62; argument binding118→115/135. Dev tool selection
51→55/62; argument binding116→119/132. Gains on dev do not demonstrate transfer
to the disjoint-tool stress partition. Inspected test history still prevents a
pristine heldout claim. Full masks differ from historical reports due one
no-prefix answer and runtime variability; compare only the matched fresh mask.

**Verdict:** exact leading rules recovered two policy responses, but allocating
2819of8192rows to them reduced synthetic catalog capacity8192→5373 and did not
improve overall quality. Stress recall and termination worsened. Exact KV rows
do not ensure perfect behavior when later layers receive changed residuals.
Keep compressed-only as reference; no deploy, extra training, schema restoration
or new experiment started. This tests one fixed-budget partition, not every
partial-compression strategy. Increasing total budget to keep8192synthetic rows
plus2819exact rows would be a different, untested memory tradeoff.

## Budget, time and evidence

Both arms:8192rows ×16full-attention layers, KV536870912bytes=512MiB. Mixed
uses2819exact FP16 +5373synthetic BF16-rounded FP16 rows. Control BF16 artifact
installs in FP16 runtime KV, so effective resident KV bytes match; on-disk dtype
names alone are not the comparison. Same recurrent-state representation in both
arms,158859264bytes in captured FP32 state. No recurrent-state compression.
Full teacher attention KV1706098688bytes (offset metadata excluded), so attention
KV alone is3.178× smaller; including unchanged recurrent state, about2.681×.
Paged runtime capacity remains32768 in this harness: occupied-row accounting,
**not a measured reduction of allocated process VRAM**.

Capture183.520s; corrected control2130.774s; mixed2130.977s; evaluations
111.642+552.273+74.832+256.766+111.596+541.605s = **6093.985s (~1h41m34s)**
recorded total, excluding3.6s pilot, CPU tests, launch gaps and analysis.
No capture/training/evaluation process still running.

Artifact root `/mnt/data/artifacts/kvcompile/artifacts/agent/mixed27b_v1/`:
`teacher/`, `traj/`, `pilot/`, `control/`, `compiled/`, filtered `probes_dev.json`,
`{dev,agent78,stress197}_{baseline,mixed}.json`, `summary.json`.
Local machine-readable result [MIXED27B_SUMMARY.json](MIXED27B_SUMMARY.json).
Hashes for manifests included there. Source prompt SHA256
`0ba38930d86e54e73fc6d63ec1553be3d7e2d1b39f60091ea2e670fb318e20ef`, identical
locally/XTX; tokenized block identity260281d80bc9c370. Original artifacts intact.
Implementationc2bc78a, evaluationf460e5c, matched-controlbddf0c1,
export/summary5c84ca4. No remote Git push or integration.

## Earlier verified checkpoints (chronological)

Implementation `c2bc78a`. CPU production optimizer/export/resume checks pass:
exact leading rows frozen and preserved FP16, synthetic tail updated, causal
live mask correct, total budget fixed, completed layer skipped on resume.
Capture PID772677 finished71/71 across16attention layers in183.5s.
Measured n_sys26033, exact2819, synthetic5373,
catalog tail23214. Teacher-state restore bit-exact; greedy first-token agreement;
logit max difference0.03223, consistent with recorded runtime nondeterminism.
No compilation or generation quality result yet. Original71 input unchanged.
Capture prompt hash260281d80bc9c370 matches original; normalized input hash
ed9c68e02ee22d73. GPU two-step projected compile pilot passed in3.6s: exported
8192rows,2819exact FP16 verified against teacher, all finite. Fixed400step
compressed-only and mixed controls started: wrapper777510, control Python777514.
First two control layers each132.6s; observed rate suggests about35min per
16-layer arm, not a guaranteed total ETA. Evaluation remains pending. Dev198
minus4duplicates=194, fixed78 and stress197 unchanged. No quality result yet.

Compressed-only corrected control finished16/16layers in2130.8s (35m31s),
manifest complete. Mixed arm now runs as Python777510; separate evaluation
wait wrapper785384 will start only after completed manifests for both arms.
No generation result yet. Checkpointed artifact paths and source prompt intact.

Mixed arm completed16/16layers in2131.0s (35m31s). Frozen leading rows checked
against captured teacher before export. Both manifests complete. Combined
control+mixed compile4261.8s; capture183.5s separately. Evaluation wrapper785384
advancing to dev first; no generation results at this checkpoint.

Dev complete: control167/194, mixed174/194; same teacher/no-prefix informative
mask89, control69/89, mixed79/89. Paired16gains/9losses. Cap1→3. Teacher193/194,
none104/194. Dev control112.4s and mixed+teacher+none552.0s approximately (exact
durations in JSON). Promising dev gain with termination tradeoff; no partition/
recipe change or checkpoint selection. Fixed78/stress197 evaluation proceeding.

Fixed78 complete: control75/78, mixed75/78; informative44/45→45/45 with one
fixed teacher/no-prefix mask. Paired2gains/2losses, caps1both. This suite shows
no total accuracy gain. Stress197 evaluation still active; no final verdict yet.
