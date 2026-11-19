# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Run the Part A experiments: Bees Algorithm on the six TSPLIB instances.

Full assignment experiment (6 instances x 2 neighbourhoods x 10 seeds = 120 runs), from the
problem_1 folder:

    python -m experiments.run_tsp_experiments

One single run, for example berlin52 with segment reversal and seed 0:

    python -m experiments.run_tsp_experiments --instances berlin52 --neighbourhoods reversal --seeds 0

What is saved for each run
--------------------------
* ``results/raw/tsp/<instance>_<neighbourhood>_seed<seed>.json``: everything about the run
  (settings, seed, initial and final best length, gap, runtime, evaluation count, final tour,
  best-so-far history).
* ``results/convergence/tsp/<instance>_<neighbourhood>_seed<seed>.csv``: the best-so-far
  log as two columns, ``evaluation`` and ``best_so_far_length``. Only evaluations where the
  best improved are listed; the value stays the same until the next listed evaluation.

Restartable
-----------
A run whose JSON file already exists is skipped, so an interrupted experiment can be
restarted without repeating finished runs (use ``--overwrite`` to force re-running).
Each JSON file is written to a temporary name first and then renamed, so a crash can
never leave a half-written result that would be mistaken for a finished run.
"""

import argparse
import csv
import json
import os
from pathlib import Path

from src.bees_tsp import TSP_BEES_SETTINGS, TSP_SEEDS, run_bees_on_tsp
from src.tsp_instances import TSP_INSTANCES, instance_file_path
from src.tsplib import load_tsplib_instance

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent
RAW_FOLDER = PROBLEM_FOLDER / "results" / "raw" / "tsp"
CONVERGENCE_FOLDER = PROBLEM_FOLDER / "results" / "convergence" / "tsp"
NEIGHBOURHOODS = ["swap", "reversal"]


def run_file_stem(instance_name, neighbourhood, seed):
    """File name (without extension) shared by a run's JSON result and convergence CSV."""
    return f"{instance_name}_{neighbourhood}_seed{seed}"


def save_convergence_csv(result, path):
    """Write the best-so-far change points as a small CSV file."""
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["evaluation", "best_so_far_length"])
        writer.writerows(result["best_so_far_history"])


def save_json_safely(data, path):
    """Write JSON to a temporary file, then rename it; renaming is atomic on one disk."""
    temporary_path = path.with_suffix(".json.tmp")
    with open(temporary_path, "w") as handle:
        json.dump(data, handle, indent=1)
    os.replace(temporary_path, path)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Bees Algorithm TSP experiments (Part A).")
    parser.add_argument("--instances", nargs="+", default=list(TSP_INSTANCES),
                        choices=list(TSP_INSTANCES), help="instances to run (default: all six)")
    parser.add_argument("--neighbourhoods", nargs="+", default=NEIGHBOURHOODS,
                        choices=NEIGHBOURHOODS, help="neighbourhood versions (default: both)")
    parser.add_argument("--seeds", nargs="+", type=int, default=TSP_SEEDS,
                        help="random seeds (default: 0 1 ... 9)")
    parser.add_argument("--overwrite", action="store_true",
                        help="re-run and overwrite runs that already have results")
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    RAW_FOLDER.mkdir(parents=True, exist_ok=True)
    CONVERGENCE_FOLDER.mkdir(parents=True, exist_ok=True)

    print(f"BA settings: {TSP_BEES_SETTINGS.as_dict()}")
    total_runs = len(arguments.instances) * len(arguments.neighbourhoods) * len(arguments.seeds)
    run_counter = 0

    for instance_name in arguments.instances:
        cities, optimum = TSP_INSTANCES[instance_name]
        # Load and validate once per instance (not once per run).
        instance = load_tsplib_instance(instance_file_path(instance_name), instance_name, cities)

        for neighbourhood in arguments.neighbourhoods:
            for seed in arguments.seeds:
                run_counter += 1
                stem = run_file_stem(instance_name, neighbourhood, seed)
                json_path = RAW_FOLDER / f"{stem}.json"
                if json_path.exists() and not arguments.overwrite:
                    print(f"[{run_counter}/{total_runs}] {stem}: already done, skipped")
                    continue

                result = run_bees_on_tsp(instance, neighbourhood, seed, TSP_BEES_SETTINGS, optimum)

                # Convergence CSV first, JSON last: the JSON file marks the run as finished.
                save_convergence_csv(result, CONVERGENCE_FOLDER / f"{stem}.csv")
                save_json_safely(result, json_path)
                print(
                    f"[{run_counter}/{total_runs}] {stem}: length {result['final_best_length']} "
                    f"(gap {result['gap_percent']:.2f} %), {result['runtime_seconds']:.2f} s"
                )


if __name__ == "__main__":
    main()
