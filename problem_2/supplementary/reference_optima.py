# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
SUPPLEMENTARY ANALYSIS (post hoc, 2026-11-19): exact minimum-variance portfolios for the 15 cases.

Status: not part of the required experiments. The assignment limits conclusions to the RELATIVE
performance of the ES variants. The reference optima below are reported only as CONTEXT for
interpreting stagnation and problem size; they change no ES result, setting or required figure.

The problem is a convex quadratic program (QP)
----------------------------------------------
    minimise w^T Sigma w   subject to   sum(w) = 1,   r^T w >= R_min,   w >= 0.
Sigma is positive definite (checked by the tests), so the objective is strictly convex and the
constraints are linear. For such a problem there are NO local optima besides the global one, and a
point that satisfies the Karush-Kuhn-Tucker (KKT) conditions is the global minimum (a standard
theorem of convex optimisation).

KKT conditions (with multipliers lambda for the budget, mu >= 0 for the return, nu_i >= 0 for w_i >= 0):
    stationarity          2 (Sigma w)_i - lambda - mu r_i - nu_i = 0       for every asset i
    primal feasibility    sum(w) = 1, r^T w >= R_min, w >= 0
    dual feasibility      mu >= 0, nu_i >= 0
    complementarity       mu (r^T w - R_min) = 0,  nu_i w_i = 0
In words: on the assets that are held, the "marginal risk" 2(Sigma w)_i is balanced exactly by the
budget and return prices; adding any asset that is not held would not reduce the variance.

How a solution is found and checked
-----------------------------------
1. Candidate: SciPy's SLSQP solver gives an approximate solution. It is only used to GUESS which
   assets are held ("support") and whether the return constraint is active; it is never trusted.
2. Exact solve: on that support, the KKT equations are linear, so they are solved exactly (up to
   rounding) with numpy.linalg.solve.
3. Check 1, KKT residuals: every condition is evaluated and the size of each violation is reported.
4. Check 2, dual lower bound: for ANY lambda, mu >= 0, nu >= 0 the Lagrangian dual function
       g = lambda + mu R_min - (1/4) c^T Sigma^{-1} c,   with c = lambda 1 + mu r + nu,
   is a LOWER BOUND on the true minimum ("weak duality"). We evaluate g at the computed
   multipliers (clipped to be non-negative, so the bound is valid). The true minimum therefore lies
   in [g, V(w)]; the width of that interval (the "duality gap") is reported. This check does not
   depend on the support guess being right.
5. Check 3: no ES run of the 450 final runs has a lower variance than the reference.
6. Check 4: no portfolio among 20,000 random feasible portfolios has a lower variance.

What this does and does not prove
---------------------------------
All checks run in floating-point arithmetic. They are a NUMERICAL VERIFICATION: the KKT residuals
and the duality gap are tiny (reported below), which gives very strong evidence that V(w) equals the
true minimum to about the printed precision. They are not a formal mathematical proof, because a
proof would require exact arithmetic (rounding in the residuals, the bound and Sigma^{-1} is not
accounted for rigorously). Statements in the documentation are phrased accordingly.

Run from the problem_2 folder (needs requirements-supplementary.txt, i.e. SciPy):
    python -m supplementary.reference_optima

Outputs (results/supplementary/):
    reference_optima.md / .csv   reference variance, support size, return-constraint status,
                                 KKT residuals, duality gap, independent checks, ES gaps per variant
    reference_optima_weights.json  the reference weights for every case
