# Current publication case bundle

60 knowledge and 60 mock-tool cases copied verbatim from clean_eval_v2; 40 behavior
cases copied verbatim from transplant_refactors_v4. No new questions or labels.
`manifest.json` hashes the bundle, source cases, and unchanged joint prompt.
The CLI verifies byte identities and the original per-suite artifact hashes.

The bundled form can run all suites with `scripts/evaluate.py`; saved paper scores
come from separate v2/v4 runs, not an unperformed combined rerun. Per-suite
generation limits retain their original settings. No pooled score. Behavior is
an inspected, historically selected development diagnostic; see EVALUATION.md.
