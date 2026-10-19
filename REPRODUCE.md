# Reproduction on the original target

For the method and testing design, start with [README.md](README.md). This guide
is for **new model runs**, not rechecking saved tables. The two studies are
separate: first build 27B compiler caches using the 19-phase recipe below, or follow
the 4B section for a fresh three-method comparison. The 27B AM section uses captures
from the 27B recipe. Model weights and GPU dependencies are external prerequisites;
none of the fitting commands are needed for `evaluate.py verify`.

For the current evaluation-only interface use [EVALUATION.md](EVALUATION.md) and
`scripts/evaluate.py`. This document retains the original 19-phase reproduction
recipe, including its historical evaluation suites and negative continuation.
After generating its artifacts, the same current bundle can be frozen/run through
the unified evaluation CLI. Do not confuse a new evaluation with a new model fit.

Scope: Linux x86_64, RX7900XTX(gfx1100), ROCm7.2, Python3.14.4,
Torch2.13.0+rocm7.2, pinned ExLlamaV3. No other architecture/backend is promised.
Have at least90GiB free for outputs,~8GiB hostRAM plus swap,24GiBVRAM. The
bounded capture writer retains streams and exported shards; fitting loads one
layer at a time. No existing model capture/cache/projection is a prerequisite.

## External dependencies

`runtime.json` pins the model revision,weightSHA256,metadataSHA256,runtime commit
and critical package versions. Do not use a different quantization or tokenizer.

Obtain the model with the Hub CLI (downloads resume):

```sh
hf download Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw --revision 19441ac874c4018295da848e250f23511361cda4 --local-dir /path/to/model
```

Obtain the ROCm runtime without modifying another project's checkout:

```sh
git clone https://github.com/arpicato/exllamav3-rocm.git /path/to/exllamav3-rocm
git -C /path/to/exllamav3-rocm checkout 25d0dd1f77e62feee587fe2bdb15c568e1e34359
```

Use Python3.14.4 with the matching ROCm7.2Torch build; follow the pinned runtime's
ROCm installation instructions for its extension/toolchain. Install that checkout
in the environment. `uv.lock` covers only the small NumPy/safetensors dependencies,
NOT ROCm/Torch/native extensions. The runner rejects version/commit/hash mismatch;
it does not silently install a CPU/CUDA wheel. The original 19-phase reproduction
used the existing, unchanged shared environment.
A later isolated installation and short inference/resume checks also passed;
That does not mean all 19 phases were repeated during installation validation.
See [RELEASE_VALIDATION.md](results/RELEASE_VALIDATION.md) for the distinction.

Code checks require Docker and a small reproducible Python3.12.3image:

```sh
docker build -f Dockerfile.checks -t kvcompile-checks:repro .
```

The base image digest is pinned. The image contains no model or project code;
patches execute with network disabled,read-onlyroot,unprivilegeduser,resource caps.
The historical image also used Python3.12.3but included unrelated applications.
Both images must agree on saved patch checks before claiming code-score parity.

## Check the release, then rerun

All calibration/prompt/probe/task inputs are in `inputs/`;SHA256in its manifest.
Published historical annotations/raw outputs remain in `results/`. No Git history
or archive tags are required to execute the release. Use a fresh clone or
`git archive`export, not the old XTX runtime folder. `RELEASE.json` identifies the
exact shipped source/input bytes. Output must be outside the exported source.

```sh
python3 tests/test_script_layout.py
python3 tests/test_publication_results.py
python3 tests/test_reproduce.py
export EXLLAMAV3_PATH=/path/to/exllamav3-rocm
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 scripts/reproduce.py plan --model /path/to/model --out /path/to/new-output
python3 scripts/reproduce.py run --model /path/to/model --out /path/to/new-output
```

Run the last command detached with a log on your machine for multi-hour work.
The project procedure uses `setsid bash -c '... > /tmp/opencode/reproduce.log 2>&1'
< /dev/null >/dev/null 2>&1 &` and saves `$!`. Poll that exact wrapper/child PID;
never kill or search via a self-matching `pgrep/pkill -f`pattern.

The19phases: fresh812capture+teacher roundtrip,projection export,teacher-initialized
4k/8k400-updatefits,full/none/compiled fixed/stress/behavior evaluations,
frozen40task evaluation, fresh64capture,merge,matched80-updatecontrol/candidate,
continuation evaluations and summary. No teacher/capture/projection/compiled
artifact is read outside the new output tree. External weights/runtime/Docker
are the only prerequisites. No fitting on evaluation questions or score-based
checkpoint selection. The run reads the combined prompt;source prompts are not
rebuilt from a user's current configuration.

