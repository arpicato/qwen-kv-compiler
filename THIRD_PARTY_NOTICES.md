# Third-party material

MIT-0 applies to original project code and authored material only. It does not
replace these upstream terms or the licenses of external dependencies.

- GitHub MCP tool schemas/descriptions, including copies in prompts, calibration
  answers, probes and reports: github/github-mcp-server, revision
  `eb47a99ddb866ca2b8a162920e6bda9521f33ebb`, MIT, Copyright2025GitHub.
  Full license: `src/data_mcp/github-mcp-server/LICENSE`.
- The agent prompt embeds/adapts OpenCode instruction text. OpenCode
  (https://github.com/anomalyco/opencode), MIT, Copyright2025opencode.
  Full notice: `licenses/opencode-MIT.txt`. The precise original instruction
  revision was not recorded; do not claim otherwise. Repository policies and
  behavioral tasks in the input bundle are synthetic research fixtures.
- External ExLlamaV3/ROCm runtime: MIT, Copyright2025Turboderp; use the license
  in the pinned runtime checkout. No runtime code or weights are vendored here.
- External model: Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw, based on
  Qwen/Qwen3.8-27B; model card identifies Apache-2.0. Obtain its LICENSE with
  the pinned download. This repository does not relicense model weights or
  guarantee that derived cache state contains no source-prompt/model information.

- External Attention Matching implementation: adamzweiger/compaction, revision
  `2020f6d37940fe013e7e7f1ebf409e5d107c5670`, MIT, Copyright (c) 2026 Adam Zweiger.
  Obtain its `LICENSE` with the checkout. This project imports upstream code and
  temporarily replaces score assembly/LSQ output storage in a session-local
  wrapper; upstream implementation is not vendored.
- External CARTRIDGES: HazyResearch/cartridges, revision
  `ef34ba97a06049c34820506e2c283746284ae5f0`, Apache-2.0; retain its `LICENSE.md`
  (including Copyright 2021 The Meerkat Team) when redistributing upstream code.
  No implementation is vendored. Tested source imports use Transformers 4.57.1,
  outside the upstream package's advertised <=4.55 dependency bound; this is a
  pinned experimental integration, not an upstream compatibility guarantee.
- External Qwen/Qwen3-4B weights: obtain their Apache-2.0 LICENSE and model card.
  Exact tested file hashes are recorded in `CONTROLLED4B_CAPTURE_AUDIT.json` and
  final 4B raw evidence; do not substitute another snapshot silently.

The proposed source archive contains no model weights, captures or fitted cache
tensors. Saved answers/code remain generated research evidence and can reflect
upstream prompt content. Source-prompt rights/notices and raw-output privacy must
be reviewed together; no legal clearance or anonymization guarantee is claimed.
Archived Git history must retain applicable notices and is not the audited public
surface. No results imply endorsement. Runtime pins live in `runtime.json` and
the 4B/AM recipe in `REPRODUCE.md`.
