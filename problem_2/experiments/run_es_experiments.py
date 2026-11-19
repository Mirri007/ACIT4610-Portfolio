# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Run the Problem 2 experiments: three ES variants on the 15 portfolio test cases.

Full assignment experiment (15 cases x 3 variants x 10 seeds = 450 runs), from the problem_2 folder:

    python -m experiments.run_es_experiments

One single test case, e.g. port1 with alpha = 0.50, (1+1)-ES, seed 0:

    python -m experiments.run_es_experiments --cases port1_alpha050 --variants one_plus_one --seeds 0

Single-threaded linear algebra (why the first lines below exist)
----------------------------------------------------------------
NumPy uses a linear-algebra library (OpenBLAS) that may split each matrix-vector product over
several CPU threads. For matrices this small (at most 225 x 225) the coordination costs more
than it saves: in a preliminary measurement (seeds 900-904) port5 runs were about twice as slow
and their runtimes varied erratically between repetitions, while results were bit-for-bit
identical either way. Because runtime is a reported metric and the variants are compared on it,
the experiments run single-threaded. These variables must be set BEFORE NumPy is imported.

What is saved for each run
--------------------------
* ``results/raw/es/<case>_<variant>_seed<seed>.json``: everything recorded by ``run_es_on_case``
  (settings, target return, best valid weights, their return and variance, feasibility, runtime,
  evaluation count, archive history and variant-specific details such as step sizes).
* ``results/convergence/es/<case>_<variant>_seed<seed>.csv``: archive best-so-far log with columns
  ``evaluation`` and ``archive_best_variance`` (one row per improvement).
Finished runs are skipped on restart (``--overwrite`` re-runs them).
"""

import os

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[variable] = "1"

import argparse  # noqa: E402  (imports after setting the thread variables on purpose)
import csv  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

from src.portfolio_data import load_all_cases  # noqa: E402
from src.run_es import FINAL_SEEDS, VARIANTS, run_es_on_case  # noqa: E402

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent
RAW_FOLDER = PROBLEM_FOLDER / "results" / "raw" / "es"
CONVERGENCE_FOLDER = PROBLEM_FOLDER / "results" / "convergence" / "es"


def run_file_stem(case_name, variant, seed):
    return f"{case_name}_{variant}_seed{seed}"


def save_json_safely(data, path):
    """Write to a temporary file, then rename: a crash can never leave a half-written result."""
    temporary_path = path.with_suffix(".json.tmp")
    with open(temporary_path, "w") as handle:
        json.dump(data, handle, indent=1)
    os.replace(temporary_path, path)


def save_convergence_csv(result, path):
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["evaluation", "archive_best_variance"])
        for evaluation, value in result["archive_history"]:
            writer.writerow([evaluation, repr(value)])     # repr keeps every digit


def parse_arguments():
    all_case_names = [case.name for case in load_all_cases()]
    parser = argparse.ArgumentParser(description="Run ES portfolio experiments (Problem 2).")
    parser.add_argument("--cases", nargs="+", default=all_case_names, choices=all_case_names)
    parser.add_argument("--variants", nargs="+", default=list(VARIANTS), choices=list(VARIANTS))
    parser.add_argument("--seeds", nargs="+", type=int, default=FINAL_SEEDS)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    RAW_FOLDER.mkdir(parents=True, exist_ok=True)
    CONVERGENCE_FOLDER.mkdir(parents=True, exist_ok=True)
    cases = [case for case in load_all_cases() if case.name in arguments.cases]
    total_runs = len(cases) * len(arguments.variants) * len(arguments.seeds)
    run_counter = 0
    for case in cases:
        for variant in arguments.variants:
            for seed in arguments.seeds:
                run_counter += 1
                stem = run_file_stem(case.name, variant, seed)
                json_path = RAW_FOLDER / f"{stem}.json"
                if json_path.exists() and not arguments.overwrite:
                    print(f"[{run_counter}/{total_runs}] {stem}: already done, skipped")
                    continue
                result = run_es_on_case(case, variant, seed)
                save_convergence_csv(result, CONVERGENCE_FOLDER / f"{stem}.csv")
                save_json_safely(result, json_path)    # written last: marks the run as finished
                print(f"[{run_counter}/{total_runs}] {stem}: variance {result['final_variance']:.6e} "
                      f"feasible {result['feasible']} {result['runtime_seconds']:.2f} s", flush=True)


if __name__ == "__main__":
    main()
