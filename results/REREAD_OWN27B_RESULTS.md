# Direct compression of the combined reread state

Authorized2026-10-15 after user correction. **Complete; no jobs active.** The previous
cross-state experiment did not directly test the requested idea; do not describe
its regression as failure of direct combined-state compression.

## Final result

| Evaluation | Full context | Saved476seed | Warm refinement | Cross-state fit | Direct own-state fit |
|---|---:|---:|---:|---:|---:|
| Dev194 | 193 | 179 | 182 | 179 | **181** |
| Fixed78 | 76 | 73 | 74 | 73 | **75** |
| Stress197 | 197 | 173 | 175 | 178 | **177** |
| Strict diagnostic12 | 12 | 9 | 10 | 10 | **10** |
| Reserved6test subset | 6 | 4 | 5 | 5 | **5** |

All compressed final arms8192rows. Original fullcontext26033; uncompressed
combined state34225rows scored193/194dev (other suites not tested at that stage).
Direct own-state fit is the requested experiment; cross-state column is the
previous original-target experiment,not an interchangeable method.

- Own vswarm:dev5gains/6losses,fixed781/0,stress4/2,diagnostic0/0.
  Own vscross-state:dev7/5,fixed782/0,stress4/5,diagnostic0/0.
- Stress arguments120/135(vswarm117,cross119);selection57/62(vswarm58,cross59).
  Dev arguments121/132,selection60/62. No uniform advantage.
- Fixed78lookup28/28,style18/20,tools25/26,unrelated4/4. Recovers onboarding
  vswarm;recovers onboarding and WebFetch vscross. Remaining frozen failures:
  ADR answer startsYes(despite append-only qualification),migration explicitly
  saysreversible(frozen grader limitation),Copilot returns nonpreferred alternate
  tool. Keep scores unchanged,do not claim all failures are actual knowledge loss.
- Informative slices own dev82/89(vswarm85),fixed7844/45(vs43),stress91/107
  (vs91),diagnostic8/9(vs8). Caps own0/2/2/1respectively;warm1/2/2/0.
  Strict dev5/6,test5/6both. Diagnostic additional cap did not change strict score.

**Verdict:** own-target compression improves fixed78over both saved refinement
controls,but still loses12devcorrect vsuncompressed combined state193→181.
Stress177vswarm175is2more;dev181vs182is1less. No clear overall replacement or
proof of a hard capacity ceiling. This now directly tests combined-state
attention compression with its own targets,not final-answer CE preservation.
No longer training,budget change,newdata,promotion or additional run started.

## Measured cost/artifacts

New compiler2860.023s +new evaluations335.140s = **3195.163s(53m15s)** incremental.
Gate,capture,warm-control evaluations reused from previous experiment,not new
compute. Summary`total_s`8374.505includes those reused prerequisite/control costs;
use`incremental_s`for this run's additional cost. No recapture or control refit.
Same512MiBoccupiedattentionKV and151.5MiBFP32recurrentstate;retains advanced
recurrent values/logical52066. Physicalcache36864,no measuredprocessVRAMsaving.

Local [REREAD_OWN27B_SUMMARY.json](REREAD_OWN27B_SUMMARY.json) contains paired
scores,changes,hashes,timing. Raw outputs/manifest under prior XTXroot remain
alongside untouched old controls. Own manifestSHA256
`4d505869933165ddcc5b75a469165c6e3816143822b7427d8eb686fc8c9c7e56`.
Compile1488776/eval1489391finished. CPU checks pass;no testquestions used to fit
or select checkpoints. Saved controls are prior invocations,not fresh reruns;
runtime variability and historically inspected evaluation limit small gains.
Implementation7c91745,summarydf1644c,compilecheckpointd2aa674.

## Frozen protocol and chronological checkpoints

Use existing verified combined34225-row FP16prefix and476captured trajectories
at logical52066. Reconstruct attention targets from **combined-state prefix KV,
queries and live KV**; no `--clean-traj`/original-teacher target substitution.
Retain advanced recurrent state/logical52066 at evaluation. Original full-context
model is evaluation reference only. No new capture/data/budget/recipe sweep.

Only training target source changes vs saved cross-state arm: same seedcoverage476
8192KV,400updates/layer,24uniform examples/update,LR.001,seed0,chunk4,corrected
cosine1/projected/gated objective,frozen sink,BF16export. Same16layers. Existing
warm and cross-state controls retained,not rerun. Own-target compiler handles
34225prefix rows vs26033original targets,so equal sample work not equal FLOPs.
CPU regression explicitly checks target tensors equal direct combined-state
attention and differ from paired original targets. Preflight verifies all16
captured prefix tensors match saved combined state bit-exact before compile.

No checkpoint selection,dev fitting,LoRA,outputCE,three-way resume or promotion.
After final fit, frozen dev194/fixed78/stress197/strict12generation; same protocol
and advanced state as previous candidate. Compare saved warm teacher/none masks
and controls; historical tests are not pristine. Report caps,policy/skill,heldout
split and actual attentionKV/memory. Checkpoints per layer,progress50steps.

Artifact XTX `/mnt/data/artifacts/kvcompile/artifacts/agent/reread27b_v1/own/`;
outputs `{dev,agent78,stress197,diagnostic12}_own.json`. Earlier artifacts untouched.
Logs `/tmp/opencode/reread-own27b-{compile,eval}.log`.

Implementation7c91745. CPU direct-target regression passed. Preflight passed
476×16exact combined prefix tensor equality before fitting. Compile1488776active,
4/16layer checkpoint at713.5s; ~47m34s first-four-layer extrapolation,not guaranteed.
No generation quality result yet. No recapture needed; old controls untouched.

Own-target compile complete16/16,2860.0s (47m40s),all layers exported8192rows.
No quality/checkpoint selection. Frozen generation evaluation next.
