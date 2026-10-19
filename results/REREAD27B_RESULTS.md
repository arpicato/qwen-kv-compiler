# Compressed KV + original prompt rereading

Authorized2026-10-15. **Complete; no active jobs.** Reread recompression improves
stress by3over matched warm refinement, but loses3dev and1fixed78; not a uniform
replacement. Original artifacts intact; no promotion/new run.

## Final8192-row generation

| Suite | Saved476seed | Matched warm refinement | Reread recompression | Full context |
|---|---:|---:|---:|---:|
| Dev194 | 179 | **182** | 179 | 193 |
| Fixed78 | 73 | **74** | 73 | 76 |
| Stress197 | 173 | 175 | **178** | 197 |
| Strict diagnostic12 | 9 | **10** | **10** | 12 |
| Reserved6test (subset) | 4 | **5** | **5** | 6 |

Saved seed is earlier generation invocation (except same179dev gate result),
not a fresh arm in final evaluation. Full/none masks freshly evaluated with warm
control and shared for both arms. Historically inspected regressions and tiny
diagnostic,not pristine heldout. No checkpoint selection by these scores.

- Reread vswarm:dev1gain/4losses,fixed780/1,stress4/1,strict120/0.
  Stress selection58→59/62,args117→119/135; devselection59→58/62,args123→121/132.
  Still19stress failures vsfull context.
- Informative slices:warm→reread dev85→84/89,fixed7843→42/45,stress91→93/107,
  diagnostic8→8/9. Caps:dev1→1,fixed782→1,stress2→1,diagnostic0→1.
- Fixed78style18/20andtool24/26both; lookup28→27/28. Additional reread loss is
  WebFetch rule (`Web tool` instead). Both fail onboarding skill,ADR answer,
  migration answer,and old Copilot probe. Some source/grader limitations remain:
  migration answers explicitly say reversible, old Copilot probe expects a
  nonpreferred tool. Scores frozen,not silently repaired. Historicalshared20
  both19/20;other58warm55vsreread54.
- The intermediate193/194score drops to179after recompression. This shows the
  reread state is usable before fitting,not that its gain survives fixed budget.
  The3stress gains are counterbalanced elsewhere; no robust overall advantage.

**Verdict:** rereading itself preserved near-full-context dev accuracy, but this
original-target paired recompression recipe did not retain that advantage at
8192rows. Ordinary additional fitting also helps; do not credit all gains over
the oldseed to rereading. Candidate changes queries,gate,recurrentstate,positions
and paired objective together; no isolated causal claim or capacity ceiling.
Do not promote either artifact over the original references automatically.

## Final cost/artifacts

Gate517.038s,capture813.517s,warmcompile2502.439s,rereadcompile2585.222s,
eval1687.382s; **8105.598s (2h15m6s)** recorded total. Excludes coding/analysis
and historical seed training. Each final arm occupies512MiB attentionKV
(8192rows/layer×16); recurrent states151.5MiB FP32each,values differ. Intermediate
attentionKV2139.0625MiB(34225rows),original1627.0625MiB(26033rows). Physical cache
allocated36864capacity for final evaluations,so no measured process-VRAM saving.

XTXroot `/mnt/data/artifacts/kvcompile/artifacts/agent/reread27b_v1/` contains
`gate.json`,`state.{json,safetensors}`,`traj/`,`warm/`,`reread/`,eight per-question
`{dev,agent78,stress197,diagnostic12}_{warm,reread}.json`,and`summary.json`.
Local [REREAD27B_SUMMARY.json](REREAD27B_SUMMARY.json) records matched metrics,
paired question changes,hashes,times. Logs `/tmp/opencode/reread27b-{gate,capture,compile,eval}.log`.
All wrapper/childjobs1419875,1427803/1427807,1437286,1483847finished.
Implementationdc06162/06cb382,summary03f30fd,capture48d7329,fits e92c6a3.

## Chronological protocol/checkpoints

## Stage1 gate

Fresh dev: teacher193/194,seed179/194,reread193/194; caps0/1/0.
Teacher-correct193slice:seed179,reread192. Paired seed→reread15gains/1loss.
Gate passes. Not identical to teacher: reread fixes one teacher-graded failure
and loses another teacher-correct answer. Frozen grader/source limitations
remain unchanged. Raw generations [REREAD27B_GATE.json](REREAD27B_GATE.json).
Total517.038s (8m37s),including reread state preparation and verification.
Physical34225/logical52066verified; saved state restored bit-exact,first-query
argmax identical,logit maxdiff0.0. This is an uncompressed intermediate result,
not an8192row gain. It retains more attention KV than original26033context.
Implementationdc06162;job1419875finished. No competing GPU job.

