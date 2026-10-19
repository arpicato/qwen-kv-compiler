# LR / step sweep (phase 15b)

Static lr=1e-3, no decay, no warmup was the phase 14/15 setup (Adam,
bias_correction=False, matched to mlx defaults).

## 1. Layers plateau at very different points
Deterministic full-set loss, K=8192, projected objective (opt-in --full-eval):

| layer | % of total progress by step 200 | gain step 400->1599 |
|---|---:|---:|
| 3 | 98% | 0.0006 |
| 11 | 96% | 0.003 |
| 15 | 94% | 0.006 |
| 27 | 95% | 0.014 |
| 47 | 87% | 0.039 |
| 63 | 88% | **0.221** |

All layers converge toward ~-3.00, but deeper layers start far lower (layer 63
starts at +0.80) and need proportionally more optimisation. The single 400-step
budget was undersized for the deep layers.

## 2. Hard layers are lr-limited, not step-limited
5 hard layers, step 400, identical data/seed, full-eval:

| layer | static 1e-3 | lr 3e-3 | lr 3e-3 cosine |
|---|---:|---:|---:|
| 47 | -2.95324 | -2.99205 | -2.98058 |
| 51 | -2.91186 | -2.98366 | -2.96185 |
| 55 | -2.93408 | -2.98910 | -2.97292 |
| 59 | -2.71177 | -2.95016 | -2.87478 |
| 63 | -2.71628 | -2.94412 | -2.86847 |
| **mean** | **-2.84545** | **-2.97182** | **-2.93172** |

- Raising lr 1e-3 -> 3e-3: **-0.126 mean training loss** (up to 0.238 on the
  deepest layers); already visible by step 100.
- **Cosine decay (3e-3 -> 3e-4) is WORSE than flat 3e-3** (-0.086 vs -0.126).
  The hard layers are still descending and want the large lr for the whole
  budget; decay only helps if you would otherwise overshoot, which is not
  happening here (the 3e-3 curve is monotone on every layer).

## 3. The loss gain does NOT transfer to behaviour
| variant | agent retention | held-out retention |
|---|---:|---:|
| projected, static 1e-3 | 0.978 (44/45) | **0.774** (82/106) |
| projected + lr 3e-3 deep | 0.978 (44/45) | 0.764 (81/106) |

A -0.126 training-loss improvement produced **zero** downstream gain (a hair
worse on held-out, within noise). **The projected training loss is not a tight
proxy for behaviour once it is small**: further reducing it on plateaued layers
buys nothing, because the residual behaviour error is not located where the
remaining loss is. Mirrors the phase-14 capacity ceiling.

## Takeaways
- Use `--full-eval` only for convergence analysis (costs ~2x wall clock).
- lr is a real, cheap lever on *training loss* for deep layers (3e-3 > 1e-3);
  decay is not useful here.
- Do not chase the projected loss below the plateau: it stops predicting
  behaviour. The held-out bottleneck needs a different attack (query drift /
  trajectory refresh), not more optimisation of the same objective.
