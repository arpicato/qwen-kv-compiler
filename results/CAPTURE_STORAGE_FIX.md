# Bounded capture storage for the next run

Implemented locally; **not copied to XTX or applied to the running long-policy job**.
No competing GPU job, large remote write, or modification of live artifacts.

`scripts/capture_agent_exl3.py` now checkpoints only new trajectory batches using
`scripts/capture_store.py`. Each layer has an append-only stream; teacher prefix
is stored separately. After a durable metadata commit the batch lists are cleared.
Array contents, query selection, precision, calibration items and fitting targets
are unchanged. Only small question/index metadata grows with example count.

Checkpoint metadata records the committed byte offset for every layer. A crash
before metadata publication leaves harmless uncommitted tails; resume ignores them
and truncates them on append. Missing/truncated committed bytes fail validation.
Old incomplete checkpoints migrate one layer at a time, preserving original files
until the append-format manifest is published. Completed old captures are left
alone. Verified seed captures import one layer at a time. Checkpoint intervals now
work for every allowed value, not only intervals coinciding with multiples of five.

At completion, compatibility export assembles **one layer at a time** into the
existing `layer_NNN.pkl` format; compiler/readers require no changes. `complete`
is published only after all exported files are written. Interrupted export can
restart from captured streams without model recapture. Streams are retained for
recovery: storage is approximately doubled until explicitly cleaned up. No automatic
deletion of recovery files. One layer must still fit host RAM during export/compiler;
this fix bounds capture accumulation, not every process allocation or allocator RSS.

Verification:
- Small failing test first: missing new storage module, confirmed before implementation.
- `python3 scripts/test_capture_store.py`: passed batch release, unchanged earlier
  bytes, crash-tail recovery, committed truncation rejection, repeated export, typed
  payload byte parity and unchanged legacy shard dictionary structure.
- Synthetic32-batch fixture: >16MB written, traced Python current96,600bytes,
  peak638,224bytes. This is a CPU storage-unit measurement, not GPU/RSS benchmarking.
- Existing decision-position/query-alignment tests and Python syntax passed.

No GPU integration/parity run yet: the authorized experiment is still using the
old remote capture script. Before the next long run, sync the new capture script
**and its storage module**, run a tiny capture and compare exported arrays/positions
against the legacy path, then use normal compiler commands. Historical scripts and
artifact hashes on XTX remain intact. Do not hot-swap this into an active process.
