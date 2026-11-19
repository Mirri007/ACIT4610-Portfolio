# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
INDEPENDENT audit of the saved Part A results (all 120 runs and the summary table).

Why "independent"?
------------------
This script deliberately imports NOTHING from the project's ``src/`` or other ``experiments/``
files. It has its own TSPLIB reader, its own distance rule and uses Python's ``statistics``
module for the table. If the project code had a bug (e.g. a wrong distance or a wrong mean),
this script would not share that bug, so it would disagree and report the problem.

What it checks
--------------
For every one of the 120 saved runs:
  1. The tour is a permutation of all cities and starts at city 1.
  2. Its length, recomputed here edge by edge (including the return leg), equals the saved length.
  3. Settings are identical in all runs; evaluations = 30,000; iterations started = 195.
  4. The gap equals 100 * (L - L*) / L*, and no tour is shorter than the optimum.
  5. The best-so-far history starts at evaluation 1, improves strictly, ends at the final length,
     and is identical in the JSON file and the convergence CSV.
  6. The saved initial best equals the best of the first 6 evaluations (the initial population).
For every seed: swap and reversal start from the same initial best (same initial population).
For the summary table: every value is recomputed and compared.

Run from the problem_1 folder:
    python -m experiments.audit_tsp_results

Exit code 0 = all checks passed, 1 = at least one problem (each one is listed).
"""

import csv
import gzip
import json
import math
import statistics
import sys
from pathlib import Path

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent

# Written out again here on purpose (not imported), so this audit does not depend on project code.
OPTIMA = {"eil51": (51, 426), "berlin52": (52, 7542), "st70": (70, 675),
          "eil76": (76, 538), "kroA100": (100, 21282), "ch150": (150, 6528)}
EXPECTED_SETTINGS = {"n_scouts": 6, "n_selected_sites": 2, "n_elite_sites": 1,
                     "n_bees_elite": 100, "n_bees_selected": 50, "max_evaluations": 30000}
INITIAL_POPULATION_SIZE = 6
EXPECTED_ITERATIONS = 195   # 6 + 194 * 154 = 29,882 evaluations, then 118 more in iteration 195
SEEDS = list(range(10))
NEIGHBOURHOODS = ["swap", "reversal"]


def read_coordinates(instance_name):
    """Minimal TSPLIB reader: returns {city id: (x, y)} from the original .tsp.gz file."""
    path = PROBLEM_FOLDER / "data" / "tsplib_original" / f"{instance_name}.tsp.gz"
    lines = [line.strip() for line in gzip.open(path, "rt").read().splitlines()]
    start = lines.index("NODE_COORD_SECTION") + 1
    coordinates = {}
    for line in lines[start:]:
        if line in ("EOF", ""):
            break
        city_id, x, y = line.split()
        coordinates[int(city_id)] = (float(x), float(y))
    return coordinates


def closed_tour_length(city_ids, coordinates):
    """TSPLIB EUC_2D length: each edge rounded with floor(d + 0.5); the return edge is included."""
    next_city_ids = city_ids[1:] + city_ids[:1]   # shift by one; the last city pairs with the first
    total = 0
    for a, b in zip(city_ids, next_city_ids):
        dx = coordinates[a][0] - coordinates[b][0]
        dy = coordinates[a][1] - coordinates[b][1]
        total += math.floor(math.hypot(dx, dy) + 0.5)
    return total


def best_so_far_at(history, evaluation):
    """Best-so-far value after a given number of evaluations, read from the change-point history."""
    return [value for eval_number, value in history if eval_number <= evaluation][-1]


def main():
    problems = []

    def check(condition, message):
        if not condition:
            problems.append(message)

    runs = {}
    for path in sorted((PROBLEM_FOLDER / "results" / "raw" / "tsp").glob("*.json")):
        run = json.load(open(path))
        runs[(run["instance"], run["neighbourhood"], run["seed"])] = run
    check(len(runs) == 120, f"expected 120 runs, found {len(runs)}")

    for instance_name, (cities, optimum) in OPTIMA.items():
        coordinates = read_coordinates(instance_name)
        for neighbourhood in NEIGHBOURHOODS:
            found_seeds = sorted(s for (i, n, s) in runs if i == instance_name and n == neighbourhood)
            check(found_seeds == SEEDS, f"{instance_name}/{neighbourhood}: seeds {found_seeds}")
            for seed in found_seeds:
                run = runs[(instance_name, neighbourhood, seed)]
                label = f"{instance_name}/{neighbourhood}/seed {seed}"
                tour = run["best_tour_city_ids"]
                check(sorted(tour) == list(range(1, cities + 1)), f"{label}: tour is not a permutation")
                check(tour[0] == 1, f"{label}: tour does not start at city 1")
                check(closed_tour_length(tour, coordinates) == run["final_best_length"], f"{label}: length mismatch")
                check(run["settings"] == EXPECTED_SETTINGS, f"{label}: settings differ")
                check(run["evaluations_used"] == 30000, f"{label}: {run['evaluations_used']} evaluations")
                check(run["iterations_started"] == EXPECTED_ITERATIONS, f"{label}: {run['iterations_started']} iterations")
                expected_gap = 100 * (run["final_best_length"] - optimum) / optimum
                check(abs(run["gap_percent"] - expected_gap) < 1e-9, f"{label}: gap wrong")
                check(run["final_best_length"] >= optimum, f"{label}: shorter than the optimum (impossible)")

                history = run["best_so_far_history"]
                check(history[0][0] == 1 and history[-1][0] <= 30000, f"{label}: history evaluation range")
                check(all(a[0] < b[0] and a[1] > b[1] for a, b in zip(history, history[1:])),
                      f"{label}: history does not improve strictly")
                check(history[-1][1] == run["final_best_length"], f"{label}: history does not end at final length")
                check(best_so_far_at(history, INITIAL_POPULATION_SIZE) == run["initial_best_length"],
                      f"{label}: initial best is not the best of the initial population")
                csv_path = PROBLEM_FOLDER / "results" / "convergence" / "tsp" / f"{instance_name}_{neighbourhood}_seed{seed}.csv"
                with open(csv_path) as handle:
                    csv_rows = list(csv.reader(handle))
                check(csv_rows[0] == ["evaluation", "best_so_far_length"]
                      and [[int(a), int(b)] for a, b in csv_rows[1:]] == history,
                      f"{label}: convergence CSV differs from JSON history")

        # Same seed -> same initial population for both neighbourhoods (fair comparison).
        for seed in SEEDS:
            check(runs[(instance_name, "swap", seed)]["initial_best_length"]
                  == runs[(instance_name, "reversal", seed)]["initial_best_length"],
                  f"{instance_name}/seed {seed}: initial best differs between neighbourhoods")

    # Recompute every number in the summary table.
    with open(PROBLEM_FOLDER / "results" / "tables" / "tsp_summary.csv") as handle:
        saved_rows = list(csv.DictReader(handle))
    check(len(saved_rows) == 12, f"summary has {len(saved_rows)} rows, expected 12")
    for row in saved_rows:
        group = [runs[(row["Instance"], row["Neighbourhood"], seed)] for seed in SEEDS]
        lengths = [run["final_best_length"] for run in group]
        recomputed = {
            "Cities": OPTIMA[row["Instance"]][0],
            "Optimum": OPTIMA[row["Instance"]][1],
            "Runs": len(group),
            "Mean initial best": round(statistics.mean(run["initial_best_length"] for run in group), 1),
            "Best": min(lengths),
            "Mean": round(statistics.mean(lengths), 1),
            "Std": round(statistics.stdev(lengths), 1),          # sample standard deviation (n - 1)
            "Best gap (%)": round(min(run["gap_percent"] for run in group), 2),
            "Mean gap (%)": round(statistics.mean(run["gap_percent"] for run in group), 2),
            "Mean runtime (s)": round(statistics.mean(run["runtime_seconds"] for run in group), 3),
        }
        for column, value in recomputed.items():
            check(abs(float(row[column]) - value) < 1e-9,
                  f"summary {row['Instance']}/{row['Neighbourhood']} {column}: saved {row[column]}, recomputed {value}")

    # Extra information: the run shown in the route plot, and whether it is a tie.
    berlin = sorted((run["final_best_length"], n, s) for (i, n, s), run in runs.items() if i == "berlin52")
    print(f"berlin52 shortest tours: {berlin[:3]} (tie for best: {berlin[0][0] == berlin[1][0]})")

    print(f"Checked {len(runs)} runs, {len(OPTIMA) * len(SEEDS)} initial-population pairs and "
          f"{len(saved_rows)} summary rows.")
    if problems:
        print(f"PROBLEMS FOUND: {len(problems)}")
        for problem in problems:
            print("  -", problem)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
