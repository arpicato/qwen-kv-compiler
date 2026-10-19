# Phase 14 — EXL3 / ROCm regime on the 7900 XTX

Started 2026-10-11. Runtime: ExLlamaV3 on ROCm (gfx1100). Model:
`Qwen3.8-27B-EXL3-3.5bpw` (EXL3 3.5bpw quant of the same 27B). Prompt unchanged:
`prompts/agent_resident.txt`, 26,033 Qwen tokens, md5 `15fcd76f5573a5c84c88a0714a5476b1`.

**The teacher prompt hash `260281d80bc9c370` is identical to the MLX run**, so
the EXL3 and MLX regimes share tokenization exactly; only the weight quant
differs.

## Port and validation

New: `src/exl3.py` (runtime adapter), `scripts/exl3_selfcheck.py`,
`scripts/exl3_selfcheck_agent.py`, `scripts/capture_agent_exl3.py`,
`scripts/capture_agent_teacher_exl3.py`, `scripts/eval_agent_exl3.py`.

- Small-context cache round-trip: **BIT-EXACT** (baseline / inject / full-KV
  control all `max|d| = 0.0`).
- 26,033-token round-trip: KV and recurrent state restore bit-exactly
  (`torch.equal` on extracted K = True), token count matches n_sys exactly.
- The ROCm long-context attention kernel is **non-deterministic**: teacher-vs-
  teacher rerun spread `max|d| ≈ 0.03`, teacher-vs-inject `≈ 0.05`, with
  **identical argmax** across all runs. So greedy agreement is the fidelity bar,
  and KL thresholds carry a ~0.03–0.05 noise floor.

### Two bugs found and fixed during eval
1. **Graph path never materialised q/k/v.** Capture hooks had to force the eager
   attention path (`EXL3_*` graph flags off) to see post-RoPE tensors.
2. **Split position path corrupted multi-token prefill.** The rope kernel takes
   either `positions` (1-D, one per batch item) or `position_ids`
   (`bsz × seq_len`), mutually exclusive. Passing a scalar `positions` for a
   multi-token prefill applied the correct RoPE position to row 0 only, so the
   no-prefix arm emitted garbage (`system...# 1.# 1.` instead of
   `Node.js...npm`). Fix: `prefill_tokens_split` delegates to the rectangular
   `past_len` path whenever `physical_len == logical_pos` (teacher/none), and
   uses the per-token `position_ids` path only for the compiled arm. The first
   full eval was discarded because of this.

## Compile (ROCm, no model needed)

`compile_torch_v2.py`, E4-style minibatch, 400 steps, lr 1e-3, cosine 1.0,
frozen sink, bf16, seed 0, chunked backward (chunk 4). Chunked == full verified
on ROCm (loss rel 4e-7, grad rel 8.7e-8). **~2.5 min/layer → ~40 min per K**
(vs 140 min on the 3060).

## Results — `agent` suite (78 probes), corrected

| arm | teacher | none | compiled | informative retention |
|---|---:|---:|---:|---:|
| **K=6508** (4.0×) | 0.974 (76/78) | 0.410 (32/78) | 0.872 (68/78) | **39/45 = 0.867** |
| **K=8192** (3.2×) | 0.974 (76/78) | 0.410 (32/78) | **0.974 (76/78)** | **44/45 = 0.978** |

By kind (teacher / none / compiled):

| kind | n | K=6508 | K=8192 |
|---|---:|---|---|
| lookup | 28 | 0.96 / 0.39 / 0.75 | 0.96 / 0.39 / **0.96** |
| style | 20 | 1.00 / 0.70 / 0.95 | 1.00 / 0.70 / 0.95 |
| tool_select | 26 | 0.96 / 0.12 / 0.92 | 0.96 / 0.12 / **1.00** |
| unrelated | 4 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |

### Findings
1. **Capacity is again the dominant lever.** Raising K 6508 → 8192 lifted
   informative retention 0.867 → 0.978 and made compiled accuracy **equal the
   teacher** (76/78 both). Same conclusion as the Arclight regime, now on
   realistic content and a different quant/runtime.
