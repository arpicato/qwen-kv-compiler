#!/usr/bin/env bash
# Git-free, small-dependency checks; optional Torch tests use the separate runtime.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
count=0
for test in tests/test_*.py; do
    case $test in
        tests/test_am_diagnose.py|tests/test_am27b_attention.py|tests/test_compare4b_am.py|tests/test_compile_resume.py|tests/test_cosine_normalization.py|tests/test_policy_coverage_outputs27b.py|tests/test_natural_refactors_code.py|tests/test_nonuniform_cache.py|tests/test_nonuniform_pipeline.py) continue ;;
    esac
    echo "$(date -u +%FT%TZ) CHECK $test"
    timeout 120 "$PY" "$test"
    count=$((count+1))
done
echo "$(date -u +%FT%TZ) DONE checks=$count"
