# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Create the Problem 2 figures from the saved run results.

Run from the problem_2 folder (after run_es_experiments):

    python -m experiments.make_es_plots

Required figure
---------------
* ``es_convergence_port5_alpha050.png``: objective evaluations (x) against the MEAN archive
  best variance over the 10 runs (y), all three variants on one plot. The y-axis is LOGARITHMIC
  (labelled on the axis) because the variance falls by more than half its starting value and the
  later differences between the variants would otherwise be invisible. Light bands show the
  minimum-maximum range over the 10 runs.

Supplementary figures (not required by the assignment; they support the analysis)
---------------------------------------------------------------------------------
* ``es_comma_population_vs_archive_port5_alpha050.png``: one (μ,λ)-ES run (seed 0). The best
  variance in the CURRENT parent population (which can increase) next to the archive best
  (which cannot). Illustrates why comma selection can worsen the population best.
* ``es_step_sizes_port5_alpha050.png``: step sizes over the run: the (1+1)-ES scalar sigma
  (mean of 10 runs) shows how the 1/5 rule shrinks the step size.

Colours: one fixed colour per variant in every figure (validated colour-blind-safe palette).
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from experiments.es_results_io import load_all_es_results, select_runs  # noqa: E402
from experiments.run_es_experiments import PROBLEM_FOLDER  # noqa: E402
from src.run_es import BUDGET, VARIANTS  # noqa: E402

FIGURES_FOLDER = PROBLEM_FOLDER / "results" / "figures"
CONVERGENCE_CASE = "port5_alpha050"     # required by the assignment
VARIANT_COLOURS = {"one_plus_one": "#2a78d6", "mu_plus_lambda": "#eb6834", "mu_comma_lambda": "#1baf7a"}
NEUTRAL = "#52514e"


def apply_style():
    plt.rcParams.update({
        "savefig.dpi": 200, "font.size": 10, "axes.titlesize": 11,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.color": "#e4e3df", "grid.linewidth": 0.8, "axes.edgecolor": NEUTRAL,
        "xtick.color": NEUTRAL, "ytick.color": NEUTRAL, "legend.frameon": False, "lines.linewidth": 2,
    })


def expand_history(history, total):
    """Best-so-far value after every evaluation 1..total, rebuilt from the change points."""
    curve = np.empty(total)
    for position, (evaluation, value) in enumerate(history):
        end = history[position + 1][0] - 1 if position + 1 < len(history) else total
        curve[evaluation - 1:end] = value
    return curve


def plot_convergence(results):
    evaluations = np.arange(1, BUDGET + 1)
    figure, axes = plt.subplots(figsize=(7.8, 4.6))
    for variant, label in VARIANTS.items():
        runs = select_runs(results, CONVERGENCE_CASE, variant)
        curves = np.array([expand_history(run["archive_history"], BUDGET) for run in runs])
        colour = VARIANT_COLOURS[variant]
        axes.fill_between(evaluations, curves.min(axis=0), curves.max(axis=0), color=colour, alpha=0.13, linewidth=0)
        axes.plot(evaluations, curves.mean(axis=0), color=colour,
                  label=f"{label}: mean of {len(runs)} runs (final {curves.mean(axis=0)[-1]:.4e})")
    axes.plot([], [], color=NEUTRAL, alpha=0.3, linewidth=8, label="Shaded: min-max over the 10 runs")
    axes.set_yscale("log")
    axes.set_xlim(0, BUDGET)
    axes.set_xlabel("Objective evaluations")
    axes.set_ylabel("Archive best variance w$^T$Σw  [log scale, base 10]")
    target = runs[0]["target_return"]
    axes.set_title(f"{CONVERGENCE_CASE} (225 assets, target return R_min = {target:.6f}): ES convergence")
    axes.legend(loc="upper right", fontsize=8.5)
    figure.tight_layout()
    path = FIGURES_FOLDER / f"es_convergence_{CONVERGENCE_CASE}.png"
    figure.savefig(path)
    plt.close(figure)
    print(f"Saved {path}")


def plot_comma_population_vs_archive(results, seed=0):
    run = next(r for r in select_runs(results, CONVERGENCE_CASE, "mu_comma_lambda") if r["seed"] == seed)
    population = np.array(run["details"]["population_best_history"])
    archive_curve = expand_history(run["archive_history"], BUDGET)
    worsened = int(np.sum(np.diff(population[:, 1]) > 0))
    figure, axes = plt.subplots(figsize=(7.8, 4.6))
    axes.plot(population[:, 0], population[:, 1], color=VARIANT_COLOURS["mu_comma_lambda"], linewidth=1.2,
              label=f"Best variance in current parent population (worse than before in {worsened} "
                    f"of {len(population) - 1} generations)")
    axes.plot(np.arange(1, BUDGET + 1), archive_curve, color=NEUTRAL, linestyle="--",
              label="Archive best variance (never increases)")
    axes.set_yscale("log")
    axes.set_xlim(0, BUDGET)
    axes.set_xlabel("Objective evaluations")
    axes.set_ylabel("Variance  [log scale, base 10]")
    axes.set_title(f"(μ,λ)-ES on {CONVERGENCE_CASE}, seed {seed}: population best vs archive (supplementary)")
    axes.legend(loc="upper right", fontsize=8.5)
    figure.tight_layout()
    path = FIGURES_FOLDER / f"es_comma_population_vs_archive_{CONVERGENCE_CASE}.png"
    figure.savefig(path)
    plt.close(figure)
    print(f"Saved {path} ({worsened} generations where the population best got worse)")


def plot_step_sizes(results):
    runs = select_runs(results, CONVERGENCE_CASE, "one_plus_one")
    logs = [np.array(run["details"]["step_size_log"]) for run in runs]
    evaluations = logs[0][:, 0]
    sigmas = np.array([log[:, 1] for log in logs])
    figure, axes = plt.subplots(figsize=(7.8, 4.2))
    axes.plot(evaluations, np.exp(np.log(sigmas).mean(axis=0)), color=VARIANT_COLOURS["one_plus_one"],
              label="(1+1)-ES step size σ (geometric mean of 10 runs)")
    axes.axhline(1e-8, color=NEUTRAL, linestyle=":", linewidth=1.2, label="Lower bound 10$^{-8}$")
    axes.axhline(0.1 / np.sqrt(225), color=NEUTRAL, linestyle="--", linewidth=1.2, label="Initial σ = 0.1/√225")
    axes.set_yscale("log")
    axes.set_xlim(0, BUDGET)
    axes.set_xlabel("Objective evaluations")
    axes.set_ylabel("Step size σ  [log scale, base 10]")
    axes.set_title(f"(1+1)-ES step-size adaptation on {CONVERGENCE_CASE} (supplementary)")
    axes.legend(loc="lower left", fontsize=8.5)
    figure.tight_layout()
    path = FIGURES_FOLDER / f"es_step_sizes_{CONVERGENCE_CASE}.png"
    figure.savefig(path)
    plt.close(figure)
    print(f"Saved {path}")


def main():
    apply_style()
    FIGURES_FOLDER.mkdir(parents=True, exist_ok=True)
    results = load_all_es_results()
    plot_convergence(results)
    plot_comma_population_vs_archive(results)
    plot_step_sizes(results)


if __name__ == "__main__":
    main()
