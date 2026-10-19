# Purpose → field calibration at4096rows

Authorized2026-10-15. **Complete; no active jobs.** Same regimen as purpose27b_v1;only requested
KVbudget changes8192→4096. No data/capture changes or optimization extension.

## Final generation

| Evaluation | Full context | Purpose8192 | Purpose4096 |
|---|---:|---:|---:|
| Development | 193/194 | 187/194 | **175/194** |
| Fixed78 | 76/78 | 75/78 | **69/78** |
| Stress197 | 197/197 | 187/197 | **164/197** |
| Strict12diagnostic | 12/12 | 9/12 | **8/12** |
| Reserved6test subset | 6/6 | 5/6 | **3/6** |
| Occupied attention KV | 1627MiB | 512MiB | **256MiB** |

8192column saved prior invocation; same calibration/seed/update count/objective,
not fresh repeated generation. Fullcontext/none freshly evaluated in4096run.
Original71control(8192rows,not budgetmatched)167/194,75/78,165/197,7/12.
No checkpoint selection or retuning. Frozen grading unchanged.

- 8192→4096 paired gains/losses:dev2/14,fixed783/9,stress1/24,strict122/3.
  Stress selection56→47/62,arguments131→117/135. Dev selection58→53/62,
  arguments129→122/132. This is a substantial regression under unchanged recipe.
- Fixed78:lookup27→22/28,tools26→23/26,style18→20/20,unrelated4both. Allstyle
  probes pass but policy/repo/MCP facts also occur in lookup categories;do not
  claim policy fully retained. Losses include secrets encryption,Sentry scope/
  rate limit,migration/backfill skill and GitHub tool/field recall. Gains include
  WebFetch,ADR,migration-grader answer;groundtruth limitations still apply.
  Shared20:20→16;other58:55→53. Some required-field grading is too narrow:
  create_issue returnsowner but frozen expectation differs;no score changes.
- Caps8192→4096:dev0→1,fixed781→3,stress0→0,strict122→2. Strictdev4→5/6,
  reservedtest5→3/6;one cap in each4096split. Small diagnostic,not wholeagentproof.
- Fresh shared informative masks:dev85→76/89,fixed7843→40/45,stress97→78/106,
  strict127→5/9. Fresh stress none91/197vsprior90changes mask denominator107→106;
  compare8krescored under this mask,not historical98/107against78/106.

**Verdict:** half the occupied attentionKV,clear accuracy cost. The purpose-query
gain at8192does not survive unchanged4096recipe. No promotion or automatic
longer training/data/slot sweep. Does not prove a hard capacity limit:smaller
initialization and finite optimization can also contribute. Three-way paused.

## Measured cost and artifacts

No recapture. Compile6148.368s(1h42m28s),evaluations1711.525s,total**7859.894s
(2h10m59.9s)**. Excludes reused8kdata/capture/training and historical control
compile. Same400×72updates/sample work,not identical FLOPs:smaller attention.
Compiled16layers4096rows,268435456bytes=256MiB;unchanged151.5MiBFP32recurrent
state andlogical26033. Physicalcapacity32768,no measuredprocessVRAMsaving.

Local [PURPOSE4K27B_SUMMARY.json](PURPOSE4K27B_SUMMARY.json) generic`expanded`
means4kpurposecandidate;[PURPOSE4K27B_DETAIL.json](PURPOSE4K27B_DETAIL.json)
records paired8kchanges,commoninformative masks,splits,timing. XTXroot retains
all eight perquestion baseline/candidateJSON,compiled/,summary.json,andreferences
to unchanged8kquestions/sampling/captures/heldoutcases. CompiledmanifestSHA256
`1120ea2074381e102552d84454045f530d727bd10e2781aade6ad0c43cbd5c95`.
Compile1498451/eval1499331finished. Implementationd363dba,capturecheck551e9ff,
compilecheckpoint372b4c8. Original artifacts preserved; no app/env changes.

## Frozen protocol and chronological checkpoints

Reuse frozen780questions,476+304purposebindings,teacher,capturedtrajectories,
samplingplan,andheldoutcases via references to purpose27b_v1. Verify identities
and all16shards before compile. Same400updates,24original+24existing+24binding,
LR.001,seed0,chunk4,cosine1,correctedprojected/gatedloss,frozensink,BF16export.
Standardteacherinitializationat4096,no8kKVwarmstart. Samefullrecurrentstate and
logical26033positions. Checkpointperlayer;no benchmarkcheckpointselection.

4096/26033=15.73%occupiedattentionrows,6.36×rowcompression vsfullcontext;
8192was31.47%,3.18×. AttentionKV256MiBvs512MiBat8k,1627.06MiBfullcontext.
RecurrentFP32state151.5MiBunchanged,pagedcapacity32768retained;do not claim
equivalenttotalprocessVRAMsaving or measuredallocated-memoryreduction.

Frozen greedy/no-thinking/fullEOS/cap64;dev194,fixed78,stress197,strict12.
Freshoriginal71control+fullteacher/noneevaluations as priorpipeline;compare
saved8kpurposeoutputs separately with commonfreshteacher/nonemask. Report
caps,selection,args,shared20/other58,reserveddev/test,durations,perquestionchanges.
Previouslyinspectedsharedbindingregressions,notpristinegeneralizationtests.
Same304bindingpairs(include8answer-revealingdescriptions),reservedtoolsexcluded;
allpriorqualitycaveatsremain. No promotion/newrun/4Bcomparisonresume.

XTXroot `/mnt/data/artifacts/kvcompile/artifacts/agent/purpose4k27b_v1/`;
compiled/containsnew4096artifact;sharedinputsreferpurpose27b_v1. Script
`scripts/run_purpose4k27b.sh`;logs`/tmp/opencode/purpose4k27b-{compile,eval}.log`.

Implementationd363dba. All780×16captureQ/A andoriginalidentityedbbd57aedee3d62
verified;no recapture. Summarymixed-slotbyteaccountingtestpassed. Compile1498451
active,2/16checkpoint768.0s,about1h42mfirsttwolayerextrapolation(notguarantee).
No generation result;frozen recipe unchanged. StandardremotePython lackednumpy
for initialpreflight;retried with projectruntime and allchecks passed,no installs.

Compilecomplete16/16,6148.4s(1h42m28s),all4096slots. No generationqualityresult
yet;frozenevaluationnext,no checkpoint/recipechanges.
