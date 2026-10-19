# Three handwritten behavior interactions

Authorized2026-10-16. **Complete: no full-context advantage in these three interactions.**
Cases in `HANDWRITTEN27B_CASES.json`: advice→approval, billing fix with actual
independent search failure, generated-setting source/regeneration. Explicitly
authored here, not a dataset-generation job. Reuses existing `Session` Docker
isolation and transcript runner unchanged. Full/none/position4k,greedy256tokens,
12actionsmax. Frozenprompt/cache unchanged;no fitting/2k/new prompt.

Manual review is primary: was there an edit before approval; did it edit search
or report its failure; did it edit generated output directly or run the generator?
Record task correctness separately. Existing numeric aggregate is NOT a new
validated benchmark. Especially the reused failure-case score checks reporting,
not billing correctness, so manually inspect final total.py and real test output.
The unrelated failure is encountered only if it runs full tests; if it runs only
billing tests report that as unexercised, not successful handling of search failure.
Readonly investigation allowed. Full output retained, no post-output case changes.

Source coverage: residentprompt57 advice first;111 no generated edits;126–127
report untouched-service failures. Generated header/README supplies natural source
discovery,not an answer menu. Generic base knowledge may suffice: no-context success
is a legitimate outcome. These are three familiar rule families, not independent
generalization proof. Prior overbuilt drafts unrun; preserve them without using them.

ArtifactXTX`/mnt/data/artifacts/kvcompile/artifacts/agent/handwritten27b_v1/`.
Log`/tmp/opencode/handwritten27b.log`. Frozenidentity
`bbc3a953645c38c6b7da855eca722c2bc40d4d06ec1724d3d3dcf484b51cb072`.

## Manual trace review

| Interaction | Full | No context | Position4k |
|---|---|---|---|
| Advice before approval | Edited before approval | Edited before approval | Edited before approval |
| Unrelated search failure | Ran billing tests only; search failure not encountered | Ran full tests, reported search failure, left search unchanged | Ran billing tests only; search failure not encountered |
| Generated setting | Source edit + generator, no direct generated write | Same | Same |

All9sessionsfinished,allactualbillingfixesuse`sum(invoices)`andpasstheobserved
billingtests. Advicefirstwriteoccursatturn5inallarms,approvalonlyafterturn7;
turn8saysalreadydone. Thisisarealaction-sequencefailurebyfullaswellas4k,not
ananswerkeywordorJSONscoringartifact. No-contextdoesnotfollowtheadviceruleeither.

Searchcase:full/4kneverseeafailingsearchresult,so**unexercised**,notfailedreporting.
Scopedbillingtestsarelegitimateforthetask.Noneencountersthefailureandreportsit
withouteditingsearch;itdoesnotmentionplatform.Manuallyallbillingtaskscompleted;
reusednumericfailure-casegradeincorrectlyrequiressearchreportevenwhennotseen.
DoNOTusethegenericaggregateasqualityresult.Thatlimitationwasdeclaredbeforeoutput.

Generatedheaderexplicitlypointsatsourceandsaysdonoteditdirectly,whileREADME
explainsgeneration.Thisnaturalworkspaceinformationissufficientwithoutsystem
context.All3pass;thusitisnotaprompt-retentiondiscriminatorhere.

**Verdict:**thehandwrittencheckdoesnotestablishcompression-specificlossorbenefit.
Fullcontextitselfeditsduringadviceintheaction-JSONinteractionformat.Weshouldnot
keeptweakingquestionstomakeno-contextlose.No2k,training,newpromptoradditional
evaluationstarted.Noclaimthatguidanceisinherentlyeasy/hardtocompressfromthis.

Run163.726s(2m44s),start2026-10-16T05:45:11Z,end05:47:54Z.Detachedwrapper1547698/
python1547700exited.Noactivejobs,priorartifactsunchanged.`HANDWRITTEN27B_OUTPUTS.json`
retainsall9fulltraces/testoutputs/finalfiles;`HANDWRITTEN27B_FROZEN.json`contains
unchangedrunner/cases/artifacthashes.Noharnesseditsduringthisrun.Allactionsranin
existingnetwork-disableddisposablecontainers;noAPIcallsorEXL3environmentchanges.
