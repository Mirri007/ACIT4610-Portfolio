# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
INDEPENDENT audit of the saved Problem 2 results (all 450 runs and the summary table).

This script imports NOTHING from the project's src/ or other experiments/ files, and not even
NumPy: it has its own dataset reader, builds the covariance itself and computes every variance as
an explicit double sum  V(w) = sum_i sum_j w_i w_j s_i s_j C_ij  in plain Python. A bug in the
project's formulas would therefore show up as a disagreement here.

Checks for each of the 450 runs:
  1. Every case x variant has seeds 0-9.
  2. The target return equals (1 - alpha) R_eq + alpha r_max, recomputed from the raw file.
  3. The best weights satisfy the assignment tolerances (w_i >= -1e-8, |sum - 1| <= 1e-8,
     R(w) >= R_min - 1e-8), and the saved "feasible" flag agrees.
  4. Variance and return recomputed independently match the saved values (relative 1e-9).
  5. Settings match the assignment (mu = 10, lambda = 70, sigma0 = 0.1/sqrt(n), bounds
     [1e-8, 1], tau' = 1/sqrt(2n), tau = 1/sqrt(2 sqrt n)); evaluations = 30,000;
     (1+1): 29,999 trials; population ES: 429 generations with a final batch of 30 children.
  6. The archive history starts at evaluation 1, improves strictly, ends at the final variance,
     and equals the convergence CSV; the final variance is <= the initial best variance.
  7. For the same seed, (mu+lambda) and (mu,lambda) start from the same initial best variance
     (identical initial parents), as the paired comparison assumes.
And the summary table: every value recomputed (variance statistics over valid runs only,
runtime over all 10 runs).

Run from the problem_2 folder:
    python -m experiments.audit_es_results

Exit code 0 = all checks passed, 1 = at least one problem (each one is listed).
"""

import csv
import json
import math
import statistics
import sys
from pathlib import Path

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent
DATASET_SIZES = {"port1": 31, "port2": 85, "port3": 89, "port4": 98, "port5": 225}
ALPHAS = {"025": 0.25, "050": 0.50, "075": 0.75}
VARIANTS = ["one_plus_one", "mu_plus_lambda", "mu_comma_lambda"]
SEEDS = list(range(10))
TOLERANCE = 1e-8


def read_dataset(name):
    """Plain-Python reader: returns (returns list, std list, correlation dict {(i, j): c}) with 0-based i, j."""
    lines = [line.split() for line in open(PROBLEM_FOLDER / "data" / f"{name}.txt") if line.strip()]
    n = int(lines[0][0])
    returns = [float(line[0]) for line in lines[1:n + 1]]
    stds = [float(line[1]) for line in lines[1:n + 1]]
    correlation = {}
    for line in lines[n + 1:]:
        i, j, c = int(line[0]) - 1, int(line[1]) - 1, float(line[2])
        correlation[(i, j)] = correlation[(j, i)] = c
    return returns, stds, correlation


def variance_double_sum(w, stds, correlation):
    n = len(w)
    return sum(w[i] * w[j] * stds[i] * stds[j] * correlation[(i, j)] for i in range(n) for j in range(n))


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-15)


def main():
    problems = []

    def check(condition, message):
        if not condition:
            problems.append(message)

    runs = {}
    for path in sorted((PROBLEM_FOLDER / "results" / "raw" / "es").glob("*.json")):
        run = json.load(open(path))
        runs[(run["case"], run["variant"], run["seed"])] = run
    check(len(runs) == 450, f"expected 450 runs, found {len(runs)}")

    case_names = []
    for dataset, n in DATASET_SIZES.items():
        returns, stds, correlation = read_dataset(dataset)
        check(len(returns) == n, f"{dataset}: {len(returns)} assets")
        equal_return = sum(returns) / n
        max_return = max(returns)
        for alpha_text, alpha in ALPHAS.items():
            case = f"{dataset}_alpha{alpha_text}"
            case_names.append(case)
            target = (1 - alpha) * equal_return + alpha * max_return
            for variant in VARIANTS:
                found = sorted(s for (c, v, s) in runs if c == case and v == variant)
                check(found == SEEDS, f"{case}/{variant}: seeds {found}")
                for seed in found:
                    run = runs[(case, variant, seed)]
                    label = f"{case}/{variant}/seed {seed}"
                    w = run["best_weights"]
                    check(len(w) == n, f"{label}: {len(w)} weights")
                    check(close(run["target_return"], target), f"{label}: target return differs")
                    portfolio_return = sum(r * x for r, x in zip(returns, w))
                    feasible = (min(w) >= -TOLERANCE and abs(sum(w) - 1) <= TOLERANCE
                                and portfolio_return >= target - TOLERANCE)
                    check(feasible == run["feasible"], f"{label}: feasibility flag disagrees")
                    check(feasible, f"{label}: final portfolio NOT feasible")
                    check(close(portfolio_return, run["final_expected_return"]), f"{label}: return differs")
                    check(close(variance_double_sum(w, stds, correlation), run["final_variance"]), f"{label}: variance differs")
                    check(run["evaluations_used"] == 30000, f"{label}: {run['evaluations_used']} evaluations")
                    check(run["invalid_evaluations"] == 0, f"{label}: {run['invalid_evaluations']} invalid evaluations")
                    s = run["settings"]
                    check(math.isclose(s["initial_step_size"], 0.1 / math.sqrt(n)), f"{label}: sigma0")
                    check(s["step_size_bounds"] == [1e-8, 1.0], f"{label}: step-size bounds")
                    if variant == "one_plus_one":
                        check(run["details"]["trials"] == 29999, f"{label}: trials")
                    else:
                        check(s["mu"] == 10 and s["lambda"] == 70, f"{label}: mu/lambda")
                        check(math.isclose(s["tau_prime"], 1 / math.sqrt(2 * n)), f"{label}: tau'")
                        check(math.isclose(s["tau"], 1 / math.sqrt(2 * math.sqrt(n))), f"{label}: tau")
                        check(s["selection"] == ("plus" if variant == "mu_plus_lambda" else "comma"), f"{label}: selection")
                        check(run["details"]["generations"] == 429 and run["details"]["final_batch_size"] == 30,
                              f"{label}: generations / final batch")
                    history = run["archive_history"]
                    check(history[0][0] == 1 and history[-1][0] <= 30000, f"{label}: history range")
                    check(all(a[0] < b[0] and a[1] > b[1] for a, b in zip(history, history[1:])), f"{label}: history not improving")
                    check(history[-1][1] == run["final_variance"], f"{label}: history end != final variance")
                    check(run["final_variance"] <= run["initial_best_variance"], f"{label}: final worse than initial")
                    with open(PROBLEM_FOLDER / "results" / "convergence" / "es" / f"{case}_{variant}_seed{seed}.csv") as handle:
                        rows = list(csv.reader(handle))
                    check(rows[0] == ["evaluation", "archive_best_variance"]
                          and [[int(a), float(b)] for a, b in rows[1:]] == history, f"{label}: CSV != JSON history")
            for seed in SEEDS:
                plus, comma = runs[(case, "mu_plus_lambda", seed)], runs[(case, "mu_comma_lambda", seed)]
                check(plus["initial_best_variance"] == comma["initial_best_variance"],
                      f"{case}/seed {seed}: plus and comma did not start from the same parents")

    labels = {"(1+1)-ES": "one_plus_one", "(μ+λ)-ES": "mu_plus_lambda", "(μ,λ)-ES": "mu_comma_lambda"}
    with open(PROBLEM_FOLDER / "results" / "tables" / "es_summary.csv") as handle:
        saved_rows = list(csv.DictReader(handle))
    check(len(saved_rows) == 45, f"summary has {len(saved_rows)} rows, expected 45")
    for row in saved_rows:
        group = [runs[(row["Case"], labels[row["Variant"]], seed)] for seed in SEEDS]
        valid = [run["final_variance"] for run in group if run["feasible"]]
        expected = {
            "Best variance": min(valid), "Mean variance": statistics.mean(valid), "Std variance": statistics.stdev(valid),
            "Mean runtime (s)": statistics.mean(run["runtime_seconds"] for run in group),
            "Mean initial best variance": statistics.mean(run["initial_best_variance"] for run in group),
        }
        for column, value in expected.items():
            check(close(float(row[column]), value), f"summary {row['Case']}/{row['Variant']} {column}")
        check(row["Feasible runs"] == f"{len(valid)}/10", f"summary {row['Case']}/{row['Variant']} feasible count")

    print(f"Checked {len(runs)} runs, {len(case_names)} cases and {len(saved_rows)} summary rows.")
    if problems:
        print(f"PROBLEMS FOUND: {len(problems)}")
        for problem in problems[:40]:
            print("  -", problem)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
