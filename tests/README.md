# Regression checks

Run individual files directly with Python from the project root; no test framework
is required for the current checks. Tests do not train a real model.

Dependency-free:
- `test_release.py`: exact Git-free inventory and obvious credential rejection.
- `test_final_eval_results.py`, `test_final4b_results.py`, `test_am27b_results.py`: final response-bound reviews, frozen identities, paired counts and regraded traces.
- `test_compare4b.py`: shared812train examples, grouped validation, causal query/EOS indexing and group-weighted validation. `test_compare4b_am.py` needs Torch and the pinned `COMPACTION_DIR`; tiny CPU solver/checkpoint parity only.
- `test_evaluate.py`: unified publication CLI, input/result provenance, table regeneration and no-model resume identity checks.
- `test_transplant_refactors.py`, `test_transplant_results.py`:40verbatimrecoveredquestions,all160responses,baselinegate,candidatecountsandreviewhashes.
- `test_natural_refactors_results.py`: all160naturalresponses, reviewed-source hashes, diagnostics and preflight counts.
- `test_natural_refactors.py`:40naturalrequests,reference syntax,signatures,boundaries,nohelperhints and manifest hashes. `test_natural_refactors_code.py --image IMAGE --out FILE` validates authored references/buggy controls in Docker only.
- `test_clean_eval_v2.py`, `test_clean_eval_v2_results.py`: 200case definition checks, all800records regraded, manual-source hashes and descriptive clustered contrasts.
- `test_clean_eval.py`: fresh-set definitions, exact recall, positive/negative tool grading.
- `test_clean_eval_results.py`: all256records regraded; manual-source hashes and separate tables.
- `test_publication_results.py`: frozen counts,160task records regraded,annotations.
- `test_reproduction_results.py`: fresh run counts,160task traces,manual source hashes,parity differences.
- `test_script_layout.py`:source-archive syntax and frozen algorithm hashes; no Git dependency.
- `test_reproduce.py`:input hashes,fresh command plan,recipe/path invariants.
- `test_capture_store.py`: boundedRAM,crash tails,resume,bit-preserving shard output.
- `test_long_policy27b.py`, `test_policy_coverage27b.py`: authored fixtures/positions.
- `test_joint_tools27b.py`, `test_task_eval27b.py`: prompt length/task grading.
- `test_storage_paths.py`: no obsolete storage paths in scripts.

NumPy required: `test_probe_diversity.py`, `test_probesets.py`, `test_grader_parity.py`.
PyTorch/NumPy/safetensors: `test_compile_resume.py`, `test_cosine_normalization.py`.
`test_policy_coverage_outputs27b.py` requires explicit items and an existing Docker
image argument; executes calibration code in an isolated container, never on host.

Historical MLX/4B tests remain at `archive/pre-unified-release`; their removal does
not establish replacement GPU runtime coverage. Existing GPU capture parity is
documented in the experiment reports. Full publication-source reproduction on the
existing pinned runtime completed; installation into a fresh runtime environment
is being verified separately. See `results/RELEASE_VALIDATION.md` for the measured
current status, not an assumption that shared-runtime success is a fresh install.
