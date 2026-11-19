# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Pilot study used to CHOOSE the Bees Algorithm settings for Part B (continuous functions).

Design (fixed BEFORE the pilot was run, to keep the choice independent of the experiments)
-----------------------------------------------------------------------------------------
* Candidates: the same four settings A-D as in the Part A pilot (imported, so they are identical).
* Dimension D = 20. The experiments use D = 10 and D = 30, so the pilot uses no experiment case.
  (All four functions are required by the assignment, so the functions themselves cannot be
  avoided; using a different dimension is the closest equivalent to "different instances".)
* Seeds 100-104 (experiment seeds are 0-9).
* 30,000 evaluations per run, as in the experiments.

Selection rule (decided before running)
---------------------------------------
For each function, rank the four settings by their mean final objective value over the 5 seeds
(1 = lowest). The chosen setting has the lowest AVERAGE RANK over the four functions.
Ranks are used because the functions have completely different scales (Rosenbrock values are
thousands, Ackley values below 22), so averaging raw values would let one function dominate.
Ties in average rank are broken by the number of functions on which a setting ranks first, then
by the alphabetical label (deterministic).

Run from the problem_1 folder:
    python -m experiments.continuous_pilot_settings

Outputs:
    results/tables/continuous_pilot_settings.csv  (one row per setting x function)
    results/tables/continuous_pilot_settings.md   (ranks and the chosen setting)
"""

import csv
from pathlib import Path

import numpy as np

from experiments.tsp_pilot_settings import CANDIDATE_SETTINGS
from src.bees_continuous import run_bees_on_function
from src.benchmark_functions import BENCHMARK_FUNCTIONS

PILOT_DIMENSION = 20
PILOT_SEEDS = [100, 101, 102, 103, 104]
TABLES_FOLDER = Path(__file__).resolve().parent.parent / "results" / "tables"


def main():
    rows = []
    for label, settings in CANDIDATE_SETTINGS.items():
        for function_name in BENCHMARK_FUNCTIONS:
            values = [run_bees_on_function(function_name, PILOT_DIMENSION, seed, settings)["final_best_value"]
                      for seed in PILOT_SEEDS]
            rows.append({
                "setting": label,
                "function": function_name,
                "dimension": PILOT_DIMENSION,
                "mean_final_value": float(np.mean(values)),
                "std_final_value": float(np.std(values, ddof=1)),
            })
            print(f"{label:28s} {function_name:10s} mean {np.mean(values):14.6f} ± {np.std(values, ddof=1):.6f}")

    # Rank the settings within each function (1 = lowest mean final value).
    ranks = {label: [] for label in CANDIDATE_SETTINGS}
    for function_name in BENCHMARK_FUNCTIONS:
        ordered = sorted((row for row in rows if row["function"] == function_name),
                         key=lambda row: row["mean_final_value"])
        for rank, row in enumerate(ordered, start=1):
            row["rank"] = rank
            ranks[row["setting"]].append(rank)

    average_rank = {label: float(np.mean(values)) for label, values in ranks.items()}
    first_places = {label: values.count(1) for label, values in ranks.items()}
    chosen = min(CANDIDATE_SETTINGS, key=lambda label: (average_rank[label], -first_places[label], label))

    TABLES_FOLDER.mkdir(parents=True, exist_ok=True)
    with open(TABLES_FOLDER / "continuous_pilot_settings.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        f"# Part B settings pilot (D = {PILOT_DIMENSION}, seeds {PILOT_SEEDS[0]}-{PILOT_SEEDS[-1]}, 30,000 evaluations per run)",
        "",
        "Mean final objective value over 5 seeds (rank within the function in brackets, 1 = best).",
        "",
        "| Setting | " + " | ".join(BENCHMARK_FUNCTIONS) + " | Average rank | First places |",
        "|---|" + "---|" * len(BENCHMARK_FUNCTIONS) + "---|---|",
    ]
    for label in CANDIDATE_SETTINGS:
        cells = []
        for function_name in BENCHMARK_FUNCTIONS:
            row = next(r for r in rows if r["setting"] == label and r["function"] == function_name)
            cells.append(f"{row['mean_final_value']:.4g} ({row['rank']})")
        lines.append(f"| {label} | " + " | ".join(cells) + f" | {average_rank[label]:.2f} | {first_places[label]} |")
    lines += ["", f"Chosen by the pre-defined rule: **{chosen}**"]
    text = "\n".join(lines) + "\n"
    (TABLES_FOLDER / "continuous_pilot_settings.md").write_text(text)
    print("\n" + text)


if __name__ == "__main__":
    main()
