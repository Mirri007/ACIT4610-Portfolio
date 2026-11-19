# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Tests for distances, tour length and tour validity.

The most important test here is ``test_published_optimal_tours_have_published_lengths``:
TSPLIB publishes an optimal tour for each instance. If our distance rule and tour-length
function are correct, those tours must give exactly the published optimal lengths
(e.g. 7542 for berlin52). These optimal tours are stored only in the tests folder and are
used ONLY for this check, never by the Bees Algorithm.
"""

import gzip

import numpy as np
import pytest

from src.tsp_instances import TSP_INSTANCES, instance_file_path
from src.tsp_tour import (
    closed_route_city_ids,
    compute_distance_matrix,
    create_random_tour,
    is_valid_tour,
    tour_length,
    tour_to_city_ids,
)
from src.tsplib import load_tsplib_instance
from tests.reference_paths import REFERENCE_TOURS_FOLDER

# Rectangle 3 wide and 4 high, cities numbered anticlockwise:
#   city 1 (0,0), city 2 (3,0), city 3 (3,4), city 4 (0,4).
# Sides are 3 and 4, the diagonals are 5 (a 3-4-5 triangle), so lengths are easy by hand.
RECTANGLE = np.array([[0, 0], [3, 0], [3, 4], [0, 4]], dtype=float)


def load_reference_tour(file_path):
    """Read a TSPLIB .opt.tour(.gz) file and return the tour as 0-based indices (test use only)."""
    with gzip.open(file_path, "rt") as handle:
        tokens = handle.read().split()
    start = tokens.index("TOUR_SECTION") + 1
    city_ids = []
    for token in tokens[start:]:
        if token in ("-1", "EOF"):
            break
        city_ids.append(int(token))
    return np.array(city_ids) - 1


# ---------------------------------------------------------------- distances

def test_distance_matrix_by_hand_on_rectangle():
    distances = compute_distance_matrix(RECTANGLE)
    expected = np.array([
        [0, 3, 5, 4],
        [3, 0, 4, 5],
        [5, 4, 0, 3],
        [4, 5, 3, 0],
    ])
    assert np.array_equal(distances, expected)


@pytest.mark.parametrize(
    "point_b, expected_distance",
    [
        ((1.0, 1.0), 1),    # sqrt(2) = 1.414 -> 1
        ((1.5, 0.0), 2),    # exactly 1.5 -> rounds UP to 2
        ((2.5, 0.0), 3),    # exactly 2.5 -> 3 (Python's round(2.5) would give 2!)
        ((0.49, 0.0), 0),   # 0.49 -> 0
        ((0.5, 0.0), 1),    # 0.5 -> 1
        ((2.0, 2.0), 3),    # sqrt(8) = 2.83 -> 3
    ],
)
def test_tsplib_rounding_rule(point_b, expected_distance):
    distances = compute_distance_matrix(np.array([(0.0, 0.0), point_b]))
    assert distances[0, 1] == expected_distance


def test_python_round_would_give_a_different_answer():
    # Documents WHY we use floor(x + 0.5) instead of round(): they disagree on halves.
    assert round(2.5) == 2
    assert int(np.floor(2.5 + 0.5)) == 3


@pytest.mark.parametrize("name", list(TSP_INSTANCES))
def test_distance_matrix_is_symmetric_with_zero_diagonal(name):
    distances = compute_distance_matrix(load_tsplib_instance(instance_file_path(name)).coordinates)
    assert np.array_equal(distances, distances.T)
    assert np.all(np.diag(distances) == 0)
    assert distances.dtype == np.int64


# ---------------------------------------------------------------- tour length

def test_tour_length_includes_return_leg():
    distances = compute_distance_matrix(RECTANGLE)
    # Around the rectangle: 1->2 (3) + 2->3 (4) + 3->4 (3) + return 4->1 (4) = 14.
    # Without the return leg it would be 10, so this test fails if the return leg is missing.
    assert tour_length(np.array([0, 1, 2, 3]), distances) == 14


def test_tour_length_with_crossing_diagonals():
    distances = compute_distance_matrix(RECTANGLE)
    # 1->3 (5) + 3->2 (4) + 2->4 (5) + return 4->1 (4) = 18 (worse: the route crosses itself).
    assert tour_length(np.array([0, 2, 1, 3]), distances) == 18


def test_reversed_tour_has_same_length():
    # Symmetric distances: travelling the same circle the other way gives the same length.
    distances = compute_distance_matrix(RECTANGLE)
    assert tour_length(np.array([0, 1, 2, 3]), distances) == tour_length(np.array([0, 3, 2, 1]), distances)


@pytest.mark.parametrize("name", list(TSP_INSTANCES))
def test_published_optimal_tours_have_published_lengths(name):
    _cities, published_optimum = TSP_INSTANCES[name]
    instance = load_tsplib_instance(instance_file_path(name))
    distances = compute_distance_matrix(instance.coordinates)
    optimal_tour = load_reference_tour(REFERENCE_TOURS_FOLDER / f"{name}.opt.tour.gz")
    assert is_valid_tour(optimal_tour, instance.dimension)
    assert tour_length(optimal_tour, distances) == published_optimum


# ---------------------------------------------------------------- random tours and validity

def test_random_tours_are_valid_and_start_at_city_1():
    rng = np.random.default_rng(123)
    for _ in range(200):
        tour = create_random_tour(52, rng)
        assert is_valid_tour(tour, 52)
        assert tour[0] == 0


def test_random_tours_depend_on_seed_and_are_reproducible():
    tour_a = create_random_tour(52, np.random.default_rng(1))
    tour_b = create_random_tour(52, np.random.default_rng(1))
    tour_c = create_random_tour(52, np.random.default_rng(2))
    assert np.array_equal(tour_a, tour_b)
    assert not np.array_equal(tour_a, tour_c)


def test_random_tours_are_roughly_uniform():
    # With 4 cities, positions 1..3 hold cities 2..4 in one of 3! = 6 orders.
    # Over 6000 draws each order should appear about 1000 times.
    rng = np.random.default_rng(0)
    counts = {}
    for _ in range(6000):
        key = tuple(create_random_tour(4, rng))
        counts[key] = counts.get(key, 0) + 1
    assert len(counts) == 6
    assert all(850 < count < 1150 for count in counts.values())


@pytest.mark.parametrize(
    "tour, reason",
    [
        ([0, 1, 2], "too short"),
        ([0, 1, 2, 2], "city repeated, city 4 missing"),
        ([1, 0, 2, 3], "does not start at city 1"),
        ([0, 1, 2, 4], "index out of range"),
        ([0, 1, 2, 3, 3], "too long"),
    ],
)
def test_invalid_tours_are_detected(tour, reason):
    assert not is_valid_tour(np.array(tour), 4), reason


def test_city_id_conversion_and_closed_route():
    assert tour_to_city_ids(np.array([0, 3, 1, 2])) == [1, 4, 2, 3]
    # City 1 is appended only for display, closing the loop.
    assert closed_route_city_ids(np.array([0, 3, 1, 2])) == [1, 4, 2, 3, 1]
