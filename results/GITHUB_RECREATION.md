# Reproduction from the public GitHub clone — 2026-10-19

User requested cloning the published repository into a new directory and
recreating results. This authorizes new reproduction runs, not changes to the
frozen cases, objectives, budgets, grading or original outputs.

## Source and prerequisites

- Cloned from `https://github.com/arpicato/qwen-kv-compiler.git`, public commit
  `73eab719c8f617b446af384f52d5dfc1ec68e4ff` (not a private working-tree export).
- GPU source: `/mnt/data/artifacts/kvcompile/github-recreate-20261019-source`.
- New output root: `/mnt/data/artifacts/kvcompile/github-recreate-20261019`.
- Reuse only existing model weights and the newly installed isolated dependencies
  in `release-validation-20261019`; no previous capture or fitted cache is input
  to the fresh 27B reproduction.
- Saved-result verification and all29CPUtestfiles passed from the GitHub clone.
  Logs `/tmp/opencode/github-recreate-{verify.json,cpu.log,plan.json}` on XTX.
- Started with74GiB free. Cleared only this agent's disposable isolated-install
  uv download cache (27.5GiB); installed environments and experiment artifacts
  untouched.102GiB free afterward, above the documented90GiB requirement.

## Planned sequence

First: the published19-phase27Brecipe, fresh812capture/projections/4k+8kfits,
historical evaluations and matched negative continuation. Then freeze and run the
final240cases against the new artifacts, review new responses separately, and
compare with published observations without selecting favorable outcomes.

After that checkpoint: fresh27BAM and controlled4Breproduction, sequential on the
GPU and subject to disk-space checks. No old teacher targets or fitted artifacts
may silently substitute for a failed fresh phase. Expected total is many hours;
901-target4Bcapture alone previously took3h50m. Runtime/model reuse is disclosed;
this is not a different machine/backend test.

## Status

Preflight/plan complete; fresh19-phase27Brecipe launched at
2026-10-19T05:14:27Z, detached wrapper1849965, runner1849969. Sequence log
`/tmp/opencode/github-recreate-27b.log`; reproduction log
`/tmp/opencode/github-recreate-reproduce.log`; wrapper exit record
`/tmp/opencode/github-recreate-27b.exit`. Run manifest will be
`/mnt/data/artifacts/kvcompile/github-recreate-20261019/27b/run.json`.
The same wrapper freezes/generates final240cases only after all19phases succeed.
No fresh-fit quality result yet.
Historical freezes/raw/reviews remain immutable. No new publication push is part
of this run. New behavior outputs require new response-bound manual reviews;
saved labels must not be copied onto changed answers.

## Authorized follow-up, not a competing run

User authorized a bounded compiler+AM uniform/nonuniform allocation study **after
reproduction finishes**. Protocol requirements are in
`NONUNIFORM_ALLOCATION_PLAN.md`. Keep that work queued behind this sequence;
no allocation fit or production-backend port starts while reproduction is active.

## Monitoring restored after laptop restart

At2026-10-19T09:42:14Z, remote wrapper1849965 and runner1849969 remained alive;
no job restart required. Fresh capture/projections and both400-step uniform fits
completed. Six of19phases complete; stress197 evaluation active. About82GiB free.
The interrupted local monitor was restored with a bounded exact-PID check and
exit-record check. No complete reproduction or final240result claimed yet.

## Completed generation and artifact audit

Wrapper exited0 at2026-10-19T11:19:02Z,21875s total.19phase recipe20075.541s;
final240×4generation1589.078s. All19phases complete and all152recordedphaseoutput
hashes rechecked successfully. Finalraw complete with60knowledge/60tools/120behavior
perarm. Knowledge/tools full60/59,none28/2,compiler4k46/51,compiler8k55/56 match
published totals. New behavior review still pending; no complete semantic
reproduction claim. User now prioritizes nonuniform ahead of AM/4Breproduction.
