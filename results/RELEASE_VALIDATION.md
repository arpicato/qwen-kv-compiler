# Final package validation — 2026-10-19

**Current status:** Git-free CPU checks, Docker preflight and archive audit passed.
Fresh isolated installation and short inference/resume checks passed.
Independent review is absent; the user chose an explicit exploratory disclaimer
instead of waiting for it. Final public-release approval remains open. Earlier status
paragraphs below are chronological checkpoints, not current pending lists.

Preparation authorized; no new benchmark, fit, case/score change, push or upload.
Branch `release/final-package`, based on completed AM checkpoint `0e8d9b1`.

Final 240-case CLI verification now covers both studies and both completed AM
variants. Legacy 160-case verification remains explicit. Small regression first
failed on old default (40 rather than 120 behavior cases); after narrow change,
CLI/resume, final27B, final4B, AM results and frozen algorithm/layout checks pass.
README/EVALUATION now distinguish separate-run provenance, 4B full-control failure,
AM precision/backend/memory limits and assistant/unblinded review.

Isolated install wrapper1815724 launched with a new root
`/mnt/data/artifacts/kvcompile/release-validation-20261019`, log
`/tmp/opencode/release-install.log`. Fresh upstream source checkouts/environments,
no shared-runtime modification, no weights downloaded/copied. Installation and
inference verification are pending, not yet claimed. Expected native build may
need toolchain diagnostics; do not replace this with shared-environment success.

Pending: Git-free full CPU tests, Docker preflight, isolated runtime short
generation/resume, exact public-surface/privacy/license audit, independent-review
packet and final artifact hashes. Genuine independent review and final user
approval remain external gates.

## Packaging checkpoint

Implementing checkpoint `e1132fc`: final240 CLI/docs/isolated installer. Follow-up
adds exact archive inventory/hash/signature check (`scripts/check_release.py`),
tracks all current source/input/result/test files in RELEASE.json, and excludes
only operational AGENTS/EXPERIMENT notes via export-ignore (Git history unchanged).
Archive will include historical failed results, but no ignored/untracked outputs,
weights, capture/checkpoint tensors, environment, or Git metadata. Notes are not
dependencies; original historical input manifests/freezes/scores remain intact.

Tracked-file signature scan found zero common GitHub/HF/AWS keys or private-key
headers. Email hits are only `fixture@example.invalid` in saved session fixtures.
Private-network examples occur in excluded operational experiment log, not in
frozen prompt. Actual historical host paths remain in provenance JSON; they are
not anonymized or rewritten. Frozen prompt uses synthetic `/home/dev/services`,
authored repository/skill policies and upstream tool schemas/OpenCode text.

Notices now cover MIT AM, Apache2 CARTRIDGES and external4Bweights, alongside
existing MCP/OpenCode/runtime/model notices. Original OpenCode instruction revision
was not recorded: provenance limitation remains. No external implementation or
weights vendored. Source-output redistribution has not been legally certified;
owner must approve exact archive. Independent review packet covers all1320final
behavior responses and preserves disagreements; no independent reviewer claimed.

## Git-free checks accepted

Candidate0d6d2c7 exported without Git:546files/545SHA256entries (manifest itself
is the remaining file). Exact inventory/hash/credential-signature check passes.
All29small-dependencyCPUtestfiles pass in a newly installed Python3.12venv with
NumPy2.5.2/safetensors0.8.0 on XTX, no sharedsitepackages. Log
`/tmp/opencode/release-cpu.log`. Local NixPython failed to load NumPy's libz.so.1;
that attempt is not counted as success. No code workaround added for host linking.

Dockerpreflight from the same Git-freecandidate:all120authoredreferences pass,
all120unchangedbuggycontrols fail; toolreferenceactions schema-valid. Existing
pinned checksimageID`sha256:fc0672c2bcfe2086f222b738ad4433707ac8bb742bb5259e96c167ab7b735c11`.
JSON/log`/tmp/opencode/release-preflight.{json,log}`. This is recorded checkimage
reuse, not a freshDockerbuild. New runtime installation remains separately open.

Follow-up verifier also compares final27Bprompt/teacher/compiledhashes against
reusedv2tasks; tamperedteacher regression rejected. Failurediagnostic now accepts
explicit original/referencepaths; no frozen source identity was rewritten.

Fresh Docker checks image also built successfully from the pinned Python3.12.3
base on local Docker29.4.1 (`kvcompile-checks:release`), then all120positive/
120negative final-casechecks passed with schema references valid. Logs
`/tmp/opencode/release-docker-build.log` and
`/tmp/opencode/release-fresh-docker-preflight.{json,log}`. No generated code runs
on host. Isolated sourcecandidate81c2584 passes all29CPUfiles again and exact
547file/546hash inventory. Archive SHA256 at that checkpoint:
`386541709d3a46588156bd88553ef223d6a56af9a9de11ef2b3ec94df1d7b2d3`.
Email scan found only fixture@example.invalid; private-network patterns zero.
These identify the tested checkpoint, not a final archive modified afterward.