2. **The realistic-regime failure mode is near-miss / adjacency confusion**,
   not wholesale fact loss — identical to the MLX finding. Remaining K=8192
   failures:
   - `title` (required create_issue argument) → `issue_number`
   - ADR editable `no` → staged self-check ("I'll check the ADR conventions…")
3. **lookup is the capacity-sensitive kind; style is not.** lookup 0.75 → 0.96
   with more slots, tool_select 0.92 → 1.00, but style stayed 0.95. This
   matches MLX (style flat, lookup the loser).
4. **EXL3 K=6508 (0.867) is slightly below the MLX K=6508 (0.904)**, but the
   teacher/none baselines and the failure *kinds* agree, so the regime
   reproduces across quantizations; the small gap is within what a different
   3.5bpw quant would explain.

### Held-out (197 generated probes, `agent_heldout`)

Teacher gets **197/197 = 1.000** (every probe is genuinely prompt-dependent:
none-arm tool_select is 0.016). The suite is much harder than the hand-written
one because probes are derived from shallow, often-shared first-sentence tool
descriptions, so many of the 131 tools are near-tied.

| arm | teacher | none | compiled | informative retention |
|---|---:|---:|---:|---:|
| **K=6508** | 1.000 (197/197) | 0.457 (90/197) | 0.782 (154/197) | **74/107 = 0.692** |
| **K=8192** | 1.000 (197/197) | 0.457 (90/197) | 0.802 (158/197) | **74/107 = 0.692** |

By kind (teacher / none / compiled):

| kind | n | K=6508 | K=8192 |
|---|---:|---|---|
| lookup | 135 | 1.000 / 0.659 / 0.822 | 1.000 / 0.659 / 0.844 |
| tool_select | 62 | 1.000 / 0.016 / 0.694 | 1.000 / 0.016 / **0.710** |

**Held-out reverses the hand-written result.** On the hand-written suite
tool_select was the *strongest* kind (1.00 at K=8192); on held-out it is the
weakest (0.71). Reason: hand-written probes used each tool's own distinctive
description; generated probes paraphrase shallowly, so selecting the exact one
of 131 tools becomes a fine-grained boundary the compressed cache does not
retain. The failures are near-miss/fabrication:

- fabricated names: `add_comment_to_pending_review` →
  `add_review_comment_to_requester_pending_`; `issue_dependency_write` →
  `issue_writeusemethodaddtocreateadependen...`
- real-but-wrong tools: `get_me` → `get_user`, `get_release_by_tag` →
  `get_release`, `push_files` → `push_multiple_files`,
  `update_pull_request_body` → `update_pull_request`.

Capacity did **not** help held-out (0.692 → 0.692): the extra 1684 slots did not
resolve exact-name boundaries. This is a different bottleneck from the
hand-written suite, where capacity clearly helped (0.867 → 0.978). Working
hypothesis: exact-name recall needs *name-local* fidelity (the token boundary),
which uniform slot allocation does not target — motivating the projected-loss /
refresh arms.

**Caveat:** these two `tool_select` numbers are not comparable in difficulty.
The hand-written suite is the better measure of *behavioural* preservation; the
held-out suite is a stress test of exact 131-way name recall.

## Artifacts (on the XTX box, `/mnt/sandisk/kvcompile/`)
- `artifacts/agent/traj/` — 71 × 16 layer shards (1.9 GB), `v2-causal-occupied`.
- `artifacts/agent/teacher/state.safetensors` — 1.87 GB, hash `260281d80bc9c370`.
- `artifacts/agent/compiled_k6508/`, `compiled_k8192/` — 16 layers each.
- `artifacts/agent/probes_agent_{dev,heldout}.json` — frozen generated suites.
- `results/agent_k{6508,8192}.json` — mirrored to `results/exl3_agent_k*.json`.

## Next
1. Held-out results; per-kind comparison.
2. Projected-loss arm at fixed K (export `o_proj`, validate vs ExLlama op, pilot
   layers 3/27/63) to attack the residual adjacency failures.
3. Decide whether the 2-decimal residual (style, ADR yes/no) is capacity-bound
   or objective-bound.

---

# Phase 16 — Query drift: paired (dirty-input → clean-target) refinement

## Motivation

