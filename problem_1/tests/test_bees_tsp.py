# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Tests for the Bees Algorithm core and for full TSP runs.

Small settings and budgets are used where possible so the tests run quickly; a few tests use
the real assignment settings (30,000 evaluations) on eil51 to check the exact budget.
"""

import numpy as np
import pytest

from src.bees_algorithm import BeesSettings, run_bees_algorithm
from src.bees_tsp import TSP_BEES_SETTINGS, percentage_gap, run_bees_on_tsp
from src.evaluation_tracker import EvaluationTracker, expand_history_to_every_evaluation
from src.tsp_instances import instance_file_path
from src.tsp_neighbourhoods import swap_move
from src.tsp_tour import compute_distance_matrix, create_random_tour, is_valid_tour, tour_length
from src.tsplib import load_tsplib_instance

SMALL_SETTINGS = BeesSettings(
    n_scouts=10, n_selected_sites=4, n_elite_sites=2, n_bees_elite=5, n_bees_selected=3,
    max_evaluations=100,
)


@pytest.fixture(scope="module")
def eil51():
    return load_tsplib_instance(instance_file_path("eil51"))


class RecordingObjective:
    """
    Objective function wrapper that independently records every call.

    This lets a test check the tracker's evaluation count against an independent count,
    and check the reported best against the minimum of ALL values ever computed.
    """

    def __init__(self, distances):
        self.distances = distances
        self.values = []

    def __call__(self, tour):
        value = tour_length(tour, self.distances)
        self.values.append(value)
        return value


def run_small_ba(instance, seed, settings=SMALL_SETTINGS):
    distances = compute_distance_matrix(instance.coordinates)
    objective = RecordingObjective(distances)
    tracker = EvaluationTracker(objective, settings.max_evaluations)
    info = run_bees_algorithm(
        tracker,
        lambda rng: create_random_tour(instance.dimension, rng),
        swap_move,
        settings,
        np.random.default_rng(seed),
    )
    return tracker, objective, info


# ---------------------------------------------------------------- settings

def test_assignment_settings_arithmetic():
    # 1*100 + 1*50 + 4 = 154 evaluations per full iteration.
    assert TSP_BEES_SETTINGS.evaluations_per_iteration() == 154
    assert TSP_BEES_SETTINGS.max_evaluations == 30_000


@pytest.mark.parametrize(
    "bad",
    [
        dict(n_scouts=5, n_selected_sites=6, n_elite_sites=2, n_bees_elite=3, n_bees_selected=2),  # m > n
        dict(n_scouts=10, n_selected_sites=4, n_elite_sites=5, n_bees_elite=3, n_bees_selected=2),  # e > m
        dict(n_scouts=10, n_selected_sites=4, n_elite_sites=2, n_bees_elite=0, n_bees_selected=2),  # nep = 0
    ],
)
def test_invalid_settings_are_rejected(bad):
    with pytest.raises(ValueError):
        BeesSettings(**bad).check()


# ---------------------------------------------------------------- evaluation counting

def test_budget_used_exactly_with_incomplete_final_iteration(eil51):
    # Small settings: 10 initial + 22 per iteration (2*5 + 2*3 + 6).
    # 100 = 10 + 4*22 (= 98) + 2 -> the 5th iteration is cut off after only 2 evaluations.
    assert SMALL_SETTINGS.evaluations_per_iteration() == 22
    tracker, objective, info = run_small_ba(eil51, seed=0)
    assert tracker.evaluations_used == 100
    assert len(objective.values) == 100   # independent count agrees: nothing evaluated uncounted
    assert info["iterations_started"] == 5


def test_budget_can_run_out_during_the_scouting_phase(eil51):
    # Budget 29 = 10 initial + 16 recruits (2*5 + 2*3) + only 3 of the 6 fresh scouts.
    # The run must stop in the middle of scouting, inside the FIRST iteration.
    settings = BeesSettings(n_scouts=10, n_selected_sites=4, n_elite_sites=2, n_bees_elite=5,
                            n_bees_selected=3, max_evaluations=29)
    tracker, objective, info = run_small_ba(eil51, seed=0, settings=settings)
    assert tracker.evaluations_used == 29
    assert len(objective.values) == 29
    assert info["iterations_started"] == 1


def test_budget_equal_to_initial_population_runs_no_iterations(eil51):
    settings = BeesSettings(n_scouts=10, n_selected_sites=4, n_elite_sites=2, n_bees_elite=5,
                            n_bees_selected=3, max_evaluations=10)
    tracker, objective, info = run_small_ba(eil51, seed=0, settings=settings)
    assert tracker.evaluations_used == 10
    assert info["iterations_started"] == 0
    assert info["initial_best_value"] == tracker.best_value


def test_initial_best_is_best_of_initial_population(eil51):
    tracker, objective, info = run_small_ba(eil51, seed=1)
    assert info["initial_best_value"] == min(objective.values[:SMALL_SETTINGS.n_scouts])


def test_reported_best_is_minimum_of_all_evaluated_candidates(eil51):
    tracker, objective, _ = run_small_ba(eil51, seed=2)
    assert tracker.best_value == min(objective.values)


def test_best_so_far_never_gets_worse(eil51):
    tracker, _, _ = run_small_ba(eil51, seed=3)
    curve = expand_history_to_every_evaluation(tracker.history, tracker.evaluations_used)
    assert np.all(np.diff(curve) <= 0)


def test_full_assignment_run_uses_exactly_30000_evaluations(eil51):
    result = run_bees_on_tsp(eil51, "reversal", seed=0, optimal_length=426)
    assert result["evaluations_used"] == 30_000
    # 6 initial + 194 full iterations of 154 = 29,882; the 195th iteration gets the last 118.
    assert result["iterations_started"] == 195
    assert result["best_so_far_history"][0][0] == 1


# ---------------------------------------------------------------- results and validity

@pytest.mark.parametrize("neighbourhood", ["swap", "reversal"])
def test_full_run_returns_valid_tour_and_consistent_numbers(eil51, neighbourhood):
    result = run_bees_on_tsp(eil51, neighbourhood, seed=4, optimal_length=426)
    tour_indices = np.array(result["best_tour_city_ids"]) - 1
    assert is_valid_tour(tour_indices, 51)
    assert result["best_tour_city_ids"][0] == 1
    distances = compute_distance_matrix(eil51.coordinates)
    assert tour_length(tour_indices, distances) == result["final_best_length"]
    assert result["final_best_length"] >= 426            # cannot beat the optimum
    assert result["final_best_length"] < result["initial_best_length"]  # BA improved
    assert result["gap_percent"] == pytest.approx(100 * (result["final_best_length"] - 426) / 426)
    assert result["best_so_far_history"][-1][1] == result["final_best_length"]


def test_percentage_gap_formula():
    assert percentage_gap(426, 426) == 0.0
    assert percentage_gap(450, 426) == pytest.approx(5.6338, abs=1e-4)


# ---------------------------------------------------------------- reproducibility

def test_same_seed_gives_identical_run(eil51):
    first = run_bees_on_tsp(eil51, "swap", seed=5)
    second = run_bees_on_tsp(eil51, "swap", seed=5)
    for key in ("final_best_length", "initial_best_length", "best_tour_city_ids", "best_so_far_history"):
        assert first[key] == second[key]


def test_different_seeds_give_different_runs(eil51):
    first = run_bees_on_tsp(eil51, "swap", seed=5)
    second = run_bees_on_tsp(eil51, "swap", seed=6)
    assert first["best_so_far_history"] != second["best_so_far_history"]


def test_both_neighbourhoods_start_from_same_initial_population(eil51):
    # Same seed -> the random generator produces the same 50 initial tours before any
    # neighbourhood move is used, so both versions start from identical scouts (fair comparison).
    swap_result = run_bees_on_tsp(eil51, "swap", seed=7)
    reversal_result = run_bees_on_tsp(eil51, "reversal", seed=7)
    assert swap_result["initial_best_length"] == reversal_result["initial_best_length"]


def test_unknown_neighbourhood_is_rejected(eil51):
    with pytest.raises(ValueError, match="Unknown neighbourhood"):
        run_bees_on_tsp(eil51, "insertion", seed=0)
