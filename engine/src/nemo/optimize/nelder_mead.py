"""Bounded Nelder-Mead search on variables scaled to [0, 1].

Gradient-free: it only needs the objective value, so it works with code checks
that have corners (max of several checks) and with discrete choices handled
outside it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

Objective = Callable[[list[float]], float]


@dataclass(frozen=True)
class NelderMeadResult:
    x: list[float]
    value: float
    evaluations: int
    iterations: int


def nelder_mead(
    objective: Objective,
    start: Sequence[float],
    *,
    max_iter: int = 200,
    initial_step: float = 0.15,
    tolerance: float = 1e-7,
) -> NelderMeadResult:
    n = len(start)
    cache: dict[tuple[float, ...], float] = {}
    evaluations = 0

    def f(x: list[float]) -> float:
        nonlocal evaluations
        key = tuple(round(v, 12) for v in x)
        if key not in cache:
            cache[key] = objective(list(x))
            evaluations += 1
        return cache[key]

    x0 = _clip(list(start))
    simplex = [x0]
    for i in range(n):
        vertex = list(x0)
        vertex[i] = vertex[i] + initial_step if vertex[i] + initial_step <= 1.0 else vertex[i] - initial_step
        simplex.append(_clip(vertex))
    values = [f(v) for v in simplex]

    iterations = 0
    for iterations in range(1, max_iter + 1):
        order = sorted(range(n + 1), key=lambda i: values[i])
        simplex = [simplex[i] for i in order]
        values = [values[i] for i in order]
        if abs(values[-1] - values[0]) <= tolerance * (abs(values[0]) + 1e-12):
            spread = max(max(abs(a - b) for a, b in zip(v, simplex[0])) for v in simplex[1:])
            if spread < 1e-4:
                break

        centroid = [sum(v[d] for v in simplex[:-1]) / n for d in range(n)]
        worst = simplex[-1]
        reflected = _clip([c + (c - w) for c, w in zip(centroid, worst)])
        fr = f(reflected)
        if values[0] <= fr < values[-2]:
            simplex[-1], values[-1] = reflected, fr
            continue
        if fr < values[0]:
            expanded = _clip([c + 2.0 * (r - c) for c, r in zip(centroid, reflected)])
            fe = f(expanded)
            simplex[-1], values[-1] = (expanded, fe) if fe < fr else (reflected, fr)
            continue
        contracted = _clip([c + 0.5 * (w - c) for c, w in zip(centroid, worst)])
        fc = f(contracted)
        if fc < values[-1]:
            simplex[-1], values[-1] = contracted, fc
            continue
        best = simplex[0]
        for i in range(1, n + 1):
            simplex[i] = _clip([b + 0.5 * (v - b) for b, v in zip(best, simplex[i])])
            values[i] = f(simplex[i])

    best_index = min(range(n + 1), key=lambda i: values[i])
    return NelderMeadResult(simplex[best_index], values[best_index], evaluations, iterations)


def _clip(x: list[float]) -> list[float]:
    return [min(max(float(v), 0.0), 1.0) for v in x]
