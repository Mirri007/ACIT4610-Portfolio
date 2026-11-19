# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Tests for the swap and segment-reversal neighbourhood moves.

``FixedPositionsRng`` is a tiny stand-in for a random generator that always "chooses" the
positions we tell it to. It lets us check each move against an example worked out by hand.
"""

import numpy as np
import pytest

from src.tsp_neighbourhoods import pick_two_different_positions, reversal_move, swap_move
from src.tsp_tour import create_random_tour, is_valid_tour


class FixedPositionsRng:
    """Fake generator: rng.choice(...) returns the two positions given at construction."""

    def __init__(self, first, second):
        self.positions = np.array([first, second])

    def choice(self, options, size, replace):
        assert size == 2 and replace is False
        assert all(position in options for position in self.positions)
        return self.positions


# ---------------------------------------------------------------- hand-worked examples

def test_swap_example_from_docstring():
    tour = np.array([0, 1, 2, 3, 4, 5])
    neighbour = swap_move(tour, FixedPositionsRng(1, 4))
    assert neighbour.tolist() == [0, 4, 2, 3, 1, 5]


def test_reversal_example_from_docstring():
    tour = np.array([0, 1, 2, 3, 4, 5])
    neighbour = reversal_move(tour, FixedPositionsRng(1, 4))
    assert neighbour.tolist() == [0, 4, 3, 2, 1, 5]


def test_positions_given_in_reverse_order_are_sorted():
    # (4, 1) must behave exactly like (1, 4).
    tour = np.array([0, 1, 2, 3, 4, 5])
    assert reversal_move(tour, FixedPositionsRng(4, 1)).tolist() == [0, 4, 3, 2, 1, 5]


# ---------------------------------------------------------------- properties over many random moves

@pytest.mark.parametrize("move", [swap_move, reversal_move])
def test_moves_keep_valid_permutation_and_city_1_first(move):
    rng = np.random.default_rng(7)
    for _ in range(2000):
        tour = create_random_tour(20, rng)
        neighbour = move(tour, rng)
        assert is_valid_tour(neighbour, 20)
        assert neighbour[0] == 0


@pytest.mark.parametrize("move", [swap_move, reversal_move])
def test_moves_do_not_modify_the_original_site(move):
    rng = np.random.default_rng(8)
    tour = create_random_tour(20, rng)
    original = tour.copy()
    for _ in range(100):
        move(tour, rng)
    assert np.array_equal(tour, original)


def test_swap_changes_exactly_two_positions():
    rng = np.random.default_rng(9)
    for _ in range(2000):
        tour = create_random_tour(30, rng)
        neighbour = swap_move(tour, rng)
        changed = np.flatnonzero(tour != neighbour)
        assert len(changed) == 2
        first, second = changed
        assert neighbour[first] == tour[second] and neighbour[second] == tour[first]


def test_reversal_reverses_one_contiguous_segment_only():
    rng = np.random.default_rng(10)
    for _ in range(2000):
        tour = create_random_tour(30, rng)
        neighbour = reversal_move(tour, rng)
        changed = np.flatnonzero(tour != neighbour)
        # Reversing a segment of length >= 2 always changes its two end positions.
        first, last = changed.min(), changed.max()
        assert np.array_equal(neighbour[first:last + 1], tour[first:last + 1][::-1])
        assert np.array_equal(neighbour[:first], tour[:first])
        assert np.array_equal(neighbour[last + 1:], tour[last + 1:])


def test_position_zero_is_never_chosen_and_positions_differ():
    rng = np.random.default_rng(11)
    seen = set()
    for _ in range(5000):
        first, second = pick_two_different_positions(6, rng)
        assert 1 <= first < second <= 5
        seen.add((first, second))
    # All 10 possible pairs from positions 1..5 should appear.
    assert len(seen) == 10


@pytest.mark.parametrize("move", [swap_move, reversal_move])
def test_moves_work_on_smallest_possible_tour(move):
    # 3 cities: only positions 1 and 2 can move, so the neighbour must be [0, 2, 1].
    rng = np.random.default_rng(12)
    assert move(np.array([0, 1, 2]), rng).tolist() == [0, 2, 1]
