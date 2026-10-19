# Purpose → field calibration at8192rows

Authorized2026-10-15,no KV increase. **Complete,no active jobs.** Purpose→field
calibration improves shared-binding retrieval at8192rows;not broadgeneralization
or automaticpromotion. Original artifacts preserved.

## Final generation results

| Evaluation | Fullcontext | Fresh original71 | Previous reverse780 | Purpose780 |
|---|---:|---:|---:|---:|
| Development | 193/194 | 167/194 | 176/194 | **187/194** |
| Fixed78 | 76/78 | 75/78 | 75/78 | **75/78** |
| Stress197 | 197/197 | 165/197 | 175/197 | **187/197** |
| Strict12diagnostic | 12/12 | 7/12 | 7/12 | **9/12** |
| Reserved6test subset | 6/6 | 3/6 | 3/6 | **5/6** |

Previous reverse scores are saved priorinvocation,samebindingpairs,samplingand
compilerrecipe;not fresh repeatedcontrol. Correctedoriginal71artifact freshly
evaluated for pairedscores. Runtimevariability can move borderlineanswers.
Full/noneinformativemask shared perpairedsuite. No evaluationcheckpointselection.

- **Stress arguments119→131/135 vsreverse;selection56→56/62.** Direct101binding
  slice86→98/101;other34arguments33→33. Sharedbindings,notunseenfacts. Captured
  calibrationquerydirection/answerlength changed together;not isolated answerCE.
- Devlookup129/132,selection58/62. Direct98binding slice87→95;other34args32→34.
  Vspreverse13gains/2lossesdev,13/1stress,0/0fixed78,3/1strict12.
- Pairedoriginal71→purpose:dev23gains/3losses,stress24/2,fixed781/1,strict123/1.
  Informative69→85/89dev,80→98/107stress,44→43/45fixed78,5→7/9diagnostic.
- Capsoriginal→purpose:dev1→0,stress1→0,fixed781→1,strict120→2. Strictdev4/6
  unchanged with2caphits;reservedtest3→5/6withoutcaps. Sixcases too small for
  wholeagentreliability. Reservedtools remain excluded from newcalibration.
- Fixed78samecorrectnessvectorasreverse780:lookup27/28,style18/20,tools26/26,
  unrelated4/4. Relativeoriginal,create_issuegain/WebFetchloss. Shared20:20/20;
  other58:55/58(vsoriginal56). No universalpolicy/skillimprovement.
- Remaining4stressargumentmisses:commentNodeID→comment_id,failed_only→failed_jobs,
  modified→published,minimal_output→minimal. Sixselectionmisses include aliases
  andsub_issue_writegroundtruthlimitations;frozengradingunchanged.

**Verdict:** usefuldirection-matchedcoveragelead,especiallyfieldnames. Same304
bindings asked in retrievaldirection outperform reverse-descriptiontraining;
do not interpretas independenttestsuccess or proofallremainingerrorsfixed.
NoKVincrease,backendchange,newrun,checkpointtuningorautomaticpromotion.

## Measured cost/artifacts

Capture1536.043s,compile7557.376s,evaluations1745.320s,total**10838.740s
(3h0m39s)**. Historicalcontrolcompile/reverserunexcluded. Same72samples/update
asreverse,compile2h5m57s vs2h6m33s;3×sampleworkvs476baseline,notfixedcompute
comparisonwith476. Allcompressedarms8192rows/layer=512MiBoccupiedattentionKV,
unchanged151.5MiBFP32recurrentstate;physicalcapacity32768,no measuredprocessVRAM
saving. Prompt26033tokensunchanged,logicalcontinuation26033.

