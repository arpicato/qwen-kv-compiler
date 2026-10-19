# Publication readiness — 2026-10-19

Current status: experiments and technical release validation complete;
**published with an exploratory disclaimer** at
[arpicato/qwen-kv-compiler](https://github.com/arpicato/qwen-kv-compiler).
The user authorized creation and push of the audited snapshot on2026-10-19.
The old proposal in `FINAL_PUBLICATION_PLAN.md` was approved and executed; its
chronology is retained, not permission to launch additional experiments.

| Gate | Status / evidence |
|---|---|
| Final240case definition/preflight/freeze | Complete; final inputs,120positive/120negative checks, overlap ledger |
| 27B final behavior | Complete480responses, allEOS, response-bound review; knowledge/tools reused with same prompt/cache identity |
| Controlled4B | Complete901capturetargets,3fits,5arms/1200responses,600behaviorreviews; full fails target behaviors |
| 27B AM | Complete4k; originalFP16 8kfailure retained; separate64headFP32V8k/240cases complete |
| Public docs/current verifier | Updated; final240default, bothstudies/AM, separate provenance and narrow claims |
| Git-free package / Docker | Passed29CPUfiles and120positive/120negative checks from a freshly built pinned image; exact source inventory/secret-signature scan passed |
| Isolated runtime install / short inference | Passed: fresh install6,826s, checks1,609s; compiler4k/8k, AM4k/FP32V8k, allfive4Barms and completed resumes. Evidence: `RELEASE_RUNTIME_SMOKES.json`; initial failure retained |
| Independent behavior review | Not performed. User selected publication with an explicit exploratory/AI-assistant/unblinded disclaimer instead; README and main report disclose this. Optional review packet retained |
| Privacy/license/public archive | Audited source snapshot published with user approval; no weights/caches or operational notes. Notices retained; audit is not legal certification |
| User approval and public upload | Authorized and completed2026-10-19; clean public history, not the private development branches |

Supported claims: static-prefix compression on this pinned 27B target; observed
tool/sharing/gating tradeoffs versus off-policy uniform AM, with precision/backend/
memory differences explicit; separate controlled4B knowledge/tool comparison.
No pooled overall winner, equal-compute/memory claim, pristineholdout, general
policy retention or safety, or cross-model causal comparison. Full4B behavior
failure blocks compressed-retention claims. More seeds/holdouts are not required
to publish these narrow findings but would be needed for broader claims.

Current evidence: `FINAL_EVAL_RESULTS.md`, `CONTROLLED4B_RESULTS.md`,
`AM27B_RESULTS.md`, `AM27B_FP32_RESULTS.md`, `REPRODUCTION27B_RESULTS.md`.
Historical raw/freezes/scores and failed pilots remain unchanged. `RELEASE.json`
identifies current shipped bytes, not replacement identities for historical runs.

User chose the disclaimer route on 2026-10-19; this does not establish independent
agreement or change any score. Source-prompt notices and provenance limitations
remain, including the unrecorded OpenCode instruction revision. Audit is not a
legal certification or a certification of the unshipped private Git history.
