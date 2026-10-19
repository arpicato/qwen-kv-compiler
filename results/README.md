# results/

Small, human-readable JSON summaries that back the claims in
`EXPERIMENT_LOG.md` and the top-level `README.md`.

These files are **tracked on purpose** (unlike `artifacts/`, which holds the
large teacher-state and compiled-KV tensors and is rebuilt by the scripts).

Each file is written by an eval script and contains a `summary` block
(accuracies, retention, by-kind breakdown) plus a `raw` list with one row per
probe: grade flags, per-system stop reason, generated-token counts, per-probe
generation time, KL divergence, and the full generated text for teacher,
compiled, and no-context baselines.

| file | what it is |
|---|---|
| `tool_handbook_k4738_n103.json` | Full 103-probe tool-handbook eval at K=4738 (4x compression). Headline: compiled acc 0.825, raw retention 0.859, informative retention 0.814. |

Reproduce with (see top-level README for the full recipe):

```bash
uv run python scripts/eval_toolset_fast.py \
  --compiled artifacts/tool/compiled_ratio025 \
  --baseline-cache artifacts/tool/baseline \
  --out artifacts/tool/eval_ratio025_n103.json
```
