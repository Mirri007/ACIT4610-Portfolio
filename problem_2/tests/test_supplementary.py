# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Tests for the supplementary analyses of Problem 2: the reference-optimum certificate and the (1+1)
diagnostics.

The certificate functions need only NumPy and are tested on small problems whose solution is known
analytically. The SLSQP search (SciPy) is tested only if SciPy is installed.
"""

import numpy as np
import pytest

from src.portfolio_data import build_case, load_case, PortfolioData, build_covariance
from src.portfolio_model import repair_portfolio, portfolio_variance
from src.run_es import run_es_on_case
from supplementary.one_plus_one_diagnostics import improvement_probability, run_one_plus_one_diagnostic
from supplementary.reference_optima import (
    dual_lower_bound,
    is_certified,
    kkt_residuals,
    solve_kkt_on_support,
)


# ---------------------------------------------------------------- reference optimum: known solutions

def test_two_assets_return_constraint_active():
    """
    Variances 0.04 and 0.01, no correlation, returns 10 % and 2 %, target 5 %.
    Without the target the minimum would be w = (0.2, 0.8) with return 3.6 % (too low), so the target
    binds: 0.10 w1 + 0.02 (1 - w1) = 0.05 -> w1 = 0.375, V = 0.375^2 * 0.04 + 0.625^2 * 0.01 = 0.00953125.
    """
    covariance = np.diag([0.04, 0.01])
    returns = np.array([0.10, 0.02])
    w, lam, mu = solve_kkt_on_support(covariance, returns, 0.05, np.array([0, 1]), return_active=True)
    assert w == pytest.approx([0.375, 0.625])
    assert w @ covariance @ w == pytest.approx(0.00953125)
    residuals = kkt_residuals(covariance, returns, 0.05, w, lam, mu)
    assert is_certified(residuals) and mu > 0
    assert dual_lower_bound(covariance, returns, 0.05, w, lam, mu) == pytest.approx(0.00953125, rel=1e-12)


def test_two_assets_return_constraint_inactive():
    """Same assets, target 3 %: the unconstrained minimum w = (0.2, 0.8), V = 0.04*0.04 + 0.64*0.01 = 0.008."""
    covariance = np.diag([0.04, 0.01])
    returns = np.array([0.10, 0.02])
    w, lam, mu = solve_kkt_on_support(covariance, returns, 0.03, np.array([0, 1]), return_active=False)
    assert w == pytest.approx([0.2, 0.8]) and mu == 0.0
    assert is_certified(kkt_residuals(covariance, returns, 0.03, w, lam, mu))


def test_assignment_three_asset_example_against_independent_solution():
    """
    Assignment example (std 10/20/30 %, zero correlation, returns 2/6/10 %, target 4 %). Independent
    solution: with diagonal Sigma, stationarity gives w_i = (lambda + mu r_i) / (2 s_i^2); the two
    unknowns follow from the budget and return equations (a 2x2 linear system solved here directly).
    """
    s2 = np.array([0.01, 0.04, 0.09])
    r = np.array([0.02, 0.06, 0.10])
    a = 1 / (2 * s2)
    system = np.array([[a.sum(), (a * r).sum()], [(a * r).sum(), (a * r * r).sum()]])
    lam, mu = np.linalg.solve(system, [1.0, 0.04])
    expected = a * (lam + mu * r)
    w, _, _ = solve_kkt_on_support(np.diag(s2), r, 0.04, np.array([0, 1, 2]), return_active=True)
    assert np.all(expected > 0)
    assert w == pytest.approx(expected, rel=1e-12)
    # It is better than the assignment's candidate B (variance 0.0081), as an optimum must be.
    assert w @ np.diag(s2) @ w < 0.0081


def test_certificate_rejects_a_non_optimal_portfolio():
    """
    A wrong support guess must fail. On port1 the optimum holds only 6 of 31 assets; solving the KKT
    equations as if ALL 31 were held gives a point that violates at least one condition (e.g. a
    negative weight), so the certificate must reject it.
    """
    case = load_case("port1_alpha025")
    n = case.data.n_assets
    w, lam, mu = solve_kkt_on_support(case.data.covariance, case.data.mean_returns, case.min_return,
                                      np.arange(n), return_active=True)
    assert not is_certified(kkt_residuals(case.data.covariance, case.data.mean_returns, case.min_return, w, lam, mu))


def test_dual_bound_never_exceeds_any_feasible_variance():
    """Weak duality: for arbitrary multipliers (mu, nu >= 0) the bound is below every feasible variance."""
    case = load_case("port2_alpha050")
    data = case.data
    rng = np.random.default_rng(1013)
    weights = repair_portfolio(rng.normal(size=data.n_assets), data.mean_returns, case.min_return, case.best_asset_index)
    for _ in range(20):
        bound = dual_lower_bound(data.covariance, data.mean_returns, case.min_return, weights,
                                 lam=rng.normal(0, 0.01), mu=abs(rng.normal(0, 0.1)))
        for _ in range(20):
            other = repair_portfolio(rng.normal(size=data.n_assets), data.mean_returns, case.min_return, case.best_asset_index)
            assert bound <= portfolio_variance(other, data.covariance) + 1e-15


def test_slsqp_search_finds_certified_optimum_on_port1():
    pytest.importorskip("scipy")
    from supplementary.reference_optima import find_reference_optimum
    reference = find_reference_optimum(load_case("port1_alpha050"))
    assert is_certified(reference["residuals"])
    assert reference["variance"] == pytest.approx(1.1663242820e-03, rel=1e-9)
    assert abs(reference["variance"] - reference["dual_bound"]) <= 1e-12 * reference["variance"]


# ---------------------------------------------------------------- (1+1) diagnostics

@pytest.mark.parametrize("case_name", ["port1_alpha050", "port3_alpha075"])
def test_diagnostic_one_plus_one_with_defaults_reproduces_the_assignment_algorithm(case_name):
    case = load_case(case_name)
    variance, weights = run_one_plus_one_diagnostic(case, seed=1014, budget=3000)
    official = run_es_on_case(case, "one_plus_one", seed=1014, budget=3000)
    assert variance == official["final_variance"]
    assert [float(x) for x in weights] == official["best_weights"]


def test_diagnostic_switches_change_the_run():
    case = load_case("port1_alpha050")
    default, _ = run_one_plus_one_diagnostic(case, seed=1015, budget=3000)
    fixed, _ = run_one_plus_one_diagnostic(case, seed=1015, budget=3000, adapt=False)
    assert default != fixed


def test_improvement_probability_is_zero_at_a_portfolio_with_no_better_neighbour():
    """Two assets, target equal to the best return: the only feasible portfolio is (0, 1)."""
    data = PortfolioData("toy", 2, np.array([0.01, 0.03]), np.array([0.1, 0.2]), np.eye(2),
                         build_covariance(np.array([0.1, 0.2]), np.eye(2)))
    case = build_case(data, alpha=1.0)        # R_min = r_max -> every repaired portfolio is (0, 1)
    rng = np.random.default_rng(1016)
    assert improvement_probability(case, np.array([0.0, 1.0]), 0.1, 200, rng) == 0.0
