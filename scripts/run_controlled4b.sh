#!/usr/bin/env bash
# Sequential, fail-fast, resumable phases; invoke from an immutable source export.
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1
export CARTRIDGES_DIR=/home/arpin/kvbench/cartridges
export COMPACTION_DIR=/home/arpin/kvbench/compaction
PY=/home/arpin/kvbench/env/bin/python
OUT=/mnt/data/artifacts/kvcompile/artifacts/agent/controlled4b_v1
DATA=inputs/controlled4b/cases.json
CASES=inputs/publication_final/cases.json

phase() {
    local name=$1
    shift
    echo "$(date -u +%FT%TZ) START phase=$name child_log=/tmp/opencode/controlled4b-$name.log"
    "$@" > "/tmp/opencode/controlled4b-$name.log" 2>&1 &
    local child=$!
    echo "$child" > "/tmp/opencode/controlled4b-$name.child.pid"
    for ((i=0; i<1440; i++)); do
        if ! kill -0 "$child" 2>/dev/null; then
            wait "$child"
            echo "$(date -u +%FT%TZ) DONE phase=$name"
            return
        fi
        tail -n 2 "/tmp/opencode/controlled4b-$name.log"
        sleep 30
    done
    echo "Phase deadline exceeded; child=$child remains active, no next phase" >&2
    return 1
}

# CARTRIDGES runs independently first; wait only for its recorded exact PID.
if [[ -n ${FINAL27B_PID:-} ]]; then
    for ((i=0; i<720; i++)); do
        if ! ps -p "$FINAL27B_PID" >/dev/null; then break; fi
        echo "$(date -u +%FT%TZ) waiting for 27B pid=$FINAL27B_PID"
        if [[ -f /tmp/opencode/final-eval27b-generation.log ]]; then
            tail -n 2 /tmp/opencode/final-eval27b-generation.log
        fi
        sleep 30
    done
    if ps -p "$FINAL27B_PID" >/dev/null; then exit 1; fi
    "$PY" -c 'import json; from pathlib import Path; p=Path("/mnt/data/artifacts/kvcompile/artifacts/agent/final_eval27b_v1/raw.json"); d=json.loads(p.read_text()); assert d["complete"]; assert set(d["rows"])=={"full","none","joint4k","joint8k"}; assert all(len(s["behavior"])==120 and not s["knowledge"] and not s["tools"] for s in d["rows"].values())'
fi
if [[ -n ${CARTRIDGES_PID:-} ]]; then
    for ((i=0; i<720; i++)); do
        if ! ps -p "$CARTRIDGES_PID" >/dev/null; then break; fi
        echo "$(date -u +%FT%TZ) waiting for CARTRIDGES pid=$CARTRIDGES_PID"
        tail -n 2 /tmp/opencode/controlled4b-cartridges-fit.log
        sleep 30
    done
    if ps -p "$CARTRIDGES_PID" >/dev/null; then exit 1; fi
fi
"$PY" -c 'import json; from pathlib import Path; p=Path("/mnt/data/artifacts/kvcompile/artifacts/agent/controlled4b_v1"); assert json.loads((p/"cartridges/report.json").read_text())["complete"]; assert json.loads((p/"capture-audit.json").read_text())["complete"]'
phase compiler "$PY" -B scripts/compile_torch_v2.py --traj "$OUT/capture" --out "$OUT/compiler" --slots 2509 --steps 400 --lr .001 --cosine-weight 1 --batched --batch-chunk 4 --freeze-sink --examples-per-update 72 --sampling-plan inputs/joint/sampling.json --oproj-dir "$OUT/capture" --kv-dtype bfloat16 --log-every 25 --resume
phase am "$PY" -B scripts/compare4b.py am --data "$DATA" --capture "$OUT/capture" --out "$OUT/am"
for arm in full none compiler am cartridges; do
    args=()
    if [[ $arm != full && $arm != none ]]; then args=(--artifact "$OUT/$arm"); fi
    phase "smoke-$arm" "$PY" -B scripts/evaluate.py run --backend hf4b --model /mnt/data/models/Qwen3-4B --cases "$CASES" --arm "$arm" "${args[@]}" --capture "$OUT/capture" --smoke --out "$OUT/final-smoke-$arm.json"
done
for arm in full none compiler am cartridges; do
    args=()
    if [[ $arm != full && $arm != none ]]; then args=(--artifact "$OUT/$arm"); fi
    phase "eval-$arm" "$PY" -B scripts/evaluate.py run --backend hf4b --model /mnt/data/models/Qwen3-4B --cases "$CASES" --arm "$arm" "${args[@]}" --capture "$OUT/capture" --out "$OUT/final-eval-$arm.json"
done
echo "$(date -u +%FT%TZ) DONE fits and raw evaluations; manual behavior review still required artifact=$OUT"
