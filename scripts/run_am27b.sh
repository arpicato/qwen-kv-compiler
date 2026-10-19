#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${AM_FIT_PID:?exact fit wrapper PID required}"
OUT=/mnt/data/artifacts/kvcompile/artifacts/agent/am27b_v1
PREFIX=am27b
BUDGETS=4096,8192
ARMS=am4k,am8k
if [[ ${AM_FP32:-0} == 1 ]]; then
    OUT=/mnt/data/artifacts/kvcompile/artifacts/agent/am27b_fp32_v1
    PREFIX=am27b-fp32
    BUDGETS=8192
    ARMS=am8k_fp32
fi
REF=/mnt/data/artifacts/kvcompile/artifacts/agent/reproduction27b_v1
MODEL=/mnt/data/models/Qwen3.8-27B-EXL3-3.5bpw
PY=/home/arpin/exllamav3-rocm/.venv-rocm/bin/python
export EXLLAMAV3_PATH=/home/arpin/exllamav3-rocm
export COMPACTION_DIR=/home/arpin/kvbench/compaction
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1
for ((i=0;i<720;i++)); do
    if ! ps -p "$AM_FIT_PID" >/dev/null; then break; fi
    echo "$(date -u +%FT%TZ) waiting for AM fit pid=$AM_FIT_PID"
    tail -n 2 "/tmp/opencode/$PREFIX-fit.log"
    sleep 30
done
if ps -p "$AM_FIT_PID" >/dev/null; then exit 1; fi
"$PY" -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); assert all(json.loads((p/f"am{k}/manifest.json").read_text())["complete"] for k in sys.argv[2].split(","))' "$OUT" "$BUDGETS"
phase() {
    local name=$1
    shift
    echo "$(date -u +%FT%TZ) START phase=$name"
    "$@" > "/tmp/opencode/$PREFIX-$name.log" 2>&1 &
    local child=$!
    echo "$child" > "/tmp/opencode/$PREFIX-$name.child.pid"
    for ((i=0;i<1440;i++)); do
        if ! ps -p "$child" >/dev/null; then break; fi
        tail -n 2 "/tmp/opencode/$PREFIX-$name.log"
        sleep 30
    done
    if ps -p "$child" >/dev/null; then echo "deadline exceeded pid=$child"; exit 1; fi
    wait "$child"
    echo "$(date -u +%FT%TZ) DONE phase=$name"
}
if [[ ! -f $OUT/freeze.json ]]; then
    phase smoke "$PY" -B scripts/am27b_smoke.py --slots "$BUDGETS" --model "$MODEL" --reference "$REF" --artifacts "$OUT" --out "$OUT/smoke.json"
fi
if [[ ! -f $OUT/freeze.json ]]; then
    phase freeze "$PY" -B scripts/evaluate.py freeze --model "$MODEL" --artifacts "$REF" --am-artifacts "$OUT" --am-slots "$BUDGETS" --cases inputs/publication_final/cases.json --freeze "$OUT/freeze.json"
fi
phase generation "$PY" -B scripts/evaluate.py run --freeze "$OUT/freeze.json" --cases inputs/publication_final/cases.json --arms "$ARMS" --out "$OUT/raw.json"
echo "$(date -u +%FT%TZ) DONE AM fits and raw responses; manual review required artifact=$OUT"