"""

import os

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[variable] = "1"

import csv  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

PROBLEM_FOLDER = Path(__file__).resolve().parent.parent
OUTPUT_FOLDER = PROBLEM_FOLDER / "results" / "supplementary"
CERTIFICATE_TOLERANCE = 1e-12   # allowed size of any KKT violation (absolute, in variance units)
SUPPORT_THRESHOLDS = (1e-6, 1e-7, 1e-8, 1e-5, 1e-4, 1e-9)


def solve_kkt_on_support(covariance, mean_returns, min_return, support, return_active):
    """
    Solve the KKT equations exactly for a given set of held assets ("support").

    Unknowns: the weights w_S of the held assets, lambda, and (if the return constraint is active) mu.
    Equations: 2 Sigma_SS w_S - lambda 1 - mu r_S = 0;  sum(w_S) = 1;  [r_S^T w_S = R_min].

    Returns
    -------
    (w, lambda, mu) with w a full-length vector (zeros outside the support); mu = 0 if inactive.
    """
    support = np.asarray(support)
    k = support.size
    size = k + 1 + (1 if return_active else 0)
    matrix = np.zeros((size, size))
    right_side = np.zeros(size)
    matrix[:k, :k] = 2.0 * covariance[np.ix_(support, support)]
    matrix[:k, k] = -1.0
    matrix[k, :k] = 1.0
    right_side[k] = 1.0
    if return_active:
        matrix[:k, k + 1] = -mean_returns[support]
        matrix[k + 1, :k] = mean_returns[support]
        right_side[k + 1] = min_return
    solution = np.linalg.solve(matrix, right_side)
    weights = np.zeros(mean_returns.size)
    weights[support] = solution[:k]
    lam = float(solution[k])
    mu = float(solution[k + 1]) if return_active else 0.0
    return weights, lam, mu


def kkt_residuals(covariance, mean_returns, min_return, weights, lam, mu):
    """
    Size of every KKT violation (0 = perfectly satisfied). nu is computed from stationarity.

    Returns a dict:
      stationarity_on_support   max |2(Sigma w)_i - lambda - mu r_i| over held assets
      negative_weight           max(0, -min w)
      budget                    |sum w - 1|
      return_shortfall          max(0, R_min - r^T w)
      negative_mu               max(0, -mu)
      negative_nu               max(0, -min nu_i) over assets NOT held
      return_complementarity    |mu (r^T w - R_min)|
    """
    nu = 2.0 * covariance @ weights - lam - mu * mean_returns
    held = weights > 0
    return {
        "stationarity_on_support": float(np.max(np.abs(nu[held]))),
        "negative_weight": float(max(0.0, -weights.min())),
        "budget": float(abs(weights.sum() - 1.0)),
        "return_shortfall": float(max(0.0, min_return - mean_returns @ weights)),
        "negative_mu": float(max(0.0, -mu)),
        "negative_nu": float(max(0.0, -nu[~held].min())) if (~held).any() else 0.0,
        "return_complementarity": float(abs(mu * (mean_returns @ weights - min_return))),
    }


def dual_lower_bound(covariance, mean_returns, min_return, weights, lam, mu):
    """
    Weak-duality lower bound g on the minimum variance (valid for any lambda, mu >= 0, nu >= 0).

    The multipliers from the KKT solve are used, with mu and nu clipped at 0 so that the bound is
    valid even if rounding made them slightly negative.
    """
    mu = max(mu, 0.0)
    nu = np.maximum(2.0 * covariance @ weights - lam - mu * mean_returns, 0.0)
    c = lam * np.ones(mean_returns.size) + mu * mean_returns + nu
    return float(lam + mu * min_return - 0.25 * c @ np.linalg.solve(covariance, c))


def is_certified(residuals, tolerance=CERTIFICATE_TOLERANCE):
    """True if every KKT violation is at most ``tolerance``."""
    return all(value <= tolerance for value in residuals.values())


def find_reference_optimum(case):
    """
    Candidate from SLSQP, exact KKT solve on the guessed support, and the KKT check.

    Several support thresholds and both return-constraint states are tried; the first combination
    whose exact KKT solution passes ``is_certified`` is returned. Raises RuntimeError if none passes.
    """
    from scipy.optimize import minimize   # imported here: SciPy is only needed for this analysis

    covariance, mean_returns, min_return = case.data.covariance, case.data.mean_returns, case.min_return
    n = case.data.n_assets
    constraints = [
        {"type": "eq", "fun": lambda w: w.sum() - 1.0, "jac": lambda w: np.ones(n)},
        {"type": "ineq", "fun": lambda w: mean_returns @ w - min_return, "jac": lambda w: mean_returns},
    ]
    candidate = minimize(lambda w: w @ covariance @ w, np.full(n, 1.0 / n), jac=lambda w: 2.0 * covariance @ w,
                         bounds=[(0.0, 1.0)] * n, constraints=constraints, method="SLSQP",
                         options={"maxiter": 10000, "ftol": 1e-15})
    for threshold in SUPPORT_THRESHOLDS:
        support = np.nonzero(candidate.x > threshold)[0]
        for return_active in (True, False):
            try:
                weights, lam, mu = solve_kkt_on_support(covariance, mean_returns, min_return, support, return_active)
            except np.linalg.LinAlgError:
                continue
            residuals = kkt_residuals(covariance, mean_returns, min_return, weights, lam, mu)
            if is_certified(residuals):
                variance = float(weights @ covariance @ weights)
                bound = dual_lower_bound(covariance, mean_returns, min_return, weights, lam, mu)
                return {"weights": weights, "variance": variance, "lambda": lam, "mu": mu,
                        "return_active": return_active, "support_size": int(support.size),
                        "residuals": residuals, "dual_bound": bound, "slsqp_variance": float(candidate.fun)}
    raise RuntimeError(f"{case.name}: no support guess passed the KKT check")


def random_feasible_check(case, reference_variance, samples=20000, seed=310):
    """Lowest variance among random repaired portfolios (must not be below the reference)."""
    from src.portfolio_model import portfolio_variance, repair_portfolio

    rng = np.random.default_rng(seed)
    lowest = np.inf
    for index in range(samples):
        scale = (0.001, 0.01, 0.1, 1.0)[index % 4]
        z = rng.normal(0.0, scale, size=case.data.n_assets) + rng.uniform(0, 1.0 / case.data.n_assets, case.data.n_assets)
        w = repair_portfolio(z, case.data.mean_returns, case.min_return, case.best_asset_index)
        lowest = min(lowest, portfolio_variance(w, case.data.covariance))
    return lowest


def main():
    from experiments.es_results_io import load_all_es_results, select_runs
    from src.portfolio_data import load_all_cases
    from src.run_es import VARIANTS

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    results = load_all_es_results()
    rows, weights_out = [], {}
    for case in load_all_cases():
        reference = find_reference_optimum(case)
        v_star = reference["variance"]
        es_variances = {v: [r["final_variance"] for r in select_runs(results, case.name, v)] for v in VARIANTS}
        lowest_es = min(min(values) for values in es_variances.values())
        lowest_random = random_feasible_check(case, v_star)
        row = {
            "case": case.name,
            "n_assets": case.data.n_assets,
            "reference_variance": v_star,
            "assets_held": reference["support_size"],
            "return_constraint_active": reference["return_active"],
            "max_kkt_residual": max(reference["residuals"].values()),
            "dual_lower_bound": reference["dual_bound"],
            "relative_duality_gap": (v_star - reference["dual_bound"]) / v_star,
            "lowest_es_variance_not_below_reference": lowest_es >= v_star * (1 - 1e-12),
            "lowest_random_variance_not_below_reference": lowest_random >= v_star * (1 - 1e-12),
        }
        for variant in VARIANTS:
            values = es_variances[variant]
            row[f"mean_gap_percent_{variant}"] = 100 * (np.mean(values) - v_star) / v_star
            row[f"best_gap_percent_{variant}"] = 100 * (min(values) - v_star) / v_star
        rows.append(row)
        weights_out[case.name] = [float(x) for x in reference["weights"]]
        print(f"{case.name}: V* = {v_star:.10e}, max KKT residual {row['max_kkt_residual']:.1e}, "
              f"relative duality gap {row['relative_duality_gap']:.1e}, checks "
              f"{row['lowest_es_variance_not_below_reference'] and row['lowest_random_variance_not_below_reference']}", flush=True)

    with open(OUTPUT_FOLDER / "reference_optima.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT_FOLDER / "reference_optima_weights.json").write_text(json.dumps(weights_out, indent=1))

    labels = list(VARIANTS.values())
    lines = [
        "# SUPPLEMENTARY: reference minimum-variance portfolios (post-hoc analysis, not a required result)",
        "",
        "Reference = exact KKT solution on the support suggested by SLSQP. **Numerically verified, not formally "
        "proven**: KKT residuals and the relative duality gap (distance between the reference variance and a "
        "weak-duality lower bound) are computed in floating point. Also checked: no final ES run and none of "
        "20,000 random feasible portfolios has a lower variance. Gaps are context for interpreting the ES results; "
        "the assignment's conclusions remain relative comparisons between the variants.",
        "",
        "| Case | n | Reference variance V* | Assets held | Return constraint active | Max KKT residual | Relative duality gap "
        "| Not beaten by ES / random | Mean gap " + " | Mean gap ".join(labels) + " | Best ES run gap |",
        "|---|---|---|---|---|---|---|---|" + "---|" * len(labels) + "---|",
    ]
    for row in rows:
        best_gap = min(row[f"best_gap_percent_{v}"] for v in VARIANTS)
        checks = "yes" if row["lowest_es_variance_not_below_reference"] and row["lowest_random_variance_not_below_reference"] else "NO"
        gap_cells = " | ".join(f"{row[f'mean_gap_percent_{v}']:.2f} %" for v in VARIANTS)
        lines.append(f"| {row['case']} | {row['n_assets']} | {row['reference_variance']:.10e} | {row['assets_held']} | "
                     f"{'yes' if row['return_constraint_active'] else 'no'} | {row['max_kkt_residual']:.1e} | "
                     f"{row['relative_duality_gap']:.1e} | {checks} | {gap_cells} | {best_gap:.4f} % |")
    lines += ["", "Gap = 100 × (V_ES − V*) / V*. Mean gap = gap of the mean final variance of the 10 runs."]
    (OUTPUT_FOLDER / "reference_optima.md").write_text("\n".join(lines) + "\n")
    print(f"Saved {OUTPUT_FOLDER / 'reference_optima.md'}")


if __name__ == "__main__":
    main()
