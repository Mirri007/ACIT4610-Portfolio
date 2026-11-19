# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Run one ES variant on one test case with one seed, validate the result and record everything.

Seeds (kept strictly separate)
------------------------------
* FINAL_SEEDS 0-9:            the 450 reported experiment runs only.
* PRELIMINARY_SEEDS 900-904:  smoke tests and runtime measurements before the experiments.
* Seeds >= 1000:              used inside the automated tests.
No seeds are needed for parameter tuning: every ES parameter (mu, lambda, initial step sizes,
step-size bounds, 1/5 rule factors, tau, tau') is fixed by the assignment, so nothing is tuned.
"""

import math
import time

import numpy as np

from src import es_one_plus_one, es_population
from src.portfolio_evaluator import PortfolioEvaluator
from src.portfolio_model import expected_return, feasibility_violations, portfolio_variance

BUDGET = 30_000
FINAL_SEEDS = list(range(10))
PRELIMINARY_SEEDS = [900, 901, 902, 903, 904]

# Internal names (used in file names) -> labels used consistently in tables and figures.
VARIANTS = {
    "one_plus_one": "(1+1)-ES",
    "mu_plus_lambda": "(μ+λ)-ES",
    "mu_comma_lambda": "(μ,λ)-ES",
}


def variant_settings(variant, n_assets):
    """All parameters of a variant for a given number of assets (saved with every run)."""
    if variant == "one_plus_one":
        return {
            "initial_step_size": es_one_plus_one.initial_step_size(n_assets),
            "step_size_bounds": [es_one_plus_one.STEP_SIZE_MIN, es_one_plus_one.STEP_SIZE_MAX],
            "success_factor": "exp(1/3)",
            "failure_factor": "exp(-1/12)",
            "budget": BUDGET,
        }
    tau_prime, tau = es_population.learning_rates(n_assets)
    return {
        "mu": es_population.PARENTS,
        "lambda": es_population.OFFSPRING,
        "selection": "plus" if variant == "mu_plus_lambda" else "comma",
        "initial_step_size": 0.1 / math.sqrt(n_assets),
        "step_size_bounds": [es_population.STEP_SIZE_MIN, es_population.STEP_SIZE_MAX],
        "tau_prime": tau_prime,
        "tau": tau,
        "parent_choice": "two different parents, uniformly at random",
        "budget": BUDGET,
    }


def run_es_on_case(case, variant, seed, budget=BUDGET):
    """
    Perform one complete run and return a dictionary with everything the assignment asks to record.

    Returns
    -------
    dict
        case, dataset, number of assets, alpha, target return, variant, seed, settings,
        initial best variance, final archived (best valid) weights, their expected return and
        variance, feasibility status and any violations, runtime, evaluations used,
        archive history (convergence log) and variant-specific details.
    """
    if variant not in VARIANTS:
        raise ValueError(f"Unknown variant {variant!r}")
    n_assets = case.data.n_assets
    rng = np.random.default_rng(seed)
    evaluator = PortfolioEvaluator(case, budget)

    start_time = time.perf_counter()
    if variant == "one_plus_one":
        details = es_one_plus_one.run_one_plus_one_es(evaluator, n_assets, rng)
    else:
        selection = "plus" if variant == "mu_plus_lambda" else "comma"
        details = es_population.run_population_es(evaluator, n_assets, rng, selection)
    runtime_seconds = time.perf_counter() - start_time

    weights = evaluator.archive_weights
    if evaluator.evaluations_used != budget:
        raise RuntimeError("Run did not use exactly the evaluation budget")
    variance = portfolio_variance(weights, case.data.covariance)
    if variance != evaluator.archive_variance:
        raise RuntimeError("Archived variance does not match the archived weights")
    violations = feasibility_violations(weights, case.data.mean_returns, case.min_return)

    return {
        "case": case.name,
        "dataset": case.data.name,
        "n_assets": n_assets,
        "alpha": case.alpha,
        "target_return": case.min_return,
        "variant": variant,
        "variant_label": VARIANTS[variant],
        "seed": seed,
        "settings": variant_settings(variant, n_assets),
        "initial_best_variance": float(details.pop("initial_best_variance")),
        "final_variance": float(variance),
        "final_expected_return": expected_return(weights, case.data.mean_returns),
        "feasible": not violations,
        "feasibility_violations": violations,
        "min_weight": float(weights.min()),
        "weight_sum_error": float(abs(weights.sum() - 1.0)),
        "assets_with_weight_above_1e-6": int(np.sum(weights > 1e-6)),
        "invalid_evaluations": evaluator.invalid_evaluations,
        "runtime_seconds": runtime_seconds,
        "evaluations_used": evaluator.evaluations_used,
        "best_weights": [float(value) for value in weights],
        "archive_history": [[int(evaluation), float(value)] for evaluation, value in evaluator.history],
        "details": details,
    }
