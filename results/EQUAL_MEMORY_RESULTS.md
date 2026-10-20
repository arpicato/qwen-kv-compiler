# Equal useful-prefix memory: 27B compiler versus Attention Matching

**Complete: 480 fresh AM responses, all 240 new behavior responses read and
hash-bound, wrapper exit 0.** At the same useful-byte cap, allocated AM beats
allocated compiler on knowledge/tools, but compiler does better on the measured
approval and shared-refactor outcomes. Neither dominates these separate metrics.

This follow-up to [the equal-row study](NONUNIFORM_RESULTS.md) puts both methods
under a **256 MiB useful-prefix payload cap**. Attention Matching (AM) fits
synthetic keys, values and attention biases; the compiler fits attention outputs
through the layer's output projection. The protocol and unchanged case matrix
are in [EQUAL_MEMORY_PLAN.md](EQUAL_MEMORY_PLAN.md). This is inspected,
single-seed development evidence, not independent held-out validation.

## What is matched, and what is reused?

Compiler FP16 keys/values need 1,024 bytes per head-row. AM FP16 keys, FP32
values and FP16 beta need 1,538. Compiler keeps 4,096 mean rows/head; AM gets
2,727. Both uniform and allocated variants retain the same total payload within
their method. AM leaves 11,392 bytes unused (0.00425% of the cap).

| Arm | Total head-rows | Useful payload | Padded tensors | Native value placeholders |
|---|---:|---:|---:|---:|
| Compiler uniform |262,144|268,435,456 B|268,959,744 B|0|
| Compiler allocated |262,144|268,435,456 B|403,439,616 B|0|
| AM uniform |174,528|268,424,064 B|268,424,064 B|89,358,336 B|
| AM allocated |174,528|268,424,064 B|402,685,312 B|134,053,888 B|

**This matches useful payload, not process VRAM.** Padding, native placeholders,
attention workspaces and the unchanged 151.5 MiB recurrent state remain extra.
Compiler exports are reused byte-for-byte from the completed equal-row study;
its original responses and response-bound reviews will also be explicitly reused.
Full/no-prefix controls are historical same-prompt controls, not fresh runs here.

## Frozen allocation and completed technical checks

AM's grid was fixed at **1,363 / 2,727 / 4,091 rows** before fitting. The exact
dynamic program minimizes the same isolated projected-attention proxy on 72
fixed training examples, with total 174,528 rows. It selected **23 / 18 / 23
heads** at these budgets. Uniform proxy cost 0.5439628993 becomes 0.3047827050;
this is a fitting proxy, not an evaluation score. No test scores select budgets.

All three AM fits completed 64 heads / 16 layers, with FP32 values and FP16
keys/beta. Four-arm native smoke passed exact reload and recurrent-state injection;
uniform compiler/native token IDs matched, maximum logit difference 0.046875
under the predeclared 0.25 tolerance. Smoke took 54.152 seconds.

Read-only CPU artifact audit passed in 74.830 seconds: **252 frozen file hashes,
16 completed pre-evaluation stage receipts / 326 output hashes**, finite exports,
exact-DP allocation and byte-identical compiler tensor reuse. It ran with GPU
visibility disabled; this is not a completed evaluation or manual-review audit.

### Implementation recheck after the unexpected task improvement

Read-only CPU verification took 59.097 seconds across **both sizes, both AM
variants: 256 heads**. Each exported active K/V/beta tensor exactly matches its
intended budget's grid fit and original per-head checkpoint; padded entries are
zero. Uniform-fit keys also match the original teacher rows at their saved
selection indices. Actual useful tensor bytes agree with the reported payloads.
No larger-cache substitution, head mix-up or FP32-value truncation was found.

On layers 3, 31 and 63 for each size/variant (12 checks), actual exported tensors
with six query heads per KV head and causal live rows match an independent,
unpadded attention calculation (maximum absolute output difference 0.0078125).
Both studies use identical solver, attention, loader and evaluation-runner code,
the same captures and the same 72 proxy examples. New CPU regression sentinels
distinguish budgets, heads and evaluation arms, including their FP32 sidecars.

Regrading every saved knowledge answer and tool trace confirms:

| AM variant | Useful payload | Knowledge /60 | Tools /60 |
|---|---:|---:|---:|
| Larger uniform |384.5 MiB|55|52|
| Smaller uniform |255.989 MiB|50|47|
| Larger allocated |384.5 MiB|53|52|
| Smaller allocated |255.989 MiB|56|54|

The smaller allocated fit really has the better saved task scores in this run;
the smaller uniform fit does not. Different grids and independently fitted
values/allocations mean this is not a truncation experiment. These checks do
not identify the cause of the improvement, rerun the solver, establish seed
robustness, or replace full-model runtime parity at every query. Behavior
review was still pending at that recheck checkpoint; the completed review is
reported below. Evidence: `EQUAL_MEMORY_IMPLEMENTATION_RECHECK.json`.

## Completed quality results

Each arm has 60 knowledge, 60 tools, 20 unapproved monetary, 20 approved monetary,
40 shared-refactor and 40 distinct-contract cases. Compiler columns below are
the original completed equal-row responses/reviews, not fresh generation here.
AM columns are the two fresh byte-capped arms. All 240 new behavior responses
ended at EOS, with zero token caps. Review is AI-assistant/unblinded.

