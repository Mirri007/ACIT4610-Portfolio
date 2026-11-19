# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Build the Part A tables from the saved run results.

Run from the problem_1 folder (after run_tsp_experiments):

    python -m experiments.make_tsp_tables

Outputs
-------
* ``results/raw/tsp_all_runs.csv``: one row per run (all 120 runs), the raw per-run data.
* ``results/tables/tsp_summary.csv`` and ``tsp_summary.md``: the required summary table, one
  row per instance and neighbourhood version: instance, cities, optimum, best, mean and
  standard deviation of the final tour length, mean percentage gap and mean runtime.
  Two extra columns help the discussion: the mean initial best length (to show improvement
  from the initial population) and the best gap.

Before summarising, every saved tour is checked again from scratch: it must be a valid
permutation starting at city 1, its length must be recomputed to the saved value, and the
run must have used exactly 30,000 evaluations.

Statistics
----------
"Std" is the *sample* standard deviation (``ddof=1``, dividing by n - 1 = 9). This is the
usual choice when 10 runs are treated as a sample of what the algorithm could produce.
"""

import csv

import numpy as np

from experiments.run_tsp_experiments import NEIGHBOURHOODS, PROBLEM_FOLDER
from experiments.tsp_results_io import load_all_tsp_results, select_runs
from src.bees_tsp import TSP_BEES_SETTINGS
from src.tsp_instances import TSP_INSTANCES, instance_file_path
from src.tsp_tour import compute_distance_matrix, is_valid_tour, tour_length
from src.tsplib import load_tsplib_instance

TABLES_FOLDER = PROBLEM_FOLDER / "results" / "tables"
ALL_RUNS_CSV = PROBLEM_FOLDER / "results" / "raw" / "tsp_all_runs.csv"


def verify_all_runs(results):
    """Re-check every saved run independently of the algorithm code that produced it."""
    distance_matrices = {}
    for result in results:
        name = result["instance"]
        if name not in distance_matrices:
            instance = load_tsplib_instance(instance_file_path(name))
            distance_matrices[name] = compute_distance_matrix(instance.coordinates)
        tour = np.array(result["best_tour_city_ids"]) - 1
        label = f"{name} {result['neighbourhood']} seed {result['seed']}"
        assert is_valid_tour(tour, result["cities"]), f"invalid tour: {label}"
        assert tour_length(tour, distance_matrices[name]) == result["final_best_length"], f"length mismatch: {label}"
        assert result["evaluations_used"] == TSP_BEES_SETTINGS.max_evaluations, f"wrong evaluation count: {label}"
        assert result["settings"] == TSP_BEES_SETTINGS.as_dict(), f"different settings: {label}"
    print(f"Verified {len(results)} runs: valid tours, recomputed lengths match, 30,000 evaluations each.")


def write_all_runs_csv(results):
    """Raw per-run table, one row per run, including the final tour as space-separated city ids."""
    columns = ["instance", "cities", "neighbourhood", "seed", "initial_best_length", "final_best_length",
               "optimal_length", "gap_percent", "runtime_seconds", "evaluations_used", "iterations_started"]
    with open(ALL_RUNS_CSV, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns + ["best_tour_city_ids"])
        for result in results:
            writer.writerow([result[column] for column in columns]
                            + [" ".join(str(city) for city in result["best_tour_city_ids"])])


def summarise(results):
    """One summary row per instance x neighbourhood, computed from the 10 runs (seeds)."""
    rows = []
    for instance_name, (cities, optimum) in TSP_INSTANCES.items():
        for neighbourhood in NEIGHBOURHOODS:
            runs = select_runs(results, instance_name, neighbourhood)
            final_lengths = np.array([run["final_best_length"] for run in runs], dtype=float)
            gaps = np.array([run["gap_percent"] for run in runs])
            rows.append({
                "Instance": instance_name,
                "Cities": cities,
                "Optimum": optimum,
                "Neighbourhood": neighbourhood,
                "Runs": len(runs),
                "Mean initial best": round(float(np.mean([run["initial_best_length"] for run in runs])), 1),
                "Best": int(final_lengths.min()),
                "Mean": round(float(final_lengths.mean()), 1),
                "Std": round(float(final_lengths.std(ddof=1)), 1),
                "Best gap (%)": round(float(gaps.min()), 2),
                "Mean gap (%)": round(float(gaps.mean()), 2),
                "Mean runtime (s)": round(float(np.mean([run["runtime_seconds"] for run in runs])), 3),
            })
    return rows


def write_summary(rows):
    """Save the summary as CSV (for further processing) and Markdown (easy to read / copy)."""
    TABLES_FOLDER.mkdir(parents=True, exist_ok=True)
    with open(TABLES_FOLDER / "tsp_summary.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    headers = list(rows[0])
    lines = [
        "# Part A: Bees Algorithm on TSPLIB instances (10 runs per row, 30,000 evaluations per run)",
        "",
        "Tour lengths in TSPLIB distance units (rounded EUC_2D). Gap(%) = 100 * (L_BA - L*) / L*. "
        "Std = sample standard deviation (ddof = 1). Runtime = wall-clock seconds of the search.",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[header]) for header in headers) + " |")
    (TABLES_FOLDER / "tsp_summary.md").write_text("\n".join(lines) + "\n")


def main():
    results = load_all_tsp_results()
    verify_all_runs(results)
    write_all_runs_csv(results)
    rows = summarise(results)
    write_summary(rows)
    print((TABLES_FOLDER / "tsp_summary.md").read_text())
    print(f"Saved {ALL_RUNS_CSV}\nSaved {TABLES_FOLDER / 'tsp_summary.csv'} and tsp_summary.md")


if __name__ == "__main__":
    main()
