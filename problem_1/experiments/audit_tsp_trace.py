# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
TRACE audit of the Bees Algorithm logic on real Part A runs.

Idea
----
We run the real algorithm with the real settings, but wrap its two "helpers" (make a random
tour, make a neighbour) and the objective function so that every single call is written to a
log. Then, using ONLY that log, we rebuild what the algorithm should have done according to
the Bees Algorithm definition, iteration by iteration, and check that the log matches:

  * the first 6 evaluations are random scouts (initial population);
  * in every iteration the site that receives 100 recruits is the BEST tour in the population
    (elite site) and the site receiving 50 recruits is the SECOND best (other selected site);
  * every recruit is made from its site (not from a previous recruit), city 1 never moves and
    the move really changes the tour;
  * each site keeps the best of itself and its recruits (retained solution);
  * exactly 4 fresh scouts follow, completing the new population of 6;
  * the final iteration stops at exactly 30,000 evaluations (100 elite + 18 selected recruits);
  * every created candidate was evaluated exactly once, and the reported best equals the
    minimum of all 30,000 evaluated values.

Run from the problem_1 folder:
    python -m experiments.audit_tsp_trace

Exit code 0 = all checks passed (an assertion error stops the script otherwise).
"""

import numpy as np

from src.bees_algorithm import run_bees_algorithm
from src.bees_tsp import TSP_BEES_SETTINGS
from src.evaluation_tracker import EvaluationTracker
from src.tsp_instances import instance_file_path
from src.tsp_neighbourhoods import NEIGHBOURHOOD_MOVES
from src.tsp_tour import compute_distance_matrix, create_random_tour, tour_length
from src.tsplib import load_tsplib_instance

# One small and one large instance, one run of each neighbourhood.
TRACED_RUNS = [("berlin52", "swap", 3), ("ch150", "reversal", 8)]


def trace_one_run(instance_name, neighbourhood, seed):
    settings = TSP_BEES_SETTINGS
    instance = load_tsplib_instance(instance_file_path(instance_name))
    distances = compute_distance_matrix(instance.coordinates)

    events = []   # ("scout", None) or ("recruit", value of the site the recruit was made from)
    values = []   # every objective value, in the order the tracker requested them

    def logged_objective(tour):
        values.append(tour_length(tour, distances))
        return values[-1]

    def logged_random_tour(rng):
        events.append(("scout", None))
        return create_random_tour(instance.dimension, rng)

    def logged_neighbour(site_tour, rng):
        # The site's value is computed here for the log only; it is not an extra evaluation.
        events.append(("recruit", tour_length(site_tour, distances)))
        neighbour = NEIGHBOURHOOD_MOVES[neighbourhood](site_tour, rng)
        assert neighbour[0] == 0, "city 1 moved"
        assert not np.array_equal(neighbour, site_tour), "move did not change the tour"
        return neighbour

    tracker = EvaluationTracker(logged_objective, settings.max_evaluations)
    info = run_bees_algorithm(tracker, logged_random_tour, logged_neighbour, settings, np.random.default_rng(seed))

    budget = settings.max_evaluations
    assert len(events) == len(values) == tracker.evaluations_used == budget, \
        "every created candidate must be evaluated exactly once, 30,000 in total"

    # ---- Rebuild the algorithm from the log alone ---------------------------------------------
    n, m, e = settings.n_scouts, settings.n_selected_sites, settings.n_elite_sites
    assert all(kind == "scout" for kind, _ in events[:n]), "initial population must be random scouts"
    population = values[:n]
    position = n
    iterations = 0
    while position < budget:
        iterations += 1
        ranked = sorted(population)
        new_population = []
        for site_rank in range(m):
            site_value = ranked[site_rank]       # the (site_rank + 1)-th best tour in the population
            recruits = settings.n_bees_elite if site_rank < e else settings.n_bees_selected
            block = events[position:position + recruits]
            assert all(event == ("recruit", site_value) for event in block), \
                f"iteration {iterations}: recruits were not all made from site rank {site_rank + 1}"
            block_values = values[position:position + len(block)]
            new_population.append(min([site_value] + block_values))   # best of site + its recruits
            position += len(block)
        block = events[position:position + (n - m)]
        assert all(kind == "scout" for kind, _ in block), f"iteration {iterations}: expected fresh scouts"
        new_population += values[position:position + len(block)]
        position += len(block)
        if position < budget:
            assert len(new_population) == n, f"iteration {iterations}: population size changed"
        population = new_population

    assert iterations == info["iterations_started"], "iteration count differs"
    assert tracker.best_value == min(values), "reported best is not the minimum of all evaluated values"

    scouts = sum(1 for kind, _ in events if kind == "scout")
    recruits = budget - scouts
    full_iterations = iterations - 1
    print(f"{instance_name} {neighbourhood} seed {seed}: {iterations} iterations rebuilt and matched; "
          f"{scouts} random tours ({n} initial + {n - m} x {full_iterations}), {recruits} recruits; "
          f"best {tracker.best_value}")


def main():
    for instance_name, neighbourhood, seed in TRACED_RUNS:
        trace_one_run(instance_name, neighbourhood, seed)
    print("ALL TRACE CHECKS PASSED: site selection, elite/non-elite recruitment, retention, "
          "scouting and stopping match the Bees Algorithm definition in every iteration.")


if __name__ == "__main__":
    main()
