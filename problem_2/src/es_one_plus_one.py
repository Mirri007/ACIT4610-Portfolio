# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Variant 1: the single-parent (1+1)-Evolution Strategy (assignment, "Variant 1").

What is an Evolution Strategy?
------------------------------
An ES improves solutions by repeated random variation ("mutation") and selection. Each solution
carries a STEP SIZE sigma that controls how large the random changes are. A large sigma explores
far away; a small sigma fine-tunes nearby. Good ES variants adapt sigma automatically during
the run.

(1+1) means: 1 parent, 1 child per step, and the "+" means the parent competes with its child
(the better of the two survives). It is the simplest ES.

One step ("trial"), as specified by the assignment
---------------------------------------------------
1. child z = parent w + sigma * N(0, 1) for every weight (N(0,1) = standard normal random number)
2. repair z -> feasible portfolio w', evaluate V(w')        (one evaluation)
3. if V(w') < V(parent): the child replaces the parent ("success")
4. step-size update (the 1/5th success rule):
       success:  sigma <- sigma * exp(1/3)      (about x1.40: take bigger steps)
       failure:  sigma <- sigma * exp(-1/12)    (about x0.92: take smaller steps)
   and keep sigma within [1e-8, 1.0].

Why these two factors give a "1/5 rule": if a fraction p of trials succeed, log(sigma) changes
on average by p/3 - (1 - p)/12 per trial. This is zero exactly when 4p = 1 - p, i.e. p = 1/5.
So sigma grows while more than 1 in 5 trials succeed (steps are too timid) and shrinks while
fewer succeed (steps overshoot). Sigma settles where about 20 % of mutations are improvements,
which Rechenberg found to be close to the fastest progress for simple problems.
"""

import math

import numpy as np

SUCCESS_FACTOR = math.exp(1.0 / 3.0)
FAILURE_FACTOR = math.exp(-1.0 / 12.0)
STEP_SIZE_MIN = 1e-8
STEP_SIZE_MAX = 1.0


def initial_step_size(n_assets):
    """Starting step size from the assignment: 0.1 / sqrt(n). Smaller for more assets, because a
    change in every one of n weights adds up: the total step length grows like sqrt(n)."""
    return 0.1 / math.sqrt(n_assets)


def update_step_size(step_size, success):
    """Apply the 1/5th success rule once and clamp to [1e-8, 1.0]."""
    step_size = step_size * (SUCCESS_FACTOR if success else FAILURE_FACTOR)
    return min(max(step_size, STEP_SIZE_MIN), STEP_SIZE_MAX)


def run_one_plus_one_es(evaluator, n_assets, rng, step_size_log_interval=500):
    """
    Run the (1+1)-ES until the evaluation budget is used up.

    Parameters
    ----------
    evaluator : PortfolioEvaluator
        Repairs, evaluates, counts and archives every candidate.
    n_assets : int
    rng : numpy.random.Generator
        The run's only source of randomness (created from the run's seed).
    step_size_log_interval : int
        Record sigma every this many evaluations (for analysing step-size adaptation).

    Returns
    -------
    dict with the initial variance, number of successful trials, final step size and a log of
    (evaluation number, sigma) pairs. The best portfolio is read from ``evaluator``.
    """
    # Initialisation: independent uniform values in [0, 1] for every weight, then repair.
    # (The repair turns them into a valid portfolio; this counts as evaluation 1.)
    parent_weights, parent_variance = evaluator.evaluate(rng.uniform(0.0, 1.0, size=n_assets))
    initial_variance = parent_variance
    step_size = initial_step_size(n_assets)
    successes = 0
    step_size_log = [(evaluator.evaluations_used, step_size)]

    while not evaluator.budget_exhausted():
        # Mutation: the same scalar sigma for every weight, a fresh normal number per weight.
        child_candidate = parent_weights + step_size * rng.standard_normal(n_assets)
        child_weights, child_variance = evaluator.evaluate(child_candidate)

        # Plus selection: keep the child only if it is STRICTLY better (lower variance).
        success = child_variance < parent_variance
        if success:
            parent_weights, parent_variance = child_weights, child_variance
            successes += 1
        step_size = update_step_size(step_size, success)

        if evaluator.evaluations_used % step_size_log_interval == 0:
            step_size_log.append((evaluator.evaluations_used, step_size))

    return {
        "initial_best_variance": initial_variance,
        "successful_trials": successes,
        "trials": evaluator.evaluations_used - 1,
        "final_step_size": step_size,
        "step_size_log": step_size_log,
    }
