# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Create the Part A figures from the saved run results.

Run from the problem_1 folder (after run_tsp_experiments):

    python -m experiments.make_tsp_plots

Figures (saved in results/figures/)
-----------------------------------
* ``tsp_convergence_berlin52.png`` and ``tsp_convergence_ch150.png``
  The assignment's convergence plots: objective evaluations (x) against the MEAN best-so-far
  tour length over the 10 runs (y), both neighbourhood versions on one plot, with the
  optimal length marked. A light band shows the range (minimum to maximum) over the 10 runs,
  which illustrates run-to-run variability around the mean.
* ``tsp_route_berlin52.png``
  The shortest valid berlin52 tour found across both neighbourhood versions and all 20 runs,
  labelled with neighbourhood, seed, tour length, gap and starting city, with the return leg drawn.

How the mean curve is computed
------------------------------
Each run's log only lists the evaluations at which its best-so-far improved. We first expand
each log to a value at every evaluation 1..30,000 (the best-so-far stays constant between
improvements), then average the 10 expanded curves evaluation by evaluation.
"""

import numpy as np
import matplotlib.pyplot as plt

from experiments.plot_style import (
    GRID_COLOUR,
    NEIGHBOURHOOD_COLOURS,
    NEIGHBOURHOOD_LABELS,
    REFERENCE_LINE_COLOUR,
    SECONDARY_TEXT_COLOUR,
    apply_style,
)
from experiments.run_tsp_experiments import NEIGHBOURHOODS, PROBLEM_FOLDER
from experiments.tsp_results_io import load_all_tsp_results, select_runs
from src.bees_tsp import TSP_BEES_SETTINGS
from src.evaluation_tracker import expand_history_to_every_evaluation
from src.tsp_instances import TSP_INSTANCES, instance_file_path
from src.tsp_tour import compute_distance_matrix, is_valid_tour, tour_length
from src.tsplib import load_tsplib_instance

FIGURES_FOLDER = PROBLEM_FOLDER / "results" / "figures"
CONVERGENCE_INSTANCES = ["berlin52", "ch150"]   # required by the assignment
ROUTE_INSTANCE = "berlin52"                      # required by the assignment


def plot_convergence(results, instance_name):
    """Mean best-so-far tour length vs evaluations for both neighbourhoods on one instance."""
    cities, optimum = TSP_INSTANCES[instance_name]
    budget = TSP_BEES_SETTINGS.max_evaluations
    evaluations = np.arange(1, budget + 1)

    figure, axes = plt.subplots(figsize=(7.5, 4.5))
    for neighbourhood in NEIGHBOURHOODS:
        runs = select_runs(results, instance_name, neighbourhood)
        # Matrix with one row per run and one column per evaluation number.
        curves = np.array([expand_history_to_every_evaluation(run["best_so_far_history"], budget) for run in runs])
        mean_curve = curves.mean(axis=0)
        colour = NEIGHBOURHOOD_COLOURS[neighbourhood]
        axes.fill_between(evaluations, curves.min(axis=0), curves.max(axis=0), color=colour, alpha=0.15,
                          linewidth=0, label=f"{NEIGHBOURHOOD_LABELS[neighbourhood]}: min-max over {len(runs)} runs")
        axes.plot(evaluations, mean_curve, color=colour,
                  label=f"{NEIGHBOURHOOD_LABELS[neighbourhood]}: mean of {len(runs)} runs "
                        f"(final mean {mean_curve[-1]:,.0f})")

    axes.axhline(optimum, color=REFERENCE_LINE_COLOUR, linestyle="--", linewidth=1.5,
                 label=f"Optimal length L* = {optimum:,}")
    axes.set_xlim(0, budget)
    axes.set_ylim(bottom=0)
    axes.set_xlabel("Objective evaluations")
    axes.set_ylabel("Best-so-far tour length (TSPLIB distance units)")
    axes.set_title(f"{instance_name} ({cities} cities): Bees Algorithm convergence, swap vs segment reversal")
    axes.legend(loc="upper right", fontsize=8.5)
    figure.tight_layout()
    path = FIGURES_FOLDER / f"tsp_convergence_{instance_name}.png"
    figure.savefig(path)
    plt.close(figure)
    print(f"Saved {path}")


def find_best_run(results, instance_name):
    """
    The run with the shortest final tour across BOTH neighbourhoods and all seeds.

    Ties (equal lengths) are broken deterministically: the first run in the saved order
    (swap before reversal, then lower seed) is chosen, so the figure is reproducible.
    """
    runs = [run for run in results if run["instance"] == instance_name]
    return min(runs, key=lambda run: run["final_best_length"])  # min() keeps the first of equal values


def plot_best_route(results, instance_name):
    """Draw the best tour found, including the return leg, with all required labels."""
    cities, optimum = TSP_INSTANCES[instance_name]
    best_run = find_best_run(results, instance_name)
    instance = load_tsplib_instance(instance_file_path(instance_name))
    coordinates = instance.coordinates

    # Re-check the tour before drawing it: valid permutation and recomputed length.
    tour = np.array(best_run["best_tour_city_ids"]) - 1
    distances = compute_distance_matrix(coordinates)
    assert is_valid_tour(tour, cities)
    assert tour_length(tour, distances) == best_run["final_best_length"]

    colour = NEIGHBOURHOOD_COLOURS[best_run["neighbourhood"]]
    route_points = coordinates[tour]                         # cities in visiting order
    start_point = coordinates[tour[0]]                       # city 1

    figure, axes = plt.subplots(figsize=(8, 7.5))
    # Main route: from city 1 through every city to the last city in the permutation.
    axes.plot(route_points[:, 0], route_points[:, 1], color=colour, linewidth=1.6, zorder=2,
              label="Tour (city 1 to last city)")
    # Return leg: last city back to city 1. Drawn dark, dashed and on top so it stays visible
    # even when it is short (the assignment requires the return leg to be drawn).
    axes.plot([route_points[-1, 0], start_point[0]], [route_points[-1, 1], start_point[1]],
              color="#0b0b0b", linewidth=2.2, linestyle=(0, (2, 1.5)), zorder=5,
              label=f"Return leg (city {tour[-1] + 1} back to city 1)")
    axes.scatter(coordinates[:, 0], coordinates[:, 1], s=22, color="white", edgecolor=SECONDARY_TEXT_COLOUR,
                 linewidth=1, zorder=3, label="City")
    axes.scatter([start_point[0]], [start_point[1]], s=160, marker="*", color="#0b0b0b",
                 edgecolor="white", linewidth=0.8, zorder=6, label="Starting city (city 1)")
    axes.annotate("Start: city 1", start_point, xytext=(-14, -26), textcoords="offset points", fontsize=9,
                  ha="right", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=GRID_COLOUR),
                  arrowprops=dict(arrowstyle="-", color=SECONDARY_TEXT_COLOUR, linewidth=0.8), zorder=7)

    gap = best_run["gap_percent"]
    number_of_runs = len([run for run in results if run["instance"] == instance_name])
    axes.set_title(
        f"{instance_name}: shortest tour found over all {number_of_runs} runs (both neighbourhoods)\n"
        f"{NEIGHBOURHOOD_LABELS[best_run['neighbourhood']]} neighbourhood, seed {best_run['seed']}: "
        f"length {best_run['final_best_length']:,}, gap {gap:.2f} % (L* = {optimum:,})\n"
        f"Starting city: 1 (the route returns to city 1)"
    )
    axes.set_xlabel("x coordinate (TSPLIB units)")
    axes.set_ylabel("y coordinate (TSPLIB units)")
    axes.set_aspect("equal", adjustable="datalim")
    axes.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8.5)
    figure.tight_layout()
    path = FIGURES_FOLDER / f"tsp_route_{instance_name}.png"
    figure.savefig(path)
    plt.close(figure)
    print(f"Saved {path}  (neighbourhood {best_run['neighbourhood']}, seed {best_run['seed']}, "
          f"length {best_run['final_best_length']}, gap {gap:.2f} %)")


def main():
    apply_style()
    FIGURES_FOLDER.mkdir(parents=True, exist_ok=True)
    results = load_all_tsp_results()
    for instance_name in CONVERGENCE_INSTANCES:
        plot_convergence(results, instance_name)
    plot_best_route(results, ROUTE_INSTANCE)


if __name__ == "__main__":
    main()
