# Publication readiness — updated 2026-10-20

Current status: experiments and technical release validation complete;
**published with an exploratory disclaimer** at
[arpicato/qwen-kv-compiler](https://github.com/arpicato/qwen-kv-compiler).
The user authorized creation and push of the audited snapshot on 2026-10-19,
then authorized the allocation follow-up update on 2026-10-20. That update was
pushed after export and diff checks; public main was
`076e25688479fb07577cae7ffd141d68f8044b10` at the last verified check.
The README edit after that checkpoint is local and has not been published.
The old proposal in `FINAL_PUBLICATION_PLAN.md` was approved and executed; its
chronology is retained, not permission to launch additional experiments.

| Gate | Status / evidence |
|---|---|
| Final240case definition/preflight/freeze | Complete; final inputs,120positive/120negative checks, overlap ledger |
| 27B final behavior | Complete480responses, allEOS, response-bound review; knowledge/tools reused with same prompt/cache identity |
| Controlled4B | Complete901capturetargets,3fits,5arms/1200responses,600behaviorreviews; full fails target behaviors |
| 27B AM | Complete4k; originalFP16 8kfailure retained; separate64headFP32V8k/240cases complete |
| Equal-row head allocation follow-up | Complete960responses/480newbehaviorreviews; FP16failure preserved, separateFP32Vextension; `NONUNIFORM_RESULTS.md`, audit and wall times |
| Equal useful-byte cap follow-up | Complete480freshAMresponses/240newbehaviorreviews; compilerexplicitlyreused; 256MiBcap, allocation/artifact audits, 256headimplementationrecheck and wall times in `EQUAL_MEMORY_RESULTS.md` |
| Public-clone reproduction extension | Fresh27B19phases/finalgeneration/hash audit complete; its separatebehaviorreview pending, freshAM/4Breproduction deferred. Not a completed all-method public-clone reproduction |
| Public docs/current verifier | Updated; final240default, bothstudies/AM, separate provenance and narrow claims |
| Git-free package / Docker | Passed29CPUfiles and120positive/120negative checks from a freshly built pinned image; exact source inventory/secret-signature scan passed |
| Isolated runtime install / short inference | Passed: fresh install6,826s, checks1,609s; compiler4k/8k, AM4k/FP32V8k, allfive4Barms and completed resumes. Evidence: `RELEASE_RUNTIME_SMOKES.json`; initial failure retained |
| Independent behavior review | Not performed. User selected publication with an explicit exploratory/AI-assistant/unblinded disclaimer instead; README and main report disclose this. Optional review packet retained |
| Privacy/license/public archive | Audited source snapshot published with user approval; no weights/caches or operational notes. Notices retained; audit is not legal certification |
| User approval and public upload | Initial release and allocation follow-up authorized and pushed; clean public history, not the private development branches |

Supported claims: static-prefix compression on this pinned 27B target; observed
tool/sharing/gating tradeoffs versus off-policy uniform AM, with precision/backend/
memory differences explicit; separate controlled4B knowledge/tool comparison.
No pooled overall winner, equal-compute or equal-process-VRAM claim, pristineholdout, general
policy retention or safety, or cross-model causal comparison. Full4B behavior
failure blocks compressed-retention claims. More seeds/holdouts are not required
to publish these narrow findings but would be needed for broader claims.
The new follow-up supports a matched **useful-prefix payload cap** comparison
only (AM11,392bytes below256MiB), with padding/placeholders/precision explicit.
Its task and behavior tradeoffs do not establish an overall size/method winner.

Current evidence: `FINAL_EVAL_RESULTS.md`, `CONTROLLED4B_RESULTS.md`,
`AM27B_RESULTS.md`, `AM27B_FP32_RESULTS.md`, `REPRODUCTION27B_RESULTS.md`.
Allocation additions: `NONUNIFORM_RESULTS.md`, `EQUAL_MEMORY_RESULTS.md`, their
raw/review/summary/freezes/allocations/audits/timing and implementation recheck.
Historical raw/freezes/scores and failed pilots remain unchanged. `RELEASE.json`
identifies current shipped bytes, not replacement identities for historical runs.

User chose the disclaimer route on 2026-10-19; this does not establish independent
agreement or change any score. Source-prompt notices and provenance limitations
remain, including the unrecorded OpenCode instruction revision. Audit is not a
legal certification or a certification of the unshipped private Git history.

## Allocation follow-up upload record

2026-10-20 checkpoint: reader-facing links/scope corrected; current Git-free
595-file / 594-hash export passed exact inventory and credential-signature scan,
and all32small-dependencyCPUtestfiles passed in the existing isolated CPU env
(GPU not used). Local system Python initially lacked NumPy; that environment
failure is not a passing full-suite run. Targeted local result/evaluator/release
checks passed. Log: `/tmp/opencode/publish-followups-cpu.log` on XTX.
Final public-diff review excluded an unrelated storage-maintenance report from
the release inventory (local record preserved): final export is 594 files /
593 hashes. No operational instruction files or private Git history are included.

- Keep exploratory/assistant-unblinded/one-seed/inspected-case qualifications and
  explicit reused results; no further GPU experiment is required for these claims.
- Export only the current `RELEASE.json` inventory; rerun saved-evidence tests,
  exact Git-free inventory/hash/credential-signature checks and CPU suite on that
  export. Do not ship `AGENTS.md`, operational notes, private Git history, models,
  caches or credentials. Existing license/source-prompt notices remain required.
- The allocation update was pushed from a clean public checkout after the user
  approved it. Later edits need their own diff review and approval before push;
  never push the private development history.
- Independent behavior review, further seeds/holdouts and completing deferred
  public-clone reproduction are optional stronger validation, not work already
  completed. Do not advertise those as passed gates.
