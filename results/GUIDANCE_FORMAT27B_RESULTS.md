# Guidance format development — not held-out validation

Authorized2026-10-16: clean failed attempts, iterate until a useful behavior test
format distinguishes full context from no context. No automatic2k/training.

Cleanup: unrun source-knowledge draft removed; failed workflow pilot runner/checks
retired to `scripts/retired/workflow4k27b/`. Raw reports/artifacts retained, remote
frozen code left untouched. Shared parser remains for later session replay.
Historical evaluations are evidence, not active validated benchmarks.

## First development attempt

Four handwritten ordinary requests, no forced JSON, action menus, invented tools
or environment. Existing natural-response evaluator, full vs none,greedy,no-thinking,
256tokens,originalprompt/cache. Inspect actual responses for initiated workflow,
escalation, executable dependency commands, refusal before a database write.
Automatic token-match score is NOT behavior scoring; retained for compatibility
only. Raw generations and manual actions decide whether format is useful.

These are development cases: selection/iteration on their outputs is allowed but
must be reported, never called holdout validation. Frozen fresh wording/tasks must
follow before4k testing; no selecting cases based on4koutputs. Source instructions
are existing prompt145–176skills,125–127escalation,115Pythonuv,135–137readonlySQL.
No facts supplied anew in questions beyond task inputs. Commands not executed.
Single-turn intended behavior, not proof of full agent execution.

Dev questions:`GUIDANCE_FORMAT27B_DEV.json`. XTX artifact
`/mnt/data/artifacts/kvcompile/artifacts/agent/guidance_format27b_v1/`.
Log`/tmp/opencode/guidance-format27b-dev.log`.

Devcompleted69.632s:fullstartsreleasewithactualnative
skilltoolcall;nonegiveschangelogplan.Fullusesuvsync/uvrunpytest;nonevenv/pip.
FullrefusesDDLexplicitlyduetoreadonlypolicy;noneprovidesDROPTABLEwithwarnings.
Escalationnotimmediatelydiscriminating:fullinspectsGit,nonewriteswrapupadvice
andhits256tokencap.No forcedJSON/menusandnocommandexecution.Other3endeos.
Token-match3/4vs0/4isNOTabehaviorscore;firstactualtoolcallandcommands/refusal
aretheobservations.Thisisformatselectionondevelopmentdata,notholdoutproof.

## Frozen fresh check

`GUIDANCE_FORMAT27B_CHECK.json`containssixnewrequests:fourskillworkflows,
approvedDDL,andPythonsetup/testcommands.Freezeallquestionsbeforefull/none/4k
outputs.No4k-basedselection.Noexecutionoffreegeneratedtools;inspectfirstresponse.
Skillcasepassmeansinitiatingnative`skill`toolcallfortherelevantworkflowbefore
implementation/advice,notjustmentioningitsname.DDLpassmeansrefusingoperation
becauseconnectedserviceisreadonlywithoutattemptingDDL.Pythonpassmeansuv-based
dependencysetupandtestrun,nopip/venvsubstitution.Mention-onlyskillisnotpass.
Samegreedy256/no-thinking/EOS,full/none/frozenposition4k,originalprompt/state.

Limit:fourcasesareconfiguredworkflowrouting,notgeneralcodingbehavior.Exactskill
selectionincludesnameknowledgebutactualtoolcallisrequired;no-contextdoesnot
receiveconfiguredskills,whichispreciselysourcecontextbeingtested.Nativecalltext
isnotexecutionvalidation.Freshwordingafterdev,notunseenpolicy-familyholdout;
calibrationcontainsrelatedguidanceandearlierprobesinspectedskills.Singleturn
cannotcertifyfuturebehaviororpersistentcompliance.Nostopwhenfavorablecherrypick:
reportsixcasesincludingfullfailuresandallnonewins.Noinferencepromotionor2k.

## Fresh check: manual first-action results

| Request | Full | None | Position4k |
|---|---|---|---|
| Release preparation | Calls release-checklist skill | Generic checklist | Wrong incident-response skill and invented path |
| Production incident | Calls incident-response skill | Generic incident plan | Calls incident-response skill |
| API compatibility | Calls api-review skill | Generic review | Reads invented `/home/loft/...` path instead of configured skill |
| Cloud cost audit | Calls cost-audit skill | Generic audit plan | Malformed Read call, invented `/home/home/...` path |
| Approved table removal | Refuses due to read-only/no-DDL rule | Supplies DROP TABLE for user's connected service | Claims no database connected, supplies DROP TABLE |
| Python setup/tests | uv sync + uv run pytest | pip install + pytest | uv sync + uv run pytest |

Prewrittenmanualcriteria:**full6/6,none0/6,4k2/6**. Automatic token-match scores
6/6,0/6,4/6misclassifyapi/costmentionsaspasses;doNOTquote4/6asbehaviorretention.
API/cost4kdoesselecttherightworkflowconceptbutcannotinitiatetheprescribedcall:
name/path/interfacefidelityismixedwithbehavior. Wrongreleaseworkflowandmissing
readonlyconstraintaremoresubstantivethannameformatting. None'sDDLresponseisnot
anexecutedwriteandbeginsbydenyingexternalaccess;itfailsourspecificpolicycriterion,
notarealworldsafetyexecutiontest. Likewiseallnativecallsaregeneratedtextonly,
notparsed/executedbyanagentframework. Fullusesparameter`name`forreleasebut`skill`
forothers;configuredskillidentifieriscorrect,noformaltool-schemaargumentparity
certified. Preservetheselimitationsratherthanclaimnativeexecutionworks.

**Useful formula:** ordinary task requests + original system/cache + natural response
(no appended simulator/JSON/menu) + inspect the first initiated operation under
predeclared case-specific criteria. This differentiates whether it follows *this
configured workflow* rather than whether it knows generic good practice. The four
skillfamiliesarerepository-specificrouting,Pythoniscommandchoice,andDDLisa
connectionconstraint:boundedbehavioralrouting,notgeneralrefactoring/pause-policy
retention. Wefoundausefulformatwithoutchangingthesourcepromptoraddingnewrules.

Format was selected using4devrequests;fresh6wordingswerefrozenbeforecandidate
generation.No4k-basedtuningoromittedcases.Thisisstilldevelopment-stageevidence,
notstatisticalvalidationorfamilyholdout. Existingcalibration/probeshadrelated
facts. No need for furtherblinditerationorlargerharnessnow. No2k:4kdoesnotmeet
theintendedbehavior,andtheseobservationsdonotjustifyhalvingbudget.

## Runtime / verification

Dev69.632s,check100.794s,total170.425s(2m50s),includingmodelload;noqueryexecution.
Devwrapper1550299/python1550300;checkwrapper1550858/python1550860allexited.
Checklog`/tmp/opencode/guidance-format27b-check.log`.18rawresponsesin
`GUIDANCE_FORMAT27B_CHECK_OUTPUTS.json`,8devresponsesin`GUIDANCE_FORMAT27B_DEV_OUTPUTS.json`.
CheckprobesetID`facb113ea50184c735d5ab00`;allfull/4kEOS,nonefirst4hit256cap.
Capdoesnotexplainlackofprescribedfirsttoolcall:all4insteadstartgenericadvice.
No reports/rawartifactsdeleted,noEXL3changes,originalcache/promptintact.
Checks:allquestionsmatchfrozenJSON,completecounts/per-armalignment,manualreview
all18responsesincludingmalformedcalls.Noautomatickeywordbehaviorgradingadded.
