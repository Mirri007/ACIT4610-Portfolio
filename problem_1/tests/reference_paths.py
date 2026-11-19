# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Location of the published TSPLIB optimal tours.

These files are kept inside tests/ on purpose: they are used ONLY to check that our distance
and tour-length calculations reproduce the published optimal lengths. No code in src/ or
experiments/ reads them, so they cannot initialise or guide the Bees Algorithm.

Source: https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/<name>.opt.tour.gz
"""

from pathlib import Path

REFERENCE_TOURS_FOLDER = Path(__file__).resolve().parent / "reference_optimal_tours"
