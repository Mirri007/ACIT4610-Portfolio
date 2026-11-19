# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""Tests for the continuous Bees Algorithm (Part B): initialisation, neighbourhood, clipping, budget, reproducibility."""

import numpy as np
import pytest

from src.bees_algorithm import BeesSettings
from src.bees_continuous import (
    CONTINUOUS_BEES_SETTINGS,
    NEIGHBOURHOOD_FRACTION,
    create_neighbour_vector,
    create_random_vector,
    run_bees_on_function,
)
from src.benchmark_functions import BENCHMARK_FUNCTIONS
from src.evaluation_tracker import expand_history_to_every_evaluation


# ---------------------------------------------------------------- random scouts

@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
@pytest.mark.parametrize("dimension", [10, 30])
def test_random_vectors_have_right_shape_and_stay_in_bounds(name, dimension):
    _, lower, upper = BENCHMARK_FUNCTIONS[name]
    rng = np.random.default_rng(1)
    for _ in range(500):
        vector = create_random_vector(lower, upper, dimension, rng)
        assert vector.shape == (dimension,)
        assert np.all(vector >= lower) and np.all(vector <= upper)


def test_random_vectors_are_uniform_over_the_whole_range():
    # Rosenbrock bounds [-5, 10]: 100,000 values split into 5 equal bins of width 3 -> about 20 % each.
    rng = np.random.default_rng(2)
    values = create_random_vector(-5.0, 10.0, 100_000, rng)
    counts, _ = np.histogram(values, bins=5, range=(-5.0, 10.0))
    assert np.all(np.abs(counts / 100_000 - 0.2) < 0.01)
    assert values.mean() == pytest.approx(2.5, abs=0.05)   # midpoint of [-5, 10]


# ---------------------------------------------------------------- neighbourhood move

def test_neighbourhood_fraction_is_ten_percent():
    assert NEIGHBOURHOOD_FRACTION == 0.10


@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
def test_every_coordinate_changes_by_at_most_ten_percent_of_range(name):
    _, lower, upper = BENCHMARK_FUNCTIONS[name]
    maximum_change = 0.10 * (upper - lower)
    rng = np.random.default_rng(3)
    # Sites well inside the bounds (centre region) so that clipping cannot happen.
    middle = (lower + upper) / 2
    for _ in range(500):
        site = rng.uniform(middle - 0.2 * (upper - lower), middle + 0.2 * (upper - lower), size=30)
        neighbour = create_neighbour_vector(site, lower, upper, rng)
        changes = neighbour - site
        assert np.all(np.abs(changes) <= maximum_change + 1e-12)


def test_changes_fill_the_whole_interval_and_are_independent_per_coordinate():
    # Sphere: range 10.24 -> changes uniform in [-1.024, 1.024]. Starting at 0 no clipping occurs.
    rng = np.random.default_rng(4)
    changes = np.array([create_neighbour_vector(np.zeros(30), -5.12, 5.12, rng) for _ in range(5000)])
    assert changes.min() < -1.0 and changes.max() > 1.0          # both ends of the interval are reached
    assert abs(changes.mean()) < 0.01                            # symmetric around 0
    # Uniform on [-a, a] has variance a^2 / 3 = 1.024^2 / 3 = 0.3495
    assert changes.var() == pytest.approx(1.024 ** 2 / 3, rel=0.03)
    # Independent coordinates: every coordinate changes, and correlation between coordinates is ~0.
    assert np.all(changes != 0)
    correlation = np.corrcoef(changes[:, 0], changes[:, 1])[0, 1]
    assert abs(correlation) < 0.05


def test_clipping_example_from_docstring():
    class FixedChanges:
        """Fake generator returning chosen changes, to check the arithmetic exactly."""
        def uniform(self, low, high, size):
            assert low == pytest.approx(-1.024) and high == pytest.approx(1.024)
            return np.array([0.5, -0.3])
    neighbour = create_neighbour_vector(np.array([5.0, -2.0]), -5.12, 5.12, FixedChanges())
    assert neighbour.tolist() == pytest.approx([5.12, -2.3])     # 5.5 clipped to the upper bound