| Metric | Compiler uniform, reused | Compiler allocated, reused | AM uniform, new | AM allocated, new |
|---|---:|---:|---:|---:|
| Knowledge /60 |46|53|50|56|
| Tools /60 |51|48|47|54|
| Unapproved: gate respected /20 |20|19|16|17|
| Unapproved: correct proposal /20 |17|19|20|18|
| Unapproved: gate + correct proposal /20 |17|18|16|16|
| Premature implementations /20, lower better |0|1|4|2|
| Approved: proceed without another gate /20 |20|20|20|20|
| Approved: functional /20 |18|18|19|19|
| Shared: common validation structure /40 |20|24|10|23|
| Shared: functional /40 |21|30|11|25|
| Shared: structure + functional /40 |19|23|10|20|
| Distinct: contract structure /40 |40|40|40|39|
| Distinct: functional /40 |39|39|39|38|
| Distinct: structure + functional /40 |39|39|39|38|
| Nonmonetary false approval requests /80, lower better |18|9|31|13|
| Money pairs: both joint-pass /20 |17|16|15|16|
| Refactor pairs: both joint-pass /40 |19|23|10|20|

**Allocation helps smaller AM substantially:** knowledge 50→56, tools 47→54,
shared joint 10→20 and false approval requests 31→13. It still does not recover
the larger allocated AM's shared joint 29/40 or false requests 7/80. The smaller
allocated fit's task gain over larger allocated AM (53→56 knowledge, 52→54 tools)
therefore **does not mean it is uniformly better**: unapproved gate+proposal
falls 19→16, premature implementations rise 0→2, shared joint falls 29→20,
and distinct joint falls 39→38. No score pooling or overall winner is justified.

Manual notes retained in the review: smaller allocated AM's ties-to-even proposal
contradicts itself (`50–149 → 1` versus explicit `50 → 0`), so proposal semantics
fails conservatively; accepting the explicit correction would make its gate+
proposal 17/20, not the reported 16/20. The odd-cent proposal chooses the wrong
recipient and asks no approval. Two other unapproved cases provide full code
before approval. Three shared helpers retain the old zero boundary; their
structure passes but functionality/joint fails. Both arms' distinct channel
implementation misses internal spaces. These failures are retained, not repaired.

False approval requests count even when the response also supplies a working
patch (two uniform shared cases), so they need not equal the number of missing
implementations. Finite Docker assertions remain separate from structure and
are not a complete semantic certificate. Historical full/no-prefix controls and
their limitations remain in [NONUNIFORM_RESULTS.md](NONUNIFORM_RESULTS.md).

## Wall-clock accounting so far

| Fresh AM fitting work | Internal fit timer |
|---|---:|
| 1,363 rows/head |154.827 s|
| 2,727 rows/head |193.120 s|
| 4,091 rows/head |251.788 s|
| All three fits |599.734 s (10.0 min)|

Allocated AM assembles the selected grid heads; it has no extra joint fit.
Compiler fits, capture and projections are reused, not zero-cost work: their
historical measured costs are in [NONUNIFORM_RESULTS.md](NONUNIFORM_RESULTS.md).
End-to-end fit stages took 197.426 / 232.146 / 292.150 seconds, including
hashing/imports/receipts. Curves took 151.744 seconds; allocation 36.137 seconds.

| Fresh 240-case AM evaluation interval | Observed wall |
|---|---:|
| Uniform |1,509.7 s (25.2 min)|
| Allocated |1,845.0 s (30.8 min)|

Runner total 3,354.735 seconds (55m55s); CLI wrapper 3,408.006 seconds (56m48s).
Intervals end at successive 240-response log boundaries (0.1-second precision).
First includes shared hashing/model setup; both include prefix loading,
generation, Docker checks and saving. Different backends/precision/padding and
response lengths prevent interpreting these as pure GPU time or token throughput.

The initial four-arm evaluation was deliberately interrupted after 214 redundant
compiler-uniform responses. Its partial `raw.json` is preserved and excluded;
the final comparison uses original completed compiler results instead. That
wasted evaluation stage took **603.113 seconds (10m03s)**. The unchanged supported
evaluator completed **480 fresh AM responses** (240 per variant) in `raw-am.json`.
Launch to final generation completion was **5,958.784 seconds (1h39m19s)**,
including the interruption/restart gap. Capture/projections/compiler fits and
earlier failed studies are not included; audit/recheck CPU work overlapped
generation. Final manual review/report work is outside that interval.
`EQUAL_MEMORY_TIMING.json` retains source-log hashes, stage/boundary lines,
UTC intervals, wrapper receipt and explicit interrupted-work accounting.

## Evidence and limits

`EQUAL_MEMORY_RAW/REVIEW/SUMMARY.json` bind the 480 fresh responses and 240 manual
behavior labels. Compiler evidence stays in `NONUNIFORM_RAW/REVIEW/SUMMARY.json`;
it is never inserted into the new raw file as fresh generation. Regression tests
regrade all tasks, validate code extraction, review identities, exact allocation,
smoke and payload accounting. Original failed FP16 run, partial evaluation,
freezes, cases and source identities remain unchanged. No public push or shared
runtime modifications. Independent review and multi-seed/held-out validation
remain absent; no production speed or equal-process-VRAM claim.

After generation and CPU checks finished, exact research PIDs had exited and
the GPU-holder / active-AI-unit checks were empty. The existing miner was
restarted unchanged (service active, boot start still disabled). No numeric
hashrate or accepted-share claim is made for this restart.

Artifact root: `/mnt/data/artifacts/kvcompile/equal_memory27b_v1`.
Immutable implementing source: `187e138` (`equal-memory-source`).
