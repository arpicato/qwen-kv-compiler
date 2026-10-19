# Publication-source reproduction

Authorized2026-10-17; latest steering: complete release checks BEFORE starting
the expensive rerun. **Complete: all19phases finished; tool/task totals reproduced,
4kbehavior differs by one case.**

Original code MIT-0,third-party notices retained. Tracked exact joint812prompt/
Q/A/sampling/78/197/24/40cases plus continuation64/positions;new standalone
`scripts/reproduce.py` reads no historical artifact directory. Model/runtime
explicit external pinned dependencies. Unchanged shared EXL3environment read/run
only. Source exported from committed tracked files,output separate under
`/mnt/data/artifacts/kvcompile/artifacts/agent/reproduction27b_v1/`.

Reproduce frozen recipe,not new selector/recipe:4096/8192teacherinit400updates,
48catalog+24policy,LR.001,seed0,projected/gated cosine/frozen sink. Then negative
continuation80updatesfromnew4k,.00025LR,matchedcontrol/candidate. Exact old inputs,
new captures/projections/teacher/KV. No benchmark-basedselection/promotion.

Gate before launch: all CPU tests,source archive independentofGit,trackedinput
hashes,command plan,model/runtime acquisition identities,small publicDockerimage
parity on saved patches,release signature scan. Logs/PIDs/commit to be recorded.
Fullenvironmentinstallationnotclaimed;runtime unchanged. No public upload/push.

## Release gate passed

Candidate code `cee55a4` (MIT-0/input/runner checkpoint590f7b6). Exported solely
via `git archive` to XTX `/mnt/data/artifacts/kvcompile/releases/candidate-v1/`,
with no `.git` or untracked project files. All15testfiles passed there, including
realDockerboundarychecks for40authoredcontinuationpatches;noGPUfit used for
preflight. Earlier first archive hit an overbroad mount-path assertion in the test
only;fixed before running any capture,allchecks now pass from actual release path.

Public pinned-basePython3.12.3Dockerimage `kvcompile-checks:repro` built successfully;
all72historical refactor checks match the original privateimage across6arms.
Project signature scan found no privatekey/HF/GitHub/AWScredential signatures
in379checkedfiles;not a certification of entire Git history. No public upload.
Weightidentity will be fully SHA256verified by runner beforecapture;runtimecommit/
criticalversions/cleantrackedruntime likewise enforced. Source+inputs `RELEASE.json`
is immutable for resume. No historical artifacts read by the19-phase runner.
Log `/tmp/opencode/release-preflight.log` locally retains fullcheckoutput.

## Launch checkpoint

Started2026-10-17T07:26:46Z after all release checks. Detachedwrapper1590814,
orchestrator1590815,capture1590855. Log`/tmp/opencode/reproduction27b.log`.
Source archive `cee55a4` atcandidate-v1, no runtimefile edits while running.
Both15.3GBmodelweightshards fullySHA256verified;metadata/runtimecommit/package
checks passed. Runtime remains shared/read-only;not a fresh environment install.
Fresh teacher26341prefix roundtrip bit-exact states and equalargmax,maxlogitdiff
.015625. Capture35/812progress verified;no errors. Teacher/KV/capture allnew,
nooldseed/reusedartifact. No secondGPUjob or promotion.

Fresh812capture finished594s(meta includesmodel/prefixcheck/capture/export),all16
layers exported;wrapper capture phase612.690s includesmodel load (hashing accounted
outside phase duration). Export
boundedwriter43.4s. Projection export1591497completedall16;newweights,notoldoproj.
4kcompiler1591938started07:39:11Z,layer3step125progress verified,recipe4096/
400/.001/72,seed0,freeze/gate/projectedobjective. Bothmodelweightshashesmatch.
Fastercapturethanold6858s is consistent withboundedwriterbut notanisolatedtiming
benchmark;do not change historical duration or claim fixedspeedup.

08:42Zmonitorcheckpoint:4k9/16layerscompleted,layer39inprogress,~397s/layer,
noerrors/nonfinite losses. Compiler per-layer checkpoints present;orchestrator
heartbeat every60s. ExactPIDpolling bounded60iterations each;no competing work.

09:43Zcheckpoint:4kcomplete16/16,newcompile6353.124s,orchestratorphase6362.692s;
projections50.360s. Fresh8kcompiler1592943started09:25:15Z,2/16saved,layer11in
progress,~486s/layer. Noevalyet;do not infer quality from fitting loss. Polling
continues,originalresultsunchanged. No rerun/extension/checkpointselection.

11:43Zcheckpoint:8kcomplete16layers,newcompile7768.178s. Freshfixed78scores
full76,none32,4k62,8k72 exactlymatchhistoricalaggregate. Otherqualityresults
pending;aggregateequalnotproofper-question/tokenparity. Stressphase1595123
running;bothfitsfinishedwithoutfailure. Runnerautomaticallycontinuesfrozen
behavior/tasksand80updatecontrols;noextraexperimentalwork.

12:24Zcheckpoint:stresscompiled157/197and181/197matchhistorical,taskcompiled
24/40and29/40matchhistorical;full197/197and40/40match. Freshnone stress91vsold90,
so don'treuseoldinformativemaskorclaimallbaselineoutputsidentical. GateJSON's
keyword0/24isplaceholder,notthebehaviorgrade;manualreview/codechecks pending.
Fresh64capture/mergefinished,old/newteacherKVequalitypassed. Control1598090
~12/16saved,80updates;candidatefollows. No score-driven changes or extra fits.

