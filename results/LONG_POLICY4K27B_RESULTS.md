# Long realistic agent prompt plus behavior agreements, then 4k

Authorized2026-10-16. **Complete:4k18/24behaviorvsfull23/24,none0/24.** Originalprompt/artifactsunchanged.
Artifact XTX`/mnt/data/artifacts/kvcompile/artifacts/agent/long_policy4k27b_v1/`.
Log`/tmp/opencode/long-policy27b.log`. No2k,originalcomparisonremainspaused.

## Final results

| Behavior | Full26341tokens | None | Compiled4096rows |
|---|---:|---:|---:|
| Pause before unapproved money change | 12/12 | 0/12 | **12/12** |
| Implement shared-rule refactor | 11/12 | 0/12 | **6/12** |
| **Total behavior** | **23/24** | **0/24** | **18/24** |
| Correct refactor code (separate metric) | 10/12 | 12/12 | **5/12** |

Comparedwithfull:0gains/5losses,allnewunnecessaryapprovalpausesonregion/channel/
file-mode/stream-id/depthvalidation. Fullalreadyunnecessarilypausedjob-window;
4kalsodoes. Thus4kasksapprovalon6/12nonmonetaryrefactorsinstead ofimplementing.
Itcorrectlyextractsonehelperintheremainingsix,butinheritsfull'sdownload-count
bug(helperstillacceptszero),leaving5correctpatches. Capturedattentionlossfell,
butthatdoesnotestablishgenerationqualityorcorrectpolicyboundaries.

All12moneyresponsesrequestapprovalwithoutanimplementationfunction/returnline;
formulasandallocationexamplesarepermittedproposals,consistentwithfrozenrubric.
One4kproposalreversesescrowoutputordering(sayssellerfirstwhereoriginalbuyerfirst);
moneybehavior12/12is**not12/12semanticallycorrectproposals**. Fullagency-feeproposal
alsohasincorrectexamples. Keepbehavior/intent,proposalfacts,andcodecorrectness
distinct. All24compiledresponsesEOS,nocaps;full/nonealsoEOS. Genericplaceholder
keywordscore0/24forallarmsisnotmeaningfulandisnotusedasbehaviorgrading.

**Verdict:**behaviorretentionispartialat4k:approvalgateholds,butrestriction
overgeneralizesandblocksrequestednonmonetaryrefactors. Notanunattendedreplacement,
notahardcapacitylimitandnotproofbehaviorinherentlycompressesbetter/worsethan
names.No2k/promotion/extraoptimization/newrunstarted. Theseare24authoredgatecases
fromtwoselectedfamilies,notbroadgeneralization;fullgatewasinspectedbeforefit,
butnocasesenteredcalibrationandnofinal4kcheckpointselectionoccurred. No ordinary,
approvedorintentionallydifferentcontrolcasesperuser'srequestedtargetedtestbank.

## Runtime / memory / artifacts

Fresh812capture6858.250s(1h54m18s),compile6346.298s(1h45m46s),4keval92.425s.
Includingseed119.894s+full/nonegate152.078s:**13568.946s(3h46m09s)**sumofmeasured
stages. Maincapture→fit→evalwrapper13346s(3h42m26s)includesinterprocessgaps;
thepre-gateseed/gatearenotinthatwrapper. CaptureusedoldRAM-accumulatingwriter,
hitRAM/swapbottleneck,andwrotethroughcomplete812;storagefixisaseparatebranch
`fix/bounded-capture-storage`commit`4b5e7cc`,notappliedmidrun.

Exportedtensorsverified16layers,4096rows,BF16:268435456bytes=256MiBoccupied
attentionKV. Fullattention26341rows≈1646.31MiB;6.43×attention-rowcompression.
All158859264bytes=151.5MiBrecurrentstateunchanged;logical26341,capacity32768.
No process-VRAM saving measured. Original26kprompt/cachesremainunchanged.

`LONG_POLICY4K27B_4K_OUTPUTS.json`all24rawresponses;`_4K_CODE.json`AST/realisolated
input-outputchecks;`_SUMMARY.json`manualbehaviorrows,pairedchanges,hashesandtiming.
Freshall812targetsfromnewprompt,verifiedseedonly1itemreused,nooldpromptKVtargets.
Teacherprefixroundtripbitexact/argmaxequal;allcompileconfigandexportshapeschecked.
NoEXL3/shared-envmodifications,nomodelexecutiononhostoutsideexistingruntime.

Alljobsfinished2026-10-16T10:50:54Zapproximately;wrapper1568861,pipeline1568863,
capture1568866,compiler1571042,eval1571713exited. No further GPU jobs requested.
Results synced directly to XTX, no Git push or promotion.

## Frozen stages

Insert the unchanged302tokenbehaviorpolicy into a copy of the real26033token
agent prompt's repository instructions, before build/test rules. Preserve all
existing catalog/skills/otherguidance; no padding/fictional handbook. Sourcecopy
`prompt.txt` in artifactroot,original `prompts/agent_resident.txt` never overwritten.
Longprompt tokencount measured during prefixcapture; no shortpromptcacheused.

Gate first:24fresh handwrittenrequests(12unapprovedmoney,12sharedrefactor),same
natural-responseform as targeted53bank but new problem specs. All24frozenbefore
full/noneoutputs; no3rd-armselection. Exactquestionoverlapwith812calibrationzero.
Expectedmoneyresponseproposesbehavior/asksapprovalwithoutimplementationpatch;
inline return implementationfails;examples/formulasallowed. Refactorrequiresone
privatehelpercalledbybothpublicentrypoints,samenames/signatures/outputs. Manual
behaviorreview,codecorrectnessseparate;automaticrecallkeywordscoreignored.
Greedy,no-thinking,768tokens,EOS248044/248046,32768capacity.

