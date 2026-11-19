# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
POST-HOC DIAGNOSTICS (2026-11-19, after the final experiments): why does the (1+1)-ES stagnate?

Status: not part of the required experiments. The modified (1+1) versions used here (higher step-size
floor, fixed step size) are NOT the assignment's (1+1)-ES; they are diagnostic tools only, run with
diagnostic seeds 300-304, and they never enter the results tables or required figures.

Questions and designs
---------------------
Q1 Is slow progress ASSOCIATED with a small step size?  (saved data, no new runs)
   Using the saved step-size logs (every 500 evaluations) and archive histories of all 150 final
   (1+1) runs: the relative improvement in each 500-evaluation window, grouped by sigma at the start.

Q2 Is the step-size collapse a CAUSE?  (intervention, seeds 300-304)
   Run the (1+1)-ES unchanged except that sigma may not fall below 1e-4 or 1e-3, or sigma stays at
   its initial value (no adaptation). If preventing the collapse removes most of the gap to the
   reference optimum, the collapse is a cause. Done for all five datasets (alpha = 0.50).

Q3 WHY does sigma collapse?  (probe at the saved stagnated solutions, seed-0 runs)
   For sigma from 1e-8 to 1e-2, estimate the probability that ONE mutation + repair improves the
   saved final (1+1) solution (3,000 samples per sigma). The 1/5 rule only stops shrinking sigma if
   some sigma reaches a 20 % success rate. The same probe at the reference optimum must give 0.

Q4 Step-size adaptation versus high-dimensional difficulty (decomposition per dataset, n = 31..225)
   * gap of the (1+1)-ES as specified;
   * gap that REMAINS when the collapse is prevented (best of the three diagnostic versions);
   * gap of the population ES (saved final results).
   The part of the gap removed by preventing the collapse is attributed to step-size adaptation;
   the part that remains, and grows with n, to the difficulty of finding improving directions with
   one isotropic step size in many dimensions. Caveats: datasets differ in more than n; "best of
   three versions" is chosen after seeing the results (optimistic); 5 seeds per setting.

Run from the problem_2 folder AFTER supplementary.reference_optima (it needs the reference optima):
    python -m supplementary.one_plus_one_diagnostics

