"""Built-in padeye stress analysis."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from build123d import Box
from skfem import Basis, ElementTetP2, ElementVector, asm
from skfem.models.elasticity import lame_parameters, linear_elasticity

from nemo.data import get_material
from nemo.fea import mesh_part, to_skfem
from nemo.fea.solver import _assemble_elasticity
from nemo.loads import LiftScenario, padeye_loads
from nemo.parts.padeye import PadeyeDesign
from nemo.parts.padeye.fea import analyse_padeye

DESIGN = PadeyeDesign(20, 45, 21, 200, 90, 8)
LOADS = padeye_loads(LiftScenario(4000, 2, 60))
STEEL = get_material("S355")


def test_fast_assembly_matches_scikit_fem():
    m = to_skfem(mesh_part(Box(50, 20, 10), global_size_mm=6))
    basis = Basis(m, ElementVector(ElementTetP2()))
    lam, mu = lame_parameters(210_000, 0.3)
    reference = asm(linear_elasticity(lam, mu), basis)
    fast = _assemble_elasticity(m, basis, lam, mu)
    assert abs(reference - fast).max() < 1e-12 * abs(reference).max()


@pytest.fixture(scope="module")
def study():
    return analyse_padeye(DESIGN, material=STEEL, loads=LOADS, levels=(1.0, 0.7))


def test_applied_load_equals_sling_force(study):
    applied = np.array(study.levels[-1].applied_force_n)
    expected = np.array([LOADS.horizontal_n, LOADS.side_n, LOADS.vertical_n])
    # The pin-bearing shape is scaled to the sling force; on a faceted hole its
    # resultant direction differs from the sling by a tiny amount.
    assert applied == pytest.approx(expected, rel=1e-4)


def test_supports_balance_the_load(study):
    for level in study.levels:
        assert level.reaction_balance_error < 1e-6


def test_head_stress_converges(study):
    assert study.converged
    assert study.convergence_change < 0.05


def test_result_is_consistent_with_code_check(study):
    # Nominal pin bearing stress F / (Dp t) = 22,648 / (19.1 x 20) = 59.3 MPa. The FEA peak at the
    # contact must be higher (stress concentration) but within a plausible range for a pinned lug.
    nominal = LOADS.sling_force_n / (19.1 * 20)
    assert 1.0 * nominal < study.head_von_mises_mpa < 3.0 * nominal
    assert study.factor_of_safety_on_yield > 2.0


def test_thinner_plate_has_higher_stress(study):
    thin = analyse_padeye(replace(DESIGN, main_thickness_mm=12), material=STEEL, loads=LOADS, levels=(1.0,))
    assert thin.head_von_mises_mpa > study.head_von_mises_mpa * 1.3
