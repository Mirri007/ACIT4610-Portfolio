# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Reading saved TSP run results back from disk (shared by the table and plot scripts).

All tables and figures are calculated from these saved files, never typed in by hand.
"""

import json

from experiments.run_tsp_experiments import NEIGHBOURHOODS, RAW_FOLDER
from src.bees_tsp import TSP_SEEDS
from src.tsp_instances import TSP_INSTANCES


def load_all_tsp_results():
    """
    Load every saved run and check that the full experiment is complete.

    Returns
    -------
    list of dict
        One dictionary per run (the content of each JSON file), sorted by instance order of
        the assignment table, then neighbourhood, then seed.

    Raises
    ------
    FileNotFoundError
        If any of the 120 required runs is missing, so incomplete results can never be
        summarised by accident.
    """
    results = []
    missing = []
    for instance_name in TSP_INSTANCES:
        for neighbourhood in NEIGHBOURHOODS:
            for seed in TSP_SEEDS:
                path = RAW_FOLDER / f"{instance_name}_{neighbourhood}_seed{seed}.json"
                if not path.exists():
                    missing.append(path.name)
                    continue
                with open(path) as handle:
                    results.append(json.load(handle))
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} run(s) missing, e.g. {missing[:3]}. Run experiments.run_tsp_experiments first."
        )
    return results


def select_runs(results, instance_name, neighbourhood):
    """Return the runs for one instance and one neighbourhood version (10 runs, one per seed)."""
    return [r for r in results if r["instance"] == instance_name and r["neighbourhood"] == neighbourhood]
