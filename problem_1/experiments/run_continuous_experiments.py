# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Run the Part B experiments: Bees Algorithm on the four benchmark functions.

Full assignment experiment (4 functions x 2 dimensions x 10 seeds = 80 runs), from the
problem_1 folder:

    python -m experiments.run_continuous_experiments

One single run, for example Rastrigin in 10 dimensions with seed 0:

    python -m experiments.run_continuous_experiments --functions rastrigin --dimensions 10 --seeds 0

What is saved for each run
--------------------------
* ``results/raw/continuous/<function>_D<dimension>_seed<seed>.json``: settings, seed, bounds,
  initial and final best value, final best vector, runtime, evaluation count, best-so-far history.
* ``results/convergence/continuous/<function>_D<dimension>_seed<seed>.csv``: best-so-far log with
  columns ``evaluation`` and ``best_so_far_value`` (one row per improvement; the value stays the
  same until the next row).

Like the TSP experiment, finished runs are skipped on restart (``--overwrite`` re-runs them),
and each JSON file is written under a temporary name and then renamed.
"""

import argparse
import csv
from pathlib import Path

from experiments.run_tsp_experiments import save_json_safely
from src.bees_continuous import CONTINUOUS_BEES_SETTINGS, CONTINUOUS_DIMENSIONS, CONTINUOUS_SEEDS, run_bees_on_function
from src.benchmark_functions import BENCHMARK_FUNCTIONS

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent
RAW_FOLDER = PROBLEM_FOLDER / "results" / "raw" / "continuous"
CONVERGENCE_FOLDER = PROBLEM_FOLDER / "results" / "convergence" / "continuous"


def run_file_stem(function_name, dimension, seed):
    """File name (without extension) shared by a run's JSON result and convergence CSV."""
    return f"{function_name}_D{dimension}_seed{seed}"


def save_convergence_csv(result, path):
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["evaluation", "best_so_far_value"])
        # repr() keeps every digit of the float, so the log is exact.
        for evaluation, value in result["best_so_far_history"]:
            writer.writerow([evaluation, repr(value)])


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Bees Algorithm continuous experiments (Part B).")
    parser.add_argument("--functions", nargs="+", default=list(BENCHMARK_FUNCTIONS),
                        choices=list(BENCHMARK_FUNCTIONS), help="functions to run (default: all four)")
    parser.add_argument("--dimensions", nargs="+", type=int, default=CONTINUOUS_DIMENSIONS,
                        help="dimensions D (default: 10 30)")
    parser.add_argument("--seeds", nargs="+", type=int, default=CONTINUOUS_SEEDS,
                        help="random seeds (default: 0 1 ... 9)")
    parser.add_argument("--overwrite", action="store_true", help="re-run runs that already have results")
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    RAW_FOLDER.mkdir(parents=True, exist_ok=True)
    CONVERGENCE_FOLDER.mkdir(parents=True, exist_ok=True)

    print(f"BA settings: {CONTINUOUS_BEES_SETTINGS.as_dict()}")
    total_runs = len(arguments.functions) * len(arguments.dimensions) * len(arguments.seeds)
    run_counter = 0
    for function_name in arguments.functions:
        for dimension in arguments.dimensions:
            for seed in arguments.seeds:
                run_counter += 1
                stem = run_file_stem(function_name, dimension, seed)
                json_path = RAW_FOLDER / f"{stem}.json"
                if json_path.exists() and not arguments.overwrite:
                    print(f"[{run_counter}/{total_runs}] {stem}: already done, skipped")
                    continue
                result = run_bees_on_function(function_name, dimension, seed, CONTINUOUS_BEES_SETTINGS)
                save_convergence_csv(result, CONVERGENCE_FOLDER / f"{stem}.csv")
                save_json_safely(result, json_path)   # written last: marks the run as finished
                print(f"[{run_counter}/{total_runs}] {stem}: best {result['final_best_value']:.6g} "
                      f"(initial {result['initial_best_value']:.6g}), {result['runtime_seconds']:.2f} s")


if __name__ == "__main__":
    main()
