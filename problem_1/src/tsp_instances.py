# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
The six TSPLIB instances required by the assignment, with their published optimal tour lengths.

The optimal lengths (L*) are copied from the assignment table, which cites TSPLIB's list of
optimal solutions for symmetric TSPs. They are used ONLY to:
  * compute the percentage gap of the final result, and
  * draw the "optimum" reference line in convergence plots.
They are never given to the Bees Algorithm, so they cannot guide the search.
"""

from pathlib import Path

# Folder that holds the original, unmodified .tsp.gz downloads.
TSPLIB_DATA_FOLDER = Path(__file__).resolve().parent.parent / "data" / "tsplib_original"

# Official download location (Heidelberg University TSPLIB95 page).
TSPLIB_BASE_URL = "https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/"

# name -> (number of cities, optimal tour length L*), in the order of the assignment table.
TSP_INSTANCES = {
    "eil51": (51, 426),
    "berlin52": (52, 7542),
    "st70": (70, 675),
    "eil76": (76, 538),
    "kroA100": (100, 21282),
    "ch150": (150, 6528),
}


def instance_file_path(instance_name):
    """Return the path of the original compressed file for one instance, e.g. data/.../eil51.tsp.gz."""
    return TSPLIB_DATA_FOLDER / f"{instance_name}.tsp.gz"


def instance_source_url(instance_name):
    """Return the official download URL for one instance (documented in the README)."""
    return f"{TSPLIB_BASE_URL}{instance_name}.tsp.gz"