`run.json` records identities,commands,phase durations and output hashes. Restart
the same command to resume. Completed phases verify hashes; unfinished capture
resumes at committed batches,compiler at completed layers,evaluation per question.
Compiler does NOT checkpoint Adam within a layer (historical layers~6–8min).
No silent fallback,automatic recipe change or historical output overwrite.

`summary.json` contains automatic probe/task counts and refactor checks. Money
approval still requires manual review of new outputs; do not copy old labels to
new answers. Publish raw outputs,paired changes,stops/caps,manual decisions and
runtime. Small numerical changes can change greedy tokens. Report reproduction
differences rather than choosing whichever run scores better.

## Controlled 4B and AM runtimes

Use separate environments: 27B inference needs the pinned Python3.14.4/
Torch2.13.0+rocm7.2; 4B and AM solving use Python3.12/Torch2.8.0+rocm6.4,
Transformers4.57.1, accelerate1.12.0, NumPy2.5.4, safetensors0.8.0,
tokenizers0.22.2. The latter is **not** the small project `uv.lock` environment.
The solver crashed under the inference Torch build; do not silently combine them.

`scripts/install_release_runtime.sh` installs new upstream checkouts, two isolated
venvs and a fresh gfx1100 native extension. Requires `uv`, Git, HIP build tools,
Python development headers and Clang; paths are detected with `hipconfig` (or
explicit `ROCM_HOME`, `CC`, `CXX`). The original host has systemHIP7.1/Clang21
under `/usr`, while inferenceTorch bundles ROCm7.2. Uses two compile jobs to bound RAM. Supply a new absolute
root on a disk with room for both Torch builds. Never use a shared checkout as
that root. Repeat with `--resume` only for a root bearing this installer's marker;
downloads reuse cache, package installs are idempotent and native build reuses
completed object files. Its measured status is in `results/RELEASE_VALIDATION.md`.

```sh
bash scripts/install_release_runtime.sh /path/to/new-runtime-root
export EXLLAMAV3_PATH=/path/to/new-runtime-root/exllamav3
export COMPACTION_DIR=/path/to/new-runtime-root/compaction
export CARTRIDGES_DIR=/path/to/new-runtime-root/cartridges
export CARTRIDGES_OUTPUT_DIR=/path/to/new-4b-output
```

AM revision `2020f6d37940fe013e7e7f1ebf409e5d107c5670` and CARTRIDGES revision
`ef34ba97a06049c34820506e2c283746284ae5f0` are enforced. CARTRIDGES uses source
imports with Transformers4.57.1, outside its declared <=4.55 range. Native tile
constants are32/32/1/FORCE_USE_FLEX_ATTENTION; saved partition is64frozen tokens.
Do not infer that pip-installing unpinned upstream extras reproduces this runtime.

## 4B fresh capture and fitting

Acquire Qwen/Qwen3-4B separately, retaining its LICENSE. Check all model files
against `results/CONTROLLED4B_CAPTURE_AUDIT.json` identity.model_sha256; a Hub
revision was not recorded, so file hashes, not an invented revision, are the
authoritative identity. Existing weights may be reused read-only.
`inputs/controlled4b/cases.json` is tracked (812train/89validation/75groups).
Use the hf-env Python for the following commands, from an immutable source export:

```sh
python scripts/compare4b.py capture --data inputs/controlled4b/cases.json --model /path/to/Qwen3-4B --teacher-forward full --out /path/to/4b/capture
python tests/check_compare4b_capture.py --out /path/to/4b/capture-audit.json --capture /path/to/4b/capture --data inputs/controlled4b/cases.json --source /path/to/immutable-source
python scripts/compare4b.py cartridges-gate --data inputs/controlled4b/cases.json --model /path/to/Qwen3-4B --capture /path/to/4b/capture --out /path/to/4b/cartridges-gate
python scripts/compare4b.py am-gate --data inputs/controlled4b/cases.json --model /path/to/Qwen3-4B --capture /path/to/4b/capture --out /path/to/4b/am-gate
python scripts/compare4b.py cartridges --data inputs/controlled4b/cases.json --model /path/to/Qwen3-4B --capture /path/to/4b/capture --out /path/to/4b/cartridges
python scripts/compile_torch_v2.py --traj /path/to/4b/capture --out /path/to/4b/compiler --slots 2509 --steps 400 --lr .001 --cosine-weight 1 --batched --batch-chunk 4 --freeze-sink --examples-per-update 72 --sampling-plan inputs/joint/sampling.json --oproj-dir /path/to/4b/capture --kv-dtype bfloat16 --log-every 25 --resume
python scripts/compare4b.py am --data inputs/controlled4b/cases.json --capture /path/to/4b/capture --out /path/to/4b/am
```

