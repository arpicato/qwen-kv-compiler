"""Choose one measured budget per head with an exact total, without test scores.

Curves must come from a separately frozen calibration/validation protocol.
This solves the sum of supplied per-head losses, not end-to-end model quality.
"""
import math


def allocate(curves, total):
    if type(total) is not int or total <= 0 or not curves:
        raise ValueError('positive integer total and nonempty head curves required')
    heads = sorted(curves)
    choices = []
    for head in heads:
        points = curves[head]
        if not points:
            raise ValueError(f'empty curve: {head}')
        seen = set()
        for rows, loss in points:
            if type(rows) is not int or rows <= 0 or rows in seen or not math.isfinite(loss):
                raise ValueError(f'invalid curve: {head}')
            seen.add(rows)
        choices.append(sorted(points))
    # Sparse dynamic programming also handles nonmonotone/nonconvex curves.
    states = {0: (0., ())}
    for points in choices:
        next_states = {}
        for used, (loss, counts) in states.items():
            for rows, cost in points:
                size = used + rows
                if size > total:
                    continue
                candidate = (loss + cost, counts + (rows,))
                if size not in next_states or candidate < next_states[size]:
                    next_states[size] = candidate
        states = next_states
    if total not in states:
        raise ValueError('total budget cannot be reached by the measured choices')
    loss, counts = states[total]
    return dict(zip(heads, counts)), loss
