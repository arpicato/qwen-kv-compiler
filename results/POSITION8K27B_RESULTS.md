# Position-aware calibration at 8,192 KV rows

Authorized 2026-10-16. **Complete: small gains over purpose8k, not production-ready.**
XTX artifact: `/mnt/data/artifacts/kvcompile/artifacts/agent/position8k27b_v1/`.
Log: `/tmp/opencode/position8k27b.log`.

## Results

| Evaluation | Purpose8k | Position4k | Position8k | Full context |
|---|---:|---:|---:|---:|
| Development | 187/194 | 179/194 | **189/194** | 193/194 |
| Fixed probes | 75/78 | 71/78 | **76/78** | 76/78 |
| Stress total | 187/197 | 163/197 | **188/197** | 197/197 |
| Stress tool selection | 56/62 | 49/62 | **57/62** | 62/62 |
| Stress arguments | 131/135 | 114/135 | **131/135** | 135/135 |
| Strict diagnostic | 9/12 | 7/12 | **10/12** | 12/12 |
| Reserved test | 5/6 | 2/6 | **5/6** | 6/6 |

Versus purpose8k paired gains/losses:dev3/1,fixed78 1/0,stress2/1,strict12 1/0.
Devselection58→60/62;arguments129/132unchanged. Fixed78 restores OpenCode skill
answer;lookup28/28,selection26/26,unrelated4/4,style18/20. **Style18/20alsoin
purpose8k**, not a new selector regression;position4k was20/20. The new artifact
ties full-context aggregate76/78 but does not match its per-question behavior or
prove parity. Reservedtest5/6unchanged;strictdev4→5/6. Onecap,strictdev;nonein
dev194/fixed78/stress197. Stressstillmisses9/197(5selection+4arguments).

Verdict: at8k this fixed-row selector yields small improvements across inspected
suite totals without new paired fixed78losses, but argumentstressunchanged and
reservedtestunchanged. Singlefit/seed,smallpairedcounts,inspected/sharedbinding
probes: no robust generalization or production-readiness claim. No promotion or
additional run. At4k selector was mixed; do not assume this modest8kgaintransfers
to4korprovesahardcapacitylimit. Sourceanswer/schema-derivedcalibration and local
attentionloss remain distinct from answerCE.

Againstposition4kpairedgains/losses:dev13/3,fixed78 7/2,stress26/1,strict12 5/2.
This costs2×occupiedattentionKV(256→512MiB),samefullrecurrentstate151.5MiB.
Onecommonfreshinformativemask:purpose8k→position8kdev85→86/89,fixed43→44/45,
stress98→99/107,strict7→8/9;position4k79/89,41/45,79/107,4/9respectively.
Freshteacher193/194,76/78,197/197,12/12;none104/194,32/78,90/197,3/12.

Newcompile7528.910s+eval1737.271s=**9266.181s(2h34m26s)**. Actualwrapper9354s
includesinterprocessload/startupgaps. Norecapture;priorcapture5769.057s/equality
audit51.925sreused,nothiddeninnewruntime. OccupiedKV536870912bytesverifiedin
16exportedlayers;manifestSHA256
`1eb45b054f1a450ba2b68cce919870ee5c0662c372a6c647e96de4f61a13c523`.

[POSITION8K27B_SUMMARY.json](POSITION8K27B_SUMMARY.json)generic`expanded`isnew8k;
`control`isfreshoriginal71control,notpurpose8k.
[POSITION8K27B_DETAIL.json](POSITION8K27B_DETAIL.json)retainsactualpurpose8k/position4k
pairedchanges,changedgenerations,commonscoremasks,hashesanddurations. All8complete
per-questionevalJSONsstayonXTX. Data/sampling/positionsbyte-equalposition4k;
sameverifiedcapturelink. Compilerconfigchecksagainstbothcomparatorspassed.
Alljobsfinished2026-10-16T02:44:27Z,originalartifactsintact,nofurtherGPUwork.

## Frozen protocol

Same position-aware780 captures, Q/A, per-example query counts and sampling plan
as position4k27b_v1. Reuse completed capture/equality audit; no fresh model capture.
Only KV rows change4096→8192; standard full-teacher initialization, no4k warmstart.
400updates/layer,16layers,24original+24existing+24binding examples/update,seed0,
LR0.001,chunk4,frozen sink,corrected projected/gated cosine objective,BF16 export.
Same original71 and purpose304 query rows, changed404/405older tool examples.
No CE, new training data, backend changes, reread, or uneven layer allocation.

8192rows occupy512MiB attentionKV; full recurrent state remains151.5MiB,logical
continuation26033. 3.18× attention-row compression vs26033full rows, not total-memory
or measured process-VRAM compression. Harness paged capacity remains32768.

Compare final400-update artifact with saved purpose8k (187/194dev,75/78fixed,
187/197stress:56selection/131arguments,9/12strict,test5/6) and position4k
(179/194,71/78,163/197:49selection/114arguments,7/12strict,test2/6).
Former isolates selector at8k; latter measures budget under unchanged recipe,
not a hard-capacity-limit test. Both comparators are saved generations, not new
repeated fits. Original71control/full/none evaluated freshly as in previous run.

Frozen eval:dev194,fixed78,stress197,strict12(dev6/test6);same greedy no-thinking,
cap64,EOSset and grading. Retain per-question outputs, paired gains/losses and
common fresh informative masks. No test-fitting, checkpoint selection, training
extension, automatic promotion, or claim of fresh generalization. Original
compiler/CARTRIDGES/AM comparison remains paused.

## Execution and verification

`scripts/run_position8k27b.sh` validates complete capture/audit identities, links
shared inputs without overwriting existing artifacts, and uses existing resumable
compile/eval pipeline. Layer checkpoints and per-question eval resume unchanged.
Check final compiler configuration against position4k (onlyslots/path/results
expected different), and purpose8k (onlytrajectory/path/results expected different).
Occupied tensors must match manifest8192rows and536870912bytes.

Implementation checks: shell syntax, existing selector/alignment/memory tests,
remote preparation hash/identity checks. Record PID, start time, progress and
measured durations below before claiming results. No competing GPU jobs observed
at setup;252GiB disk free,6.1GiB hostRAM available. NoEXL3/environment modifications.

Implementation96e6685. Remote preparation passed complete780capture/audit and
question/position-plan hash checks. Started2026-10-16T00:08:33Z;detachedwrapper
1511684,compilerpython1511689. Layer3step25verifiedprogress(8192slots,400steps,
72examples/update);noerror. Capturecostreused,notincurredagain. Pipeline schedules
frozen eval after compilation;checksummed sharedinputs/originalreferences untouched.

Compilecompleted2026-10-16T02:14:08Z,7528.910s,16/16layers. Manifestconfiguration
checkedagainstposition4k(onlyslots,trajectorypath,layerresults,timingdiffer)and
purpose8k(onlytrajectorypath,layerresults,timingdiffer). Evaluationwrapper1512667
started;allfourfrozensuitesscheduled.Noextraoptimizationorcheckpointselection.
