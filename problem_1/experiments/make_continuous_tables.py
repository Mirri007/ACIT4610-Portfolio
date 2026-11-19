# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Build the Part B tables from the saved run results.

Run from the problem_1 folder (after run_continuous_experiments):

    python -m experiments.make_continuous_tables

Outputs
-------
* ``results/raw/continuous_all_runs.csv``: one row per run (80 runs), including the final vector.
* ``results/tables/continuous_summary.csv`` and ``continuous_summary.md``: the required summary,
  one row per function and dimension (8 cases): best, mean and standard deviation of the final
  objective values and mean runtime. Extra columns for the discussion: mean initial best value
  (improvement from the initial population) and median.

Before summarising, every run is checked again: the saved vector has the right length, lies
inside the bounds, re-evaluates to exactly the saved value, and the run used 30,000 evaluations.

Because every function's global minimum is 0, each final value is also the run's error.
"Std" is the sample standard deviation (ddof = 1, dividing by 10 - 1 = 9).
"""

import csv

import numpy as np

from experiments.continuous_results_io import load_all_continuous_results, select_runs
from experiments.run_continuous_experiments import PROBLEM_FOLDER
from src.bees_continuous import CONTINUOUS_BEES_SETTINGS, CONTINUOUS_DIMENSIONS
from src.benchmark_functions import BENCHMARK_FUNCTIONS

TABLES_FOLDER = PROBLEM_FOLDER / "results" / "tables"
ALL_RUNS_CSV = PROBLEM_FOLDER / "results" / "raw" / "continuous_all_runs.csv"


def verify_all_runs(results):
    """Re-check every saved run independently of the run that produced it."""
    for result in results:
        function, lower, upper = BENCHMARK_FUNCTIONS[result["function"]]
        vector = np.array(result["best_vector"])
        label = f"{result['function']} D={result['dimension']} seed {result['seed']}"
        assert vector.shape == (result["dimension"],), f"wrong vector length: {label}"
        assert np.all(vector >= lower) and np.all(vector <= upper), f"vector outside bounds: {label}"
        assert function(vector) == result["final_best_value"], f"value does not match vector: {label}"
        assert result["evaluations_used"] == CONTINUOUS_BEES_SETTINGS.max_evaluations, f"wrong evaluation count: {label}"
        assert result["settings"] == CONTINUOUS_BEES_SETTINGS.as_dict(), f"different settings: {label}"
    print(f"Verified {len(results)} runs: vectors in bounds, values reproduce exactly, 30,000 evaluations each.")


def write_all_runs_csv(results):
    columns = ["function", "dimension", "seed", "lower_bound", "upper_bound", "initial_best_value",
               "final_best_value", "runtime_seconds", "evaluations_used", "iterations_started"]
    with open(ALL_RUNS_CSV, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns + ["best_vector"])
        for result in results:
            writer.writerow([result[column] for column in columns]
                            + [" ".join(repr(value) for value in result["best_vector"])])


def summarise(results):
    rows = []
    for function_name in BENCHMARK_FUNCTIONS:
        for dimension in CONTINUOUS_DIMENSIONS:
            runs = select_runs(results, function_name, dimension)
            finals = np.array([run["final_best_value"] for run in runs])
            rows.append({
                "Function": function_name,
                "D": dimension,
                "Runs": len(runs),
                "Mean initial best": float(np.mean([run["initial_best_value"] for run in runs])),
                "Best": float(finals.min()),
                "Mean": float(finals.mean()),
                "Std": float(finals.std(ddof=1)),
                "Median": float(np.median(finals)),
                "Mean runtime (s)": float(np.mean([run["runtime_seconds"] for run in runs])),
            })
    return rows


def write_summary(rows):
    TABLES_FOLDER.mkdir(parents=True, exist_ok=True)
    # CSV keeps full precision; Markdown shows 4 significant digits for readability.
    with open(TABLES_FOLDER / "continuous_summary.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    headers = list(rows[0])
    lines = [
        "# Part B: Bees Algorithm on benchmark functions (10 runs per row, 30,000 evaluations per run)",
        "",
        "Values are final best objective values f(x); the global minimum of every function is 0, so these are "
        "the objective errors. Std = sample standard deviation (ddof = 1). Runtime = wall-clock seconds of the search.",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        cells = []
        for header in headers:
            value = row[header]
            if header == "Mean runtime (s)":
                cells.append(f"{value:.3f}")
            elif isinstance(value, float):
                cells.append(f"{value:.4g}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    (TABLES_FOLDER / "continuous_summary.md").write_text("\n".join(lines) + "\n")


def main():
    results = load_all_continuous_results()
    verify_all_runs(results)
    write_all_runs_csv(results)
    rows = summarise(results)
    write_summary(rows)
    print((TABLES_FOLDER / "continuous_summary.md").read_text())


if __name__ == "__main__":
    main()
