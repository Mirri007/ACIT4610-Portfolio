# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Running the Bees Algorithm on a continuous benchmark function (Part B).

The Bees Algorithm itself is the SAME code as in Part A (``bees_algorithm.run_bees_algorithm``).
Only three things change from the TSP version:

=====================  ==================================  ======================================
                       Part A (TSP, discrete)               Part B (functions, continuous)
=====================  ==================================  ======================================
solution               permutation of cities                vector of D real numbers
random solution        shuffle cities 2..n                  uniform random value in [lower, upper]
                                                            for every coordinate
neighbour (recruit)    one swap or one segment reversal     add a random change of up to +-10 % of
                                                            the range to EVERY coordinate, then
                                                            clip to the bounds
objective              tour length                          benchmark function value
=====================  ==================================  ======================================

Everything else (site selection, elite recruitment, retention, scouting, evaluation counting,
stopping at 30,000 evaluations, best-so-far tracking) is shared.
"""

import time

import numpy as np

from src.bees_algorithm import BeesSettings, run_bees_algorithm
from src.benchmark_functions import BENCHMARK_FUNCTIONS
from src.evaluation_tracker import EvaluationTracker

# Neighbourhood size from the assignment: each coordinate changes by a value drawn uniformly
# between -10 % and +10 % of the allowed range (upper bound - lower bound).
NEIGHBOURHOOD_FRACTION = 0.10

# BA settings for Part B: one setting for all four functions and both dimensions.
# Chosen with a pilot study at dimension D = 20 (not an experiment dimension) and seeds 100-104
# (not experiment seeds), using a selection rule fixed before the pilot was run (lowest average
# rank over the four functions): experiments/continuous_pilot_settings.py.
# See docs/implementation_notes.md for the pilot table and its limitations.
#   n=10 scouts, m=3 selected sites, e=1 elite site, nep=100, nsp=50
#   -> 1*100 + 2*50 + (10-3) = 207 evaluations per full iteration.
#   -> 30,000 = 10 (initial) + 144 full iterations (29,808) + 182 in an incomplete 145th iteration
#      (100 recruits for the elite site, 50 + 32 for the two other selected sites, no scouts).
CONTINUOUS_BEES_SETTINGS = BeesSettings(
    n_scouts=10,
    n_selected_sites=3,
    n_elite_sites=1,
    n_bees_elite=100,
    n_bees_selected=50,
    max_evaluations=30_000,
)

CONTINUOUS_SEEDS = list(range(10))
CONTINUOUS_DIMENSIONS = [10, 30]


def create_random_vector(lower, upper, dimension, rng):
    """
    A scout bee for Part B: every coordinate drawn uniformly at random inside the bounds.

    Assignment: "Initialize scouts uniformly within the bounds". Each of the D coordinates is
    independent; any value between ``lower`` and ``upper`` is equally likely.

    Returns
    -------
    numpy.ndarray of shape (dimension,)
    """
    return rng.uniform(lower, upper, size=dimension)


def create_neighbour_vector(vector, lower, upper, rng):
    """
    A recruited bee for Part B: a small random change to EVERY coordinate of a site, then clipping.

    Assignment rule, step by step:
      1. range = upper - lower (e.g. 10.24 for Sphere/Rastrigin, 15 for Rosenbrock).
      2. For each coordinate independently, draw a change uniformly between -10 % and +10 % of
         that range (e.g. between -1.024 and +1.024 for Sphere).
      3. Add the changes to the site's coordinates.
      4. "Clip" to the bounds: any coordinate that went below ``lower`` is set to ``lower``, any
         above ``upper`` is set to ``upper``. This keeps every candidate a valid point.

    Example (Sphere, range 10.24, maximum change 1.024): site (5.0, -2.0) and drawn changes
    (+0.5, -0.3) give (5.5, -2.3); 5.5 exceeds the upper bound 5.12, so the result is (5.12, -2.3).

    The site vector itself is not modified (NumPy's ``+`` creates a new array).

    Returns
    -------
    numpy.ndarray, same shape as ``vector``, with every coordinate in [lower, upper].
    """
    maximum_change = NEIGHBOURHOOD_FRACTION * (upper - lower)
    changes = rng.uniform(-maximum_change, maximum_change, size=vector.shape)
    return np.clip(vector + changes, lower, upper)


def run_bees_on_function(function_name, dimension, seed, settings=CONTINUOUS_BEES_SETTINGS):
    """
    Perform one complete BA run on one benchmark function in one dimension.

    Parameters
    ----------
    function_name : str
        "sphere", "rosenbrock", "rastrigin" or "ackley".
    dimension : int
        Number of coordinates D (10 or 30 in the experiments).
    seed : int
        Seed of the run's random generator (same seed = identical run).
    settings : BeesSettings

    Returns
    -------
    dict
        Everything the assignment asks us to record: function, dimension, seed, settings,
        bounds, initial best value, final best value (= objective error, since the minimum is 0),
        final best vector, runtime, evaluations used and the best-so-far history.
    """
    if function_name not in BENCHMARK_FUNCTIONS:
        raise ValueError(f"Unknown function {function_name!r}")
    objective, lower, upper = BENCHMARK_FUNCTIONS[function_name]
    rng = np.random.default_rng(seed)

    def create_random_solution(random_generator):
        return create_random_vector(lower, upper, dimension, random_generator)

    def create_neighbour(vector, random_generator):
        return create_neighbour_vector(vector, lower, upper, random_generator)

    tracker = EvaluationTracker(objective, settings.max_evaluations)
    start_time = time.perf_counter()
    run_info = run_bees_algorithm(tracker, create_random_solution, create_neighbour, settings, rng)
    runtime_seconds = time.perf_counter() - start_time

    best_vector = tracker.best_solution
    best_value = float(tracker.best_value)

    # Safety checks: correct length, inside the bounds, recorded value reproducible, exact budget.
    if best_vector.shape != (dimension,):
        raise RuntimeError("Best vector has the wrong dimension")
    if np.any(best_vector < lower) or np.any(best_vector > upper):
        raise RuntimeError("Best vector lies outside the bounds")
    if objective(best_vector) != best_value:
        raise RuntimeError("Recorded best value does not match the vector")
    if tracker.evaluations_used != settings.max_evaluations:
        raise RuntimeError("Run did not use exactly the evaluation budget")

    return {
        "function": function_name,
        "dimension": dimension,
        "seed": seed,
        "settings": settings.as_dict(),
        "lower_bound": lower,
        "upper_bound": upper,
        "neighbourhood_fraction": NEIGHBOURHOOD_FRACTION,
        "initial_best_value": float(run_info["initial_best_value"]),
        "final_best_value": best_value,
        "runtime_seconds": runtime_seconds,
        "evaluations_used": tracker.evaluations_used,
        "iterations_started": run_info["iterations_started"],
        # float() of a NumPy number gives Python's shortest exact representation, so saving to
        # JSON and reading back reproduces the vector bit-for-bit.
        "best_vector": [float(value) for value in best_vector],
        "best_so_far_history": [[int(evaluation), float(value)] for evaluation, value in tracker.history],
    }