## Stage2 frozen continuation

Recompress to8192via existing paired attention-loss path: capture476reread
query/gate/live-KV trajectories, same original476Q/A/token-row selection and
original clean attention targets. Logical query/key offsets shift+26033 but
pair by identical token rows,not absolute position. Original targets are never
replaced by reread outputs. Both fits start from identical coverage476KV,
400updates,24uniform examples/update,LR.001,seed0,chunk4,cosine1,projected/gated,
frozen sink,BF16export. Control is ordinary clean-trajectory warm-start fit;
candidate uses paired reread inputs/original targets. Gate factors and queries
change together; not pure data/position effect. Same optimizer sample work,
not exactly equal FLOPs/walltime (paired target construction differs).

Fresh candidate capture checkpoint25items,progress5items; compiler resume per
layer (each historically<15min). No checkpoint selection. Evaluate all194dev,
fixed78,stress197and strict12diagnostic only after both final fits. Same greedy
no-thinking/fullEOS/cap64. Reread candidate retains advanced recurrent state,
logical52066with physical8192. Warm control retains original recurrent state,
logical26033/physical8192. Original full-context reference retained from gate/
fresh control outputs. Report policy/skill regression separately. No test fits,
no further run or promotion authorized by a positive dev score alone.

Stage2 implementation06cb382; shifted-position paired-loss CPU test passes
(identical targets/masks for a pure offset shift,finite nonzero KV gradients).
Capture child1427807(wrapper1427803)active; checkpoint25items. Compile/eval not
yet launched. First220/476captured with original inputs; final integrity check
must verify all476×16row counts and exact+26033logical offsets before fitting.

Capture complete476items,813.517s (13m34s),physical34225/logical52066.
Per-layer final integrity assertion is the compile launcher's fail-fast gate;
matched warm/reread fits next. No candidate generation result at8192rows yet.

All476×16paired row/shape/offset checks passed before fitting. Warm-start
control complete16/16,2502.439s (41m42s). Reread fit active7/16checkpoint,
same400×24recipe. Wrapper1437286,bash1437290; no final generation result yet.

Both fits complete16/16. Reread2585.2s (~43m5s),warm2502.439s; combined matched
fits~1h24m48s. No generation-based checkpoint selection. Evaluation next.

Partial final evaluation: dev warm182/194vsreread179,caps1both;fixed78warm74vs
reread73,caps2vs1. The193/194intermediate benefit has not survived8192row
recompression on dev. Stress/strict12pending; evalwrapper1483847active. Do not
tune recipe or rerun checkpoints in response to these scores.

Stage1: install coverage4768192-row compressed cache plus original full recurrent
state, at logical26033; actually process the unchanged original26033-token
system block again. No separately-prefilled concatenation, no RoPE reset.
Final physical34225rows,logical52066; recurrent state advances through reread.
Runtime max_seq_len65536,physical cache capacity36864. Same greedy no-thinking,
full EOS set,cap64. FP16 occupied prefix saved, unchanged first8192rows verified,
state roundtrip bit-exact and first-query argmax parity required before scoring.

Frozen gate: compare fresh full teacher,seed476,and reread on all194existing dev
questions. Proceed only if reread total correct AND teacher-correct-slice score
are >=seed,with no additional cap hits. No tuning or repeat-until-pass. No
fixed78/stress197/reserved tests at gate. Dev historically inspected,not pristine.
Changing context length/cache allocation may change borderline scores; retain
paired outputs. Same original full-context teacher remains reference, not
unverified doubled-context answers.

If gate fails, stop before capture/recompression. If passes, freeze stage2
protocol before next long run: original476training inputs only,8192final rows,
400updates,24examples/update,matched-work warm-start control from same seed,
same corrected projected/gated objective. Recompression uses reread state/
queries with original full-context teacher attention targets; original teacher
and warm-start control keep original recurrent states/positions. Reread arm
keeps advanced recurrent state/logical52066; report this as a compound
intervention,not an isolated attention-KV effect. No dev-question fitting,
output-supervised KV,LoRA,or three-way comparison resume. No automatic promotion.

Root `/mnt/data/artifacts/kvcompile/artifacts/agent/reread27b_v1/`.
Stage1 script `scripts/reread_agent27b.py`, CPU check
`scripts/test_reread_agent27b.py`; checkpoint after every dev question.
Log `/tmp/opencode/reread27b-gate.log`. Stage1 seed chosen from prior dev result,
so this is exploratory development,not a prospective generalization claim.
