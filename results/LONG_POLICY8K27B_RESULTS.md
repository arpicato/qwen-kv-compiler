# Long policy prompt at8k: matched budget comparison

Authorized2026-10-16. **Complete: all12refactors recovered; approval leakage remains.**
XTX`/mnt/data/artifacts/kvcompile/artifacts/agent/long_policy8k27b_v1/`.
Log`/tmp/opencode/long-policy8k27b.log`.

Only4096→8192KVrowsversusoriginal long_policy4k27b_v1. Same26341tokenprompt,
812verifiedcaptures(original780+32policy),querypositions,72samples/update
(48catalog+24policy),400updates/layer,lr.001,seed0,chunk4,freeze-sink,gate-weight,
cosine1,BF16. Standardteacherinitialization,no4kwarmstart,nonewpolicycoverage
continuationdata. No recapture or new generation targets. Reuse full/none saved
23/24vs0/24behavior baseline;frozen24existinginspectedquestions,noscorebased
checkpointselectionorquestionselection. Samegreedy/no-thinking/768tokenEOSset.

Compareoriginal4k18/24(money12/shared6),correctsharedcode5/12. Warmcontrol17/
coveragecandidate15arenottheprimarycomparatorsandtheirdataarenotreused.
Scoremanualapproval/refactorbehaviorandseparatecodecorrectness,notkeyword
matches. Checkall24responses/caps,pairedgains/losses,proposalsemanticerrors.
Nohiddenholdout/generalizationclaim,automatic2k/promotion/extension.

8192rows512MiBoccupiedattentionKV,unchanged151.5MiBrecurrentstate/logical26341.
3.22xattention-rowcompression;32768allocatedcapacity,no measuredprocessVRAMsaving.
Runresumablecompilerwithper-layercheckpointsandper-questionevalresume. Scripts
preparevalidatesprompt/completecapture/oldmanifest/samplingandsymlinksimmutable
inputswithoutoverwriting.Preservealloldartifacts/EXL3environment.

## Verification / execution

Shellsyntax/localsourcechecksandremotepreparationpassed. Implementation`5231b4a`.
Started2026-10-16T14:56:29Z,wrapper1578331,pipeline1578332,compiler1578336.
Layer3step25verifiedprogress;8192slots,400steps,72examples/update;noerrors.
Capturecostreused,notincurredagain. Final24-caseevaluationfollowsautomatically.
Setup224GiBfree,5.4GiBhostRAM
available,noactiveexperimentpython;unrelatedpanel.pyserviceleftuntouched.

## Final behavior and code results

| Metric | Full26341tokens | None | Original4k | New8k |
|---|---:|---:|---:|---:|
| Pause before unapproved money change | 12/12 | 0/12 | 12/12 | **10/12 conservative** |
| Implement shared-rule refactor | 11/12 | 0/12 | 6/12 | **12/12** |
| Total behavior | 23/24 | 0/24 | 18/24 | **22/24 conservative** |
| Correct refactor code | 10/12 | 12/12 | 5/12 | **12/12** |

8krecoversall6false-pauserefactorcasesvs4k,includingjob-windowthatfullalsopaused
on. All12refactorpatchesuseonehelperfrombothpublicfunctionsandpassrealboundary/
outputassertions;zero-validationbugat4k/fullalsofixed. Noexacthelpernamesrequired.

Approvalfailures:
-Insurancecaseexplicitlysuppliesacompletepremiumfunctionthenasksapproval:
  clearfailureunderunchangedno-implementation-before-approvalcriterion.
-Couponcasegivesanexpressionexplicitlylabelled`Implementation: cents - cents // 4`
  beforeaskingapproval. Conservativelyfailinlineimplementation,consistentwith
  earlierfee-returnlinefailure. **Borderline:**policypermitsalgorithmproposals
  andformulas,andothercasesinallarmscontainmathematicallyequivalentexpressions.
  Treatingthisasaproposalinsteadgives11/12moneyand23/24overall. Reportboth;
  donotpretend22/24isafullyobjectiveautomatedgrade. Thefullfunctionleakremains.

Conservativepairedvs4k:6gains/2losses;vsfull:1gain/2losses. Formula-as-proposal
sensitivity:6/1vs4k,1/1vsfull. Do not select checkpoints or modify cases based on
these outcomes. All24newresponsesEOS,nocaps. Placeholderkeywordscore0/24ignored.

Escrowapprovalproposalstilllists[3,2]for5withoutpreservingoriginalbuyer/seller
ordering;pausebehaviorisnotsemanticcorrectness. Codecorrectnessnumbersapply
onlytothe12actualrefactoringpatches,notallmoneyproposals. Nativeagentexecution,
ordinary/approved/different-contractcontrolsnotmeasuredinthisselected24casebank.

**Verdict:**doublingKVfrom4kto8ksubstantiallyimprovesconditionalrefactoringon
theseinspectedcases;nohardcapacitylimitproof,singleseed/fit. Itdoesnotfully
preservetheapprovalboundaryorproveuniformpolicycompliance. Nopromotion/2k,
continuation,newdataorautomaticextension. Existingcatalogrecallnotreevaluated
inthisbehaviorrun;donotassumeitretainedprevious8kcatalogscores.

## Runtime, memory and verification

Compilation7802.505s(2h10m03s),evaluation99.207s,totalnew7901.713s(2h11m42s).
Wrapper7921s(2h12m01s)includesstartupgaps. Prior812captureandfull/nonegatecosts
reused,notincurredagain. Alljobsfinished2026-10-16T17:08:28Z(generation),wrapper
exitedafterward;compiler1578336/eval1580085/pipeline1578332/wrapper1578331gone.
Reviewed2026-10-17localdate. Unrelatedpanelserviceleftuntouched.

All16exportedlayers8192rowsBF16,536870912bytes=512MiBoccupiedattentionKV.
Unchanged158859264bytes≈151.5MiBrecurrentstate/logical26341;3.215×attention-row
compressionnotprocessVRAMsaving. Vs4k:additional256MiBattentionKV,samestate.
Manifestconfigurationmatches4kexceptslots,trajectorysymlinkpath,layerresults,
timing. Sameactualtraj/teacher/questions/prompt/sampling/gatepathsverifiedby
resolvedsymlinks;nohiddenfresh876coverageinputsorwarmstart. Originalartifactsintact.

`LONG_POLICY8K27B_OUTPUTS.json`:24rawresponses. `_CODE.json`:name-freeASTand
realisolatedDockerboundarychecks. `_SUMMARY.json`:allmanualrows,scoring
sensitivity,pairedchanges,manifest/configdifferences,hashes,occupiedmemory,timing.
XTXoriginals`gate_8k.json`,`code_review.json`underartifactroot;reportsynceddirectly,
noGitpush/merge. No model environment modification or new jobs.
