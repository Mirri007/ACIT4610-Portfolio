# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Build the Problem 2 tables from the saved run results.

Run from the problem_2 folder (after run_es_experiments):

    python -m experiments.make_es_tables

Outputs
-------
* ``results/raw/es_all_runs.csv``: one row per run (450), including the best weights.
* ``results/tables/es_summary.csv`` / ``es_summary.md``: the required summary, one row per
  case and variant (45 rows): case, number of assets, target return, best and mean variance,
  standard deviation, feasible-run rate and mean runtime.
* ``results/tables/es_comparison.md``: mean variance of the three variants side by side per case,
  plus paired per-seed comparisons (used in the analysis).
* ``results/tables/es_analysis.md``: stagnation, sparsity, constraint activity, (1+1) step-size
  behaviour and a sign test for (μ+λ) vs (μ,λ).

Statistics follow the assignment: variance statistics use only VALID (feasible) runs; the number
of valid runs out of 10 is reported; mean runtime is averaged over ALL 10 runs.
"Std" is the sample standard deviation (ddof = 1). Variance is in squared return units
(the returns in the data are decimal fractions per period, e.g. 0.003 = 0.3 %).

Before summarising, every run is re-checked: the saved weights are feasible within the
assignment tolerances, re-evaluate to exactly the saved variance and return, and the run used
30,000 evaluations.
"""

import csv
import math

import numpy as np

from experiments.es_results_io import load_all_es_results, select_runs
from experiments.run_es_experiments import PROBLEM_FOLDER
from src.portfolio_data import load_all_cases
from src.portfolio_model import expected_return, feasibility_violations, portfolio_variance
from src.run_es import BUDGET, FINAL_SEEDS, VARIANTS

TABLES_FOLDER = PROBLEM_FOLDER / "results" / "tables"
ALL_RUNS_CSV = PROBLEM_FOLDER / "results" / "raw" / "es_all_runs.csv"


def verify_all_runs(results, cases_by_name):
    for result in results:
        case = cases_by_name[result["case"]]
        weights = np.array(result["best_weights"])
        label = f"{result['case']} {result['variant']} seed {result['seed']}"
        assert result["evaluations_used"] == BUDGET, f"wrong evaluation count: {label}"
        assert portfolio_variance(weights, case.data.covariance) == result["final_variance"], f"variance mismatch: {label}"
        assert expected_return(weights, case.data.mean_returns) == result["final_expected_return"], f"return mismatch: {label}"
        recomputed_violations = feasibility_violations(weights, case.data.mean_returns, case.min_return)
        assert (not recomputed_violations) == result["feasible"], f"feasibility flag wrong: {label}"
    print(f"Verified {len(results)} runs: variances and returns reproduce exactly, feasibility flags "
          f"confirmed, 30,000 evaluations each; feasible runs: {sum(r['feasible'] for r in results)}/{len(results)}.")


def write_all_runs_csv(results):
    columns = ["case", "dataset", "n_assets", "alpha", "target_return", "variant", "seed",
               "initial_best_variance", "final_variance", "final_expected_return", "feasible",
               "min_weight", "weight_sum_error", "assets_with_weight_above_1e-6", "runtime_seconds",
               "evaluations_used"]
    with open(ALL_RUNS_CSV, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns + ["best_weights"])
        for result in results:
            writer.writerow([result[column] for column in columns]
                            + [" ".join(repr(value) for value in result["best_weights"])])


def summarise(results, cases):
    rows = []
    for case in cases:
        for variant, label in VARIANTS.items():
            runs = select_runs(results, case.name, variant)
            valid = [run for run in runs if run["feasible"]]
            variances = np.array([run["final_variance"] for run in valid])
            rows.append({
                "Case": case.name,
                "Assets": case.data.n_assets,
                "Target return": case.min_return,
                "Variant": label,
                "Feasible runs": f"{len(valid)}/{len(runs)}",
                "Best variance": float(variances.min()) if len(valid) else float("nan"),
                "Mean variance": float(variances.mean()) if len(valid) else float("nan"),
                "Std variance": float(variances.std(ddof=1)) if len(valid) > 1 else float("nan"),
                "Mean initial best variance": float(np.mean([run["initial_best_variance"] for run in runs])),
                "Mean runtime (s)": float(np.mean([run["runtime_seconds"] for run in runs])),
            })
    return rows


def format_cell(header, value):
    if header == "Target return":
        return f"{value:.6f}"
    if header == "Mean runtime (s)":
        return f"{value:.2f}"
    if isinstance(value, float):
        return f"{value:.5e}"
    return str(value)


def write_summary(rows):
    TABLES_FOLDER.mkdir(parents=True, exist_ok=True)
    with open(TABLES_FOLDER / "es_summary.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    headers = list(rows[0])
    lines = [
        "# Problem 2: ES variants on the 15 portfolio cases (10 runs each, 30,000 evaluations per run)",
        "",
        "Variance = portfolio variance w^T Sigma w of the best valid allocation (archive) of each run, in squared "
        "return units. Variance statistics over valid runs; Std = sample standard deviation (ddof = 1); "
        "runtime = mean wall-clock seconds over all 10 runs.",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(format_cell(h, row[h]) for h in headers) + " |")
    (TABLES_FOLDER / "es_summary.md").write_text("\n".join(lines) + "\n")


def write_comparison(results, cases):
    """Side-by-side mean variances and paired per-seed comparisons between the variants."""
    labels = list(VARIANTS.values())
    lines = [
        "# Problem 2: comparison of the ES variants",
        "",
        "## Mean final variance per case (lowest in bold)",
        "",
        "| Case | Assets | " + " | ".join(labels) + " | Lowest | (μ+λ) vs (μ,λ): relative difference |",
        "|---|---|" + "---|" * len(labels) + "---|---|",
    ]
    lowest_counts = {label: 0 for label in labels}
    for case in cases:
        means = {VARIANTS[v]: np.mean([r["final_variance"] for r in select_runs(results, case.name, v) if r["feasible"]])
                 for v in VARIANTS}
        best_label = min(means, key=means.get)
        lowest_counts[best_label] += 1
        cells = [f"**{means[l]:.5e}**" if l == best_label else f"{means[l]:.5e}" for l in labels]
        plus, comma = means[VARIANTS["mu_plus_lambda"]], means[VARIANTS["mu_comma_lambda"]]
        lines.append(f"| {case.name} | {case.data.n_assets} | " + " | ".join(cells)
                     + f" | {best_label} | {100 * (plus - comma) / comma:+.2f} % |")
    lines += ["", "Cases where each variant has the lowest mean variance: "
              + ", ".join(f"{label}: {count}" for label, count in lowest_counts.items()), ""]

    # Paired comparisons. For the same seed, (μ+λ) and (μ,λ) start from IDENTICAL initial
    # parents (the random generator is used identically during initialisation), so comparing
    # them seed by seed removes the luck of the starting population.
    lines += ["## Paired per-seed comparisons (150 pairs = 15 cases x 10 seeds)", "",
              "| Comparison | First lower | Second lower | Equal |", "|---|---|---|---|"]
    pairs = [("mu_plus_lambda", "mu_comma_lambda"), ("mu_plus_lambda", "one_plus_one"), ("mu_comma_lambda", "one_plus_one")]
    for first, second in pairs:
        first_lower = second_lower = equal = 0
        for case in cases:
            for seed in FINAL_SEEDS:
                a = next(r for r in results if r["case"] == case.name and r["variant"] == first and r["seed"] == seed)
                b = next(r for r in results if r["case"] == case.name and r["variant"] == second and r["seed"] == seed)
                if a["final_variance"] < b["final_variance"]:
                    first_lower += 1
                elif a["final_variance"] > b["final_variance"]:
                    second_lower += 1
                else:
                    equal += 1
        lines.append(f"| {VARIANTS[first]} vs {VARIANTS[second]} | {first_lower} | {second_lower} | {equal} |")
    (TABLES_FOLDER / "es_comparison.md").write_text("\n".join(lines) + "\n")


def sign_test_p_value(wins, losses):
    """
    Exact two-sided sign test: if two variants were equally good, each paired comparison would be
    a fair coin flip. The p-value is the probability of a split at least this uneven by chance.
    p = 2 * P(X <= min(wins, losses)) with X ~ Binomial(wins + losses, 1/2), capped at 1.
    """
    n = wins + losses
    k = min(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def write_analysis(results):
    """
    Extra statistics used in the discussion (stagnation, sparsity, constraint activity,
    step-size behaviour and significance), computed per variant over all 150 runs.
    """
    lines = [
        "# Problem 2: analysis statistics (all 15 cases x 10 seeds per variant)",
        "",
        "| Variant | Runs with return constraint active (R = R_min) | Mean assets with weight > 1e-6 "
        "| Median evaluation reaching within 1 % of final variance | Median evaluation of last archive improvement |",
        "|---|---|---|---|---|",
    ]
    for variant, label in VARIANTS.items():
        runs = [r for r in results if r["variant"] == variant]
        active = sum(abs(r["final_expected_return"] - r["target_return"]) < 1e-12 for r in runs)
        assets = np.mean([r["assets_with_weight_above_1e-6"] for r in runs])
        within = [next(e for e, v in r["archive_history"] if v <= 1.01 * r["final_variance"]) for r in runs]
        last = [r["archive_history"][-1][0] for r in runs]
        lines.append(f"| {label} | {active}/{len(runs)} | {assets:.1f} | {np.median(within):.0f} | {np.median(last):.0f} |")

    one_plus_one = [r for r in results if r["variant"] == "one_plus_one"]
    rates = [r["details"]["successful_trials"] / r["details"]["trials"] for r in one_plus_one]
    collapsed = sum(r["details"]["final_step_size"] < 1e-7 for r in one_plus_one)
    lines += ["", f"(1+1)-ES success rate: mean {np.mean(rates):.3f}, min {min(rates):.3f}, max {max(rates):.3f}; "
              f"runs ending with step size below 1e-7: {collapsed}/{len(one_plus_one)}.", ""]

    wins = losses = 0
    for r in results:
        if r["variant"] != "mu_plus_lambda":
            continue
        partner = next(o for o in results if o["variant"] == "mu_comma_lambda" and o["case"] == r["case"] and o["seed"] == r["seed"])
        wins += r["final_variance"] < partner["final_variance"]
        losses += r["final_variance"] > partner["final_variance"]
    lines.append(f"Sign test (μ+λ)-ES vs (μ,λ)-ES over 150 seed pairs: (μ+λ) lower in {wins}, (μ,λ) lower in {losses}; "
                 f"two-sided p = {sign_test_p_value(wins, losses):.3f}.")
    (TABLES_FOLDER / "es_analysis.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    cases = load_all_cases()
    cases_by_name = {case.name: case for case in cases}
    results = load_all_es_results()
    verify_all_runs(results, cases_by_name)
    write_all_runs_csv(results)
    write_summary(summarise(results, cases))
    write_comparison(results, cases)
    write_analysis(results)
    print((TABLES_FOLDER / "es_summary.md").read_text())
    print((TABLES_FOLDER / "es_comparison.md").read_text())


if __name__ == "__main__":
    main()
