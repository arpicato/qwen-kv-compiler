# Supported entry points

| Command | Purpose |
|---|---|
| `evaluate.py verify` | Regrade and verify current publication tables without GPU |
| `evaluate.py preflight` | Validate reference actions/programs and buggy controls |
| `evaluate.py freeze` | Pin source, inputs, model and cache identities |
| `evaluate.py run` | Run all current suites with per-case resume |
| `evaluate.py report` | Validate response-bound manual review and regenerate summary |
| `install_release_runtime.sh NEW_ROOT` | Install isolated EXL3 and 4B/AM environments |
| `reproduce.py plan` / `run` | Original 19-phase fresh capture/fit/evaluation/negative-control recipe |

Start with [EVALUATION.md](../EVALUATION.md) or [REPRODUCE.md](../REPRODUCE.md).
These are the publication interfaces. The existing training recipe is not silently
redefined by the newer evaluation bundle. Shared internal modules are not separate
benchmarks: `run_clean_eval.py` supplies generation/orchestration, `clean_eval.py`
grading and Docker checks, `task_eval27b.py` mock action parsing/schema checks.

## Core pipeline

`capture_agent_teacher_exl3.py`, `capture_agent_exl3.py`, `capture_store.py`,
`export_oproj_exl3.py`, `compile_torch_v2.py`, `eval_agent_exl3.py`, and
`eval_tasks27b.py` retain the capture, layer fitting, cache installation and greedy
generation implementations. `freeze_task27b.py` provides the streamed digest;
`review_long_policy27b.py` retains original grading. No math/grading rewrite is
part of publication cleanup. Runtime dependencies live in `src/`.

## Provenance helpers, not alternative public workflows

`prepare_clean_eval*.py`, `prepare_natural_refactors.py`,
`prepare_transplant_refactors.py`, `summarize_clean_eval*.py`, `joint_tools27b.py`,
`task_cases27b.py`, `prepare_long_policy27b.py`, `policy_coverage27b.py` and
`prepare_policy_coverage_continue27b.py` preserve experiment authoring/history or
the original reproduction dependency closure. Do not rerun generators to alter
scored cases. They remain because recorded source manifests/tests depend on them;
there is no new generator or runner per future problem type.

Tests live in `tests/`, with stdlib checks callable directly. Historical removed
MLX/selector/reread/pilot code lives at recorded archive tags; reports/raw text
remain in `results/`. Current 4B training uses `compare4b.py`; 27B AM uses
`am27b.py`, `am27b_attention.py`, `am_block_scores.py`, `am27b_smoke.py` and the
precision gate. Exact commands are in REPRODUCE.md. `run_controlled4b.sh` and
`run_am27b.sh` are original-machine orchestration records with absolute paths,
not portable launchers. No shared runtime or old artifact is modified.
