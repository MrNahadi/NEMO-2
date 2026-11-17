"""Foil hydrodynamics for the stabilizer fin.

* ``naca_00xx``: coordinates of a symmetric NACA four-digit section.
* ``panel_solve``: 2D Hess-Smith panel method (constant-strength sources on
  each panel plus one vortex strength shared by all panels, with the Kutta
  condition at the trailing edge). Gives the pressure around the section and
  its lift coefficient in inviscid flow. Checked against the exact flow around
  a circle and against the thick-foil lift slope 2 pi (1 + 0.77 t/c).
* ``whicker_fehlner``: lift of a low-aspect-ratio control surface from
  Whicker and Fehlner (1958), as given in Molland and Turnock, Marine Rudders
  and Control Surfaces (2007): a linear lift-slope term plus a cross-flow term.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

SEA_WATER_DENSITY = 1025.0  # kg/m3
VAPOUR_PRESSURE_PA = 1700.0  # sea water at about 15 C
ATMOSPHERE_PA = 101_325.0
CROSSFLOW_DRAG = 0.8  # square tip, Whicker and Fehlner
KNOT = 0.514444


def naca_thickness(x: np.ndarray, t: float) -> np.ndarray:
    """Half thickness y_t / c of a NACA 00xx section at x / c (closed trailing edge form)."""
    return 5.0 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1036 * x**4)


def naca_00xx(t: float, panels: int = 160) -> tuple[np.ndarray, np.ndarray]:
    """Panel end points, clockwise from the trailing edge along the lower surface (chord 1)."""
    half = panels // 2
    beta = np.linspace(0.0, math.pi, half + 1)
    x = 0.5 * (1.0 - np.cos(beta))  # cosine spacing, 0 at the leading edge
    y = naca_thickness(x, t)
    xs = np.concatenate([x[::-1], x[1:]])
    ys = np.concatenate([-y[::-1], y[1:]])
    return xs, ys


@dataclass(frozen=True)
class PanelResult:
    alpha_deg: float
    cl: float
    x_mid: np.ndarray
    cp: np.ndarray

    @property
    def cp_min(self) -> float:
        return float(self.cp.min())


def panel_solve(xs: np.ndarray, ys: np.ndarray, alpha_deg: float) -> PanelResult:
    """Hess-Smith panel method. ``xs, ys`` are closed-contour panel end points, clockwise."""
    alpha = math.radians(alpha_deg)
    n = len(xs) - 1
    xm, ym = 0.5 * (xs[:-1] + xs[1:]), 0.5 * (ys[:-1] + ys[1:])
    dx, dy = np.diff(xs), np.diff(ys)
    length = np.hypot(dx, dy)
    theta = np.arctan2(dy, dx)

    xi, yi = xm[:, None], ym[:, None]
    r1 = np.hypot(xi - xs[None, :-1], yi - ys[None, :-1])
    r2 = np.hypot(xi - xs[None, 1:], yi - ys[None, 1:])
    beta = np.arctan2((xi - xs[None, :-1]) * (yi - ys[None, 1:]) - (yi - ys[None, :-1]) * (xi - xs[None, 1:]),
                      (xi - xs[None, :-1]) * (xi - xs[None, 1:]) + (yi - ys[None, :-1]) * (yi - ys[None, 1:]))
    np.fill_diagonal(beta, math.pi)
    log = np.log(np.where(np.eye(n, dtype=bool), 1.0, r2 / np.maximum(r1, 1e-14)))
    d = theta[:, None] - theta[None, :]
    sin_d, cos_d = np.sin(d), np.cos(d)
    two_pi = 2.0 * math.pi
    src_n = (sin_d * log + cos_d * beta) / two_pi
    src_t = (sin_d * beta - cos_d * log) / two_pi
    vor_n = -src_t
    vor_t = src_n

    a = np.zeros((n + 1, n + 1))
    rhs = np.zeros(n + 1)
    a[:n, :n] = src_n
    a[:n, n] = vor_n.sum(axis=1)
    rhs[:n] = np.sin(theta - alpha)  # minus the free stream's normal component
    a[n, :n] = src_t[0] + src_t[-1]
    a[n, n] = vor_t[0].sum() + vor_t[-1].sum()
    rhs[n] = -(math.cos(alpha - theta[0]) + math.cos(alpha - theta[-1]))
    sol = np.linalg.solve(a, rhs)
    q, gamma = sol[:n], sol[n]
    vt = src_t @ q + gamma * vor_t.sum(axis=1) + np.cos(alpha - theta)
    cp = 1.0 - vt**2
    chord = xs.max() - xs.min()
    cl = 2.0 * gamma * length.sum() / chord
    return PanelResult(alpha_deg, float(cl), xm, cp)


def section_lift_slope(t: float) -> float:
    """Lift slope (per radian) of the 2D section from the panel method."""
    xs, ys = naca_00xx(t)
    return panel_solve(xs, ys, 4.0).cl / math.radians(4.0)


def pressure_peak(t: float, cl: float) -> tuple[float, float]:
    """Section angle that gives section lift ``cl``, and the lowest pressure coefficient at that angle."""
    slope = section_lift_slope(t)
    alpha = math.degrees(cl / slope)
    xs, ys = naca_00xx(t)
    return float(alpha), float(panel_solve(xs, ys, alpha).cp_min)


def whicker_fehlner(aspect_ratio: float, alpha_deg: float, sweep_deg: float = 0.0) -> tuple[float, float]:
    """Lift coefficient and lift slope (per radian) of a low-aspect-ratio control surface."""
    a = aspect_ratio
    cos_l = math.cos(math.radians(sweep_deg))
    slope = 0.9 * 2.0 * math.pi * a / (cos_l * math.sqrt(a**2 / cos_l**4 + 4.0) + 1.8)
    alpha = math.radians(alpha_deg)
    return float(slope * alpha + CROSSFLOW_DRAG / a * alpha**2), float(slope)


def cavitation_number(depth_m: float, speed_ms: float) -> float:
    return (ATMOSPHERE_PA + SEA_WATER_DENSITY * 9.80665 * depth_m - VAPOUR_PRESSURE_PA) / (0.5 * SEA_WATER_DENSITY * speed_ms**2)


def circle_contour(panels: int = 120) -> tuple[np.ndarray, np.ndarray]:
    """A unit-diameter circle, clockwise, for checking the panel method against the exact solution."""
    ang = np.linspace(0.0, -2.0 * math.pi, panels + 1)
    return 0.5 + 0.5 * np.cos(ang), 0.5 * np.sin(ang)
