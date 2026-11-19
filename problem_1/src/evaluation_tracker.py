# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Counting objective evaluations and recording the best-so-far history.

Why a separate component?
-------------------------
The assignment is strict about evaluations:

* every run gets exactly 30,000 objective evaluations;
* the count includes the initial population, every recruited neighbour and every fresh
  scout, *including candidates that are rejected*;
* the run stops when the budget is reached, even in the middle of an iteration;
* we must record the initial best value, the best-so-far history and the final best solution.

If evaluations were counted in several places in the algorithm, it would be easy to miss one.
Instead, **every** candidate is scored by calling :meth:`EvaluationTracker.evaluate`, and
that single method does all the bookkeeping. The Bees Algorithm asks
:meth:`EvaluationTracker.budget_exhausted` before creating each new candidate.

What is "best-so-far"?
----------------------
After k evaluations, the best-so-far value is the lowest objective value among the first k
candidates scored. It can only go down or stay the same, never up. A convergence plot shows
this value against the number of evaluations.

To keep log files small but exact, we save only the evaluations at which the best-so-far
*improved* (the "change points"). Between two change points the value is constant, so the
full 30,000-point curve can be rebuilt exactly (see :func:`expand_history_to_every_evaluation`).
"""

import numpy as np


class EvaluationTracker:
    """
    Wraps an objective function, counts calls to it and tracks the best solution found.

    Parameters
    ----------
    objective_function : callable
        Takes one candidate solution and returns its objective value (lower is better).
    max_evaluations : int
        The evaluation budget (30,000 in every experiment of this assignment).

    Attributes
    ----------
    evaluations_used : int
        How many candidates have been scored so far.
    best_value, best_solution :
        The lowest objective value seen so far and the solution that produced it.
    history : list of (int, float)
        Change points of the best-so-far curve: (evaluation number, new best value).
        The first entry is always evaluation 1, the first candidate ever scored.
    """

    def __init__(self, objective_function, max_evaluations):
        if max_evaluations < 1:
            raise ValueError("max_evaluations must be at least 1")
        self.objective_function = objective_function
        self.max_evaluations = max_evaluations
        self.evaluations_used = 0
        self.best_value = None
        self.best_solution = None
        self.history = []

    def budget_exhausted(self):
        """Return True when no evaluations are left. Checked before creating every candidate."""
        return self.evaluations_used >= self.max_evaluations

    def evaluate(self, solution):
        """
        Score one candidate, count it and update the best-so-far record.

        Every candidate counts, whether or not the algorithm later keeps it. That is how the
        assignment's rule "including candidates that are rejected" is guaranteed.

        Parameters
        ----------
        solution :
            A candidate solution (a tour array for TSP, a real vector for Part B).

        Returns
        -------
        float or int
            The candidate's objective value.

        Raises
        ------
        RuntimeError
            If called after the budget is used up. This should never happen, because the
            algorithm checks :meth:`budget_exhausted` first; the error is a safety net that
            makes a counting mistake impossible to miss.
        """
        if self.budget_exhausted():
            raise RuntimeError("Evaluation budget exceeded: the algorithm must stop at the budget")

        value = self.objective_function(solution)
        self.evaluations_used += 1

        # Strictly lower ("<") counts as an improvement. If a later candidate only ties the
        # best value, we keep the earlier one, so the record changes only on real progress.
        if self.best_value is None or value < self.best_value:
            self.best_value = value
            # Copy the solution so later changes to the candidate cannot alter the record.
            self.best_solution = np.array(solution, copy=True)
            self.history.append((self.evaluations_used, value))

        return value


def expand_history_to_every_evaluation(history, total_evaluations):
    """
    Rebuild the full best-so-far curve (one value per evaluation) from its change points.

    Example: with change points [(1, 900), (3, 850), (6, 800)] and 7 evaluations, the curve is::

        evaluation:  1    2    3    4    5    6    7
        best-so-far: 900  900  850  850  850  800  800

    This is used to average the curves of 10 runs at every evaluation number for the
    convergence plots. Because every run uses exactly the same budget, all expanded curves
    have the same length and can be averaged position by position.

    Parameters
    ----------
    history : list of (int, float)
        Change points (evaluation number, best value). The first must be evaluation 1.
    total_evaluations : int
        Length of the curve to build (normally 30,000).

    Returns
    -------
    numpy.ndarray, shape (total_evaluations,)
        Entry k - 1 is the best-so-far value after k evaluations.
    """
    if not history or history[0][0] != 1:
        raise ValueError("history must start at evaluation 1")

    curve = np.empty(total_evaluations, dtype=float)
    for position, (evaluation_number, value) in enumerate(history):
        # Each value holds from its own evaluation until just before the next change point.
        if position + 1 < len(history):
            next_change = history[position + 1][0]
        else:
            next_change = total_evaluations + 1
        curve[evaluation_number - 1:next_change - 1] = value
    return curve
