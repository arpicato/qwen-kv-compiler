# Rebuilt targeted behavior bank

User requested a cleaner bank after rejecting nondiscriminating/ambiguous tests.
Scope:40naturalnonmonetaryvalidationchanges;noapprovalcases,helperhints,
solutionfragmentsorapproved/distinctcontrols. Prior raw/results immutable.

Source `scripts/prepare_natural_refactors.py`; cases/rubric/evidence and authored
references in `inputs/natural_refactors_v3/`. Only question text is model-visible.
Eight groups: numeric,text,path,collection,mapping,compound,stdlib,protocol.
Each changes actual validation shared by two public entry points. Natural wording
and names vary; same underlying source instruction, not40policyfamilies.

Report structure, functional assertions and their intersection. No whole-agent
or over-refactoring claim without contrast controls. Disclose scope narrowed after
v1/v2 outcomes; do not discard old evidence or select cases by full/none advantage.
Manual review required; existing primary/secondary-only helper diagnostic is not
valid for these function names. No model outputs or training in this checkpoint.

Preflight complete: syntax/signatures/boundary counts/absence of implementation
hints/exact question non-overlap checked automatically. Isolated Docker executed
all40referencesand40unchangedbuggycontrols:allreferencespass,allnegativesfail.
Reference tests include newly accepted inputs as well as newly rejected inputs;
accepted outputs are checked against preserved original return expressions,
without accidentally retaining the old rejection rules. Cases use varying public
names and both one-argument and compound-argument functions. Stdlib format cases
cover actual date/IPv4/JSON validation, not keywords or names.

Source checkpoint `839eb95`;preflight records in NATURAL_REFACTORS_V3_PREFLIGHT.json,
source/input identity in inputs/natural_refactors_v3/manifest.json. Logs at
`/tmp/opencode/natural-refactors-v3-preflight.log`. All checks CPU/Docker only;
no GPU job launched, no runtime/model/cache changes. Old evaluation files intact.
User explicitly authorized execution. Source03e17bfadds named-function helper
diagnostics to existing runner (old defaults unchanged) and adapts the40casebank
without altering question/reference bytes. Launchwrapper1654519,log
`/tmp/opencode/natural-refactors-v3-run.log`,outputnatural_refactors27b_v3.
Full/none/joint4k/joint8k,160records,1536tokens,greedyEOS. Freeze verifies model
and all source/cache identities before first output. No new debug split:existing
generation transport previously exercised;40positive/40negativecodechecks and
named-function regressions passed before launch. Not gated on full-context success.
4B fitting remains paused. Manual output inspection completed after generation.

## Final results

| Metric /40 | Full | None | Joint4k | Joint8k |
|---|---:|---:|---:|---:|
| Common changed rule in one private helper | 14 | 0 | 10 | 9 |
| Finite functional assertions passed | 38 | 37 | 37 | 37 |
| Both structure and functional assertions | **13** | **0** | **10** | **9** |

All160responsesfinishedEOS,nocaps. Run603.791s(10m03.8s),completed
2026-10-17T16:04:23Z. Source03e17bf,freezeSHA256
ecf8ac4c9f9ef8f8ebf3aef1db036b9be37ccce77c050e121190d58ea9629cce.
Samepublication-source27Bteacher/4k/8kcaches,noextraGPUworkortraining.

Manualinspectionofall160programsconfirmshelperdiagnosticsforthesecases,not
generalvalidityofASTgrading.4kascii-digitsusesaprivatepredicatewithlocalraise
plumbing:theactualruleiscentralized.4krelative-pathcentralizesnewparent-segment
checkbutleavesoldabsolute-pathchecksincallers:countschanged-ruleadherence,
notcompletevalidationcentralization. Sharedregex/stdlibcallswithoutprivatehelper
do not satisfy the stated project instruction.

Full functional failures: duplicate-values iterates dict keys as(name,destination)
pairs rather than values/items;JSON-object returns decoded objects/lengths instead
of preserving original text/length. None/4k/8ksharethosetwofailuresandalsoallow
nonbreakingwhitespacewithASCII-onlystring.whitespace. Full'sbrokenaliashelper
countsstructurebutnotjointsuccess. No unnecessary approval pauses observed.

Fullcontextonlyfollowshelperpolicy14/40here:thebankdoesnotestablishrobustfull
compliance.4k/8karepartialandnotorderedmonotonicallybybudget;9vs10doesnot
establishgeneralbudgetinversion. None solves most functionalchangesbutnever
centralizesthevalidation. This demonstrates a bounded structural difference, not
general agent safety/compliance. All26fullstructurefailures/tiesremain;nocase
wasremovedbecausethemodeldidnotbehaveaswewanted.

## Limitations exposed by inspection

Functionalassertionsarefinite,notcompletecorrectness:regex$canacceptafinal
newlineinhex/tokenresponses,butfixturesomitthatboundary.Someconfigresponses
addworkerrestrictionsbeyondrequestedshape;fixturesdon'tcoveralloriginalworker
values. Full/8kexclusive-optionsuseis-not-Noneratherthankeypresence,andfixtures
don'tcoverpresentNone. No posthoc test repair/regrade or model rerun was done.
Retain these limitations instead of presenting38/40asproof38fullycorrectprograms.

Fortyrelatedproblemsstilltestoneprojectrule,eightgroupsarenoteightindependent
policies. No distinct-contract controls,soover-refactoringisnotmeasured. Cases
wereauthoredbeforev3outputsbutfocuswaschosenafterv1/v2;notapristineholdout.
Revieweristheauthoringassistantwitharmlabelsvisible,notindependenthumanreview.
Referencesandcheckingmetadataareneverpassedtomodels;onlynaturalrequestq.

Rawresponses,freezeandmanualper-responserationale/hashare
NATURAL_REFACTORS_V3_{RAW,FREEZE,REVIEW}.json. Oldresultsuntouched. No scored
rerun,fit,cachepromotion,publicpushor4Btraining. BothjobPIDsfinished.
