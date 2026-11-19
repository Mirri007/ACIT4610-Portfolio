# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Variants 2 and 3: the population ES, (mu + lambda)-ES and (mu, lambda)-ES (assignment, "Variants 2 & 3").

Notation
--------
* mu = 10 parents, lambda = 70 offspring per generation.
* Each individual carries its weights w AND its own vector of step sizes sigma_1..sigma_n
  (one per weight). The step sizes evolve together with the weights: this is SELF-ADAPTATION.
  Individuals whose step sizes produce good children tend to survive, and so do their step sizes.

One generation, step by step (for each of the 70 children)
---------------------------------------------------------
1. Choose two parents uniformly at random.
2. Recombination (mixing the parents):
       weights:     w_r = (w(1) + w(2)) / 2                     (average)
       step sizes:  sigma_r,i = sqrt(sigma_i(1) * sigma_i(2))    (geometric mean)
   The geometric mean is used for step sizes because they act multiplicatively: the geometric
   mean of 0.01 and 1.0 is 0.1, halfway on a log scale, whereas the ordinary mean (0.505) would
   be dominated by the larger value.
3. Self-adaptation of the step sizes (log-normal update):
       sigma'_i = sigma_r,i * exp(tau' * Z0 + tau * Z_i),  clamped to [1e-8, 1.0]
       tau' = 1 / sqrt(2 n),   tau = 1 / sqrt(2 sqrt(n))
   Z0 is ONE standard-normal number shared by all coordinates of this child: it scales all step
   sizes up or down together (an overall "bolder or more careful" change). Each Z_i is a separate
   standard-normal number per coordinate: it lets individual step sizes differ. Multiplying by
   exp(...) keeps step sizes positive and makes doubling and halving equally likely.
4. Mutation with the NEW step sizes: z_i = w_r,i + sigma'_i * N_i(0, 1) (fresh normal numbers),
   then repair z -> feasible w and evaluate (one evaluation). The child stores sigma'.
5. Survivor selection when all 70 children are evaluated:
       (mu + lambda): the 10 lowest-variance individuals among the 10 parents AND 70 children.
                      The best individual can never be lost ("elitist").
       (mu , lambda): the 10 lowest-variance individuals among the 70 CHILDREN only. Every parent
                      dies after one generation, even a very good one, so the population's best
                      variance can get WORSE from one generation to the next. The archive (in the
                      evaluator) still remembers the best portfolio ever seen, so the reported
                      result never gets worse; the archive is not used to choose parents.

Budget: 10 initial evaluations + 70 per generation. 30,000 = 10 + 428 x 70 + 30, so the last
generation creates only 30 children. They are evaluated (and can enter the archive), and the run
stops there; no survivor selection follows because no further generation will be created.

Interpretation choices (the assignment does not specify these details)
---------------------------------------------------------------------
* "Two parents selected uniformly at random": the two parents are DIFFERENT individuals
  (drawn without replacement). Choosing the same parent twice would make recombination a copy.
