# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Small pilot study used to CHOOSE the Bees Algorithm settings for Part A.

Why a pilot?
------------
The assignment says "Choose and record the BA settings". Rather than guessing, we compare a
few reasonable settings on a short test and pick the best one *before* running the real
experiments. To avoid tuning on the very runs we report, the pilot uses different seeds
(100-104) from the final experiments (0-9).

Every candidate setting uses the same 30,000-evaluation budget, so the comparison is fair.

Run from the problem_1 folder:
    python -m experiments.tsp_pilot_settings

Output: results/tables/tsp_pilot_settings.csv (one row per setting x instance x neighbourhood).
"""

import csv
from pathlib import Path

import numpy as np

from src.bees_algorithm import BeesSettings
from src.bees_tsp import run_bees_on_tsp
from src.tsp_instances import TSP_INSTANCES, instance_file_path
from src.tsplib import load_tsplib_instance

PILOT_SEEDS = [100, 101, 102, 103, 104]          # disjoint from the experiment seeds 0-9
PILOT_INSTANCES = ["eil51", "kroA100", "ch150"]   # small, medium and largest instance
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "results" / "tables" / "tsp_pilot_settings.csv"

# Candidate settings, from "many sites, many scouts" (more exploration)
# to "few sites, many recruits per site" (more exploitation).
CANDIDATE_SETTINGS = {
    "A_n50_m10_e3_nep40_nsp20": BeesSettings(50, 10, 3, 40, 20),
    "B_n20_m5_e2_nep50_nsp20": BeesSettings(20, 5, 2, 50, 20),
    "C_n10_m3_e1_nep100_nsp50": BeesSettings(10, 3, 1, 100, 50),
    "D_n6_m2_e1_nep100_nsp50": BeesSettings(6, 2, 1, 100, 50),
}


def main():
    rows = []
    for label, settings in CANDIDATE_SETTINGS.items():
        for instance_name in PILOT_INSTANCES:
            cities, optimum = TSP_INSTANCES[instance_name]
            instance = load_tsplib_instance(instance_file_path(instance_name), instance_name, cities)
            for neighbourhood in ["swap", "reversal"]:
                gaps = [
                    run_bees_on_tsp(instance, neighbourhood, seed, settings, optimum)["gap_percent"]
                    for seed in PILOT_SEEDS
                ]
                rows.append({
                    "setting": label,
                    "evaluations_per_iteration": settings.evaluations_per_iteration(),
                    "instance": instance_name,
                    "neighbourhood": neighbourhood,
                    "mean_gap_percent": round(float(np.mean(gaps)), 2),
                    "std_gap_percent": round(float(np.std(gaps, ddof=1)), 2),
                })
                print(f"{label:28s} {instance_name:8s} {neighbourhood:8s} mean gap {np.mean(gaps):7.2f} %")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    # Overall ranking: average of the mean gaps over all pilot instances and both moves.
    print("\nAverage mean gap per setting (lower is better):")
    for label in CANDIDATE_SETTINGS:
        average = np.mean([row["mean_gap_percent"] for row in rows if row["setting"] == label])
        print(f"  {label:28s} {average:7.2f} %")
    print(f"\nSaved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