XTXpurpose27b_v1containsquestions/samplingJSON,traj/,compiled/,controlreference,
heldout/diagnosticJSON,allperquestion{dev,agent78,stress197,diagnostic12}_{baseline,candidate}.json,
summary.json. Local [PURPOSE27B_SUMMARY.json](PURPOSE27B_SUMMARY.json) uses generic
label`expanded`forpurpose780;[PURPOSE27B_DETAIL.json](PURPOSE27B_DETAIL.json)
recordsreversecomparisons,slicesanddurations. CompiledmanifestSHA256
`d93aadd27e51be1f3f453612edea8bb510b04f72204c9c12185550c6c3d96670`.
Capture1492044,compile1493003,eval1494389finished. CPU tests andpaired totals
verified. Implementation8808828,capturec1b7a33,compileea4ec56,dev39547c8.

## Frozen protocol and chronological checkpoints

Change direction of the same304source bindings used in bindings27b_v1: ask exact
schema purpose,give exact field name. Keep original71+405unchanged,total780.
Same247optional/conditional+57required,six reserved tools excluded. No choice
from dev/stress failures,new field expansion,or abandoned143data. Source prompt
unchanged. Questions systematically generated from schemas,not probe text.

Exact field-name selfmentions masked129times across103descriptions;8rows become
ambiguous after masking(e.g.Filter by state/resolution),so original description
retained and flagged. These8are answer-revealing source queries,not robust
retrieval tests. Some remaining related spellings may cue answers. No synthetic
paraphrases. Frozen evaluations ask closely related schema descriptions:
**direction-matched shared-binding regression,not independent generalization**.
Zero exact normalized question overlap checked across all frozen evaluations;
that alone does not imply semantic independence. AuditPURPOSE27B_AUDIT.json.

Same recipe as reversebindings780:8192rows/layer,16layers,400updates,LR.001,
seed0,cosine1,projected/gated objective,frozen sink,BF16export,chunk4. Each update
24original71+24existing405+24new304. Same72examplebudget as reverse run,3×sample
work vscoverage476. Start from standard teacher initialization,not warm-start
or reread. Original full recurrent states/logical26033retained. This isolates
bindingdirection/answerlength effects better than comparison vs476,but capture
queries/token counts andruntime still differ. No loss/checkpoint selection.

Reuse476original fullteacher trajectories only after Q/A and prefixKV bit-exact
checks;freshcapture304purposequeries. Checkpoint25items,progress5items;compiler
checkpoint each layer. Frozen greedy/no-thinking/fullEOS/cap64evaluations:
dev194,fixed78,stress197,strict12;report20shared78slice,reserved6test separately.
No questions used to train based on their evaluation result. Preserve originals.

XTXroot `/mnt/data/artifacts/kvcompile/artifacts/agent/purpose27b_v1/`.
Runtime scriptsprepare_bindings27b.py --direction purpose-to-field and
run_purpose27b.sh reuse tested bindings pipeline. Logs
`/tmp/opencode/purpose27b-{capture,compile,eval}.log`. No automaticpromotion or
extension;paused4Bcomparison remains paused. EXL3checkout/environment untouched.

Implementation8808828. CPU source-direction and existing sampler/optimizer tests
passed. Capture1492044active:original476Q/A and allprefixKVverifiedbit-exact,
teacher state roundtripbit-exact,firstqueryargmaxequal,maxlogitdiff0.015625.
Fresh304capture underway,noqualityresult. Compile/eval not launched yet.

Capturecomplete780×16,1536.043s(25m36s),allshardQ/Aandcountsverified;
calibrationidentityedbbd57aedee3d62. Frozen72examples/update compile next.

Compile1493003active,firstlayer470.1s(7m50s),manifest24/24/24sampling. Firstlayer
extrapolation~2h5mfor16layers,notguaranteedETA. No generation result.

Compilecomplete16/16,7557.4s(2h5m57s),same8192rowsand24/24/24quotas. Frozen
evaluations next;no generation-based recipe/checkpoint changes.

Devcomplete:freshoriginal71control167/194,candidate187/194,caps1→0,vsreverse780
176andcoverage476179inpreviousinvocations. Direction-matcheddev,notindependent
heldout. Remainingfixed78/stress/strict12pending;eval1494389active,no retuning.
