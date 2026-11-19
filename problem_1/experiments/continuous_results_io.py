# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Reading saved Part B run results back from disk (shared by the table and plot scripts).

All tables and figures are calculated from these saved files, never typed in by hand.
"""

import json

from experiments.run_continuous_experiments import RAW_FOLDER, run_file_stem
from src.bees_continuous import CONTINUOUS_DIMENSIONS, CONTINUOUS_SEEDS
from src.benchmark_functions import BENCHMARK_FUNCTIONS


def load_all_continuous_results():
    """
    Load all 80 saved runs (4 functions x 2 dimensions x 10 seeds), in a fixed order.

    Raises FileNotFoundError if any run is missing, so incomplete results are never summarised.
    """
    results = []
    missing = []
    for function_name in BENCHMARK_FUNCTIONS:
        for dimension in CONTINUOUS_DIMENSIONS:
            for seed in CONTINUOUS_SEEDS:
                path = RAW_FOLDER / f"{run_file_stem(function_name, dimension, seed)}.json"
                if not path.exists():
                    missing.append(path.name)
                    continue
                with open(path) as handle:
                    results.append(json.load(handle))
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} run(s) missing, e.g. {missing[:3]}. Run experiments.run_continuous_experiments first."
        )
    return results


def select_runs(results, function_name, dimension):
    """The 10 runs (one per seed) for one function and one dimension."""
    return [r for r in results if r["function"] == function_name and r["dimension"] == dimension]
