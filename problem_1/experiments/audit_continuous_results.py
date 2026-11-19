# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
INDEPENDENT audit of the saved Part B results (all 80 runs and the summary table).

Like audit_tsp_results.py, this script imports NOTHING from the project's src/ or other
experiments/ files. It re-evaluates the saved vectors with its own copy of the SFU reference
formulas (plain loops and the math module), so a bug in the project's functions would show up
as a disagreement.

Checks for each of the 80 runs:
  1. Seeds 0-9 are present for every function and dimension (4 x 2 x 10 = 80 runs).
  2. The saved vector has D coordinates, all inside the function's bounds.
  3. Re-evaluating the vector with the independent formulas gives the saved value
     (relative tolerance 1e-9, because summing in a different order changes the last digits).
  4. Settings are identical in all runs; evaluations = 30,000; iterations started = 145.
  5. The final value is >= 0 (no run can beat the global minimum 0) and <= the initial best.
  6. The best-so-far history starts at evaluation 1, improves strictly, ends at the final value,
     and the convergence CSV is identical to the JSON history.
  7. The initial best equals the best of the first 10 evaluations (the initial population).
And the summary table: every value is recomputed with Python's statistics module.

Run from the problem_1 folder:
    python -m experiments.audit_continuous_results

Exit code 0 = all checks passed, 1 = at least one problem (each one is listed).
"""

import csv
import json
import math
import statistics
import sys
from pathlib import Path

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent

# Written out again here on purpose (not imported).
BOUNDS = {"sphere": (-5.12, 5.12), "rosenbrock": (-5.0, 10.0),
          "rastrigin": (-5.12, 5.12), "ackley": (-32.768, 32.768)}
EXPECTED_SETTINGS = {"n_scouts": 10, "n_selected_sites": 3, "n_elite_sites": 1,
                     "n_bees_elite": 100, "n_bees_selected": 50, "max_evaluations": 30000}
INITIAL_POPULATION_SIZE = 10
EXPECTED_ITERATIONS = 145   # 10 + 144 * 207 = 29,818 evaluations, then 182 more in iteration 145
DIMENSIONS = [10, 30]
SEEDS = list(range(10))


# Line-by-line copies of the SFU R reference code (https://www.sfu.ca/~ssurjano/).
def sfu_sphere(xx):
    return sum(value ** 2 for value in xx)


def sfu_rosen(xx):
    return sum(100 * (xx[i + 1] - xx[i] ** 2) ** 2 + (xx[i] - 1) ** 2 for i in range(len(xx) - 1))


def sfu_rastr(xx):
    return 10 * len(xx) + sum(value ** 2 - 10 * math.cos(2 * math.pi * value) for value in xx)


def sfu_ackley(xx, a=20, b=0.2, c=2 * math.pi):
    d = len(xx)
    term1 = -a * math.exp(-b * math.sqrt(sum(value ** 2 for value in xx) / d))
    term2 = -math.exp(sum(math.cos(c * value) for value in xx) / d)
    return term1 + term2 + a + math.exp(1)


REFERENCE = {"sphere": sfu_sphere, "rosenbrock": sfu_rosen, "rastrigin": sfu_rastr, "ackley": sfu_ackley}


def close(a, b):
    """Equal up to floating-point rounding (relative 1e-9, absolute 1e-12 for values near 0)."""
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def main():
    problems = []

    def check(condition, message):
        if not condition:
            problems.append(message)

    runs = {}
    for path in sorted((PROBLEM_FOLDER / "results" / "raw" / "continuous").glob("*.json")):
        run = json.load(open(path))
        runs[(run["function"], run["dimension"], run["seed"])] = run
    check(len(runs) == 80, f"expected 80 runs, found {len(runs)}")

    for function_name, (lower, upper) in BOUNDS.items():
        for dimension in DIMENSIONS:
            found_seeds = sorted(s for (f, d, s) in runs if f == function_name and d == dimension)
            check(found_seeds == SEEDS, f"{function_name}/D{dimension}: seeds {found_seeds}")
            for seed in found_seeds:
                run = runs[(function_name, dimension, seed)]
                label = f"{function_name}/D{dimension}/seed {seed}"
                vector = run["best_vector"]
                check(len(vector) == dimension, f"{label}: vector has {len(vector)} coordinates")
                check(all(lower <= value <= upper for value in vector), f"{label}: vector outside bounds")
                check(close(REFERENCE[function_name](vector), run["final_best_value"]),
                      f"{label}: independent re-evaluation differs from saved value")
                check(run["settings"] == EXPECTED_SETTINGS, f"{label}: settings differ")
                check(run["evaluations_used"] == 30000, f"{label}: {run['evaluations_used']} evaluations")
                check(run["iterations_started"] == EXPECTED_ITERATIONS, f"{label}: {run['iterations_started']} iterations")
                check(run["final_best_value"] >= -1e-12, f"{label}: below the global minimum (impossible)")
                check(run["final_best_value"] <= run["initial_best_value"], f"{label}: final worse than initial")

                history = run["best_so_far_history"]
                check(history[0][0] == 1 and history[-1][0] <= 30000, f"{label}: history evaluation range")
                check(all(a[0] < b[0] and a[1] > b[1] for a, b in zip(history, history[1:])),
                      f"{label}: history does not improve strictly")
                check(history[-1][1] == run["final_best_value"], f"{label}: history does not end at final value")
                initial_best = [value for evaluation, value in history if evaluation <= INITIAL_POPULATION_SIZE][-1]
                check(initial_best == run["initial_best_value"], f"{label}: initial best is not best of initial population")
                csv_path = PROBLEM_FOLDER / "results" / "convergence" / "continuous" / f"{function_name}_D{dimension}_seed{seed}.csv"
                with open(csv_path) as handle:
                    csv_rows = list(csv.reader(handle))
                check(csv_rows[0] == ["evaluation", "best_so_far_value"]
                      and [[int(a), float(b)] for a, b in csv_rows[1:]] == history,
                      f"{label}: convergence CSV differs from JSON history")

    with open(PROBLEM_FOLDER / "results" / "tables" / "continuous_summary.csv") as handle:
        saved_rows = list(csv.DictReader(handle))
    check(len(saved_rows) == 8, f"summary has {len(saved_rows)} rows, expected 8")
    for row in saved_rows:
        group = [runs[(row["Function"], int(row["D"]), seed)] for seed in SEEDS]
        finals = [run["final_best_value"] for run in group]
        recomputed = {
            "Runs": len(group),
            "Mean initial best": statistics.mean(run["initial_best_value"] for run in group),
            "Best": min(finals),
            "Mean": statistics.mean(finals),
            "Std": statistics.stdev(finals),          # sample standard deviation (n - 1)
            "Median": statistics.median(finals),
            "Mean runtime (s)": statistics.mean(run["runtime_seconds"] for run in group),
        }
        for column, value in recomputed.items():
            check(close(float(row[column]), value),
                  f"summary {row['Function']}/D{row['D']} {column}: saved {row[column]}, recomputed {value}")

    print(f"Checked {len(runs)} runs and {len(saved_rows)} summary rows.")
    if problems:
        print(f"PROBLEMS FOUND: {len(problems)}")
        for problem in problems:
            print("  -", problem)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
