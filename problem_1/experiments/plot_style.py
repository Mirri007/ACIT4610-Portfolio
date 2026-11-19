# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Shared colours and Matplotlib style for all Problem 1 figures, so every figure looks consistent.

Colours come from a palette validated for colour-vision deficiency (the two series colours stay
distinguishable for colour-blind readers). The same neighbourhood always gets the same colour
in every figure.
"""

import matplotlib

matplotlib.use("Agg")  # draw to files without needing a screen (works on any computer/server)
import matplotlib.pyplot as plt  # noqa: E402  (must be imported after choosing the backend)

TEXT_COLOUR = "#0b0b0b"
SECONDARY_TEXT_COLOUR = "#52514e"
GRID_COLOUR = "#e4e3df"
REFERENCE_LINE_COLOUR = "#52514e"   # neutral grey for the optimum / reference lines

# Fixed colour per neighbourhood version (blue = swap, orange = reversal).
NEIGHBOURHOOD_COLOURS = {"swap": "#2a78d6", "reversal": "#eb6834"}
NEIGHBOURHOOD_LABELS = {"swap": "Swap", "reversal": "Segment reversal"}


def apply_style():
    """Set readable, uncluttered defaults: light grid, no top/right frame, clear font sizes."""
    plt.rcParams.update({
        "figure.dpi": 100,
        "savefig.dpi": 200,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "axes.edgecolor": SECONDARY_TEXT_COLOUR,
        "axes.labelcolor": TEXT_COLOUR,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID_COLOUR,
        "grid.linewidth": 0.8,
        "xtick.color": SECONDARY_TEXT_COLOUR,
        "ytick.color": SECONDARY_TEXT_COLOUR,
        "text.color": TEXT_COLOUR,
        "legend.frameon": False,
        "lines.linewidth": 2,
    })