Outputs: results/supplementary/one_plus_one_diagnostics.md (all four tables) and .json.
"""

import os

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[variable] = "1"

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

from src import es_one_plus_one  # noqa: E402
from src.portfolio_data import load_case  # noqa: E402
from src.portfolio_evaluator import PortfolioEvaluator  # noqa: E402
from src.portfolio_model import portfolio_variance, repair_portfolio  # noqa: E402

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent
OUTPUT_FOLDER = PROBLEM_FOLDER / "results" / "supplementary"
RAW_FOLDER = PROBLEM_FOLDER / "results" / "raw" / "es"
DIAGNOSTIC_SEEDS = [300, 301, 302, 303, 304]
PROBE_SEED = 305
CASES = ["port1_alpha050", "port2_alpha050", "port3_alpha050", "port4_alpha050", "port5_alpha050"]
PROBE_STEP_SIZES = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
DIAGNOSTIC_VERSIONS = {
    "as specified (floor 1e-8)": {"step_size_floor": 1e-8, "adapt": True},
    "floor 1e-4": {"step_size_floor": 1e-4, "adapt": True},
    "floor 1e-3": {"step_size_floor": 1e-3, "adapt": True},
    "fixed sigma0 (no adaptation)": {"step_size_floor": 1e-8, "adapt": False},
}


def run_one_plus_one_diagnostic(case, seed, step_size_floor=1e-8, adapt=True, budget=30_000):
    """
    (1+1)-ES identical to src/es_one_plus_one.py except for two DIAGNOSTIC switches:
    a different lower bound for sigma, or no step-size adaptation at all. With the default values
    it reproduces the assignment's (1+1)-ES exactly (checked by a test).

    Returns the archive best variance after ``budget`` evaluations.
    """
    n = case.data.n_assets
    rng = np.random.default_rng(seed)
    evaluator = PortfolioEvaluator(case, budget)
    parent_weights, parent_variance = evaluator.evaluate(rng.uniform(0.0, 1.0, size=n))
    step_size = es_one_plus_one.initial_step_size(n)
    while not evaluator.budget_exhausted():
        child_weights, child_variance = evaluator.evaluate(parent_weights + step_size * rng.standard_normal(n))
        success = child_variance < parent_variance
        if success:
            parent_weights, parent_variance = child_weights, child_variance
        if adapt:
            factor = es_one_plus_one.SUCCESS_FACTOR if success else es_one_plus_one.FAILURE_FACTOR
            step_size = min(max(step_size * factor, step_size_floor), es_one_plus_one.STEP_SIZE_MAX)
    return evaluator.archive_variance, evaluator.archive_weights


def improvement_probability(case, point, step_size, samples, rng):
    """Fraction of `samples` mutations (point + sigma * N(0,1), then repair) with lower variance than `point`."""
    data = case.data
    base = portfolio_variance(point, data.covariance)
    better = 0
    for _ in range(samples):
        child = repair_portfolio(point + step_size * rng.standard_normal(data.n_assets),
                                 data.mean_returns, case.min_return, case.best_asset_index)
        better += portfolio_variance(child, data.covariance) < base
    return better / samples


def saved_one_plus_one_runs():
    return [json.load(open(path)) for path in sorted(RAW_FOLDER.glob("*_one_plus_one_seed*.json"))]


def question_1(runs):
    """Mean relative improvement per 500-evaluation window, by sigma at the window start."""
    bins = [("≥ 1e-3", 1e-3, np.inf), ("1e-4 – 1e-3", 1e-4, 1e-3), ("1e-5 – 1e-4", 1e-5, 1e-4),
            ("1e-6 – 1e-5", 1e-6, 1e-5), ("1e-7 – 1e-6", 1e-7, 1e-6), ("< 1e-7", 0.0, 1e-7)]
    gains = {label: [] for label, _, _ in bins}

    def best_at(history, evaluation):
        return [value for e, value in history if e <= evaluation][-1]

    for run in runs:
        history, log = run["archive_history"], run["details"]["step_size_log"]
        for (start, sigma), (end, _) in zip(log, log[1:]):
            before = best_at(history, start)
            gain = (before - best_at(history, end)) / before
            for label, low, high in bins:
                if low <= sigma < high:
                    gains[label].append(gain)
    rows = [(label, len(values), float(np.mean(values)), float(np.median(values))) for label, values in gains.items() if values]
    first_below = {t: float(np.median([next((e for e, s in r["details"]["step_size_log"] if s < t), 30000) for r in runs]))
                   for t in (1e-4, 1e-5, 1e-6)}
    within_one_percent = float(np.median([next(e for e, v in r["archive_history"] if v <= 1.01 * r["final_variance"]) for r in runs]))
    return {"windows": rows, "median_first_below": first_below, "median_within_1_percent": within_one_percent}


def main():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    references = json.loads((OUTPUT_FOLDER / "reference_optima_weights.json").read_text())
    runs = saved_one_plus_one_runs()
    report = {"q1": question_1(runs), "q2": {}, "q3": {}, "q4": {}}

    for name in CASES:
        case = load_case(name)
        v_star = portfolio_variance(np.array(references[name]), case.data.covariance)
        # Q2: interventions on diagnostic seeds.
        gaps = {}
        for label, options in DIAGNOSTIC_VERSIONS.items():
            values = [run_one_plus_one_diagnostic(case, seed, **options)[0] for seed in DIAGNOSTIC_SEEDS]
            gaps[label] = float(np.mean([100 * (v - v_star) / v_star for v in values]))
        report["q2"][name] = gaps
        # Q3: probe at the saved stagnated solution (seed 0) and at the reference optimum.
        rng = np.random.default_rng(PROBE_SEED)
        stagnated = np.array(json.load(open(RAW_FOLDER / f"{name}_one_plus_one_seed0.json"))["best_weights"])
        probe = [improvement_probability(case, stagnated, s, 3000, rng) for s in PROBE_STEP_SIZES]
        at_optimum = max(improvement_probability(case, np.array(references[name]), s, 1000, rng) for s in (1e-6, 1e-4, 1e-2))
        report["q3"][name] = {"probe": probe, "max_at_reference_optimum": at_optimum,
                              "gap_of_probed_point_percent": 100 * (portfolio_variance(stagnated, case.data.covariance) - v_star) / v_star}
        # Q4: decomposition with the saved final results (seeds 0-9) of the population ES for comparison.
        population = [json.load(open(RAW_FOLDER / f"{name}_{variant}_seed{seed}.json"))["final_variance"]
                      for variant in ("mu_plus_lambda", "mu_comma_lambda") for seed in range(10)]
        report["q4"][name] = {
            "n_assets": case.data.n_assets,
            "specified": gaps["as specified (floor 1e-8)"],
            "best_without_collapse": min(gaps["floor 1e-4"], gaps["floor 1e-3"], gaps["fixed sigma0 (no adaptation)"]),
            "population_es_saved": float(np.mean([100 * (v - v_star) / v_star for v in population])),
        }
        print(f"{name}: done", flush=True)

    (OUTPUT_FOLDER / "one_plus_one_diagnostics.json").write_text(json.dumps(report, indent=1))
    write_markdown(report)


def write_markdown(report):
    q1 = report["q1"]
    lines = [
        "# POST-HOC DIAGNOSTICS: (1+1)-ES stagnation (not part of the required experiments)",
        "",
        "Modified (1+1) versions below are diagnostic tools, not the assignment's algorithm. Diagnostic seeds 300–304; "
        "probes use the saved seed-0 final solutions. Gaps are relative to the numerically verified reference optima "
        "(reference_optima.md).",
        "",
        "## Q1. Association in the saved final runs (150 runs, 500-evaluation windows)",
        "",
        "| σ at window start | Windows | Mean relative improvement per window | Median |",
        "|---|---|---|---|",
    ]
    lines += [f"| {label} | {count} | {100 * mean:.4f} % | {100 * median:.5f} % |" for label, count, mean, median in q1["windows"]]
    b = q1["median_first_below"]
    lines += ["", f"Median evaluation at which σ first falls below 1e-4: {b[1e-4]:.0f}; below 1e-5: {b[1e-5]:.0f}; "
              f"below 1e-6: {b[1e-6]:.0f}. Median evaluation at which the archive is within 1 % of its final value: "
              f"{q1['median_within_1_percent']:.0f}. (Association only: a difficult landscape could cause both.)", "",
              "## Q2. Intervention: mean gap to the reference optimum (seeds 300–304, α = 0.50)", "",
              "| Case | n | " + " | ".join(DIAGNOSTIC_VERSIONS) + " |", "|---|---|" + "---|" * len(DIAGNOSTIC_VERSIONS)]
    for name, gaps in report["q2"].items():
        lines.append(f"| {name} | {report['q4'][name]['n_assets']} | " + " | ".join(f"{gaps[k]:.2f} %" for k in DIAGNOSTIC_VERSIONS) + " |")
    lines += ["", "## Q3. Probability that one mutation + repair improves the saved stagnated (1+1) solution", "",
              "| Case | Gap of probed point | " + " | ".join(f"σ = {s:.0e}" for s in PROBE_STEP_SIZES) + " | Same probe at reference optimum (max) |",
              "|---|---|" + "---|" * len(PROBE_STEP_SIZES) + "---|"]
    for name, q3 in report["q3"].items():
        lines.append(f"| {name} | {q3['gap_of_probed_point_percent']:.1f} % | " + " | ".join(f"{p:.3f}" for p in q3["probe"])
                     + f" | {q3['max_at_reference_optimum']:.3f} |")
    lines += ["", "3,000 samples per σ (standard error ≤ 0.009). The 1/5 rule stops shrinking σ only where the success rate "
              "reaches 0.2.", "",
              "## Q4. Step-size adaptation vs high-dimensional difficulty (mean gap to the reference optimum)", "",
              "| Case | n | (1+1) as specified | (1+1) with collapse prevented (best of 3 diagnostic versions) "
              "| Part of the gap removed by preventing the collapse | Population ES (saved final runs) |",
              "|---|---|---|---|---|---|"]
    for name, q4 in report["q4"].items():
        removed = 100 * (q4["specified"] - q4["best_without_collapse"]) / q4["specified"]
        lines.append(f"| {name} | {q4['n_assets']} | {q4['specified']:.2f} % | {q4['best_without_collapse']:.2f} % | "
                     f"{removed:.0f} % | {q4['population_es_saved']:.2f} % |")
    lines += ["", "Caveats: the datasets differ in more than their size; the best of three diagnostic versions is selected "
              "after seeing the results (optimistic); 5 seeds per setting; the population-ES column uses the final seeds 0–9."]
    (OUTPUT_FOLDER / "one_plus_one_diagnostics.md").write_text("\n".join(lines) + "\n")
    print(f"Saved {OUTPUT_FOLDER / 'one_plus_one_diagnostics.md'}")


if __name__ == "__main__":
    main()
