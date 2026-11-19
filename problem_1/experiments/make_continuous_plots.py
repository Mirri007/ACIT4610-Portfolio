# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Create the Part B figures from the saved run results.

Run from the problem_1 folder (after run_continuous_experiments):

    python -m experiments.make_continuous_plots

Figures (saved in results/figures/)
-----------------------------------
* ``continuous_convergence_rastrigin_D10.png``
  Required convergence plot: objective evaluations (x) against the MEAN best-so-far objective
  value over the 10 runs (y), Rastrigin at D = 10 only. The y-axis uses a LOGARITHMIC scale
  (base 10), labelled on the axis as the assignment requires ("Label any axis transformation"),
  because values fall from about 130 to about 30 and the early drop would otherwise hide the
  later progress. A light band shows the minimum-maximum range over the 10 runs.
* ``continuous_boxplots_D30.png``
  Required final-result plot: boxplots of the 10 final objective values for the four functions at
  D = 30, as four panels in one figure. Each panel has its own y-axis because the functions have
  very different scales (Ackley around 10, Rosenbrock in the thousands). The individual runs are
  shown as dots on top of each box.

How to read a boxplot: the box spans the middle 50 % of the runs (first to third quartile), the
line inside is the median, the whiskers reach the most extreme runs within 1.5 box-lengths of the
box, and any run further out would be drawn as a separate outlier marker.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter

from experiments.continuous_results_io import load_all_continuous_results, select_runs
from experiments.plot_style import SECONDARY_TEXT_COLOUR, apply_style
from experiments.run_continuous_experiments import PROBLEM_FOLDER
from src.bees_continuous import CONTINUOUS_BEES_SETTINGS
from src.benchmark_functions import BENCHMARK_FUNCTIONS
from src.evaluation_tracker import expand_history_to_every_evaluation

FIGURES_FOLDER = PROBLEM_FOLDER / "results" / "figures"
SERIES_COLOUR = "#2a78d6"   # first colour of the validated palette (one series per plot)
FUNCTION_TITLES = {"sphere": "Sphere", "rosenbrock": "Rosenbrock", "rastrigin": "Rastrigin", "ackley": "Ackley"}


def plot_rastrigin_convergence(results, dimension=10):
    runs = select_runs(results, "rastrigin", dimension)
    budget = CONTINUOUS_BEES_SETTINGS.max_evaluations
    evaluations = np.arange(1, budget + 1)
    # One row per run, one column per evaluation number; then average over runs (rows).
    curves = np.array([expand_history_to_every_evaluation(run["best_so_far_history"], budget) for run in runs])
    mean_curve = curves.mean(axis=0)

    figure, axes = plt.subplots(figsize=(7.5, 4.5))
    axes.fill_between(evaluations, curves.min(axis=0), curves.max(axis=0), color=SERIES_COLOUR, alpha=0.15,
                      linewidth=0, label=f"Min-max over {len(runs)} runs")
    axes.plot(evaluations, mean_curve, color=SERIES_COLOUR,
              label=f"Mean of {len(runs)} runs (final mean {mean_curve[-1]:.2f})")
    axes.set_yscale("log")
    # A log axis spanning less than one power of ten shows almost no default labels, so we place
    # readable tick values ourselves (spaced logarithmically, written as plain numbers).
    tick_values = [value for value in (10, 15, 20, 30, 40, 50, 70, 100, 150, 200, 300)
                   if curves.min() * 0.8 <= value <= curves.max() * 1.2]
    axes.yaxis.set_major_locator(FixedLocator(tick_values))
    axes.yaxis.set_major_formatter(FixedFormatter([str(value) for value in tick_values]))
    axes.yaxis.set_minor_formatter(NullFormatter())
    axes.set_xlim(0, budget)
    axes.set_xlabel("Objective evaluations")
    axes.set_ylabel("Best-so-far f(x)  [log scale, base 10]")
    axes.set_title(f"Rastrigin, D = {dimension}: Bees Algorithm convergence (global minimum f = 0)")
    axes.legend(loc="upper right", fontsize=8.5)
    figure.tight_layout()
    path = FIGURES_FOLDER / f"continuous_convergence_rastrigin_D{dimension}.png"
    figure.savefig(path)
    plt.close(figure)
    print(f"Saved {path}")


def plot_boxplots(results, dimension=30):
    figure, axes_grid = plt.subplots(1, 4, figsize=(12, 4.2))
    rng = np.random.default_rng(0)   # only for the small horizontal jitter of the dots (display only)
    for axes, function_name in zip(axes_grid, BENCHMARK_FUNCTIONS):
        finals = [run["final_best_value"] for run in select_runs(results, function_name, dimension)]
        axes.boxplot(finals, widths=0.5, patch_artist=True,
                     boxprops=dict(facecolor="#dbe8f8", edgecolor=SERIES_COLOUR, linewidth=1.5),
                     medianprops=dict(color=SERIES_COLOUR, linewidth=2),
                     whiskerprops=dict(color=SECONDARY_TEXT_COLOUR), capprops=dict(color=SECONDARY_TEXT_COLOUR),
                     flierprops=dict(marker="o", markerfacecolor="white", markeredgecolor=SECONDARY_TEXT_COLOUR))
        jitter = rng.uniform(-0.08, 0.08, size=len(finals))
        axes.scatter(1 + jitter, finals, s=18, color=SERIES_COLOUR, edgecolor="white", linewidth=0.6, zorder=3,
                     label="Individual run")
        axes.set_title(f"{FUNCTION_TITLES[function_name]} (D = {dimension})")
        axes.set_xticks([1])
        axes.set_xticklabels([f"{len(finals)} runs"])
        axes.set_ylabel("Final best f(x) (objective error)")
        axes.grid(axis="x", visible=False)
    figure.suptitle(f"Final objective values of the Bees Algorithm at D = {dimension} "
                    f"(30,000 evaluations per run; lower is better; global minimum 0)", fontsize=11)
    figure.tight_layout()
    path = FIGURES_FOLDER / f"continuous_boxplots_D{dimension}.png"
    figure.savefig(path)
    plt.close(figure)
    print(f"Saved {path}")


def main():
    apply_style()
    FIGURES_FOLDER.mkdir(parents=True, exist_ok=True)
    results = load_all_continuous_results()
    plot_rastrigin_convergence(results, dimension=10)
    plot_boxplots(results, dimension=30)


if __name__ == "__main__":
    main()
