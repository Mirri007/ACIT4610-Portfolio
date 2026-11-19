# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Parameter ROBUSTNESS check for Part A, performed AFTER the settings were chosen and the 120
experiment runs were finished.

Why this exists
---------------
The original settings pilot (experiments/tsp_pilot_settings.py) used separate seeds (100-104),
but three of the six assignment instances (eil51, kroA100, ch150). So the chosen setting D was
independent of the evaluation *seeds* but not of the evaluation *instances*. This script checks
whether D is still competitive on three TSPLIB instances that are NOT in the assignment set.

It is a check only. It does NOT change the settings used for the 120 runs, and it was run
after them (see docs/implementation_notes.md for the exact order of events).

What is kept identical to the original pilot
--------------------------------------------
* The same four candidate settings A-D (imported from tsp_pilot_settings.py, so they cannot differ).
* Both neighbourhoods, 30,000 evaluations per run, 5 seeds per combination.

What is different
-----------------
* Instances: pr76 (76 cities), rat99 (99) and ch130 (130), similar sizes to the assignment set.
* Seeds: 200-204, which differ from the experiment seeds (0-9) and the original pilot seeds (100-104).

Two ways of comparing the settings are reported:
1. Average mean gap (as in the original pilot). This uses the optimal lengths to put instances
   of different scale on a common percentage scale.
2. Average rank (1 = best) in each instance x neighbourhood combination. Within one instance,
   ranking by gap is the same as ranking by raw tour length, so this needs no optimal lengths.

Run from the problem_1 folder:
    python -m experiments.tsp_robustness_pilot

Outputs:
    results/tables/tsp_robustness_pilot.csv  (one row per setting x instance x neighbourhood)
    results/tables/tsp_robustness_pilot.md   (both comparisons, as tables)
"""

import csv
from pathlib import Path

import numpy as np

from experiments.tsp_pilot_settings import CANDIDATE_SETTINGS
from src.bees_tsp import run_bees_on_tsp
from src.tsp_instances import ROBUSTNESS_PILOT_INSTANCES, robustness_instance_file_path
from src.tsplib import load_tsplib_instance

ROBUSTNESS_SEEDS = [200, 201, 202, 203, 204]
NEIGHBOURHOODS = ["swap", "reversal"]
TABLES_FOLDER = Path(__file__).resolve().parent.parent / "results" / "tables"


def run_all_combinations():
    """Run every setting x instance x neighbourhood x seed; return one summary row per combination."""
    rows = []
    for label, settings in CANDIDATE_SETTINGS.items():
        for instance_name, (cities, optimum) in ROBUSTNESS_PILOT_INSTANCES.items():
            instance = load_tsplib_instance(robustness_instance_file_path(instance_name), instance_name, cities)
            for neighbourhood in NEIGHBOURHOODS:
                runs = [run_bees_on_tsp(instance, neighbourhood, seed, settings, optimum) for seed in ROBUSTNESS_SEEDS]
                gaps = [run["gap_percent"] for run in runs]
                lengths = [run["final_best_length"] for run in runs]
                rows.append({
                    "setting": label,
                    "instance": instance_name,
                    "neighbourhood": neighbourhood,
                    "mean_length": round(float(np.mean(lengths)), 1),
                    "mean_gap_percent": round(float(np.mean(gaps)), 2),
                    "std_gap_percent": round(float(np.std(gaps, ddof=1)), 2),
                })
                print(f"{label:28s} {instance_name:6s} {neighbourhood:8s} mean gap {np.mean(gaps):7.2f} %")
    return rows


def average_mean_gap(rows, setting, neighbourhood=None):
    """Average of the mean gaps of one setting, optionally for one neighbourhood only."""
    values = [row["mean_gap_percent"] for row in rows
              if row["setting"] == setting and (neighbourhood is None or row["neighbourhood"] == neighbourhood)]
    return float(np.mean(values))


def average_ranks(rows):
    """
    Rank the four settings within every instance x neighbourhood combination (1 = shortest mean
    tour) and average the ranks per setting. Ranking is done on mean tour length, so no optimal
    length is involved.
    """
    ranks = {setting: [] for setting in CANDIDATE_SETTINGS}
    for instance_name in ROBUSTNESS_PILOT_INSTANCES:
        for neighbourhood in NEIGHBOURHOODS:
            combination = [row for row in rows if row["instance"] == instance_name and row["neighbourhood"] == neighbourhood]
            combination.sort(key=lambda row: row["mean_length"])
            for rank, row in enumerate(combination, start=1):
                ranks[row["setting"]].append(rank)
    return {setting: float(np.mean(values)) for setting, values in ranks.items()}


def write_outputs(rows):
    TABLES_FOLDER.mkdir(parents=True, exist_ok=True)
    with open(TABLES_FOLDER / "tsp_robustness_pilot.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    ranks = average_ranks(rows)
    lines = [
        "# Part A: parameter robustness check on non-assignment instances",
        "",
        "Performed after the settings were chosen and the 120 runs were finished; it did not change the settings.",
        f"Instances: {', '.join(ROBUSTNESS_PILOT_INSTANCES)}. Seeds: {ROBUSTNESS_SEEDS[0]}-{ROBUSTNESS_SEEDS[-1]}. "
        "30,000 evaluations per run.",
        "",
        "| Setting | Avg mean gap, swap (%) | Avg mean gap, reversal (%) | Avg mean gap, both (%) | Avg rank (1 = best) |",
        "|---|---|---|---|---|",
    ]
    for setting in CANDIDATE_SETTINGS:
        lines.append(
            f"| {setting} | {average_mean_gap(rows, setting, 'swap'):.2f} | {average_mean_gap(rows, setting, 'reversal'):.2f} "
            f"| {average_mean_gap(rows, setting):.2f} | {ranks[setting]:.2f} |"
        )
    lines += ["", "Per instance and neighbourhood (mean gap % ± sample std over 5 seeds):", "",
              "| Instance | Neighbourhood | " + " | ".join(CANDIDATE_SETTINGS) + " |",
              "|---|---|" + "---|" * len(CANDIDATE_SETTINGS)]
    for instance_name in ROBUSTNESS_PILOT_INSTANCES:
        for neighbourhood in NEIGHBOURHOODS:
            cells = []
            for setting in CANDIDATE_SETTINGS:
                row = next(r for r in rows if r["setting"] == setting and r["instance"] == instance_name
                           and r["neighbourhood"] == neighbourhood)
                cells.append(f"{row['mean_gap_percent']:.2f} ± {row['std_gap_percent']:.2f}")
            lines.append(f"| {instance_name} | {neighbourhood} | " + " | ".join(cells) + " |")
    text = "\n".join(lines) + "\n"
    (TABLES_FOLDER / "tsp_robustness_pilot.md").write_text(text)
    print("\n" + text)


def main():
    rows = run_all_combinations()
    write_outputs(rows)


if __name__ == "__main__":
    main()
