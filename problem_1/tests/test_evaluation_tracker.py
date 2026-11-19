# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""Tests for evaluation counting, best-so-far tracking and history expansion."""

import numpy as np
import pytest

from src.evaluation_tracker import EvaluationTracker, expand_history_to_every_evaluation


def test_every_evaluation_is_counted_and_best_is_tracked():
    tracker = EvaluationTracker(objective_function=lambda x: float(x[0]), max_evaluations=10)
    for value in [5, 7, 3, 3, 9, 1]:
        tracker.evaluate(np.array([value]))
    assert tracker.evaluations_used == 6          # rejected (worse) candidates counted too
    assert tracker.best_value == 1
    assert tracker.best_solution.tolist() == [1]
    # Change points only: 5 at eval 1, 3 at eval 3, 1 at eval 6. The tie (3 at eval 4) is not an improvement.
    assert tracker.history == [(1, 5.0), (3, 3.0), (6, 1.0)]


def test_evaluating_beyond_budget_raises():
    tracker = EvaluationTracker(lambda x: 0.0, max_evaluations=2)
    tracker.evaluate(np.array([0]))
    tracker.evaluate(np.array([0]))
    assert tracker.budget_exhausted()
    with pytest.raises(RuntimeError, match="budget exceeded"):
        tracker.evaluate(np.array([0]))


def test_best_solution_is_a_copy():
    tracker = EvaluationTracker(lambda x: float(x.sum()), max_evaluations=5)
    candidate = np.array([1, 2])
    tracker.evaluate(candidate)
    candidate[0] = 100  # changing the candidate afterwards must not change the record
    assert tracker.best_solution.tolist() == [1, 2]


def test_expand_history_example_from_docstring():
    curve = expand_history_to_every_evaluation([(1, 900), (3, 850), (6, 800)], 7)
    assert curve.tolist() == [900, 900, 850, 850, 850, 800, 800]


def test_expand_history_single_change_point():
    assert expand_history_to_every_evaluation([(1, 42)], 4).tolist() == [42, 42, 42, 42]


def test_expand_history_rejects_history_not_starting_at_one():
    with pytest.raises(ValueError):
        expand_history_to_every_evaluation([(2, 5)], 4)