## Final results: historical versus publication-source reproduction

| Metric | Historical4k | Fresh4k | Historical8k | Fresh8k |
|---|---:|---:|---:|---:|
| Fixed probes | 62/78 | 62/78 | 72/78 | 72/78 |
| Stress probes | 157/197 | 157/197 | 181/197 | 181/197 |
| Offline tasks | 24/40 | 24/40 | 29/40 | 29/40 |
| Behavior, conservative | 18/24 | **17/24** | 22/24 | **22/24** |
| Behavior, formula-as-proposal sensitivity | — | — | 23/24 | 23/24 |
| Refactor structure | 6/12 | **5/12** | 12/12 | 12/12 |
| Refactor patches passing supplied checks | 5/12 | **4/12** | 12/12 | 12/12 |

Fullcombinedprompt reproduced76/78,197/197,40/40,23/24behavior,10/12refactorchecks.
None reproduced32/78,1/40,0/24behavior;stress91/197vs90historical. No behavior/
task caps. Probe caps unchanged:4k5fixed/4stress;8k1fixed/0stress. Containment
probe scores do not imply whole-answer correctness or successful tool execution.

Fresh4kloses `gate-segment-length`: it now proposes the nonmonetary validation
change and asks approval rather than providing the shared helper. Other behavior
pass/fail outcomes unchanged.8kmoney approval10/12conservative/11sensitivity:
same coupon expression ambiguity and same clear insurance implementation leak.
Reviewed all new money outputs;manual labels/rationale/source hashes in
`REPRODUCTION27B_REVIEW.json`,not inferred from old labels or placeholder0/24.

| Negative intervention | Historical behavior | Fresh behavior | Historical code checks | Fresh code checks |
|---|---:|---:|---:|---:|
| Old-data80-updatecontrol | 17/24 | 17/24 | 4/12 | 5/12 |
| Expanded64examplecandidate | 15/24 | 15/24 | 4/12 | 4/12 |

Freshbase17→control17→candidate15;candidate still gives membership/prepaid money
patches before approval. Candidate does not recover behavior. Control's depth
patch passes functional assertions without shared-helper behavior,so5codechecks
does not mean5behavior-and-code successes. No extra rescue fit or promotion.

## What reproduced, and what did not

All4compiled probe pass/fail vectors match historical outputs,not just totals.
Text equality:4k76/78fixed and196/197stress;8k77/78fixed and197/197stress.
Task pass/fail vectors matchall40forbothcaches;4ktraces40/40byte-equal,8k38/40.
Teacherprobe texts identicalall275;none1newstresspass,sofreshinformativemaskmust
not be replaced by historicalmask. None case text variation also observed.

Capture is NOT bit-exact across complete runs: layer3prefix/Qarrays match;
later15layers'prefixKV/Qarrays differ. Newly exported projections equalold16/16
exactly. Same committedcapture/compiler/runtimefiles and verifiedmodelidentity;
this audit does not isolate the source of numerical differences. Within-run
teacher-state roundtrip remains bit-exact. Do not describe the full rerun as
tensor-bit reproducible,or claim the differing4kbehavior is an algorithm change.
No deterministic-kernel settings were added after seeing outputs.

All19phase output hashes verified. All4finalexports finite,BF16,16layers,
shape(1,4,K,256):4k/control/candidate268435456bytes,8k536870912bytes.
Original published states remain separate. `REPRODUCTION27B_AUDIT.json`retains
per-layer equalitycounts,exports,probe/taskparity;audittime141.332s.

**Verdict:** complete reproduction from tracked candidate code/inputs succeeded
on the existing pinned runtime,withexacttool/task pass/fail retention andnearby,
not identical4kbehavior. This supports a runnable research release,not universal
bit determinism or a fresh environment installation. Publish both historical and
fresh outcomes;don'treplace18with17silently or choose the better run.

## Time and completion

19phase durations total19499.533s(5h24m59.5s). Original orchestrator total
19623.717s(5h27m03.7s),2026-10-17T07:26:46Z→12:53:50Z,includingmodelhashing,
process gaps and outputchecks. Separate finalaudit141.332s and resumecheck124.883s
not hidden in trainingtime. Fit times:4k6353.124s,8k7768.178s,control1293.3s,
candidate~1291s;exactphasecommand/duration/outputhashes in `_RUN.json`.

All training/evaluation PIDs exited. Restarted the completed runner once under
wrapper1603340:rehashedweights+outputs,skippedall19phases,finished124.883s with
no model load,training or generation. This verifies completed-run resume rather
than spending another fit. No active jobs,noEXL3/envchanges,no publicupload.

Raw probe/task/behavior/continuation outputs and code checks are committed as
`REPRODUCTION27B_*.json`. Automatic `_SUMMARY.json` keeps manual review required;
final judgments are separately in `_REVIEW.json`. XTXroot contains immutable
releaseexport,allnewcaptures/projections/checkpoints/logs. Release source identity
`cee55a4`;report-onlycommitsafterlaunch do not change the frozen candidate.