Capture uses full prefill for every target; prefix reuse failed its probability
parity gate. Each method sees the same examples, not equal objectives/exposure/
compute. CARTRIDGES uses top20teacherKL,8epochs/lr.02/accum32; bestepoch7 selected
by groupmeanvalidation only. Compiler400steps/layer,48catalog+24policy sampling;
AM offpolicyuniformRMS/NNLS2/LSQ. All methods2509rows/head,36layers.
Capture checkpoints committed batches; CARTRIDGES update checkpoints/epoch-best;
compiler completed layers; AM completed heads/layers. Restart identical commands.
Run gates/smokes before scores, one GPU job at a time. Follow EVALUATION.md for
five-arm training-question smoke and final240evaluation/manual-review commands.
Observed costs: capture13791.739s, compiler cumulative10233.221s, CARTRIDGES5238.104s,
AM338.191s; final5armgeneration8915.9s. Costs exclude failed/discarded partial work
unless the experiment manifest explicitly includes it; no equal-compute claim.

## 27B AM fitting and precision failure

Use fresh 27B reproduction captures as `--reference`; 812samequeries, original
recurrent state/logical26341. First run solver gate with hf-env, then native gate
with exl-env and `--load-head`, same output directory:

```sh
python scripts/am27b.py gate --solver-only --reference /path/to/reproduction --model /path/to/27b-model --out /path/to/am/gate-v2
python scripts/am27b.py gate --load-head --reference /path/to/reproduction --model /path/to/27b-model --out /path/to/am/gate-v2
python scripts/am27b.py fit --slots 4096 --gate /path/to/am/gate-v2/gate.json --reference /path/to/reproduction --model /path/to/27b-model --out /path/to/am/am4096
```

Gate requires zero-beta native parity, nonzero-beta reload and unchanged recurrent
state. Fitting uses hf-env and per-head RNG checkpoints, RMS/NNLS2/LSQ/seed0,
uniform rows. Native smoke/evaluation use exl-env. Original FP16 8192 fit failed
layer23/head3 when finite LSQV exceeded65504; do not clamp, drop heads or score it.

Historical precision-gate replay requires original failed `am8192/heads/head_022`
and `failure_diagnostic.json`, not shipped tensors. To acquire them from scratch,
run the same `am27b.py fit` command with `--slots 8192 --out /path/to/am/am8192`
in hf-env; expect it to fail rather than marking it complete. Then diagnose:

```sh
python scripts/am27b_diagnose.py --original /path/to/am --reference /path/to/reproduction
```

It resumes the RNG before layer23/head3 and writes `failure_diagnostic.json`.
If the expected failure is absent/different on another runtime, stop and report
it rather than inventing a matching failure. With those artifacts, run
`am27b_fp32_gate.py solver` in hf-env then
`native` in exl-env, supplying `--original /path/to/am --reference ... --model ...
--out /path/to/precision-gate`. This failure-specific recipe is documented but
has not been rerun in full for the isolated-install check. The successful gate is not
permission to omit all-layer checks on a new fit.

```sh
python scripts/am27b.py fit --values-fp32 --precision-gate /path/to/precision-gate/gate.json --slots 8192 --gate /path/to/am/gate-v2/gate.json --reference /path/to/reproduction --model /path/to/27b-model --out /path/to/am-fp32/am8192
python scripts/am27b_smoke.py --slots 8192 --model /path/to/27b-model --reference /path/to/reproduction --artifacts /path/to/am-fp32 --out /path/to/am-fp32/smoke.json
```

Keep the same original accepted `gate-v2/gate.json` in the FP32 root for freeze.
FP32 sidecars retain V without rounding; Q/K promoted for SDPA, output cast back
to native activation type; native cache holds prefix-V placeholders/live FP16.
Attention payload768MiB+1MiBbeta, not equal512MiBFP16KV. Prototype also allocates
native placeholders/temporaries; peaksmoke14.565GiB is not the payload size.
Fit401.862s/smoke105.301s/eval2563.938s; 4kfit266.049s/smoke98.602s/eval567.463s.
Precision/backend and rows differ, so no isolated memory/speed/capacity claim.

## Licensing and publication boundary

Original code MIT-0;embedded upstream text keeps its notices. See
`THIRD_PARTY_NOTICES.md`. Do not upload model weights or claim caches anonymize
their prompt. No public upload or remote Git push is part of this reproduction.
The input/prompt provenance and limitations remain as documented; reproducibility
does not turn inspected evaluations into a pristine holdout.
