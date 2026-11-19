# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Small, transparent statistics helpers used to compare the (μ+λ)-ES and (μ,λ)-ES.

Why these methods?
------------------
We compare two variants on 15 test cases with 10 seeds each. The 150 seed pairs are NOT 150
independent observations: pairs from the same case share the same data and target, so they tend to
behave alike. Treating them as independent (as a plain sign test over 150 pairs does) overstates
the amount of evidence. Therefore:

* The main analysis treats the CASE as the statistical unit: each case contributes one number
  (its mean paired difference), and the 15 case numbers are tested together.
* Within one case, the 10 seed pairs ARE comparable repetitions (same data, same starting
  population for plus and comma), so a per-case test is valid, but with 15 such tests some
  "significant" results appear by chance; the Holm correction accounts for that.

The exact sign-flip (randomisation) test
----------------------------------------
Question: is the mean of the differences d_1..d_k larger in size than we would expect if the two
variants were equally good? If they were, each difference would be equally likely to be positive or
negative (it is a matter of luck which variant ends lower). So we list ALL 2^k ways of flipping the
signs of the differences, compute the mean for each, and count how often the absolute mean is at
least as large as the one we observed. That fraction is the p-value. With k = 15 cases there are
32,768 patterns and with k = 10 seeds 1,024, so the test is computed exactly, without approximations
and without assuming a normal distribution.
Assumption: under "no difference", each difference is symmetric around 0.

The percentile bootstrap confidence interval
--------------------------------------------
To show how precisely the mean difference is known, we resample the k values WITH replacement many
times, compute the mean each time, and take the 2.5th and 97.5th percentiles as an approximate 95 %
interval. With few units (15 cases, or 10 seeds) this interval is only approximate and tends to be a
little too narrow; it is reported as a description of uncertainty, not as an exact guarantee.

The Holm correction
-------------------
When m tests are run, the chance that at least one gives p < 0.05 by luck grows with m. Holm's method
sorts the p-values, multiplies the smallest by m, the next by m - 1, and so on, and keeps the result
non-decreasing (and at most 1). A corrected value below 0.05 then controls the chance of ANY false
"significant" result at 5 %.
"""

import itertools

import numpy as np


def exact_sign_flip_p_value(differences):
    """
    Two-sided exact sign-flip test of "mean difference = 0".

    Parameters
    ----------
    differences : sequence of numbers (at most about 20, because 2^k patterns are enumerated)

    Returns
    -------
    float : fraction of all 2^k sign patterns whose |mean| is >= the observed |mean|.

    Example: d = (1, 2, 3). Observed mean 2. Of the 8 sign patterns, only (+,+,+) and (-,-,-) give
    |mean| = 2; all others give smaller values. So p = 2/8 = 0.25.
    """
    d = np.asarray(differences, dtype=float)
    if d.size > 20:
        raise ValueError("too many values for exact enumeration")
    observed = abs(d.mean())
    patterns = np.array(list(itertools.product([1.0, -1.0], repeat=d.size)))
    flipped_means = np.abs((patterns * d).mean(axis=1))
    # A tiny tolerance so that patterns with exactly the observed |mean| are counted despite rounding.
    return float(np.mean(flipped_means >= observed - 1e-12 * max(1.0, observed)))


def bootstrap_mean_interval(values, n_resamples=20000, confidence=0.95, seed=12345):
    """
    Percentile bootstrap interval for the mean of ``values`` (fixed seed for reproducibility).

    Returns
    -------
    (lower, upper)
    """
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    resampled_means = rng.choice(values, size=(n_resamples, values.size), replace=True).mean(axis=1)
    tail = 100 * (1 - confidence) / 2
    lower, upper = np.percentile(resampled_means, [tail, 100 - tail])
    return float(lower), float(upper)


def holm_adjusted(p_values):
    """
    Holm-adjusted p-values, returned in the ORIGINAL order.

    Example: (0.01, 0.04, 0.03) -> sorted 0.01, 0.03, 0.04 -> multiplied by 3, 2, 1 -> 0.03, 0.06,
    0.04 -> made non-decreasing -> 0.03, 0.06, 0.06 -> original order (0.03, 0.06, 0.06).
    """
    p = np.asarray(p_values, dtype=float)
    m = p.size
    order = np.argsort(p)
    adjusted_sorted = np.minimum(1.0, np.maximum.accumulate((m - np.arange(m)) * p[order]))
    adjusted = np.empty(m)
    adjusted[order] = adjusted_sorted
    return adjusted.tolist()