* Ties in variance during survivor selection are broken by position (Python's sort is stable):
  in (mu + lambda) parents come before children, so an equally good parent is kept.
"""

import math
from dataclasses import dataclass

import numpy as np

PARENTS = 10        # mu
OFFSPRING = 70      # lambda
STEP_SIZE_MIN = 1e-8
STEP_SIZE_MAX = 1.0


@dataclass
class Individual:
    """One member of the population: its (repaired, feasible) weights, its step sizes and its variance."""

    weights: np.ndarray
    step_sizes: np.ndarray
    variance: float


def learning_rates(n_assets):
    """tau' = 1/sqrt(2n) (shared, overall) and tau = 1/sqrt(2 sqrt(n)) (per coordinate)."""
    tau_prime = 1.0 / math.sqrt(2.0 * n_assets)
    tau = 1.0 / math.sqrt(2.0 * math.sqrt(n_assets))
    return tau_prime, tau


def recombine(parent_1, parent_2):
    """Intermediate recombination of weights (average) and geometric mean of step sizes."""
    weights = (parent_1.weights + parent_2.weights) / 2.0
    step_sizes = np.sqrt(parent_1.step_sizes * parent_2.step_sizes)
    return weights, step_sizes


def self_adapt_step_sizes(step_sizes, shared_normal, coordinate_normals, tau_prime, tau):
    """sigma'_i = sigma_i * exp(tau' * Z0 + tau * Z_i), then clamp every value to [1e-8, 1.0]."""
    adapted = step_sizes * np.exp(tau_prime * shared_normal + tau * coordinate_normals)
    return np.clip(adapted, STEP_SIZE_MIN, STEP_SIZE_MAX)


def select_survivors(parents, offspring, selection):
    """
    Return the mu individuals with the lowest variance.

    selection = "plus":  choose from parents + offspring (elitist).
    selection = "comma": choose from offspring only (parents are always discarded).
    """
    if selection == "plus":
        pool = parents + offspring
    elif selection == "comma":
        pool = list(offspring)
    else:
        raise ValueError(f"selection must be 'plus' or 'comma', not {selection!r}")
    pool.sort(key=lambda individual: individual.variance)   # stable: equal variances keep their order
    return pool[:PARENTS]


def create_child(parents, n_assets, tau_prime, tau, evaluator, rng):
    """Steps 1-4 for one child: choose parents, recombine, self-adapt, mutate, repair + evaluate."""
    first_index, second_index = rng.choice(len(parents), size=2, replace=False)
    recombined_weights, recombined_step_sizes = recombine(parents[first_index], parents[second_index])
    shared_normal = rng.standard_normal()                   # Z0: one number for the whole child
    coordinate_normals = rng.standard_normal(n_assets)      # Z_i: one number per coordinate
    new_step_sizes = self_adapt_step_sizes(recombined_step_sizes, shared_normal, coordinate_normals, tau_prime, tau)
    candidate = recombined_weights + new_step_sizes * rng.standard_normal(n_assets)   # fresh N_i
    weights, variance = evaluator.evaluate(candidate)
    return Individual(weights, new_step_sizes, variance)


def run_population_es(evaluator, n_assets, rng, selection):
    """
    Run the (mu + lambda)-ES (selection="plus") or (mu, lambda)-ES (selection="comma")
    until the evaluation budget is used up.

    Returns
    -------
    dict with the initial best variance, number of generations (including an incomplete last one),
    and ``population_best_history``: (evaluation number, best variance in the CURRENT parent
    population) after initialisation and after every survivor selection. For (mu, lambda) this
    can go up; the archive in ``evaluator`` cannot.
    """
    tau_prime, tau = learning_rates(n_assets)
    initial_step_sizes = np.full(n_assets, 0.1 / math.sqrt(n_assets))

    # Initialisation: mu parents, each with uniform [0, 1] weights repaired into a portfolio
    # (one evaluation each) and the same initial step-size vector 0.1 / sqrt(n).
    parents = []
    for _ in range(PARENTS):
        weights, variance = evaluator.evaluate(rng.uniform(0.0, 1.0, size=n_assets))
        parents.append(Individual(weights, initial_step_sizes.copy(), variance))
    initial_best_variance = min(parent.variance for parent in parents)
    population_best_history = [(evaluator.evaluations_used, initial_best_variance)]

    generations = 0
    while not evaluator.budget_exhausted():
        generations += 1
        offspring = []
        for _ in range(OFFSPRING):
            if evaluator.budget_exhausted():
                break     # last generation: fewer than 70 children (assignment allows this)
            offspring.append(create_child(parents, n_assets, tau_prime, tau, evaluator, rng))

        if len(offspring) == OFFSPRING:
            parents = select_survivors(parents, offspring, selection)
            population_best_history.append((evaluator.evaluations_used, parents[0].variance))
        # An incomplete last batch has already been evaluated and archived; the run ends here.

    return {
        "initial_best_variance": initial_best_variance,
        "generations": generations,
        "final_batch_size": len(offspring),
        "population_best_history": population_best_history,
        "final_population_mean_step_size": float(np.mean([np.mean(p.step_sizes) for p in parents])),
    }