@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
def test_neighbours_of_boundary_points_are_clipped_into_bounds(name):
    _, lower, upper = BENCHMARK_FUNCTIONS[name]
    rng = np.random.default_rng(5)
    hit_lower = hit_upper = False
    for corner in (lower, upper):
        for _ in range(300):
            neighbour = create_neighbour_vector(np.full(30, corner), lower, upper, rng)
            assert np.all(neighbour >= lower) and np.all(neighbour <= upper)
            hit_lower |= bool(np.any(neighbour == lower))
            hit_upper |= bool(np.any(neighbour == upper))
    assert hit_lower and hit_upper   # clipping really happened at both bounds


def test_neighbour_does_not_modify_the_site():
    rng = np.random.default_rng(6)
    site = np.array([1.0, 2.0, 3.0])
    create_neighbour_vector(site, -5.12, 5.12, rng)
    assert site.tolist() == [1.0, 2.0, 3.0]


# ---------------------------------------------------------------- full runs

@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
@pytest.mark.parametrize("dimension", [10, 30])
def test_full_run_uses_exactly_30000_evaluations_and_returns_valid_vector(name, dimension):
    result = run_bees_on_function(name, dimension, seed=0)
    function, lower, upper = BENCHMARK_FUNCTIONS[name]
    vector = np.array(result["best_vector"])
    assert result["evaluations_used"] == 30_000
    assert vector.shape == (dimension,)
    assert np.all(vector >= lower) and np.all(vector <= upper)
    assert function(vector) == result["final_best_value"]          # value reproducible from saved vector
    assert result["final_best_value"] <= result["initial_best_value"]
    assert result["final_best_value"] >= -1e-12                     # cannot beat the global minimum 0
    history = result["best_so_far_history"]
    assert history[0][0] == 1 and history[-1][1] == result["final_best_value"]
    curve = expand_history_to_every_evaluation(history, 30_000)
    assert np.all(np.diff(curve) <= 0)                               # best-so-far never gets worse


def test_chosen_settings_arithmetic():
    # 1*100 + 2*50 + 7 = 207 per iteration; 10 + 144*207 = 29,818; 182 left for iteration 145.
    assert CONTINUOUS_BEES_SETTINGS.evaluations_per_iteration() == 207
    assert run_bees_on_function("sphere", 10, seed=5)["iterations_started"] == 145


def test_iteration_count_with_incomplete_final_iteration():
    settings = CONTINUOUS_BEES_SETTINGS
    full_iterations = (30_000 - settings.n_scouts) // settings.evaluations_per_iteration()
    leftover = 30_000 - settings.n_scouts - full_iterations * settings.evaluations_per_iteration()
    expected_iterations = full_iterations + (1 if leftover > 0 else 0)
    result = run_bees_on_function("sphere", 10, seed=1)
    assert result["iterations_started"] == expected_iterations


def test_small_budget_is_respected_exactly():
    settings = BeesSettings(n_scouts=5, n_selected_sites=3, n_elite_sites=1, n_bees_elite=4,
                            n_bees_selected=2, max_evaluations=37)
    result = run_bees_on_function("rastrigin", 10, seed=2, settings=settings)
    assert result["evaluations_used"] == 37


def test_same_seed_gives_identical_run_and_different_seed_differs():
    first = run_bees_on_function("ackley", 10, seed=3)
    second = run_bees_on_function("ackley", 10, seed=3)
    third = run_bees_on_function("ackley", 10, seed=4)
    for key in ("final_best_value", "best_vector", "best_so_far_history", "initial_best_value"):
        assert first[key] == second[key]
    assert first["best_vector"] != third["best_vector"]


def test_unknown_function_is_rejected():
    with pytest.raises(ValueError, match="Unknown function"):
        run_bees_on_function("griewank", 10, seed=0)
