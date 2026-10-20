# Equal useful-prefix memory follow-up — 27B

Authorized2026-10-20 after completed equal-row study. Separate output
`/mnt/data/artifacts/kvcompile/equal_memory27b_v1`; prior source/artifacts,
cases, scores and failures remain unchanged. No public push or runtime edits.

## Frozen byte cap and allocation rule (before fitting/evaluation)

**256MiB useful prefix payload cap per arm**, excluding unchanged recurrentstate,
native cache capacity and padding overhead. Compiler FP16K/V occupies1024bytes
per head-row; its262144rows exactly fill268435456bytes. AMFP16K/FP32V plusFP16beta
occupies1538bytes per head-row. Largest uniform integer count under that cap is
**2727rows/head**,174528totalrows,268424064bytes; **11392bytes (0.00425%) unused**.
Do not call payload bytes bit-for-bit identical or call this equal processVRAM.

Compiler uniform/allocated fits, grid and fixed allocation are reused from
`nonuniform27b_fp32v_v1` after protocol/hash/shape/finite/length checks; tensor
exports must be byte-identical. No needless compiler refit or test-selected
allocation. AM freshgrid **1363/2727/4091**: symmetric2727±1364 (mean//2+1).
Same64heads, calibration72seed1729/original48+24plan, isolated projectedattention
MSE+cosine cost, exactDP total174528rows. Costs measured before allocation;
no test-score search, on-policy/data/objective/seed change. AMsame pinned
RMS/NNLS2/unregularizedLSQ and freshseed0fit, allVFP32/KbetaFP16. Byte cap/row
conversion/grid are arithmetic choices, not selected from evaluation outcomes.

Same original812captures/projections/prompt/model/151.5MiBrecurrentstate.
Reuse existing FP32solver/sidecar code; run baseAM and FP32failed-head native
gates in newroot before fitting. Failurehalts, no precision fallback/clamp/ridge/
headremoval. Uniform/allocated AMuse common paddedmaskedFP32attentionpath.
Exports record useful/paddedbytes and nativeVplaceholder overhead. Native4arm
smoke exactreload/recurrent checks; uniformcompiler native tokens/maxdiff<=.25.

Freeze same final240cases/graders; fresh240×4responses, newresponse-bound480
manualbehaviorreviews (AIassistant/unblinded). Reused full/no-prefix controls
from earlier same-prompt study disclosed, not newcontrolruns. Report knowledge,
tools, approvalgate/proposal, prematureimplementation, falsepauses, structure,
functional/joint and pairs separately; no pooledwinner/holdout/generalclaim.
Record internalfit times, stagewall/UTC and arm evaluation intervals, reusedcosts
separate from incrementalrun. Different backendprecision/padding precludes
processVRAM/speed claim even with near-matched useful payload.

## Execution

CPU-only budget/export/runnerfixtures passed with GPUhidden. Existingminer
stays on through CPUprep, must stop and verify devices clear before anyGPUstep.
New immutable source; sequential prepare→basegates→FP32gates→threeAMfits→AMcurves/
DP→four exports(reusedcompiler)→smoke→freeze→evaluate. DirectPIDpolling, bounded
stagewaits/checkpointreceipts; each verifiedstagejournal before nextlongrun.
No GPU launch yet at this protocolcheckpoint. Restart existing unchangedminer
only after researchcompletion and GPUidleverification; no bootenablement.

## Launch and gate checkpoint

Immutable implementing source `187e138`, exported to
`/mnt/data/artifacts/kvcompile/equal-memory-source`. Git-free582file/581hash
inventory and31small-dependencyCPUfiles passed, plus TorchCPUbyte-cap/export/
runnerfixtures. Miner stopped; zeroGPUholders/activeAIunits verified before
launch. Wrapper1945030, mainlog `/tmp/opencode/equal-memory-sequence.log`,
currentchild `/tmp/opencode/equal-memory-child.pid`, receipts
`/tmp/opencode/equal-memory-stages`, terminalrecord `/tmp/opencode/equal-memory.exit`.

Directpoll02:42Z: prepare/basegates/FP32gates passed; FP32native78.796s,
tokensequal/maxdiff.0234375, reload/recurrentexact,13.971GiB. AM1363/2727
fits completed;4091activechild1946308, lastcheckpoint32/64heads at02:41:19Z.
41GiBfree. No allocation/evaluationresult yet. Each verifiedstage appends
output `execution.md` before nextstage; failurehalts/directpoll/mineroff.

## Evaluation scope correction — 2026-10-20

User clarified running **both new AMvariants**,480freshresponses. Earlier fourarm
runner unnecessarily regenerated unchangedcompiler responses; stopped exact
evaluationPID1946933 withTERM at03:03Z, wrapper1945030 exited on child-15. This
is deliberate interruption, not gate/model failure or studycompletion. Partial
`raw.json` retained: compileruniform60knowledge+60tools+94behavior, otherarms0;
no outputs discarded or relabeled as fresh AMresults. All completedfits/exports/
gates/freeze unchanged. AMallocation already fixed, not selected from tests.

Use unchanged supported `evaluate.py run --arms am_uniform,am_allocated` with
existing freeze, separate `raw-am.json`; explicit originalcompilerresponses
reused from `nonuniform27b_fp32v_v1`, never inserted into fresh AMraw. New wrapper
1952183, log `/tmp/opencode/equal-memory-am-only-sequence.log`, generationlog
`equal-memory-am-only-generation.log`, childPIDfile `equal-memory-am-only-child.pid`,
terminalrecord `equal-memory-am-only.exit`; bothvariants240cases each. Miner off.
Record wasted partialevaluation walltime separately. NewmanualAMreviews needed;
reuse compilerreviews only with their unchanged originalsource binding.

## Completed checkpoint — 2026-10-20

AM-only wrapper exited0; 480responses complete at04:01:26Z, runner3354.735s,
wrapper3408.006s. All240behaviorresponses read in full against questions and
newhash-boundreview; allEOS/zerocaps. Results/evidence in `EQUAL_MEMORY_RESULTS.md`
and `EQUAL_MEMORY_{RAW,REVIEW,SUMMARY,TIMING}.json`. Compileroriginalresponses/
reviews explicitly reused, partial214responsefile excluded and preserved.
Uniform→allocatedAMknowledge50→56/tools47→54/sharedjoint10→20/falsepauses31→13;
allocatedAMvscompiler53/48/shared23/false9 is a tradeoff, not overall dominance.
OriginallargerAMallocatedshared29/false7 outperforms smallerAMbehavior even
though smallerAMtask56/54 beats53/52. Conservative proposal contradiction
and all boundary/approval failures retained; no score tuning.

Artifactaudit252frozenfiles/326stagehashes and separate256headreal-tensor
implementationrecheck passed; CPUregressions regrade task/codeextraction,
responsebindings/exactDP/bytes/smoke/timing. GPUresearch finished, exact generation/
audit PIDs exited; minerhandoff requires finalGPUidlecheck. No publicpush/runtimeedits.

Final GPUholder/activeAIunit checks empty; existing `~/mining/mine start`
restored miner.serviceactivePID1965651, bootdisabled/configunchanged. No new
GPUresearch queued. Restart-specific share/hashrate verification not yet recorded.
