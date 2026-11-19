# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
TRACE audit of the Bees Algorithm logic on real Part B runs.

As in audit_tsp_trace.py, the real algorithm is run with the real settings while every call to
"make a random vector", "make a neighbour" and the objective function is logged. From the log
alone we rebuild the Bees Algorithm iteration by iteration and check:

  * the first 10 evaluations are random scouts (initial population), inside the bounds;
  * in every iteration the site receiving 100 recruits is the BEST vector in the population
    (elite site), and the 2nd and 3rd best each receive 50 recruits (other selected sites);
  * every recruit is made from its site: EVERY coordinate differs from the site by at most
    10 % of the range (upper - lower), and the result lies inside the bounds (clipping);
  * each site keeps the best of itself and its recruits; 7 fresh scouts complete the population;
  * the final iteration stops at exactly 30,000 evaluations (100 + 50 + 32 recruits, no scouts);
  * every created candidate is evaluated exactly once; the reported best is the minimum of all values.

Run from the problem_1 folder:
    python -m experiments.audit_continuous_trace

Exit code 0 = all checks passed (an assertion error stops the script otherwise).
"""

import numpy as np

from src.bees_algorithm import run_bees_algorithm
from src.bees_continuous import CONTINUOUS_BEES_SETTINGS, create_neighbour_vector, create_random_vector
from src.benchmark_functions import BENCHMARK_FUNCTIONS
from src.evaluation_tracker import EvaluationTracker

# One unimodal and one multimodal function, both dimensions; a function with clipping at
# narrow bounds (Rastrigin) and one with wide bounds (Ackley).
TRACED_RUNS = [("rastrigin", 10, 3), ("ackley", 30, 8), ("rosenbrock", 30, 1)]


def trace_one_run(function_name, dimension, seed):
    settings = CONTINUOUS_BEES_SETTINGS
    objective, lower, upper = BENCHMARK_FUNCTIONS[function_name]
    maximum_change = 0.10 * (upper - lower)

    events = []   # ("scout", None) or ("recruit", value of the site the recruit was made from)
    values = []

    def logged_objective(vector):
        values.append(objective(vector))
        return values[-1]

    def logged_random_vector(rng):
        events.append(("scout", None))
        vector = create_random_vector(lower, upper, dimension, rng)
        assert vector.shape == (dimension,) and np.all(vector >= lower) and np.all(vector <= upper)
        return vector

    def logged_neighbour(site_vector, rng):
        events.append(("recruit", objective(site_vector)))   # for the log only, not counted
        neighbour = create_neighbour_vector(site_vector, lower, upper, rng)
        assert np.all(neighbour >= lower) and np.all(neighbour <= upper), "neighbour outside bounds"
        assert np.all(np.abs(neighbour - site_vector) <= maximum_change + 1e-12), "change larger than 10 % of range"
        return neighbour

    tracker = EvaluationTracker(logged_objective, settings.max_evaluations)
    info = run_bees_algorithm(tracker, logged_random_vector, logged_neighbour, settings, np.random.default_rng(seed))

    budget = settings.max_evaluations
    assert len(events) == len(values) == tracker.evaluations_used == budget, \
        "every created candidate must be evaluated exactly once, 30,000 in total"

    n, m, e = settings.n_scouts, settings.n_selected_sites, settings.n_elite_sites
    assert all(kind == "scout" for kind, _ in events[:n]), "initial population must be random scouts"
    population = values[:n]
    position = n
    iterations = 0
    last_iteration_recruits = []
    while position < budget:
        iterations += 1
        ranked = sorted(population)
        new_population = []
        recruits_this_iteration = []
        for site_rank in range(m):
            site_value = ranked[site_rank]
            recruits = settings.n_bees_elite if site_rank < e else settings.n_bees_selected
            block = events[position:position + recruits]
            assert all(event == ("recruit", site_value) for event in block), \
                f"iteration {iterations}: recruits not all made from site rank {site_rank + 1}"
            new_population.append(min([site_value] + values[position:position + len(block)]))
            recruits_this_iteration.append(len(block))
            position += len(block)
        block = events[position:position + (n - m)]
        assert all(kind == "scout" for kind, _ in block), f"iteration {iterations}: expected fresh scouts"
        new_population += values[position:position + len(block)]
        position += len(block)
        if position < budget:
            assert len(new_population) == n, f"iteration {iterations}: population size changed"
        population = new_population
        last_iteration_recruits = recruits_this_iteration + [len(block)]

    assert iterations == info["iterations_started"], "iteration count differs"
    assert tracker.best_value == min(values), "reported best is not the minimum of all evaluated values"
    scouts = sum(1 for kind, _ in events if kind == "scout")
    print(f"{function_name} D={dimension} seed {seed}: {iterations} iterations rebuilt and matched; "
          f"{scouts} random vectors, {budget - scouts} recruits (all within +-10 % of range, in bounds); "
          f"last iteration recruits per site {last_iteration_recruits[:-1]}, scouts {last_iteration_recruits[-1]}; "
          f"best {tracker.best_value:.6g}")


def main():
    for function_name, dimension, seed in TRACED_RUNS:
        trace_one_run(function_name, dimension, seed)
    print("ALL TRACE CHECKS PASSED: site selection, elite/non-elite recruitment, +-10 % neighbourhood with "
          "clipping, retention, scouting and stopping match the Bees Algorithm definition in every iteration.")


if __name__ == "__main__":
    main()
