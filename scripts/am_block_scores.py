"""Bounded row-score temporaries; retain upstream NNLS and least-squares solvers."""
import contextlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import torch
from compaction.algorithms.base import CompactionAlgorithm
from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction


def _scores(q, keys, bias=None):
    scores = (q @ keys.T).float() * (keys.shape[1] ** -0.5)
    if bias is not None:
        scores += bias
    maximum = scores.max(dim=1, keepdim=True).values
    return torch.exp(scores - maximum)


@contextlib.contextmanager
def block_scores(rows=1024, checkpoint_dir=None, recipe=None, offload_cache=False, values_dtype=None):
    original_select = HighestAttentionKeysCompaction._select_keys_highest_attention
    original_values = CompactionAlgorithm._compute_C2
    original_compute = HighestAttentionKeysCompaction.compute_compacted_cache
    original_cat = torch.cat

    def cat(tensors, dim=0, *, out=None):
        result = original_cat(tensors, dim=dim, out=out)
        # Qwen3's eight per-head exports become one finished cache layer.
        if offload_cache and dim == 1 and len(tensors) == 8 and out is None:
            if all(x.ndim in (3, 4) and x.shape[:2] == (1, 1) for x in tensors):
                return result.cpu()
        return result
    completed = 0
    started_all = time.monotonic()
    if checkpoint_dir is not None:
        checkpoint_dir = Path(checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        config_path = checkpoint_dir / 'recipe.json'
        if config_path.exists():
            assert json.loads(config_path.read_text()) == recipe, 'AM checkpoint recipe differs'
        else:
            config_path.write_text(json.dumps(recipe, indent=2))

    def compute(self, K, V, queries, t, attention_bias=None):
        nonlocal completed
        from safetensors.torch import load_file, save_file
        path = checkpoint_dir / f'head_{completed:03d}.safetensors'
        completed += 1
        if path.exists():
            cached = load_file(str(path), device=str(K.device))
            assert cached['k'].shape == (t, K.shape[1]), 'AM checkpoint shape differs'
            assert all(torch.isfinite(cached[key]).all() for key in ('k', 'beta', 'v'))
            result = cached['k'], cached['beta'], cached['v'], cached['indices'].tolist()
            torch.set_rng_state(cached['cpu_rng'].cpu())
            if K.is_cuda:
                torch.cuda.set_rng_state(cached['cuda_rng'].cpu(), K.device)
            print(f'{datetime.now(timezone.utc).isoformat()} resumed head={completed}', flush=True)
        else:
            result = original_compute(self, K, V, queries, t, attention_bias)
            assert all(torch.isfinite(value).all() for value in result[:3])
            temporary = path.with_suffix('.partial')
            tensors = {'k': result[0].cpu().contiguous(), 'beta': result[1].cpu().contiguous(),
                       'v': result[2].cpu().contiguous(), 'indices': torch.tensor(result[3]),
                       'cpu_rng': torch.get_rng_state()}
            if K.is_cuda:
                tensors['cuda_rng'] = torch.cuda.get_rng_state(K.device)
            save_file(tensors, str(temporary))
            temporary.replace(path)
        elapsed = time.monotonic()-started_all
        print(f'{datetime.now(timezone.utc).isoformat()} checkpoint heads={completed} '
              f'elapsed={elapsed:.1f}s rate={completed/max(elapsed,.001):.3f}heads/s artifact={path}', flush=True)
        return result

    def progress(phase, completed, total, start):
        elapsed = time.monotonic() - start
        rate = completed / max(elapsed, .001)
        print(f'{datetime.now(timezone.utc).isoformat()} {phase} elapsed={elapsed:.1f}s '
              f'completed={completed}/{total} rate={rate:.1f}rows/s '
              f'ETA={(total-completed)/rate:.1f}s', flush=True)

    def select(self, K, queries, t, attention_bias=None):
        assert self.score_method == 'rms' and self.pooling is None and self.beta_method == 'nnls'
        assert attention_bias is None, 'agent prefix fitting has no original bias'
        n = queries.shape[0]
        assert n > 0
        sums = torch.zeros(K.shape[0], device=K.device, dtype=torch.float32)
        started = time.monotonic()
        for start in range(0, n, rows):
            exp = _scores(queries[start:start+rows].to(K.device), K)
            weights = exp / exp.sum(dim=1, keepdim=True)
            sums += weights.square().sum(dim=0)
        progress('key-score', n, n, started)
        key_scores = torch.sqrt(sums / n)
        selected = torch.topk(key_scores, t, largest=True).indices
        C1 = K[selected]
        M = torch.empty(n, t, device=K.device, dtype=torch.float32)
        target = torch.empty(n, device=K.device, dtype=torch.float32)
        started = time.monotonic()
        for start in range(0, n, rows):
            exp = _scores(queries[start:start+rows].to(K.device), K)
            M[start:start+rows] = exp[:, selected]
            target[start:start+rows] = exp.sum(dim=1)
        progress('NNLS-matrix', n, n, started)
        print(f'{datetime.now(timezone.utc).isoformat()} NNLS solve shape={tuple(M.shape)}', flush=True)
        if K.is_cuda:
            torch.cuda.empty_cache()
        B = self._nnls_pg(M, target, self.nnls_iters, self.nnls_lower_bound, self.nnls_upper_bound)
        return C1, torch.log(B).to(K.dtype), selected.cpu().tolist()

    def values(self, C1, beta, K, V, queries, attention_bias=None, ridge_lambda=0,
               solver='lstsq', ridge_scale='spectral'):
        assert attention_bias is None and ridge_lambda == 0 and solver == 'lstsq'
        n, t = queries.shape[0], C1.shape[0]
        X = torch.empty(n, t, device=K.device, dtype=torch.float32)
        Y = torch.empty(n, V.shape[1], device=K.device, dtype=torch.float32)
        started = time.monotonic()
        for start in range(0, n, rows):
            q = queries[start:start+rows].to(K.device)
            exp = _scores(q, K)
            Y[start:start+rows] = (exp / exp.sum(dim=1, keepdim=True)) @ V.float()
            scores = (q @ C1.T).float() * (K.shape[1] ** -0.5) + beta.float()
            exp = torch.exp(scores - scores.max(dim=1, keepdim=True).values)
            X[start:start+rows] = exp / exp.sum(dim=1, keepdim=True)
        progress('value-matrix', n, n, started)
        print(f'{datetime.now(timezone.utc).isoformat()} value lstsq shape={tuple(X.shape)}', flush=True)
        if K.is_cuda:
            torch.cuda.empty_cache()
        # Same unregularized solver and driver as upstream, not normal equations.
        fitted = torch.linalg.lstsq(X, Y, driver='gels').solution
        assert torch.isfinite(fitted).all(), 'nonfinite least-squares solution'
        return fitted.to(K.dtype if values_dtype is None else values_dtype)

    HighestAttentionKeysCompaction._select_keys_highest_attention = select
    CompactionAlgorithm._compute_C2 = values
    if checkpoint_dir is not None:
        HighestAttentionKeysCompaction.compute_compacted_cache = compute
    if offload_cache:
        torch.cat = cat
    try:
        yield
    finally:
        HighestAttentionKeysCompaction._select_keys_highest_attention = original_select
        CompactionAlgorithm._compute_C2 = original_values
        HighestAttentionKeysCompaction.compute_compacted_cache = original_compute
        torch.cat = original_cat
