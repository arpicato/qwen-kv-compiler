# Phase 15 — Projected-loss arm: attacking the tool-name boundary

Date: 2026-10-11. Follows phase 14. Question: phase 14 showed the held-out
`agent_heldout` retention stalls at 0.692 regardless of capacity (K=6508 and
K=8192 both 0.692). Is that a *capacity* limit or an *objective* limit?

## The objective

The compiler's raw loss compares the per-head attention output to the teacher's.
But the attention output is immediately passed through the output projection
`o_proj` (`Hq*D = 6144 -> hidden = 5120`) into the residual stream. The raw
objective penalises error that `o_proj` averages away, and ignores error that
`o_proj` amplifies.

The **projected** objective maps both the gated student output and the teacher
target through the frozen `o_proj` and compares them there:

    err = o_proj( sigmoid(gate) * out_student ) - o_proj( sigmoid(gate) * out_teacher )

so it penalises exactly the residual-stream contribution. Energy normalisation
(`c_layer`) is computed in the **same projected space** (otherwise it
under-scales the projected MSE).

## Implementation
- `scripts/export_oproj_exl3.py` — reconstructs `o_proj` from the EXL3 trellis
  via `LinearEXL3.get_weight_tensor()`, validates against ExLlama's own forward
  (recon vs matmul ≤ 0.02), exports all 16 layers.
- `compile_torch_v2.py` — new `o_proj=` argument to `BatchedCausalTorchLoss` and
  `--oproj-dir` flag. Chunked == full exact; gradients finite.
- `scripts/score_compiled.py` — scores a compiled artifact in raw **and**
  projected space (the shared yardstick: the training loss is not comparable
  across objectives, but residual-stream reconstruction error is).

## Pilot (layers 3/27/63, K=8192)
Projected vs gated control, scored by projected-MSE (the metric that matters):

| layer | gated control | projected | improvement |
|---|---:|---:|---:|
| L3 | 0.02084 | **0.00271** | 7.7× |
| L27 | 3.83286 | **2.39685** | 1.6× |
| L63 | 57.965 | **35.995** | 1.6× |

The control wins on *raw* MSE (0.0001 vs 0.0002 etc.) — confirming the two arms
optimise genuinely different spaces, and the projected one is what enters the
residual stream.

## Main result — K=8192, three objectives

| objective | agent compiled | agent retention | heldout compiled | heldout retention |
|---|---:|---:|---:|---:|
| **raw** (phase 14) | 0.974 (76/78) | 0.978 (44/45) | 0.782 (154/197) | **0.692** (74/107) |
| **gated** | 0.936 (73/78) | 0.933 (42/45) | 0.822 (162/197) | **0.729** (78/107) |
| **projected** | 0.949 (74/78) | **0.978** (44/45) | **0.843** (166/197) | **0.774** (82/106) |

Isolating the projection (gated is the matched control):

- gating alone: held-out 0.692 → 0.729 (+3.7)
- projection on top: 0.729 → **0.774** (+4.5)
- projection family vs raw: 0.692 → **0.774** (+8.2 pts, +8 held-out cases)

On the hand-written suite the projected arm keeps the **best** retention
(0.978, tied with raw) while being best on held-out — so the gain is not a
trade against the easy suite.

## What the projection fixed
10 held-out cases fixed, 2 broken (net +8), all on the exact-name boundary:

- **6 tool_select**: `push_files` (was `push_multiple_files`),
  `get_team_members` (was `get_teams_members`), `discussion_comment_write`,
  `mark_all_notifications_read`, `request_pull_request_reviewers`,
  `add_reply_to_pull_request_comment`.
- **4 lookup**: `resource_id`, `bypass_actors`, `cwes`, `pullNumber`.

This is exactly the predicted mechanism: the objective targets the fine-grained
name boundary because it optimises the error that survives `o_proj`.

## Conclusion
**The held-out stall was an objective limit, not a capacity limit.** Changing
*what* the loss measures (residual-stream contribution instead of raw attention)
recovers +8.2 points of informative retention where doubling-effective capacity
did nothing. Capacity and objective are orthogonal levers: capacity fixes
aggregate facts (phase 14, hand-written 0.867→0.978), the objective fixes
fine-grained name boundaries (phase 15, held-out 0.692→0.774).

## Artifacts
- `artifacts/agent/oproj/oproj_L*.pt` — 16 output projections.
- `artifacts/agent/compiled_proj_k8192/`, `compiled_gated_k8192/` — compiled K/V.
- `results/{agent,heldout}_{raw,gated,proj}_k8192.json` (mirrored to `results/exl3_*`).
