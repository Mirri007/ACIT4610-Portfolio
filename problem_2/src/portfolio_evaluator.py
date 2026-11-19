# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Repair + evaluation + counting + best-so-far archive, all in one place (Problem 2).

Why one component?
------------------
The assignment requires, for all three ES variants:
  * every candidate z is repaired into a feasible portfolio w BEFORE its variance is computed;
  * every evaluated candidate counts toward the 30,000-evaluation budget, including the
    initial population and candidates that are later rejected;
  * the run stops at the budget (the last offspring batch may be smaller than 70);
  * a separate record ("archive") keeps the best VALID allocation found so far, including
    initialisation, and that allocation is returned at the end.

If each ES variant did this bookkeeping itself, a mistake in one variant would make the
comparison unfair. Here all three variants call the same ``evaluate`` method, so they are
counted and archived identically.

The archive is only a RECORD. The ES variants never read it to choose parents; in particular
the (mu, lambda)-ES selects parents from its offspring only, as the assignment requires.
"""

import numpy as np

from src.portfolio_model import feasibility_violations, portfolio_variance, repair_portfolio


class PortfolioEvaluator:
    """
    Repairs, evaluates and counts candidates for one test case, and keeps the best-so-far archive.

    Parameters
    ----------
    case : PortfolioCase
        The dataset and its minimum return R_min.
    max_evaluations : int
        Evaluation budget (30,000 in the assignment).

    Attributes
    ----------
    evaluations_used : int
    archive_weights, archive_variance :
        Best valid portfolio found so far and its variance (None before the first evaluation).
    history : list of (int, float)
        Change points of the archive: (evaluation number, new best variance). Starts at evaluation 1.
    invalid_evaluations : int
        Candidates that failed the feasibility tolerances after repair. The repair guarantees
        feasibility, so this should always be 0; it is counted to PROVE that, not assumed.
    """

    def __init__(self, case, max_evaluations):
        self.case = case
        self.max_evaluations = max_evaluations
        self.evaluations_used = 0
        self.archive_weights = None
        self.archive_variance = None
        self.history = []
        self.invalid_evaluations = 0

    def budget_exhausted(self):
        """True when no evaluations are left; the ES checks this before creating each candidate."""
        return self.evaluations_used >= self.max_evaluations

    def evaluate(self, candidate):
        """
        Repair one raw candidate, compute its variance, count it and update the archive.

        Parameters
        ----------
        candidate : (n,) array z
            Any real vector produced by initialisation, mutation or recombination.

        Returns
        -------
        (weights, variance)
            The repaired feasible portfolio w and its variance V(w). The ES keeps w (not z) as
            the individual, so the next mutation starts from a feasible portfolio.

        Raises
        ------
        RuntimeError if called after the budget is used up (a safety net against counting bugs).
        """
        if self.budget_exhausted():
            raise RuntimeError("Evaluation budget exceeded: the ES must stop at the budget")

        data = self.case.data
        weights = repair_portfolio(candidate, data.mean_returns, self.case.min_return, self.case.best_asset_index)
        variance = portfolio_variance(weights, data.covariance)
        self.evaluations_used += 1

        # Only VALID portfolios may enter the archive (assignment: "best valid allocation").
        valid = not feasibility_violations(weights, data.mean_returns, self.case.min_return)
        if not valid:
            self.invalid_evaluations += 1
        elif self.archive_variance is None or variance < self.archive_variance:
            # Strictly lower variance = improvement; ties keep the earlier allocation.
            self.archive_variance = variance
            self.archive_weights = np.array(weights, copy=True)   # copy: later changes cannot alter it
            self.history.append((self.evaluations_used, variance))
        return weights, variance
