# Recover the behavioral bank that worked

Development protocol authorized2026-10-17. The earlier active bank had53cases,
not12:28shared-refactor and25money-approval. Fresh40batch had20refactors with
full20/20vsnone0/20 under the SHORT policy prompt. Original12refactors were only
one slice of the later24long-prefix gate. Earlier claim that12wasallwaswrong.

Recover all28originalrefactorquestions verbatim plus all12long-prefixrefactors,
40total,none removed by current output. Money cases excluded per user steering.
No invented rewrites,helpernamesornewrules. References/testmetadata regenerated
without changing questions. This bank is explicitly historical/development data,
selected source categories already inspected,notheldoutvalidation. Older53bank
itself was selected by baseline outcomes;disclose its provenance.

Evaluate FULL versus NONE FIRST on actual26341tokenprompt and publication-source
teacher,notshortpolicycontext. No compressed-cache outputs used for selection.
Use original768token natural-response format. Full-context source/weights and
allartifacts frozen before output. Existing CPU/Docker+transport verification
reused,all40references/negativeschecked. Score process/structure,finitefunctional
tests,andintersection separately; manualinspectionrequired.

Development acceptance target fixed before output:atleast32/40fulljointpasses,
atmost8/40nonejointpasses,andatleast24casegap. This is a practical screen,not
a statistical claim. If it fails, retain the full batch and diagnose prompt/form
differences; do not silently delete failures or label a selectedsubsetvalidation.
Keep working on explicitly marked development candidates without 4k/8k peeking.
No training,4Bfits,cachechanges,historyrewriteorpublicupload.

## Baseline gate passed before candidate scoring

Source574a179,freezeSHA256
fb7d103b03b738f803e5628baabe5f9bbb7074305128c7ed8b9ba38a435db479.
All40reference/40unchangednegativeDockerchecks passed. Full/none80responses
completed348.177s,2026-10-17T16:20:37Z,wrapper1673595/python1673624exited.
RawbaselineandfreezeareTRANSPLANT_REFACTORS_V4_{BASELINES,FREEZE}.json.

Full33/40jointsuccessesvsnone0/40:predeclared32/8/24screenpasseswithoutcase
deletion. Fullhas35common-helperprograms,buttimeouts-sharedandgate-download-count
keepoldincorrectboundary;fiveothersrequestunnecessaryapproval(new-upload-size,
new-percentage,new-file-extension,new-window-seconds,gate-job-window). Thus33
actualcorrectsharedchanges. None39/40functionalpatches,all40duplicatevalidation;
page-sizeclampsratherthanrejectingabove100. No caps,allEOS. All80responsesread
manuallybeforecandidateexecution. Full28historicaltargetquestionsjoint23/28,
long-prefixslice10/12. Small drift vs earlierfull10/12functional/11structure
long-prefixresultsnotcherrypickedaway. Newtargetfunctionalitycheckedmoreexplicitly.

This is a workable40caseDEVELOPMENTdiagnostic,notapristevalidationclaim:28cases
wereretainedinhistoricallyselectedbank,and12alreadyseenwithcompressedoutputs.
No current4k/8koutputsusedtoaccept/rejectthenew40casebaselinegate;don'tclaimthe
questionshadneverbeenseenwithcompressedmodels. Next:scorebothfixedcacheson
all40withouteditingcasesorscoring. No extra search if candidates score poorly.

## Final recovered-bank results

| Metric /40 | Full | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Common private helper structure | 35 | 0 | 20 | 38 |
| Finite functional assertions | 33 | 39 | 19 | 37 |
| **Correct shared-rule implementation (both)** | **33** | **0** | **18** | **36** |

| Original question source: joint success | Full | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Historical targeted refactors /28 | 23 | 0 | 13 | 24 |
| Original long-prefix refactors /12 | 10 | 0 | 5 | 12 |

Bothbaselineandcandidaterunsusedidenticalfrozen40questions,prompt/artifact/source
identity,768tokens,EOSprotocol. All160EOS,nocaps. CandidatePID1680000completed
287.437s,2026-10-17T16:26:31Z. Baseline348.177s;sum635.615s(10m35.6s),including
two model loads but excluding one-time weight-hash freeze and CPU preflight.
All40questionshavezeroexacttextoverlapwith812calibration;samepolicy/templates
aretrained,sozerooverlapdoesnotestablishindependenceorabsenceofoverfitting.

Fullhasfivefalseapprovalpausesandtwoboundarybugs.4khas19falseapprovalpauses,
oneunsharedcorrectpatch(batch-size),onewrongclamp(page-size),andonezero-boundary
bug(download-count).8khasonefalsepause(file-extension),oneunsharedcorrectpatch
(sort-direction),andtwocodefailures(timeoutstillallowszero,page-sizeclamps).
Noneimplements39correctpatchesbutduplicatesvalidationeverywhere.

Why8kexceedsfull33→36:fourfullfalsepausesbecomevalidsharedimplementations,
download-countbugfixed;twofullsuccesseslost(page-sizeclamping,sort-direction
duplication). Timeoutbugandfile-extensionpausepersist. Thisdoesnotestablish
general8ksuperiority;keepallgains/lossesanddon'tfilterforfullwins.4kvsfull
0jointgains/15jointlosses. Fullfunctionalaccuracy33<none39showsfunctionality
andprojectbehaviorareseparatemeasurements,notinconsistentgrading.

## Interpretation and limits

This40casedevelopmentbankcleanlyseparatesfullcontextfromnoneundertheactual
longprompt,asrequested;itrestorestheworkingtaskformratherthannewv3rewrites.
Thephrase"bothintentionallyimplementthesamerule"ispartoftheoriginalquestion,
notanewhelperinstruction;systempolicyrequireshelperextraction. Removingthat
phrase/changingfunctionnameschangedthetestforminv3;nomatchedablationisolates
whichwordingcauseddifferentoutcomes. Don'tclaimacausefromseparatebanks.

Oneoldquestionasks"cappagesizeat100";theoriginalmetadataexpectsrejection,
whileclampingislinguisticallyplausible. Preserveoldbytes/gradingandall40results,
flagthelimitationinsteadofsilentlyrepairingit. Manualreviewnotblindorindependent.
Onlyoneshared-rulepolicytested;noapprovalcases,noclaimaboutgeneralcomplianceor
over-refactoring. Older53bankwasposthocselected;historicalcasesareinspected,
compressedmodelsalreadyseenonsomequestions. Thisisnotfreshheldoutvalidation.

No case removal after full/none screen or candidate scores. Current bank accepted
usingfull/noneonlybeforecurrentcandidateoutput. Rawrecords,freeze,preflight,
per-responsesourcehashes/manualrationaleallretainedasTRANSPLANT_REFACTORS_V4_*.json.
Alljobsfinished,noextraevaluationsearch,training,cachepromotion,runtimeedits,
publicpushor4Bfit. Use this as active targeted behavioral diagnostic;keepv1–v3
reports as historical evidence rather than competing headline benchmarks.
Verification:sevenlocalregressionchecks passed,all160manualresponsehashesand
automatichelperdiagnosticsrechecked. Completedcandidate-runresumeverifiedfrozen
source/artifacthashesandreturnedAlreadycompletewithoutmodelloadorgeneration.
