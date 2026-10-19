# Query-position re-audit: current purpose780 captures

**Complete; audit only.** Replayed selector using actual27Btokenizer and verified
selected absolute positions/row counts against all780×16saved trajectories shared
by8k/4kfits. No GPU/model forward,recapture,training,backend change or new testsuite.
Final pass25.801sCPUincluding allshardverification. Implementation70b9e97.

Earlier ANSWER27B_DIAGNOSTIC measured output ranks under forced answers; coverage
audit measured supervised field presence. Neither establishes current calibration
row coverage. Search of current reports found no equivalent saved780positionaudit;
this does not claim no historical audit ever occurred.

## Measured coverage

| Training group | Examples | Exact-name token positions with preceding query | EOS positions with preceding query |
|---|---:|---:|---:|
| Original policy/etc | 71 | Not name-tagged by this audit | 66/71 |
| Existing tool selection | 268 | 484/2415 | 63/268 |
| Existing required-argument answers | 137 | 722/2309 | 7/137 |
| New purpose→field | 304 | **481/482** | **304/304** |

Exact-name labels use fully-qualifiedtool strings and schemafieldnames in scoped
answers. Repeated mentions counted;toolnamespace fragments included in name-token
counts. Not a semantic label for all useful prose or alloriginal71facts.

**All304purposefield starts are covered.** One uncovered interior fragment:
`bypass_actors`tokenizesbacktick,b,ypass,_,actors,backtick. Selector skips standalone
`_`,so query before`actors`is missing. Newfield failures therefore cannot generally
be explained by missing field-start query rows. CapturedEOS input is not the same
as capturing the query precedingEOS;newgroup has both,oldgroups often do not.

**0/268tool-specific name starts have preceding query captured** in268selection
examples. Every fully-qualifiedtool uses namespace`mcp__github__`;thetokenjust
beforethetoolleaf is`__`,which selector excludes aspunctuation. Across405older
examples0/404toolleaf occurrences have precedingquery;not necessarily absence of
allother useful queries inthat example. Atwholequalified-name starts89/432selection
occurrenceshaveprecedingquery,stillnoneatthetool-specificleafboundary.

All137required-argument examples miss at least one namedentitystart(qualifiedtool
orfield);only139/1078entitystartscovered. Manycapturedrowsareinitialprose rather
thanlatefieldlists. Exampleitem72:`The exact tool that gets a specific discussion
by ID is: ...mcp__github__get_discussion`;positions[-1,0..9]captureintro,nottoolname.

## Why this happens

`scripts/capture_agent_exl3.py:choose_positions`chooses up to10**consumed-token**
positions bydecoded-contentheuristic,including substringhints like`use`,`commit`.
It excludespunctuation-onlytokens andprefers earlycontent. It alsoalwayscaptures
thelastuser-turnrow(-1relativeanswer). For tokenj,thequeryatjhasalreadyconsumedj;
it precedesnexttokenj+1. Selectingmeaningfultokenj doesnotselectthedecisionbeforej.
Thusselecting`actors`or`get_discussion`isonepositiontoolatefortheirfirstfragment.

Compilerfitslocalattentionoutputs atthesequeries,notlogits/answerCE. Anuncaptured
precedingrowdoesnotprove nootherrowconstrains thatbinding,or that tokenprediction
is trained incorrectly. Off-by-one here describes measurement/selection intent,
not a demonstrated corruption of capturedQ/KV or causal masks.

Per-example row weights equal1/Lq;pergroup quotas24eachgive groupweight1/3.
Innew304,27.38%of rowweight precedesexactfieldtokens,18.16%EOS,54.47%punctuation/
whitespace. Inselection268,20.15%precedesqualified-name tokens,66.94%othertext,
10.09%punctuation,2.82%EOS. These are **row weights**,not measured gradient norms,
loss magnitudes or information importance;punctuationqueries canretrieve useful
context. Do not declare allnon-nameweightwasted.

## Recommendation, not executed

One bounded next experiment: for existingtoolselection/requiredfieldcalibration,
choose rows **before** exacttoolleaf/fieldtokens and beforeEOS,includingpunctuation
predecessors;retainlastuserrow,original71coverageandfixedper-example rowcap.
Keep780Q/A,4096slots,sampling/updatebudget andevaluationunchanged;verify position
coverage before a costlyrun. State the priority rule for answers with more than
10candidatepositions;do not silently usealltokens/increasequerycompute. This
requires freshselected-querycapture,not merelyrelabelingstoredarrays.

No need for variable-length-per-layerbackendfeature;installedartifactlayout stays
4096rows/layer. No8k→4kteacherexperiment or unevenallocationwork started. This is
a testable selection lead,not proven quality gain or generalization evidence.

RawXTXartifact:`purpose4k27b_v1/query_position_audit.json`containsall780decoded
answersandpositions. Local [QUERY_POSITIONS27B_AUDIT.json](QUERY_POSITIONS27B_AUDIT.json)
retainscounts/rowweights,manifesthash,examples. CPUcheck
`scripts/test_query_positions27b.py`coversconsumed/predictedalignment,namespaceleaf
boundary,andEOSinput-versusprecedingquery. Noactivejob.
