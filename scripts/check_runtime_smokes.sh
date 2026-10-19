#!/usr/bin/env bash
# Short train-only checks against read-only existing artifacts. No fits/scores.
set -euo pipefail
RUNTIME=${1:?runtime root}
ARTIFACTS=${2:?artifact root}
MODEL27=${3:?27B model}
MODEL4=${4:?4B model}
OUT=${5:?new smoke output root}
mkdir -p "$OUT"
export EXLLAMAV3_PATH="$RUNTIME/exllamav3" COMPACTION_DIR="$RUNTIME/compaction"
export CARTRIDGES_DIR="$RUNTIME/cartridges" CARTRIDGES_OUTPUT_DIR="$OUT/cartridges-output"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONUNBUFFERED=1
start=$SECONDS
for test in test_compile_resume.py test_cosine_normalization.py test_compare4b_am.py; do
    "$RUNTIME/hf-env/bin/python" -B "tests/$test"
done
"$RUNTIME/exl-env/bin/python" -B tests/test_am27b_attention.py
# A train-only probe avoids running another benchmark for installation checks.
"$RUNTIME/exl-env/bin/python" - "$OUT/train-probe.json" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path('inputs/joint/questions.json').read_text())['items'][0]
Path(sys.argv[1]).write_text(json.dumps([dict(q=r['q'],answer=r['answer'],kind='lookup')]))
PY
for slots in 4096 8192; do
    for pass in 1 2; do
        echo "$(date -u +%FT%TZ) START smoke=27b-compiler$slots pass=$pass elapsed=$((SECONDS-start))s"
        "$RUNTIME/exl-env/bin/python" -B scripts/eval_agent_exl3.py --model "$MODEL27" --teacher "$ARTIFACTS/reproduction27b_v1/teacher" --compiled "$ARTIFACTS/reproduction27b_v1/compiled$slots" --prompt-file inputs/joint/prompt.txt --probeset "$OUT/train-probe.json" --max-tokens 16 --arms compiled --resume --out "$OUT/27b-compiler$slots.json"
    done
done
for spec in 'am27b_v1 4096' 'am27b_fp32_v1 8192'; do
    read -r folder slots <<< "$spec"
    echo "$(date -u +%FT%TZ) START smoke=$folder elapsed=$((SECONDS-start))s"
    if [[ ! -f $OUT/$folder.json ]]; then
        "$RUNTIME/exl-env/bin/python" -B scripts/am27b_smoke.py --slots "$slots" --model "$MODEL27" --reference "$ARTIFACTS/reproduction27b_v1" --artifacts "$ARTIFACTS/$folder" --out "$OUT/$folder.json"
    fi
done
for arm in full none compiler am cartridges; do
    args=()
    if [[ $arm != full && $arm != none ]]; then args=(--artifact "$ARTIFACTS/controlled4b_v1/$arm"); fi
    for pass in 1 2; do
        echo "$(date -u +%FT%TZ) START smoke=4b-$arm pass=$pass elapsed=$((SECONDS-start))s"
        "$RUNTIME/hf-env/bin/python" -B scripts/evaluate.py run --backend hf4b --model "$MODEL4" --capture "$ARTIFACTS/controlled4b_v1/capture" --arm "$arm" "${args[@]}" --smoke --out "$OUT/4b-$arm.json"
    done
done
echo "$(date -u +%FT%TZ) DONE elapsed=$((SECONDS-start))s artifact=$OUT"
