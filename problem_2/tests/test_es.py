# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Tests for the evaluator/archive and the three ES variants.

Besides unit tests of each formula, several tests RECORD every evaluation of a real run and
check the algorithm's rules against that record, independently of the ES code:
  * (1+1)-ES: rebuild the step-size sequence from successes/failures and check that the mutation
    noise divided by that step size behaves like standard normal numbers;
  * population ES: rebuild the best variance of each generation from the recorded children and
    check plus / comma survivor selection.
Seeds >= 1000 are used here; the experiment seeds 0-9 are never used in tests.
"""

import math

import numpy as np
import pytest

from src import es_one_plus_one as one
from src import es_population as pop
from src.portfolio_data import load_all_cases, load_case
from src.portfolio_evaluator import PortfolioEvaluator
from src.portfolio_model import is_feasible, portfolio_variance, repair_portfolio
from src.run_es import BUDGET, VARIANTS, run_es_on_case


@pytest.fixture(scope="module")
def port1():
    return load_case("port1_alpha050")


class RecordingEvaluator(PortfolioEvaluator):
    """Evaluator that also stores every raw candidate, repaired portfolio and variance, in order."""

    def __init__(self, case, max_evaluations):
        super().__init__(case, max_evaluations)
        self.candidates, self.portfolios, self.variances = [], [], []

    def evaluate(self, candidate):
        weights, variance = super().evaluate(candidate)
        self.candidates.append(np.array(candidate, copy=True))
        self.portfolios.append(weights)
        self.variances.append(variance)
        return weights, variance


# ---------------------------------------------------------------- evaluator and archive

def test_evaluator_repairs_counts_and_archives(port1):
    evaluator = PortfolioEvaluator(port1, max_evaluations=3)
    rng = np.random.default_rng(1000)
    values = [evaluator.evaluate(rng.normal(size=31))[1] for _ in range(3)]
    assert evaluator.evaluations_used == 3
    assert evaluator.archive_variance == min(values)
    assert evaluator.history[0][0] == 1                         # initialisation is archived
    assert is_feasible(evaluator.archive_weights, port1.data.mean_returns, port1.min_return)
    with pytest.raises(RuntimeError, match="budget exceeded"):
        evaluator.evaluate(np.ones(31))


def test_evaluator_returns_repaired_portfolio_and_its_variance(port1):
    evaluator = PortfolioEvaluator(port1, max_evaluations=1)
    z = np.random.default_rng(1001).normal(size=31)
    weights, variance = evaluator.evaluate(z)
    expected = repair_portfolio(z, port1.data.mean_returns, port1.min_return, port1.best_asset_index)
    assert np.array_equal(weights, expected)
    assert variance == portfolio_variance(expected, port1.data.covariance)


# ---------------------------------------------------------------- (1+1)-ES

def test_one_plus_one_constants():
    assert one.initial_step_size(31) == pytest.approx(0.1 / math.sqrt(31))
    assert one.SUCCESS_FACTOR == pytest.approx(math.exp(1 / 3))
    assert one.FAILURE_FACTOR == pytest.approx(math.exp(-1 / 12))
    # 1/5 rule: average log-change p/3 - (1-p)/12 is zero at p = 1/5.
    p = 0.2
    assert p * math.log(one.SUCCESS_FACTOR) + (1 - p) * math.log(one.FAILURE_FACTOR) == pytest.approx(0, abs=1e-15)


def test_one_plus_one_step_size_update_and_clamping():
    assert one.update_step_size(0.01, True) == pytest.approx(0.01 * math.exp(1 / 3))
    assert one.update_step_size(0.01, False) == pytest.approx(0.01 * math.exp(-1 / 12))
    assert one.update_step_size(0.9, True) == 1.0              # clamped at the upper bound
    assert one.update_step_size(1e-8, False) == 1e-8           # clamped at the lower bound


def test_one_plus_one_trace_matches_the_rules(port1):
    """Rebuild acceptance and step sizes from the recorded run and check the mutation noise."""
    evaluator = RecordingEvaluator(port1, max_evaluations=3000)
    info = one.run_one_plus_one_es(evaluator, 31, np.random.default_rng(1002))
    assert evaluator.evaluations_used == 3000 and info["trials"] == 2999

    parent_weights, parent_variance = evaluator.portfolios[0], evaluator.variances[0]
    step_size = 0.1 / math.sqrt(31)
    successes = 0
    standardized_noise = []
    for k in range(1, 3000):
        # The raw candidate must be parent + step_size * (standard normal numbers).
        standardized_noise.append((evaluator.candidates[k] - parent_weights) / step_size)
        if evaluator.variances[k] < parent_variance:           # strictly lower -> accept
            parent_weights, parent_variance = evaluator.portfolios[k], evaluator.variances[k]
            step_size = min(step_size * math.exp(1 / 3), 1.0)
            successes += 1
        else:
            step_size = max(step_size * math.exp(-1 / 12), 1e-8)
    noise = np.concatenate(standardized_noise)
    assert abs(noise.mean()) < 0.01 and noise.std() == pytest.approx(1.0, abs=0.01)
    assert successes == info["successful_trials"]
    assert step_size == pytest.approx(info["final_step_size"], rel=1e-9)


# ---------------------------------------------------------------- population ES: formulas

def test_learning_rates():
    tau_prime, tau = pop.learning_rates(31)
    assert tau_prime == pytest.approx(1 / math.sqrt(62))
    assert tau == pytest.approx(1 / math.sqrt(2 * math.sqrt(31)))


def test_recombination_by_hand():
    a = pop.Individual(np.array([0.2, 0.8]), np.array([0.01, 1.0]), 0.0)
    b = pop.Individual(np.array([0.6, 0.4]), np.array([1.0, 0.04]), 0.0)
    weights, steps = pop.recombine(a, b)
    assert weights.tolist() == pytest.approx([0.4, 0.6])        # average
    assert steps.tolist() == pytest.approx([0.1, 0.2])          # sqrt(0.01*1)=0.1, sqrt(1*0.04)=0.2


def test_self_adaptation_formula_and_clamping():
    steps = pop.self_adapt_step_sizes(np.array([0.1, 0.1, 0.5]), 1.0, np.array([0.0, -1.0, 2.0]), 0.2, 0.5)
    assert steps[0] == pytest.approx(0.1 * math.exp(0.2))
    assert steps[1] == pytest.approx(0.1 * math.exp(0.2 - 0.5))
    assert steps[2] == 1.0                                       # 0.5*exp(1.2) = 1.66 -> clamped to 1.0
    assert pop.self_adapt_step_sizes(np.array([1e-8]), -5.0, np.array([0.0]), 1.0, 1.0)[0] == 1e-8


def test_self_adaptation_statistics():
    """log(sigma'/sigma) = tau'*Z0 + tau*Z_i: variance tau'^2 + tau^2, and two coordinates of the
    same child share Z0, so their correlation is tau'^2 / (tau'^2 + tau^2)."""
    tau_prime, tau = pop.learning_rates(31)
    rng = np.random.default_rng(1003)
    logs = np.array([np.log(pop.self_adapt_step_sizes(np.full(2, 0.01), rng.standard_normal(),
                                                      rng.standard_normal(2), tau_prime, tau) / 0.01)
                     for _ in range(40000)])
    assert logs.var() == pytest.approx(tau_prime ** 2 + tau ** 2, rel=0.03)
    assert np.corrcoef(logs[:, 0], logs[:, 1])[0, 1] == pytest.approx(tau_prime ** 2 / (tau_prime ** 2 + tau ** 2), abs=0.02)


def test_children_share_z0_across_their_coordinates(port1):
    """
    Through the REAL child-creation code: all parents have step sizes 0.01, so each child's
    log(sigma'/0.01) = tau'*Z0 + tau*Z_i. Because Z0 is shared within a child, two coordinates of
    the same child are correlated with correlation tau'^2 / (tau'^2 + tau^2) (about 0.155 for
    n = 31). If Z0 were drawn separately per coordinate, the correlation would be about 0.
    """
    tau_prime, tau = pop.learning_rates(31)
    weights = np.full(31, 1 / 31)
    parents = [pop.Individual(weights.copy(), np.full(31, 0.01), 1.0) for _ in range(10)]
    evaluator = PortfolioEvaluator(port1, max_evaluations=20000)
    rng = np.random.default_rng(1012)
    logs = np.array([np.log(pop.create_child(parents, 31, tau_prime, tau, evaluator, rng).step_sizes / 0.01)
                     for _ in range(20000)])
    expected_correlation = tau_prime ** 2 / (tau_prime ** 2 + tau ** 2)
    observed = np.mean([np.corrcoef(logs[:, 2 * k], logs[:, 2 * k + 1])[0, 1] for k in range(15)])
    assert observed == pytest.approx(expected_correlation, abs=0.02)
    assert logs.var() == pytest.approx(tau_prime ** 2 + tau ** 2, rel=0.03)


def test_child_uses_two_different_parents_and_their_average():
    class ZeroNoiseRng:
        """Real parent choice, but all normal numbers 0: the child equals the recombined weights."""
        def __init__(self):
            self.real = np.random.default_rng(1004)
        def choice(self, *args, **kwargs):
            return self.real.choice(*args, **kwargs)
        def standard_normal(self, size=None):
            return 0.0 if size is None else np.zeros(size)

    case = load_case("port1_alpha025")
    a = np.zeros(31); a[0] = 1.0
    b = np.zeros(31); b[1] = 1.0
    parents = [pop.Individual(a, np.full(31, 0.01), 1.0), pop.Individual(b, np.full(31, 0.01), 1.0)]
    evaluator = RecordingEvaluator(case, max_evaluations=50)
    rng = ZeroNoiseRng()
    for _ in range(50):
        pop.create_child(parents, 31, 0.1, 0.1, evaluator, rng)
    for candidate in evaluator.candidates:
        assert candidate == pytest.approx((a + b) / 2)           # never a copy of a single parent


def test_survivor_selection_plus_and_comma():
    def individuals(variances):
        return [pop.Individual(np.zeros(1), np.ones(1), v) for v in variances]
    parents = individuals([1.0] * 10)                            # 10 excellent parents
    offspring = individuals([float(v) for v in range(2, 72)])    # 70 worse children: 2, 3, ..., 71
    plus = pop.select_survivors(parents, offspring, "plus")
    comma = pop.select_survivors(parents, offspring, "comma")
    assert [i.variance for i in plus] == [1.0] * 10              # plus keeps the better parents
    assert [i.variance for i in comma] == list(range(2, 12))     # comma must take children only
    assert all(any(i is child for child in offspring) for i in comma)
    with pytest.raises(ValueError):
        pop.select_survivors(parents, offspring, "best")


# ---------------------------------------------------------------- population ES: traced runs

@pytest.mark.parametrize("selection", ["plus", "comma"])
def test_population_trace_matches_selection_rule(port1, selection):
    budget = 10 + 70 * 30 + 25          # 30 full generations + an incomplete batch of 25
    evaluator = RecordingEvaluator(port1, max_evaluations=budget)
    info = pop.run_population_es(evaluator, 31, np.random.default_rng(1005), selection)
    assert evaluator.evaluations_used == budget
    assert info["generations"] == 31 and info["final_batch_size"] == 25

    v = evaluator.variances
    expected_best = min(v[:10])
    rebuilt = [expected_best]
    for generation in range(30):
        children = v[10 + 70 * generation:10 + 70 * (generation + 1)]
        expected_best = min(children) if selection == "comma" else min(expected_best, min(children))
        rebuilt.append(expected_best)
    assert [value for _, value in info["population_best_history"]] == rebuilt

    archive = [value for _, value in evaluator.history]
    assert all(b < a for a, b in zip(archive, archive[1:]))      # archive only improves
    assert evaluator.archive_variance == min(v)                  # includes the last 25 children
    if selection == "plus":
        assert all(b <= a for a, b in zip(rebuilt, rebuilt[1:]))  # plus: population best never worse


def test_comma_population_best_can_worsen_but_archive_cannot():
    worsened = False
    for case_name in ["port1_alpha050", "port2_alpha050", "port3_alpha050"]:
        result = run_es_on_case(load_case(case_name), "mu_comma_lambda", seed=1006, budget=10 + 70 * 100)
        history = [value for _, value in result["details"]["population_best_history"]]
        worsened |= any(b > a for a, b in zip(history, history[1:]))
        assert result["final_variance"] <= min(history)          # archive is at least as good as any population
    assert worsened, "expected at least one generation where the comma population best got worse"


# ---------------------------------------------------------------- full runs

@pytest.mark.parametrize("variant", list(VARIANTS))
def test_full_budget_run(port1, variant):
    result = run_es_on_case(port1, variant, seed=1007)
    assert result["evaluations_used"] == BUDGET == 30_000
    assert result["feasible"] and result["invalid_evaluations"] == 0
    assert result["final_variance"] <= result["initial_best_variance"]
    assert result["archive_history"][0][0] == 1
    assert result["archive_history"][-1][1] == result["final_variance"]
    if variant == "one_plus_one":
        assert result["details"]["trials"] == 29_999
    else:
        # 30,000 = 10 + 428 * 70 + 30
        assert result["details"]["generations"] == 429 and result["details"]["final_batch_size"] == 30


@pytest.mark.parametrize("case", load_all_cases(), ids=lambda case: case.name)
def test_every_case_and_variant_gives_feasible_result_short_budget(case):
    for variant in VARIANTS:
        result = run_es_on_case(case, variant, seed=1008, budget=500)
        assert result["evaluations_used"] == 500
        assert result["feasible"] and result["invalid_evaluations"] == 0
        assert result["final_expected_return"] >= case.min_return - 1e-8


def test_reproducibility(port1):
    first = run_es_on_case(port1, "mu_comma_lambda", seed=1009, budget=2000)
    second = run_es_on_case(port1, "mu_comma_lambda", seed=1009, budget=2000)
    third = run_es_on_case(port1, "mu_comma_lambda", seed=1010, budget=2000)
    assert first["best_weights"] == second["best_weights"]
    assert first["archive_history"] == second["archive_history"]
    assert first["best_weights"] != third["best_weights"]


def test_unknown_variant_is_rejected(port1):
    with pytest.raises(ValueError):
        run_es_on_case(port1, "cma_es", seed=1011)
