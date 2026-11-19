# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Running the Bees Algorithm on one TSP instance (Part A).

This module connects the general BA in ``bees_algorithm.py`` with the TSP pieces:
  * random solution  = uniformly shuffled tour with city 1 fixed first (``create_random_tour``),
  * neighbour        = one swap OR one segment reversal (``tsp_neighbourhoods.py``),
  * objective        = closed tour length with rounded EUC_2D distances (``tour_length``).

It also measures runtime, validates the final tour and computes the percentage gap.
"""

import time

import numpy as np

from src.bees_algorithm import BeesSettings, run_bees_algorithm
from src.evaluation_tracker import EvaluationTracker
from src.tsp_neighbourhoods import NEIGHBOURHOOD_MOVES
from src.tsp_tour import (
    compute_distance_matrix,
    create_random_tour,
    is_valid_tour,
    tour_length,
    tour_to_city_ids,
)

# BA settings for Part A. The SAME settings are used for both neighbourhood versions and
# all six instances (assignment: "Use the same BA settings and seed list for the two
# neighborhood versions").
#
# Chosen with a small pilot study (experiments/tsp_pilot_settings.py, seeds 100-104, which
# are NOT the experiment seeds). Concentrating recruited bees on few sites gave clearly
# smaller gaps within the 30,000-evaluation budget than spreading them over many sites.
# See docs/implementation_notes.md for the pilot table and reasoning.
#   n=6 scouts, m=2 selected sites, e=1 elite site, nep=100, nsp=50
#   -> 1*100 + 1*50 + (6-2) = 154 evaluations per full iteration.
#   -> 30,000 = 6 (initial) + 194 full iterations (29,876) + 118 in an incomplete 195th iteration.
TSP_BEES_SETTINGS = BeesSettings(
    n_scouts=6,
    n_selected_sites=2,
    n_elite_sites=1,
    n_bees_elite=100,
    n_bees_selected=50,
    max_evaluations=30_000,
)

# The 10 seeds used for every TSP instance and both neighbourhood versions.
TSP_SEEDS = list(range(10))


def percentage_gap(found_length, optimal_length):
    """
    Gap(%) = 100 * (L_BA - L*) / L*  (assignment formula).

    How far the BA's tour is above the published optimum, as a percentage of the optimum.
    Example: L* = 426 and L_BA = 450 -> 100 * 24 / 426 = 5.63 %. A gap of 0 % means the BA
    found an optimal tour. The gap cannot be negative for a correct implementation, because
    no tour can be shorter than the optimum.
    """
    return 100.0 * (found_length - optimal_length) / optimal_length


def run_bees_on_tsp(instance, neighbourhood_name, seed, settings=TSP_BEES_SETTINGS, optimal_length=None):
    """
    Perform one complete BA run on one TSP instance.

    Parameters
    ----------
    instance : TSPInstance
        A validated instance from ``tsplib.load_tsplib_instance``.
    neighbourhood_name : str
        "swap" or "reversal".
    seed : int
        Seed for this run's random generator. Same seed + same settings = identical run.
    settings : BeesSettings
    optimal_length : int, optional
        Published optimum L*, used ONLY to compute the gap after the run has finished.

    Returns
    -------
    dict
        Everything the assignment asks us to record for a run: instance, neighbourhood, seed,
        settings, initial best length, final best length, gap, runtime, evaluations used,
        final tour (as TSPLIB city ids, starting with city 1) and the best-so-far history.
    """
    if neighbourhood_name not in NEIGHBOURHOOD_MOVES:
        raise ValueError(f"Unknown neighbourhood {neighbourhood_name!r}; use 'swap' or 'reversal'")
    create_neighbour = NEIGHBOURHOOD_MOVES[neighbourhood_name]

    # Pre-compute all rounded distances once per run (outside the timed search, because it
    # is data preparation rather than part of the optimisation itself).
    distances = compute_distance_matrix(instance.coordinates)
    number_of_cities = instance.dimension

    # numpy's recommended random generator. Creating it from the seed is the ONLY source of
    # randomness in the run, which is what makes results reproducible.
    rng = np.random.default_rng(seed)

    # The objective function given to the tracker: tour -> closed tour length.
    def objective(tour):
        return tour_length(tour, distances)

    def create_random_solution(random_generator):
        return create_random_tour(number_of_cities, random_generator)

    tracker = EvaluationTracker(objective, settings.max_evaluations)

    # Wall-clock runtime of the search itself, in seconds. perf_counter is Python's most
    # precise clock for measuring short durations.
    start_time = time.perf_counter()
    run_info = run_bees_algorithm(tracker, create_random_solution, create_neighbour, settings, rng)
    runtime_seconds = time.perf_counter() - start_time

    best_tour = tracker.best_solution
    best_length = int(tracker.best_value)

    # Safety checks required by the assignment: the returned tour must be a valid
    # permutation starting at city 1, and its recomputed length must match the recorded one.
    if not is_valid_tour(best_tour, number_of_cities):
        raise RuntimeError("BA returned an invalid tour")
    if tour_length(best_tour, distances) != best_length:
        raise RuntimeError("Recorded best length does not match the tour's actual length")
    if tracker.evaluations_used != settings.max_evaluations:
        raise RuntimeError("Run did not use exactly the evaluation budget")

    result = {
        "instance": instance.name,
        "cities": number_of_cities,
        "neighbourhood": neighbourhood_name,
        "seed": seed,
        "settings": settings.as_dict(),
        "initial_best_length": int(run_info["initial_best_value"]),
        "final_best_length": best_length,
        "optimal_length": optimal_length,
        "gap_percent": None if optimal_length is None else percentage_gap(best_length, optimal_length),
        "runtime_seconds": runtime_seconds,
        "evaluations_used": tracker.evaluations_used,
        "iterations_started": run_info["iterations_started"],
        "best_tour_city_ids": tour_to_city_ids(best_tour),
        "best_so_far_history": [[int(evaluation), int(value)] for evaluation, value in tracker.history],
    }
    return result