Every compile so far trained the synthetic prefix to reproduce the teacher
attention computed from **teacher queries** — queries produced while the exact
26k prompt is resident. Deployed, the compiled prefix replaces that prompt, so
earlier layers hand later layers *slightly wrong* residuals. The deep-layer
queries the cache is actually asked to answer are therefore **not** the ones it
was trained on. The LR sweep showed loss gain does not transfer; query drift is
a candidate explanation the clean-input objective is structurally blind to.

## Tooling added

- `scripts/capture_agent_paired_exl3.py` — installs the **compiled** prefix
  (synthetic K/V at physical slots `[0,K)`, logical continuation at `n_sys`),
  forwards the identical user-turn + answer token stream, and records the
  model's own `q_rot` / `gate` / `k_live` / `v_live`. Same schema, same logical
  positions as the clean capture, so rows align item-for-item.
- `scripts/compile_torch_v2.py` — new `--clean-traj` (paired mode: inputs from
  `--traj`, target reconstructed from clean queries attending to the ORIGINAL
  prompt K/V) and `--init-from-dir` (warm start, so an arm and its control
  differ only in the objective).

## Query-drift penalty (measured, `lr=0`, K=8192 projected cache)

Both arms evaluated on the SAME warm-started cache; control = clean inputs,
paired = the model's own inputs. Full 71-item objective, projected + gated:

| layer | control | paired | drift penalty |
|---|---:|---:|---:|
| 3 | −2.999 | −2.999 | **0.000** |
| 31 | −2.982 | −2.948 | **0.034** |
| 63 | −2.716 | −0.935 | **+1.781** |

Layer 3 is a full-attention layer whose inputs come from three GatedDeltaNet
layers fed the *same injected recurrent state* in both arms, so its queries are
identical by construction — the 0.000 is a correctness check on the pipeline,
not a null result. Drift grows monotonically with depth (validated over the
whole stack: max|clean_q − paired_q| = 0.00 / 0.29 / 1.69 / 3.17 / 3.34 at
layers 3/7/31/51/63). **At layer 63 the cache scores −2.72 on the queries it was
trained on but only −0.94 on the queries it actually receives.**

## Refinement run — RESULT: clean negative

Both arms warm-start from `compiled_proj_k8192`, identical slots/steps/lr
(8192 / 400 / 3e-3), projected + gate + freeze-sink, `examples-per-update 24`:

- **control** → `refine_ctrl_k8192` (clean inputs → clean targets)
- **paired** → `refine_paired_k8192` (compiled inputs → clean targets)

### Deterministic full-set loss at layer 63 (all 71 items, `chunk=4`)

| cache | clean-input objective | paired (dirty-input) objective |
|---|---:|---:|
| baseline `compiled_proj_k8192` | −2.716 | **−0.935** |
| `refine_ctrl` | **−2.976** | −1.207 |
| `refine_paired` | −2.030 | **−2.708** |

Both arms did exactly what they were asked:

- **control** improved the clean-input loss (−2.716 → −2.976) — training works.
- **paired** nearly eliminated the drift gap on its own objective
  (−0.935 → −2.708, vs −2.72 clean), sacrificing clean-input loss to do it.

### Behaviour (informative retention)

| suite | baseline | control | paired |
|---|---:|---:|---:|
| `agent` (78) | 0.978 | 0.978 | 0.978 |
| `agent_heldout` (197) | **0.774** | 0.701 | **0.673** |

**Both arms are worse than the baseline they warm-started from, and the paired
arm — the one that solved drift at the loss level — is worst.** Query drift is
real and large (see above, −1.78 nat at L63) and is *fixable with this
objective*, but fixing it on these 71 training questions does **not** improve
held-out recall. This rules out this refinement as a remedy, not query drift
on the largely uncovered held-out tasks (see coverage audit below).

### Methodological note (a mistake made and corrected)

Mid-run I read the *minibatch* loss trajectory (24 of 71 items per step) as
"loss rising ⇒ lr overstepped", and wrongly planned a low-lr re-run. The
minibatch value is noise: at `lr=0` it still "moves" (−2.99 → −2.44 over 200
steps). The deterministic full-set loss is the only usable signal, and on it
both arms improve. The `--full-eval` flag exists precisely for this and should
have been used before drawing any conclusion. Lesson: never read minibatch loss
as a trend.

