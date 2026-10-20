"""Exact fixed-budget allocation on tiny measured loss curves; no model needed."""
import itertools
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from head_allocation import allocate

curves = {'layer0/head0': [(1, 9.), (2, 3.), (3, 2.)],
          'layer0/head1': [(1, 4.), (2, 3.), (3, 0.)]}
for budget in range(2, 7):
    counts, loss = allocate(curves, budget)
    brute = min(sum(p[1] for p in choice)
                for choice in itertools.product(*curves.values())
                if sum(p[0] for p in choice) == budget)
    assert sum(counts.values()) == budget and loss == brute
assert allocate(curves, 4) == ({'layer0/head0': 2, 'layer0/head1': 2}, 6.)
assert allocate(dict(reversed(list(curves.items()))), 4) == allocate(curves, 4)
# The curve may be nonmonotone: no smoothing or assumed diminishing returns.
assert allocate({'h': [(1, 0.), (2, 8.)]}, 2) == ({'h': 2}, 8.)
for curves, budget in (({}, 1), ({'h': []}, 1), ({'h': [(0, 1.)]}, 1),
                       ({'h': [(1, math.nan)]}, 1), ({'h': [(1, math.inf)]}, 1),
                       ({'h': [(1, 1.), (1, 2.)]}, 1),
                       ({'h': [(1, 1.)]}, 2), ({'h': [(1, 1.)]}, 1.5),
                       ({'h': [(1.5, 1.)]}, 1), ({'h': [(True, 1.)]}, 1)):
    try:
        allocate(curves, budget)
    except ValueError:
        pass
    else:
        raise AssertionError((curves, budget))
print('PASS exact allocation vs exhaustive search, deterministic order, invalid/unreachable budgets rejected')
