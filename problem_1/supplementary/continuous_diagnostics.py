# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
POST-HOC DIAGNOSTICS for Problem 1B (2026-11-19, after the final experiments).

Status: not part of the required experiments. Nothing here changes the algorithm, settings, seeds,
results or required figures of Part B. Diagnostic seeds 300-309 are used only here.

Questions and designs
---------------------
A  Are the final solutions "frozen" by the neighbourhood?  (saved final results, no new BA runs)
   For each saved final best vector: the probability that ONE neighbour drawn with the assignment's
   rule (every coordinate + U(-10 %, +10 %) of the range, then clipped) is better; the root-mean-
   square (RMS) distance of the vector to the known optimum compared with the neighbourhood's
   per-coordinate standard deviation a/sqrt(3) (a = 10 % of the range); and the share of the total
   improvement that was made after evaluation 15,000 (the second half of the budget).

B  Would other BA settings help?  (new runs, assignment-compliant, seeds 300-309, D = 10 and 30)
   Five settings from very explorative to extreme local search, all with the assignment's ±10 %
   neighbourhood and 30,000 evaluations. Reported: mean final value, ratio to the current setting C
   and the difference in units of C's standard deviation.

C  NOT ASSIGNMENT-COMPLIANT, explanatory only: does the NEIGHBOURHOOD SIZE limit the results?
   Current settings, but neighbourhood half-widths of 10 % (the assignment's value), 3 % and 1 % of
   the range. These runs violate the assignment's fixed ±10 % rule. They are written to a separate
   file whose name and title say so, and must never be presented as results; they only help explain
   why the required results look the way they do.

Run from the problem_1 folder (about 8 minutes):
    python -m supplementary.continuous_diagnostics

Outputs (results/supplementary/):
    continuous_diagnostics.md / .json                     parts A and B (assignment-compliant)
    NONCOMPLIANT_neighbourhood_size_sweep.md / .json      part C (explanatory only)
"""

import json
from pathlib import Path

import numpy as np

from src.bees_algorithm import BeesSettings, run_bees_algorithm
from src.bees_continuous import CONTINUOUS_BEES_SETTINGS, run_bees_on_function
from src.benchmark_functions import BENCHMARK_FUNCTIONS
from src.evaluation_tracker import EvaluationTracker

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent
RAW_FOLDER = PROBLEM_FOLDER / "results" / "raw" / "continuous"
OUTPUT_FOLDER = PROBLEM_FOLDER / "results" / "supplementary"
DIAGNOSTIC_SEEDS = list(range(300, 310))
PROBE_SEED = 306
DIMENSIONS = [10, 30]
KNOWN_OPTIMUM_COORDINATE = {"sphere": 0.0, "rosenbrock": 1.0, "rastrigin": 0.0, "ackley": 0.0}

SETTINGS = {
    "A (n50 m10 e3 nep40 nsp20, explorative)": BeesSettings(50, 10, 3, 40, 20),
    "C (n10 m3 e1 nep100 nsp50, CURRENT)": CONTINUOUS_BEES_SETTINGS,
    "D (n6 m2 e1 nep100 nsp50)": BeesSettings(6, 2, 1, 100, 50),
    "E (n2 m1 e1 nep200 nsp1, extreme local search)": BeesSettings(2, 1, 1, 200, 1),
    "G (n100 m5 e1 nep20 nsp10, many scouts)": BeesSettings(100, 5, 1, 20, 10),
}
CURRENT = "C (n10 m3 e1 nep100 nsp50, CURRENT)"
NEIGHBOURHOOD_FRACTIONS = [0.10, 0.03, 0.01]


def neighbour_with_fraction(vector, lower, upper, fraction, rng):
    """
    Same rule as src/bees_continuous.create_neighbour_vector, but with a configurable half-width
    (fraction of the range). With fraction = 0.10 it is identical to the assignment's neighbourhood
    (a test checks this); any other value is NOT assignment-compliant.
    """
    maximum_change = fraction * (upper - lower)
    return np.clip(vector + rng.uniform(-maximum_change, maximum_change, size=vector.shape), lower, upper)


def improvement_probability(function_name, vector, samples, rng, fraction=0.10):
    """Fraction of `samples` neighbours of `vector` that have a strictly lower function value."""
    function, lower, upper = BENCHMARK_FUNCTIONS[function_name]
    base = function(vector)
    return float(np.mean([function(neighbour_with_fraction(vector, lower, upper, fraction, rng)) < base
                          for _ in range(samples)]))


def late_improvement_share(history, initial_value, final_value, after_evaluation=15_000):
    """Share of the total improvement (initial -> final) made after `after_evaluation` evaluations."""
    total = initial_value - final_value
    if total <= 0:
        return 0.0
    value_at = [value for evaluation, value in history if evaluation <= after_evaluation][-1]
    return (value_at - final_value) / total


def run_with_fraction(function_name, dimension, seed, settings, fraction):
    """One BA run (30,000 evaluations) with a given neighbourhood fraction (0.10 = assignment)."""
    function, lower, upper = BENCHMARK_FUNCTIONS[function_name]
    tracker = EvaluationTracker(function, settings.max_evaluations)
    run_bees_algorithm(tracker,
                       lambda rng: rng.uniform(lower, upper, size=dimension),
                       lambda vector, rng: neighbour_with_fraction(vector, lower, upper, fraction, rng),
                       settings, np.random.default_rng(seed))
    assert tracker.evaluations_used == settings.max_evaluations
    return float(tracker.best_value)


def part_a():
    rng = np.random.default_rng(PROBE_SEED)
    rows = []
    for function_name, (_, lower, upper) in BENCHMARK_FUNCTIONS.items():
        half_width = 0.10 * (upper - lower)
        for dimension in DIMENSIONS:
            runs = [json.load(open(path)) for path in sorted(RAW_FOLDER.glob(f"{function_name}_D{dimension}_seed*.json"))]
            probabilities, distances, late = [], [], []
            for run in runs:
                vector = np.array(run["best_vector"])
                probabilities.append(improvement_probability(function_name, vector, 4000, rng))
                distances.append(float(np.sqrt(np.mean((vector - KNOWN_OPTIMUM_COORDINATE[function_name]) ** 2))))
                late.append(late_improvement_share(run["best_so_far_history"], run["best_so_far_history"][0][1],
                                                   run["final_best_value"]))
            rows.append({"function": function_name, "dimension": dimension,
                         "mean_improvement_probability": float(np.mean(probabilities)),
                         "max_improvement_probability": float(np.max(probabilities)),
                         "rms_distance_to_optimum": float(np.mean(distances)),
                         "neighbour_coordinate_std": half_width / np.sqrt(3),
                         "median_late_improvement_share": float(np.median(late))})
    return rows


def part_b():
    rows = []
    for function_name in BENCHMARK_FUNCTIONS:
        for dimension in DIMENSIONS:
            values = {label: [run_bees_on_function(function_name, dimension, seed, settings)["final_best_value"]
                              for seed in DIAGNOSTIC_SEEDS] for label, settings in SETTINGS.items()}
            current_mean, current_std = np.mean(values[CURRENT]), np.std(values[CURRENT], ddof=1)
            rows.append({"function": function_name, "dimension": dimension,
                         "settings": {label: {"mean": float(np.mean(v)), "ratio_to_current": float(np.mean(v) / current_mean),
                                              "difference_in_current_std": float((np.mean(v) - current_mean) / current_std)}
                                      for label, v in values.items()}})
            print(f"B {function_name} D={dimension} done", flush=True)
    return rows


def part_c():
    rows = []
    for function_name in BENCHMARK_FUNCTIONS:
        for dimension in DIMENSIONS:
            means = {fraction: float(np.mean([run_with_fraction(function_name, dimension, seed, CONTINUOUS_BEES_SETTINGS, fraction)
                                              for seed in DIAGNOSTIC_SEEDS])) for fraction in NEIGHBOURHOOD_FRACTIONS}
            rows.append({"function": function_name, "dimension": dimension, "mean_final_value": means})
            print(f"C {function_name} D={dimension} done", flush=True)
    return rows


def main():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    a, b, c = part_a(), part_b(), part_c()
    (OUTPUT_FOLDER / "continuous_diagnostics.json").write_text(json.dumps({"A": a, "B": b}, indent=1))
    (OUTPUT_FOLDER / "NONCOMPLIANT_neighbourhood_size_sweep.json").write_text(json.dumps(c, indent=1, default=str))

    lines = ["# POST-HOC DIAGNOSTICS: Problem 1B (assignment-compliant parts A and B; not required results)", "",
             "## A. Final solutions under the assignment's ±10 % neighbourhood (saved final runs, seeds 0–9)", "",
             "| Function | D | P(one neighbour improves): mean | max | RMS distance to optimum per coordinate "
             "| Neighbour per-coordinate std (a/√3) | Median share of improvement after evaluation 15,000 |",
             "|---|---|---|---|---|---|---|"]
    for row in a:
        lines.append(f"| {row['function']} | {row['dimension']} | {row['mean_improvement_probability']:.5f} | "
                     f"{row['max_improvement_probability']:.5f} | {row['rms_distance_to_optimum']:.3f} | "
                     f"{row['neighbour_coordinate_std']:.3f} | {100 * row['median_late_improvement_share']:.2f} % |")
    lines += ["", "4,000 neighbours per final vector (probe seed 306).", "",
              "## B. Settings sensitivity (assignment-compliant: ±10 % neighbourhood, 30,000 evaluations; seeds 300–309)", "",
              "Cell = mean final value (ratio to the current setting C; difference in units of C's standard deviation).", "",
              "| Function | D | " + " | ".join(label.split(" (")[0] + " " + label[label.index("("):] for label in SETTINGS) + " |",
              "|---|---|" + "---|" * len(SETTINGS)]
    for row in b:
        cells = [f"{s['mean']:.4g} ({s['ratio_to_current']:.2f}×; {s['difference_in_current_std']:+.1f} sd)"
                 for s in row["settings"].values()]
        lines.append(f"| {row['function']} | {row['dimension']} | " + " | ".join(cells) + " |")
    (OUTPUT_FOLDER / "continuous_diagnostics.md").write_text("\n".join(lines) + "\n")

    lines = ["# NOT ASSIGNMENT-COMPLIANT, EXPLANATORY ONLY: neighbourhood-size sweep for Problem 1B", "",
             "**These runs violate the assignment's fixed ±10 % neighbourhood.** They are not results of this portfolio "
             "and must not be compared with or presented as the required experiments. Their only purpose is to show "
             "whether the neighbourhood size, rather than the BA settings, limits the required results.", "",
             "Current BA settings C, 30,000 evaluations, diagnostic seeds 300–309; cell = mean final value.", "",
             "| Function | D | ±10 % (assignment) | ±3 % (non-compliant) | ±1 % (non-compliant) |", "|---|---|---|---|---|"]
    for row in c:
        m = row["mean_final_value"]
        lines.append(f"| {row['function']} | {row['dimension']} | {m[0.10]:.4g} | {m[0.03]:.4g} | {m[0.01]:.4g} |")
    (OUTPUT_FOLDER / "NONCOMPLIANT_neighbourhood_size_sweep.md").write_text("\n".join(lines) + "\n")
    print("Saved continuous_diagnostics.md and NONCOMPLIANT_neighbourhood_size_sweep.md")


if __name__ == "__main__":
    main()
