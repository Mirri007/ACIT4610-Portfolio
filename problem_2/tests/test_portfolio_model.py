# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Tests for return, variance, simplex projection, repair and feasibility checks.

Independent checks used here:
  * the assignment's numerical example (candidates A and B);
  * variance by an explicit double loop over all pairs of assets;
  * simplex projection compared with a completely different algorithm (bisection on theta),
    plus the defining property: no point of the simplex is closer to z than the projection.
"""

import numpy as np
import pytest

from src.portfolio_data import load_all_cases
from src.portfolio_model import (
    expected_return,
    feasibility_violations,
    is_feasible,
    portfolio_variance,
    project_onto_simplex,
    repair_portfolio,
)

# The assignment's three-asset example: returns 2 %, 6 %, 10 %; std 10 %, 20 %, 30 %; zero correlation.
EXAMPLE_RETURNS = np.array([0.02, 0.06, 0.10])
EXAMPLE_COVARIANCE = np.diag([0.10, 0.20, 0.30]) ** 2


def projection_by_bisection(z, iterations=200):
    """Independent method: find theta with sum(max(z - theta, 0)) = 1 by repeated halving."""
    low, high = z.min() - 1.0, z.max()     # sum >= 1 at 'low', sum = 0 at 'high'
    for _ in range(iterations):
        middle = (low + high) / 2
        if np.maximum(z - middle, 0).sum() > 1:
            low = middle
        else:
            high = middle
    return np.maximum(z - (low + high) / 2, 0)


# ---------------------------------------------------------------- return and variance

def test_assignment_numerical_example():
    a = np.array([0.5, 0.3, 0.2])
    b = np.array([0.6, 0.3, 0.1])
    assert expected_return(a, EXAMPLE_RETURNS) == pytest.approx(0.048)
    assert portfolio_variance(a, EXAMPLE_COVARIANCE) == pytest.approx(0.0097)
    assert expected_return(b, EXAMPLE_RETURNS) == pytest.approx(0.040)
    assert portfolio_variance(b, EXAMPLE_COVARIANCE) == pytest.approx(0.0081)
    # B has lower variance and still meets the 4 % target, so (1+1)-ES would replace A with B.
    assert portfolio_variance(b, EXAMPLE_COVARIANCE) < portfolio_variance(a, EXAMPLE_COVARIANCE)


@pytest.mark.parametrize("case", load_all_cases()[::3], ids=lambda case: case.data.name)
def test_variance_matches_explicit_double_loop(case):
    s, C = case.data.std_devs, case.data.correlation
    rng = np.random.default_rng(1001)
    w = rng.dirichlet(np.ones(case.data.n_assets))
    double_loop = sum(w[i] * w[j] * s[i] * s[j] * C[i, j]
                      for i in range(len(w)) for j in range(len(w)))
    assert portfolio_variance(w, case.data.covariance) == pytest.approx(double_loop, rel=1e-12)


def test_single_asset_portfolio_variance_is_its_own_variance():
    w = np.array([0.0, 1.0, 0.0])
    assert portfolio_variance(w, EXAMPLE_COVARIANCE) == pytest.approx(0.04)


# ---------------------------------------------------------------- simplex projection

def test_projection_worked_example_from_docstring():
    assert project_onto_simplex([0.3, 0.2, -0.5]) == pytest.approx([0.55, 0.45, 0.0])


@pytest.mark.parametrize(
    "z, expected",
    [
        ([0.5, 0.5], [0.5, 0.5]),          # already on the simplex: unchanged
        ([1.0, 1.0], [0.5, 0.5]),          # too large: both shifted down by 0.5
        ([2.0, 0.0], [1.0, 0.0]),          # one big entry takes everything
        ([-1.0, -1.0], [0.5, 0.5]),        # all negative: shifted up equally
        ([0.2, 0.2, 0.2], [1 / 3] * 3),    # too small: shifted up equally
    ],
)
def test_projection_hand_examples(z, expected):
    assert project_onto_simplex(z) == pytest.approx(expected)


def test_projection_matches_bisection_and_is_closest_point():
    rng = np.random.default_rng(1002)
    for _ in range(300):
        n = int(rng.integers(2, 60))
        z = rng.normal(0, rng.uniform(0.01, 3), size=n)
        q = project_onto_simplex(z)
        assert np.all(q >= 0) and q.sum() == pytest.approx(1, abs=1e-12)
        assert q == pytest.approx(projection_by_bisection(z), abs=1e-10)
        # Closest-point property: random simplex points are never closer to z than q.
        others = rng.dirichlet(np.ones(n), size=50)
        assert np.all(np.linalg.norm(others - z, axis=1) >= np.linalg.norm(q - z) - 1e-12)


def test_projection_is_idempotent():
    rng = np.random.default_rng(1003)
    q = project_onto_simplex(rng.normal(size=40))
    assert project_onto_simplex(q) == pytest.approx(q, abs=1e-15)


# ---------------------------------------------------------------- return-target repair

def test_repair_worked_example_from_docstring():
    w = repair_portfolio(np.array([0.8, 0.2, 0.0]), EXAMPLE_RETURNS, 0.04, best_asset_index=2)
    assert w == pytest.approx([2 / 3, 1 / 6, 1 / 6])
    assert expected_return(w, EXAMPLE_RETURNS) == pytest.approx(0.04, abs=1e-15)


def test_repair_leaves_feasible_projection_unchanged():
    # q = (0.2, 0.3, 0.5): return 0.072 >= 0.04, so step 2 does nothing.
    w = repair_portfolio(np.array([0.2, 0.3, 0.5]), EXAMPLE_RETURNS, 0.04, best_asset_index=2)
    assert w == pytest.approx([0.2, 0.3, 0.5])


@pytest.mark.parametrize("case", load_all_cases(), ids=lambda case: case.name)
def test_repair_always_produces_feasible_portfolios(case):
    r = case.data.mean_returns
    rng = np.random.default_rng(1004)
    for scale in (0.001, 0.1, 10):
        for _ in range(100):
            z = rng.normal(0, scale, size=case.data.n_assets)
            w = repair_portfolio(z, r, case.min_return, case.best_asset_index)
            assert is_feasible(w, r, case.min_return), feasibility_violations(w, r, case.min_return)
            q = project_onto_simplex(z)
            if expected_return(q, r) < case.min_return:
                # Repaired candidates land exactly on the target (up to rounding).
                assert expected_return(w, r) == pytest.approx(case.min_return, abs=1e-15)


# ---------------------------------------------------------------- feasibility tolerances

def test_feasibility_tolerance_boundaries():
    r = EXAMPLE_RETURNS
    assert is_feasible(np.array([0.5, 0.3, 0.2]), r, 0.048)
    assert is_feasible(np.array([0.5, 0.3, 0.2 + 0.9e-8]), r, 0.04)             # sum off by < 1e-8
    assert not is_feasible(np.array([0.5, 0.3, 0.2 + 2e-8]), r, 0.04)           # sum off by > 1e-8
    assert is_feasible(np.array([0.5 + 0.5e-8, 0.5, -0.5e-8]), r, 0.0)          # tiny negative allowed
    assert not is_feasible(np.array([0.5 + 2e-8, 0.5, -2e-8]), r, 0.0)          # too negative
    assert is_feasible(np.array([0.5, 0.3, 0.2]), r, 0.048 + 0.9e-8)            # return just within
    assert not is_feasible(np.array([0.5, 0.3, 0.2]), r, 0.048 + 2e-8)          # return too low
    assert len(feasibility_violations(np.array([1.2, 0.0, -0.2]), r, 0.5)) == 2  # negative + return
