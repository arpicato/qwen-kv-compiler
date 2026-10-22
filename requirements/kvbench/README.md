# Recorded 4B and Attention Matching environment

`requirements.txt` records all 107 installed packages from the retired research environment, captured on 2026-10-23 before deletion. Python was 3.12.15, with Torch 2.8.0+rocm6.4 and Transformers 4.57.1. The full snapshot includes packages installed for other tools.

Use [REPRODUCE.md](../../REPRODUCE.md#controlled-4b-and-am-runtimes) and `scripts/install_release_runtime.sh` for the tested runtime setup and pinned upstream source revisions. Reinstallation of this complete package snapshot has not been retested. The separate 27B inference environment is specified in that reproduction guide.

Model: `Qwen/Qwen3-4B`, downloaded revision `1cfa9a7208912126459214e8b04321603b3df60c`. Model identity and file hashes were already recorded in `results/CONTROLLED4B_CAPTURE_AUDIT.json` and the final 4B evidence. The local weights and retired environment can be downloaded/recreated from those records.

[provenance.json](provenance.json) records the exact model and retired earlier-comparison dataset revisions for downloading them again. The latter dataset is separate from the final controlled study.
