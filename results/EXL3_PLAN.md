"""Plan: EXL3 trajectory capture + compile/eval on the XTX box (Phase 14).

State: port validated. src/exl3.py round-trips the 26,033-token prefix
(bit-exact state; argmax-agreement continuations; ROCm long-ctx attention is
non-deterministic so greedy agreement is the fidelity bar).

This plan captures the calibration trajectories the compiler needs, in the
same v2-causal-occupied schema the MLX path produced, then compiles and
evaluates at K=6508 and K=8192.

--------------------------------------------------------------------------------
1. Trajectory capture (scripts/capture_agent_exl3.py)

For each of the 71 training questions:
  - Install the teacher prefix (block only) via write_prefix_state  (26,033 slots).
  - Forward the USER TURN; record, per full-attn layer L in [3,7,...,63]:
      q_rot   -- the LAST prompt row's post-RoPE query (predicts answer token 0)
      gate    -- its gate slice
    and the user-suffix live K/V (rows [n_sys, offset)) at logical positions
    n_sys..n_sys+n_user-1.
  - Forward the ANSWER (teacher-forced); record per layer:
      q_rot rows at selected answer positions, post-RoPE
      k_rot / values for all answer rows
      gate rows
  - Assemble q_rot/gate/k_live/v_live + q_logical/k_logical exactly as the MLX
    v2 capture does (causal support, occupied length only).

Capture mechanism: monkeypatch Attention.decode_flash_attn_nc for the 16
full-attn layers. The wrapper reads q,k,v,g AFTER project_qkv + RoPE (the eager
path applies RoPE inline), so it records exactly the tensors attention used.
Must run with the eager path (no bc_attn graph) - the graph path never
materialises q_rot/k_rot in python.

Output: one shard per layer, same keys as the MLX v2 shard:
    {"k_sys", "v_sys", "schema": "v2-causal-occupied", "traj": [...]}

Memory: capture ONE layer at a time -> write shard -> release. The 26k k_sys/v_sys
per layer is 4*26033*256*2*2 = ~107 MB fp16 per layer; 16 layers = 1.7 GB total.
Full teacher KV is ~853 MB fp16 (matches the recorded MLX number).

--------------------------------------------------------------------------------
2. Teacher state (scripts/capture_agent_teacher_exl3.py)

Capture + save delta/attn for the block prefix, write state.json with:
  source, system_tokens=26033, prompt_hash, model repo, kv_bytes, delta_bytes.
Reuse extract_teacher_state (already bit-exact verified).

--------------------------------------------------------------------------------
3. Compile (existing scripts/compile_torch_v2.py, unchanged)

Needs: torch+ROCm (present), safetensors. No model required. Verify:
  - chunked backward == full backward (loss rel < 1e-5) on ROCm
  - K=8192 peak memory fits the free VRAM (chunk=2)
Run: --slots 6508 and --slots 8192, --batched --batch-chunk 2 --freeze-sink
     --examples-per-update 24, steps 400, lr 1e-3, bf16.

--------------------------------------------------------------------------------
4. Eval (port scripts/eval_toolset_fast.py)

Three arms on `agent` (78 hand probes) and `agent_heldout` (generated):
  teacher  -- full prefix installed
  none     -- no resident prefix (user turn only)
  compiled -- K synthetic slots installed, continuation at logical n_sys
Greedy, max_tokens=64, full EOS set, grade via eval.grade_instruction.
Report: informative retention, per-kind, paired gains/losses, KL (with the
~0.03 noise floor noted), mean/median length, cap hits.

--------------------------------------------------------------------------------
5. Projected-loss arm (only if raw-K K=8192 leaves lookup failures)

Export o_proj for layers 3/27/63, validate layout vs ExLlama's operator, then
train K/V against o_proj(sigmoid(gate)*(attn_s - attn_t)). Pilot 3 layers
before a full compile.
"""