## Isolated installation diagnostic

Initial1815724 install downloaded/installed fresh inferenceTorch2.13+rocm7.2,
then nativebuild failed: `/opt/rocm/bin/hipcc: not found`. Host actually has
`hipconfig --path=/usr`, systemHIP7.1.52801 and Clang21.1.8 at
`/usr/lib/llvm-21/bin`, with Python3.14headers. This was a path assumption, not
proof of numerical/runtime incompatibility. Shared nativebuild used those paths.
Installer now validates paths fromhipconfig before downloads and permits only
markedrootresume. Original root manually marked after confirming sole ownership;
resume1834221 log `/tmp/opencode/release-install-v2.log`. No sharedenv edits.
Queued inference checks attempted after install exit and failed missinghfenv;
no generation/resume success is claimed. Rerun only after install success.

Fresh checksimageID is
`sha256:c18bd30069894a9e55dc08b32d969c3dd0ae868db5b1dbd767f04627fd36d74e`;
different from original hostimage, same pinned base and all240preflightoutcomes.
Sourceb1510d4 exported separately for training-onlycompiler4k/8k,AM4k/FP32V8k and
allfive4Bsmokes/resume checks, queued only after both freshenvironmentfreeze files
exist. No scored evaluation or training is queued. Native rebuild has192objects;
its outcome and new inference remain pending. Smoke output outside source:
`/mnt/data/artifacts/kvcompile/release-validation-smokes`; log
`/tmp/opencode/release-smokes-v2.log`. Monitor exactinstallPID1834221, not patterns.

## Fresh installation completed; inference checks started

Corrected isolated install finished successfully in 6,826s (including the fresh
native extension build) at 2026-10-18T21:23:19Z. Both environment package freezes
are retained under `release-validation-20261019/{exl,hf}-freeze.txt`. Models and
existing fitted artifacts are read-only inputs, not freshly trained reproduction.

User authorized the remaining short checks on 2026-10-19. Detached wrapper1844421
(launch shell1844420), source exportb1510d4, log
`/tmp/opencode/release-smokes-v2.log`, exit record
`/tmp/opencode/release-smokes-v2.exit`. Tiny compiler resume, cosine objective,
bounded upstream AM/head-resume, and AM attention/FP32 loader tests passed in the
fresh environments. Training-question 27B/4B inference and completed-resume checks
are running sequentially; no new benchmark score or fit is being produced.

## Fresh-runtime checks completed

Source export `b1510d4`; wrapper exited0 at 2026-10-19T04:12:40Z. Total sequence
1,609s (26m49s), including dependency checks, model hashing/loading and second
completed-resume passes. Both wrapper processes exited. About74GiB disk free.
Evidence, output hashes, package freezes and resume markers are retained in
`RELEASE_RUNTIME_SMOKES.json`; full log `/tmp/opencode/release-smokes-v2.log`.

- 27B compiler4096/8192: training-only generation finished at EOS, then completed
  resume reused the saved response. No quality denominator added to the report.
- AM4096 and AM8192FP32V: all-layer finite generation, bit-exact token/logit reload
  and unchanged recurrent injection passed. Smoke times97.050/110.003s; peak
 13.693/14.565GiB respectively. Both stopped at EOS on the training question.
- 4B full/none/compiler/AM/CARTRIDGES: all five generated; all five second passes
  reported `Already complete inference smoke`. CARTRIDGES retained64frozen and
  2445trainable tokens. No-prefix hit the intentional16token smoke cap; the other
  four stopped at EOS. This is successful execution, not semantic correctness:
  the 4B answers used npm despite the training reference saying pnpm.
- Tiny compiler interrupted/completed resume, objective normalization, upstream
  AM equivalence/head resume and attention/FP32 loader regression checks passed.

The native CARTRIDGES/Triton compile emitted a `_POSIX_C_SOURCE` redefinition
warning; generation and subsequent resume completed successfully. Existing models
and caches were reused read-only: this verifies fresh dependency installation and
inference, not a fresh fit or a new clean end-to-end benchmark reproduction.
Shared runtime/checkouts and original experiment outputs remain unchanged.
Remaining publication decisions: independent review or explicit exploratory
qualification, owner contents/rights approval, and authorization before upload.

## Publication disclaimer and README

User selected the exploratory-disclaimer route on 2026-10-19, not independent
review. README and main report now lead with AI-assistant/unblinded review,
single-seed/inspected-case limitations and no general superiority/safety claim.
README separates takeaways, tables, caveats, verification and licensing; scores,
raw responses, historical freezes and experiment identities are unchanged.
Independent-review packet is retained as optional future work. This decision is
not approval to push/upload or legal clearance of the exact source archive.
