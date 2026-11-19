# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Portfolio return, variance (the objective), feasibility repair and feasibility checking.

The optimisation model (assignment, "Optimization Model")
--------------------------------------------------------
A portfolio is a weight vector w = (w_1, ..., w_n): w_i is the FRACTION of the budget put into
asset i. Example: w = (0.5, 0.3, 0.2) means 50 %, 30 % and 20 % of the money.

    minimise    V(w) = w^T Sigma w          (portfolio variance = risk)
    subject to  w_i >= 0                     (no negative investments: "long-only")
                sum_i w_i = 1                (the whole budget is used)
                R(w) = r^T w >= R_min        (expected return at least the target)

How the ES handles the constraints: "repair"
--------------------------------------------
Mutation adds random numbers to the weights, so a raw candidate z can have negative weights,
weights that do not sum to 1, or too little return. Instead of throwing such candidates away,
every candidate is REPAIRED into a feasible portfolio before it is evaluated
(assignment, "Constraint Handling & Feasibility Repair"):

    Step 1  project z onto the probability simplex  -> q  (non-negative, sums to 1)
    Step 2  if q's return is too low, move q in a straight line towards the highest-return
            asset until the return is exactly R_min                        -> w

Because every evaluated portfolio is feasible, the ES can simply compare variances.
"""

import numpy as np

# Numerical tolerances from the assignment for every final reported solution.
FEASIBILITY_TOLERANCE = 1e-8


def expected_return(weights, mean_returns):
    """
    R(w) = r^T w = sum_i r_i * w_i : the weighted average of the asset returns.

    Example (assignment): r = (0.02, 0.06, 0.10), w = (0.5, 0.3, 0.2)
    -> 0.5*0.02 + 0.3*0.06 + 0.2*0.10 = 0.048, i.e. 4.8 %.
    """
    return float(mean_returns @ weights)


def portfolio_variance(weights, covariance):
    """
    V(w) = w^T Sigma w = sum_i sum_j w_i * w_j * Sigma_ij : the OBJECTIVE (lower = less risk).

    Why this measures risk: the diagonal terms w_i^2 * s_i^2 are each asset's own fluctuation;
    the off-diagonal terms w_i * w_j * s_i * s_j * C_ij add (C > 0) or cancel (C < 0) fluctuation
    depending on whether two assets tend to move together. Spreading money over assets that do
    not move together lowers V: this is diversification.

    Example (assignment, zero correlations so only the diagonal counts): s = (0.1, 0.2, 0.3),
    w = (0.5, 0.3, 0.2) -> 0.25*0.01 + 0.09*0.04 + 0.04*0.09 = 0.0097.

    The code first computes Sigma @ w (a vector), then the dot product with w.
    """
    return float(weights @ (covariance @ weights))


def project_onto_simplex(z):
    """
    Step 1 of the repair: the closest point to z (in straight-line distance) that has
    non-negative entries summing to 1. That set of points is the "probability simplex".

    Formula from the assignment: q_i = max(z_i - theta, 0), with theta chosen so that sum q = 1.
    In words: shift every weight down (or up) by the same amount theta and cut negative
    results to 0; theta is the one shift that makes the result sum to exactly 1.

    How theta is found (standard sorting method, Duchi et al. 2008; also Held et al. 1974):
      1. Sort z from largest to smallest: u_1 >= u_2 >= ... >= u_n.
      2. For k = 1..n compute the candidate shift t_k = (u_1 + ... + u_k - 1) / k. This is the
         shift that would make the k largest entries sum to 1 if exactly those k stayed positive.
      3. Let rho be the LARGEST k for which u_k - t_k > 0, i.e. the k-th largest entry is still
         positive after shifting by t_k. Then theta = t_rho.
      4. q = max(z - theta, 0).

    Worked example: z = (0.3, 0.2, -0.5)
      sorted u = (0.3, 0.2, -0.5), cumulative sums (0.3, 0.5, 0.0)
      t_1 = (0.3 - 1)/1 = -0.7    u_1 - t_1 = 1.0  > 0
      t_2 = (0.5 - 1)/2 = -0.25   u_2 - t_2 = 0.45 > 0
      t_3 = (0.0 - 1)/3 = -0.333  u_3 - t_3 = -0.167 (not > 0)
      rho = 2, theta = -0.25  ->  q = (0.55, 0.45, 0)   (sums to 1, non-negative)

    Parameters
    ----------
    z : (n,) array, any real numbers

    Returns
    -------
    (n,) array q with q_i >= 0 and sum(q) = 1 (up to floating-point rounding).
    """
    z = np.asarray(z, dtype=float)
    sorted_descending = np.sort(z)[::-1]
    cumulative_sums = np.cumsum(sorted_descending)
    k_values = np.arange(1, z.size + 1)
    candidate_shifts = (cumulative_sums - 1.0) / k_values
    still_positive = sorted_descending - candidate_shifts > 0
    # still_positive is True for k = 1..rho and False afterwards; rho is the last True position.
    rho = int(np.nonzero(still_positive)[0][-1]) + 1
    theta = candidate_shifts[rho - 1]
    return np.maximum(z - theta, 0.0)


def repair_portfolio(z, mean_returns, min_return, best_asset_index):
    """
    Turn any candidate vector z into a feasible portfolio w (assignment Steps 1 and 2).

    Step 1: q = simplex projection of z (non-negative, sums to 1).
    Step 2: if R(q) >= R_min, q is already feasible: w = q.
            Otherwise mix q with the single best-return asset j (e_j = all money in asset j):
                beta = (R_min - R(q)) / (r_max - R(q))
                w = (1 - beta) * q + beta * e_j

    Why this works: return is linear, so R(w) = (1 - beta) R(q) + beta r_max
    = R(q) + beta (r_max - R(q)) = R(q) + (R_min - R(q)) = R_min exactly. beta is between 0 and 1
    (because R(q) < R_min <= r_max), so w is a weighted average of two portfolios that are both
    non-negative and sum to 1, and therefore w is too. The repair changes q as little as needed:
    it moves just far enough towards the best asset to reach the target.

    Example: r = (0.02, 0.06, 0.10), R_min = 0.04, q = (0.8, 0.2, 0.0) -> R(q) = 0.028 < 0.04.
             j = asset 3 (r_max = 0.10), beta = (0.04 - 0.028) / (0.10 - 0.028) = 1/6,
             w = 5/6 * (0.8, 0.2, 0) + 1/6 * (0, 0, 1) = (0.6667, 0.1667, 0.1667), R(w) = 0.04.

    Returns
    -------
    (n,) array w : feasible portfolio (within floating-point rounding).
    """
    q = project_onto_simplex(z)
    return_of_q = expected_return(q, mean_returns)
    if return_of_q >= min_return:
        return q
    max_asset_return = mean_returns[best_asset_index]
    beta = (min_return - return_of_q) / (max_asset_return - return_of_q)
    w = (1.0 - beta) * q
    w[best_asset_index] += beta          # adding beta * e_j only changes entry j
    return w


def feasibility_violations(weights, mean_returns, min_return, tolerance=FEASIBILITY_TOLERANCE):
    """
    Check the assignment's numerical tolerances and return a list of violated rules (empty = feasible).

        w_i >= -1e-8              for every i
        |sum(w) - 1| <= 1e-8
        R(w) >= R_min - 1e-8

    Tolerances are needed because computers round decimal numbers: a sum that should be exactly
    1 may come out as 0.9999999999999999.
    """
    violations = []
    if np.min(weights) < -tolerance:
        violations.append(f"negative weight {np.min(weights):.3e}")
    if abs(np.sum(weights) - 1.0) > tolerance:
        violations.append(f"weights sum to {np.sum(weights):.12f}")
    portfolio_return = expected_return(weights, mean_returns)
    if portfolio_return < min_return - tolerance:
        violations.append(f"return {portfolio_return:.10f} below target {min_return:.10f}")
    return violations


def is_feasible(weights, mean_returns, min_return, tolerance=FEASIBILITY_TOLERANCE):
    """True if the portfolio satisfies all three tolerance rules."""
    return not feasibility_violations(weights, mean_returns, min_return, tolerance)
