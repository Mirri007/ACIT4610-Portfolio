# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""Reading saved Problem 2 runs back from disk (shared by the table and plot scripts)."""

import json

from experiments.run_es_experiments import RAW_FOLDER, run_file_stem
from src.portfolio_data import load_all_cases
from src.run_es import FINAL_SEEDS, VARIANTS


def load_all_es_results():
    """
    Load all 450 runs (15 cases x 3 variants x 10 seeds) in a fixed order.
    Raises FileNotFoundError if any run is missing, so incomplete results are never summarised.
    """
    results, missing = [], []
    for case in load_all_cases():
        for variant in VARIANTS:
            for seed in FINAL_SEEDS:
                path = RAW_FOLDER / f"{run_file_stem(case.name, variant, seed)}.json"
                if not path.exists():
                    missing.append(path.name)
                    continue
                with open(path) as handle:
                    results.append(json.load(handle))
    if missing:
        raise FileNotFoundError(f"{len(missing)} run(s) missing, e.g. {missing[:3]}. "
                                "Run experiments.run_es_experiments first.")
    return results


def select_runs(results, case_name, variant):
    """The 10 runs (one per seed) of one variant on one case."""
    return [r for r in results if r["case"] == case_name and r["variant"] == variant]
