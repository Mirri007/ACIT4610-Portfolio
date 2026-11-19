# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
TRACE audit of the three ES variants at the full 30,000-evaluation budget.

For one experiment run of each variant (port5_alpha050 and port1_alpha075, seed 0), the run is
REPEATED with every evaluation logged. The audit then checks, using only the log:

  (1+1)-ES
    * the first evaluation is the initial parent; then 29,999 trials;
    * acceptance happens exactly when the child's variance is strictly lower;
    * the step size rebuilt from successes/failures (x exp(1/3) / x exp(-1/12), clamped to
      [1e-8, 1]) explains the mutations: (candidate - parent) / sigma behaves like standard
      normal numbers (mean ~0, standard deviation ~1);
  (mu+lambda) and (mu,lambda)
    * 10 initial evaluations, then 428 generations of 70 children and a final batch of 30;
    * the population best after each generation equals min(previous best, children) for plus
      and min(children) for comma (so comma never takes parents or the archive);
  all variants
    * every evaluated portfolio is feasible; the archive equals the minimum of all 30,000
      variances; the repeated run reproduces the saved experiment result exactly.

Run from the problem_2 folder:
    python -m experiments.audit_es_trace
"""

import os

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[variable] = "1"

import json  # noqa: E402
import math  # noqa: E402

import numpy as np  # noqa: E402

from src import es_one_plus_one, es_population  # noqa: E402
from src.portfolio_data import load_case  # noqa: E402
from src.portfolio_evaluator import PortfolioEvaluator  # noqa: E402
from src.portfolio_model import is_feasible  # noqa: E402
from experiments.run_es_experiments import RAW_FOLDER  # noqa: E402

BUDGET = 30_000
TRACED = [("port5_alpha050", 0), ("port1_alpha075", 0)]


class RecordingEvaluator(PortfolioEvaluator):
    def __init__(self, case, max_evaluations):
        super().__init__(case, max_evaluations)
        self.candidates, self.portfolios, self.variances = [], [], []

    def evaluate(self, candidate):
        weights, variance = super().evaluate(candidate)
        self.candidates.append(np.array(candidate, copy=True))
        self.portfolios.append(weights)
        self.variances.append(variance)
        return weights, variance


def check_common(case, evaluator, variant, seed):
    saved = json.load(open(RAW_FOLDER / f"{case.name}_{variant}_seed{seed}.json"))
    assert evaluator.evaluations_used == BUDGET
    assert all(is_feasible(w, case.data.mean_returns, case.min_return) for w in evaluator.portfolios), "infeasible candidate"
    assert evaluator.archive_variance == min(evaluator.variances), "archive is not the minimum of all evaluations"
    assert [float(x) for x in evaluator.archive_weights] == saved["best_weights"], "repeated run differs from saved result"


def trace_one_plus_one(case, seed):
    n = case.data.n_assets
    evaluator = RecordingEvaluator(case, BUDGET)
    info = es_one_plus_one.run_one_plus_one_es(evaluator, n, np.random.default_rng(seed))
    check_common(case, evaluator, "one_plus_one", seed)
    parent_w, parent_v = evaluator.portfolios[0], evaluator.variances[0]
    sigma = 0.1 / math.sqrt(n)
    successes = 0
    noise_sum = noise_square_sum = noise_count = 0.0
    for k in range(1, BUDGET):
        noise = (evaluator.candidates[k] - parent_w) / sigma
        noise_sum += noise.sum(); noise_square_sum += (noise ** 2).sum(); noise_count += noise.size
        if evaluator.variances[k] < parent_v:
            parent_w, parent_v = evaluator.portfolios[k], evaluator.variances[k]
            sigma = min(sigma * math.exp(1 / 3), 1.0)
            successes += 1
        else:
            sigma = max(sigma * math.exp(-1 / 12), 1e-8)
    mean = noise_sum / noise_count
    std = math.sqrt(noise_square_sum / noise_count - mean ** 2)
    assert abs(mean) < 0.01 and abs(std - 1) < 0.01, f"mutation noise mean {mean}, std {std}"
    assert successes == info["successful_trials"]
    assert math.isclose(sigma, info["final_step_size"], rel_tol=1e-9)
    print(f"  (1+1)-ES   {case.name} seed {seed}: 29,999 trials rebuilt; {successes} successes "
          f"({100 * successes / 29999:.1f} %); noise mean {mean:+.4f}, std {std:.4f}; final sigma {sigma:.2e}")


def trace_population(case, seed, selection):
    variant = "mu_plus_lambda" if selection == "plus" else "mu_comma_lambda"
    evaluator = RecordingEvaluator(case, BUDGET)
    info = es_population.run_population_es(evaluator, case.data.n_assets, np.random.default_rng(seed), selection)
    check_common(case, evaluator, variant, seed)
    v = evaluator.variances
    best = min(v[:10])
    rebuilt = [best]
    for generation in range(428):
        children = v[10 + 70 * generation:10 + 70 * (generation + 1)]
        best = min(children) if selection == "comma" else min(best, min(children))
        rebuilt.append(best)
    assert info["generations"] == 429 and info["final_batch_size"] == 30 and 10 + 428 * 70 + 30 == BUDGET
    assert [value for _, value in info["population_best_history"]] == rebuilt, "survivor selection does not match the rule"
    worsened = sum(1 for a, b in zip(rebuilt, rebuilt[1:]) if b > a)
    if selection == "plus":
        assert worsened == 0
    print(f"  {'(μ+λ)' if selection == 'plus' else '(μ,λ)'}-ES   {case.name} seed {seed}: 429 generations "
          f"(last batch 30) rebuilt; population best got worse in {worsened} generations; "
          f"archive {evaluator.archive_variance:.6e}")


def main():
    for case_name, seed in TRACED:
        case = load_case(case_name)
        trace_one_plus_one(case, seed)
        trace_population(case, seed, "plus")
        trace_population(case, seed, "comma")
    print("ALL TRACE CHECKS PASSED")


if __name__ == "__main__":
    main()
