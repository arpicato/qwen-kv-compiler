"""Tiny CPU fixture: bounded AM matches pinned solver and resumes saved heads."""
from pathlib import Path
import os
import sys
import tempfile

sys.path.insert(0, os.environ['COMPACTION_DIR'])
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import torch
from compaction.algorithms.highest_attention_keys import HighestAttentionKeysCompaction
from am_block_scores import block_scores

torch.manual_seed(0)
k, v, q = (torch.randn(*shape) for shape in ((48, 8), (48, 8), (96, 8)))
algorithm = HighestAttentionKeysCompaction(score_method='rms', nnls_iters=2,
    nnls_lower_bound=.05, nnls_upper_bound=20, c2_method='lsq')
torch.manual_seed(1)
reference = algorithm.compute_compacted_cache(k, v, q, 8)
with tempfile.TemporaryDirectory() as directory:
    torch.manual_seed(1)
    with block_scores(rows=16, checkpoint_dir=directory, recipe={'test': True}):
        actual = algorithm.compute_compacted_cache(k, v, q, 8)
    assert actual[3] == reference[3]
    for a, b in zip(actual[:3], reference[:3]):
        assert torch.allclose(a, b, atol=1e-4, rtol=1e-4), (a-b).abs().max()
    with block_scores(rows=16, checkpoint_dir=directory, recipe={'test': True}):
        resumed = algorithm.compute_compacted_cache(k, v, q, 8)
    assert all(torch.equal(a, b) for a, b in zip(actual[:3], resumed[:3]))
print('PASS bounded AM selected keys/beta/values vs pinned upstream; exact head resume')
