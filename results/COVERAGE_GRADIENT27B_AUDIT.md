# Development coverage and frozen27B KV-gradient feasibility

Authorized2026-10-15. Audit only; no new data, optimization run or budget change.

**Complete.** Coverage alone is not an established fix; final-answer KV training
is blocked in the installed EXL3 autograd path. No active GPU jobs or backend
changes. Original artifacts and unrelated user edits untouched.

## Development coverage

Audit exact field names within tool-scoped supervised answers, and exact source
descriptions after lexical normalization. Required-field lists count as name-only
unless they include the source description. Reverse field→purpose supervision is
reported explicitly,not confused with tested purpose→field retrieval. Paraphrases
may be missed; this is not certification of semantic coverage.

Latest own-target artifact uses476inputs:13/194devfailures=2selection+11fields.
Of11failed fields,9have no explicit field answer,2name-only,0exact-description.
Across all132field probes:61no explicit answer(9fail),46name-only(2fail),25source
description(0fail). Sources are original476manifest,not abandoned143data.

Bindings780artifact:18/194devfailures=5selection+13fields. Of13failed fields,
11already have exact source description answers(all reverse-direction bindings),
1name-only(resource_id),1absent(ghsaId,on deliberately excluded reserved tool).
Across all132fields:119description(11fail),10name-only(1fail),3absent(1fail).
Selection names present51/62(absent11); lexical name presence is not a match of
intent semantics. No stress/testquestions used to propose new training rows.

**Interpretation:**476still has gaps,but filling them in reverse direction has
not guaranteed retrieval. No recommendation for bulk expansion from these
counts. A forward-direction gap test would be a distinct experiment,not yet run.
Files `DEV_COVERAGE476_AUDIT.json`,`DEV_COVERAGE780_AUDIT.json`retain each dev
question/prediction,classification and exact source row indices. Checks
`scripts/test_audit_dev_coverage27b.py`passed.

## Gradient feasibility protocol

Read/run EXL3/shared environment only. Public model.forward/prefill are decorated
torch.inference_mode; do not assume removing decorator makes custom kernels
differentiable. One existing training question(original row0),no evalquestion,
no optimizerstep. Last fullattention layer63,first32value-cache rows receive a
zero-valued autograd leaf (32768scalars),preserving forward values. Compare
native,public-with-leaf,and in-memory unwrapped-forward-with-leaf; record logits
parity,CErequires_grad,and finite nonzero gradient if available. No patches to
EXL3sources,weights or environment. If graph breaks/errors,report blocker; do
not launch speculative backend rewrite or treat missing gradient as quality result.

Probe `scripts/probe_kv_gradient27b.py`,atomic stage checkpoints. XTX artifact
`/mnt/data/artifacts/kvcompile/artifacts/agent/gradient_audit27b_v1/probe.json`;
log`/tmp/opencode/gradient-audit27b.log`. No gradient result yet.

## Measured gradient result

Completed39.451s; native first-token argmax63. Public-with-leaf and unwrapped
forward both preserve that argmax;logitmaxdifferences0.0234375and0.01953125,
consistent with previously observed runtime variability,not bit-exact parity.
The32768-scalar last-layer value leaf is an ordinary requires_gradTensor,not
an inference tensor. Yet both forwards produce logits.requires_grad=False and
CE.requires_grad=False. Public logits are inference tensors;unwrapped logits
are ordinary tensors but still disconnected. No gradient exists to optimize
in this tested path; no backward or optimizer update was attempted on a
disconnected loss. Raw evidence [GRADIENT27B_PROBE.json](GRADIENT27B_PROBE.json).

This is a runtime feasibility blocker,not a claim that final-answer objectives
are mathematically impossible. Bypassing only outer inference_mode does not
restore autograd through custom inference kernels/in-place paths. A supported
differentiable backend or explicit backward implementations would be a separate
engineering task. No such rewrite is authorized or silently begun here. Probe
tests only a last-layer value slice on one trainquestion;not all KV/model paths,
and makes no claim of finite-difference or backward parity.

## Recommendation after audit

1. Do not bulk-expand reverse-direction bindings:11/13field errors in780already
   have exact source-description supervision. The compiler still fits local
   attention outputs,not these answers directly.
2. For a low-engineering next experiment,test one ordinary476budget increase
   8192→12288rows(512→768MiBoccupiedattentionKV),same frozen data/recipe;not run.
   This is a quality-memory tradeoff,not a capacity-limit diagnosis.
3. If staying8192is mandatory,consider a separately frozen direction-matched
   training audit/pilot: purpose→field queries drawn from schema gaps,excluding
   evaluationquestions/reservedtools. Do not copy dev failures into training.
   This tests query coverage,different from merely adding answers/descriptions;
   no synthesis or pilot has started. Output-supervised KV remains higher-cost
   backend work,not an available toggle in this EXL3 runtime.

Implementationf73fe96;stdlib classifier tests and live three-mode runtime probe
verified. Audit counts do not prove causality;476and780artifacts also differ in
sampling/compute/training paths. No stress/testerror-based training additions.