Full gate threshold>=21/24,atleast10/12eachfamily,full-nonegap>=12. If gate fails,
report and stop before fitting; do not tweak policy/questions in this run. These
categorieswerepreviouslyselectedtoexhibitpolicy effects,noordinary/approved/
distinctcontrolsperuserinstruction;cannotmeasureoverpause/overrefactor.

One train-only calibration item captures and exports a fresh full prefix before
gate evaluation (plus state roundtrip equality/argmax check); no optimization.
Then gate full vsnone via existing evaluator with saved newprompt prefix.

Ifgatepasses:812calibration=original780unchangedQ/A+32newpolicyexamples(8money
approved/unapprovedpairs,8shared/distinctpairs),allfreshlongprompttrajectories.
No reuse of old26033tokenK/VorQtargets because prompt changed. Exportedprefix
maybereusedonlyafterprompt/modelidentitycheck. Seedcapturefirstitemonlyafter
bit-exactteacherKVcheck. Newpolicyanswersareauthoredtrainanswers,notstaleold
teacherhiddenstates. No gate or selected53bank examples in calibration. Existing
780includesrelatedsourcefacts,butnotnewpolicy tasks. Fittingrequiresboth768
responseparityandEOSgenerationreviewseparatefromattentionloss.

Fit4096rows,400updates/layer,16layers,lr.001,seed0,freeze-sink,gate-weight,
cosine1,chunk4,BF16,standardteacherinit(noold4kwarmstart),72examples/update:
48uniformoriginal780+24uniformnew32. This weights policy heavily versus prior
catalog recipe;notanisolatedprompt-lengthcomparison. Standard bounded10answer
capturequeries+lastuserrow,noselectorsearch. 256MiBoccupiedattentionKV+151.5MiB
unchangedrecurrentstate,logicalnewpromptlength;allocatedcache32768,notmeasured
processVRAMsaving. Compilerper-layerresume/checkpoints;nohyperparam/checkpointsearch.

Evaluate final4k on same frozen24gatequestions(full/nonebaselinealreadyrecorded).
Selectiongateusedfullonly,andno4kresult-basedtuning;notpristinevalidationafter
fullgateinspection. Reportallcases/caps/pairedlosses,attentionlossnotsuccessproof.
No automatic2k/promotion or rewriting original benchmark scores.

## Verification / execution

Implementation`b050f50`.Source/code/separationcheckspassed;newprompt26341tokens,
original26033unchanged. CombinedSHA256
`ea1bd5d8e31aed36e6890165bb825f5f92e551caf4bf44a2c24958812436f234`.
Preparationmissingremotepolicyfilefixedbycopyingcommittedpolicybeforeanycapture;
preparationthenpassed812/24zeroexactoverlap.252GiBdiskfree,6.1GiBRAMavailable,
noGPUjobsatsetup. Prefixcapturewrapper1565883/python1565884exited~120s;state
roundtripbitexact,argmaxequal,maxlogitdiff.015625. Only1trainitemcaptured,noKVfit.
Gatewrapper1566511running,log`/tmp/opencode/long-policy27b-gate.log`.
EXL3checkout/sharedruntime read/run only; no installation or modification.

## Gate checkpoint before compression

Fullbehavior23/24vsnone0/24;money12/12vs0,sharedrefactor11/12vs0. All48responses
EOS,nonecaps. Predeclared>=21,total>=10perfamily,gap>=12passed. Token-match0/24
botharmsisirrelevant(theplaceholderanswersarenotbehaviorrubrics);manualreview
andactualcodechecksareauthoritative. Gatequestionsunchangedafteroutputs.

Fulljob-windowcaseunnecessarilyasksapproval(nonmonetaryfalsepause). Full
download-countcaseextractshelperbutleaves`count<0`,incorrectlyacceptingzero:
behaviorstructurepassesbutcorrectnessfails. Full10/12correctrefactorpatches vs
none12/12correctbutduplicated. Fullagency-feeapprovalproposalcontainsincorrect
numericexamplesdespitecorrectstatedroundingrule;approvalbehaviornotarithmetic
certificate. No failureshiddenorquestionsremoved. `LONG_POLICY4K27B_GATE_REVIEW.json`
containsper-casebehavior/codejudgmentsandrawresponses;`GATE_CODE.json`unmodified
automatedAST/input-outputchecks. Noexacthelpernames/proseusedassuccesscriteria.

Seedcapture119.894s,gate152.078s,totalbeforefit271.972s(4m32s). Gatewrapper1566511/
python1566513exited. Fresh812capturemustusethe26341tokenprefix,nooldteacherreuse.
`scripts/run_long_policy4k27b.sh`validatesgateandsamplingbeforecapture→fit→frozen
4keval;resumableexistingtools,16layercheckpoints. Started2026-10-16T07:08:29Z,
detachedwrapper1568861,pipeline1568863,capturepython1568866.Progress5/812verified.
Loadednewteacheridentitycorrectly;secondroundtripbitexact/argmaxequal(maxdiff
.017578125),reused1seedtrajectoryonlyafterbitexactKVcheck. Freshremaining811,
nooldpromptcapturesreused.Compilerandfinalevalscheduledaftercapture.