### Consistent pattern across Phase 15/16

Objective changes improve local reconstruction; projected improved held-out
retention (0.692→0.774), while subsequent refinement regressed it.
Capacity (K 6508→8192) fixed the
hand-written suite (0.867→0.978) and did nothing for held-out (flat 0.692).
These runs do not isolate the binding constraint: training-query coverage
remained fixed and sparse throughout.

## Training versus held-out coverage audit (2026-10-12)

Read-only audit of the XTX `questions.json`, clean capture index, frozen dev/
held-out probes, and per-question projected/control/paired evals. Remote training
questions match the local file; the clean capture index matches all 71 questions.
The XTX capture uses canonical answers from `questions.json`, not the local older
MLX capture's `answers.json`. Every arm uses this same question coverage.

| Task | Training (71) | Held-out (197) |
|---|---:|---:|
| Policy / repo / MCP facts | 48 | 0 |
| Skill selection | 8 | 0 |
| GitHub tool selection | 15 (14 distinct tools) | 62 (62 distinct tools) |
| Tool-argument binding | 0 | 135 (81 tools) |

Only **14/131 prompt tools (10.7%)** have targeted training queries. Only
**4/62 held-out tool targets (6.5%)** appear as training answers:
`actions_list`, `create_branch`, `create_or_update_file`,
`create_repository_ruleset`. The other 58 have no targeted training query.
All 135 held-out argument bindings are uncovered; none of their canonical
answer strings occurs as a training item's canonical answer. Sixteen argument
questions name a tool trained for selection, which does not train its arguments.
All schemas remain present in teacher KV: "uncovered" means absent from the
query/answer training set, not absent from the source prompt.

Projected cache informative retention by task (teacher correct, no-prefix wrong):

| Group | Correct / informative | Retention |
|---|---:|---:|
| Tool target covered by training | 4/4 | 100% |
| Tool target absent from training | 45/57 | 78.9% |
| Argument binding (all uncovered) | 33/45 | 73.3% |
| Overall | 82/106 | 77.4% |

All **24 informative failures** concern uncovered bindings: 12 tool names and
12 arguments. This is consistent with a coverage problem, but the covered
comparison is only four questions and uncovered tasks already dominate the
suite, so it does not establish causality. In contrast, the hand-written `agent`
suite covers the training topics closely: **15/16 tool-selection questions**
target trained tools. Its 97.8% retention is principally covered-topic fidelity,
not evidence of broad schema coverage.

Refinement preserves covered tool selection (4/4 in both arms), while uncovered
informative tool retention falls from 45/57 to 41/57 (control) and 37/57 (paired).
Using one fixed baseline informative mask gives overall 82/106, 75/106, 72/106;
the regression is not an artifact of the newer runs' denominator changing to 107.

Split audit also found **four exact dev/held-out duplicate questions**. The
generator partitions before within-split deduplication, permitting repeated
source questions to land in both splits. Training overlaps neither split.
Removing these four leaves projected retention **80/103 = 77.7%**, essentially
unchanged. Deduplicate globally before splitting in the next dataset version.

**Verdict:** current training is not representative of held-out schema retrieval.
Before declaring the objective exhausted, test broader query coverage with the
same projected objective and K: independently authored paraphrases for every
tool and distinctive argument binding, including close siblings. Keep eval
question text separate; evaluate same-binding/new-wording generalization and
untrained-binding transfer separately. More steps on the existing 71 questions
do not test this hypothesis. Merely adding `agent_dev` still misses held-out
tool targets because tool-selection probes are split by tool identity.

Sources: `scripts/gen_agent_questions.py:89-123`,
`src/agent_probes_gen.py:89-109`, `scripts/capture_agent_exl3.py:218-223`,
`results/exl3_heldout_proj_k8192.json`; XTX
`artifacts/agent/{questions.json,traj/meta.json,probes_agent_dev.json,probes_agent_heldout.json}`
and `results/heldout_refine_{ctrl,paired}_k8192.json`.
