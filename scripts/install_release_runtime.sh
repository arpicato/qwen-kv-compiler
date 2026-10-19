#!/usr/bin/env bash
# Isolated original-target install. Never point ROOT at an existing environment.
set -euo pipefail
ROOT=${1:?usage: install_release_runtime.sh NEW_ABSOLUTE_ROOT [--resume]}
[[ $ROOT == /* ]] || { echo 'Root must be absolute' >&2; exit 1; }
if [[ -e $ROOT ]]; then
    [[ ${2:-} == --resume && -f $ROOT/.kvrelease-install-v1 ]] || { echo 'Existing root needs installer marker and --resume' >&2; exit 1; }
fi
mkdir -p "$ROOT"
touch "$ROOT/.kvrelease-install-v1"
export ROCM_HOME=${ROCM_HOME:-$(hipconfig --path)}
HIP_CLANG_PATH=${HIP_CLANG_PATH:-$(hipconfig --full | sed -n 's/^HIP_CLANG_PATH *://p')}
export CC=${CC:-$HIP_CLANG_PATH/clang} CXX=${CXX:-$HIP_CLANG_PATH/clang++}
[[ -x $ROCM_HOME/bin/hipcc && -x $CC && -x $CXX ]] || { echo 'HIP/Clang toolchain paths are invalid' >&2; exit 1; }
export UV_CACHE_DIR="$ROOT/download-cache" UV_LINK_MODE=copy
UV=${UV:-uv}
start=$SECONDS
checkout() {
    if [[ -d $ROOT/$1/.git ]]; then
        [[ $(git -C "$ROOT/$1" rev-parse HEAD) == "$3" ]]
        git -C "$ROOT/$1" diff --quiet HEAD
        return
    fi
    git init -q "$ROOT/$1"
    git -C "$ROOT/$1" remote add origin "$2"
    git -C "$ROOT/$1" fetch --depth 1 origin "$3"
    git -C "$ROOT/$1" checkout --detach FETCH_HEAD
}
echo "$(date -u +%FT%TZ) START isolated runtime installation root=$ROOT"
checkout exllamav3 https://github.com/arpicato/exllamav3-rocm.git 25d0dd1f77e62feee587fe2bdb15c568e1e34359
checkout compaction https://github.com/adamzweiger/compaction.git 2020f6d37940fe013e7e7f1ebf409e5d107c5670
checkout cartridges https://github.com/HazyResearch/cartridges.git ef34ba97a06049c34820506e2c283746284ae5f0
if [[ ! -f $ROOT/exl-env/pyvenv.cfg ]]; then "$UV" venv --python 3.14.4 "$ROOT/exl-env"; fi
"$UV" pip install --python "$ROOT/exl-env/bin/python" 'torch==2.13.0+rocm7.2' --index-url https://download.pytorch.org/whl/rocm7.2
"$UV" pip install --python "$ROOT/exl-env/bin/python" numpy==2.5.2 safetensors==0.8.0 tokenizers==0.23.2 setuptools==78.1.0 wheel ninja==1.13.2 rich pillow pyyaml marisa_trie pydantic 'llguidance==1.9.1'
export PYTORCH_ROCM_ARCH=gfx1100 MAX_JOBS=2
echo "$(date -u +%FT%TZ) START native extension build elapsed=${SECONDS}s"
(cd "$ROOT/exllamav3" && "$ROOT/exl-env/bin/python" setup.py build_ext --inplace)
EXLLAMA_NOCOMPILE=1 "$UV" pip install --python "$ROOT/exl-env/bin/python" --no-deps --no-build-isolation -e "$ROOT/exllamav3"
if [[ ! -f $ROOT/hf-env/pyvenv.cfg ]]; then "$UV" venv --python 3.12 "$ROOT/hf-env"; fi
"$UV" pip install --python "$ROOT/hf-env/bin/python" 'torch==2.8.0+rocm6.4' --index-url https://download.pytorch.org/whl/rocm6.4
# The tested Transformers revision differs from CARTRIDGES' advertised <=4.55.
# Use source imports as in the experiments; do not resolve its broad extras.
"$UV" pip install --python "$ROOT/hf-env/bin/python" transformers==4.57.1 accelerate==1.12.0 numpy==2.5.4 safetensors==0.8.0 tokenizers==0.22.2 einops pydrantic peft tiktoken wandb datasets evaluate matplotlib markdown
"$UV" pip freeze --python "$ROOT/exl-env/bin/python" > "$ROOT/exl-freeze.txt"
"$UV" pip freeze --python "$ROOT/hf-env/bin/python" > "$ROOT/hf-freeze.txt"
echo "$(date -u +%FT%TZ) DONE elapsed=$((SECONDS-start))s artifact=$ROOT"
