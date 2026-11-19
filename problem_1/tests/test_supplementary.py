# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""Tests for the Problem 1 supplementary diagnostics and the Part A paired comparison."""

import numpy as np
import pytest

from experiments.make_tsp_tables import paired_neighbourhood_comparison
from src.bees_continuous import create_neighbour_vector
from supplementary.continuous_diagnostics import (
    improvement_probability,
    late_improvement_share,
    neighbour_with_fraction,
    run_with_fraction,
)
from src.bees_continuous import CONTINUOUS_BEES_SETTINGS, run_bees_on_function


def test_ten_percent_neighbour_is_identical_to_the_assignment_neighbour():
    vector = np.random.default_rng(1).uniform(-5.12, 5.12, 30)
    first = neighbour_with_fraction(vector, -5.12, 5.12, 0.10, np.random.default_rng(7))
    second = create_neighbour_vector(vector, -5.12, 5.12, np.random.default_rng(7))
    assert np.array_equal(first, second)


def test_ten_percent_diagnostic_run_reproduces_the_assignment_run():
    # With the assignment's 10 % the diagnostic runner must give exactly the official result.
    official = run_bees_on_function("rastrigin", 10, seed=1017)["final_best_value"]
    assert run_with_fraction("rastrigin", 10, 1017, CONTINUOUS_BEES_SETTINGS, 0.10) == official


def test_improvement_probability_at_the_optimum_is_zero():
    rng = np.random.default_rng(2)
    assert improvement_probability("sphere", np.zeros(10), 500, rng) == 0.0


def test_improvement_probability_far_from_the_optimum_is_high():
    # At the corner (5.12, ..., 5.12) of Sphere, any change that is clipped or points inwards helps.
    rng = np.random.default_rng(3)
    assert improvement_probability("sphere", np.full(10, 5.12), 500, rng) > 0.9


def test_late_improvement_share_example():
    # Initial 100, final 10 (total improvement 90). Value at evaluation 15,000 is 19 -> 9 of 90 = 10 % later.
    history = [[1, 100.0], [10_000, 19.0], [20_000, 10.0]]
    assert late_improvement_share(history, 100.0, 10.0) == pytest.approx(0.10)
    assert late_improvement_share([[1, 5.0]], 5.0, 5.0) == 0.0


def test_paired_neighbourhood_comparison_counts():
    results = []
    for seed, (swap, reversal) in enumerate([(500, 450), (480, 480), (430, 470)] + [(600, 500)] * 7):
        results.append({"instance": "eil51", "neighbourhood": "swap", "seed": seed, "final_best_length": swap})
        results.append({"instance": "eil51", "neighbourhood": "reversal", "seed": seed, "final_best_length": reversal})
    row = next(r for r in paired_neighbourhood_comparison(results) if r["instance"] == "eil51")
    assert (row["reversal_shorter"], row["swap_shorter"], row["equal"]) == (8, 1, 1)
    assert row["mean_difference_swap_minus_reversal"] == pytest.approx((50 + 0 - 40 + 7 * 100) / 10)
