# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""Tests for the statistics helpers and the case-level (μ+λ) vs (μ,λ) analysis, with hand-worked examples."""

import pytest

from experiments.make_es_tables import plus_vs_comma_analysis
from src.portfolio_data import load_all_cases
from src.statistics_tools import bootstrap_mean_interval, exact_sign_flip_p_value, holm_adjusted


def test_sign_flip_example_from_docstring():
    # d = (1, 2, 3): only (+,+,+) and (-,-,-) reach |mean| = 2, so p = 2/8.
    assert exact_sign_flip_p_value([1, 2, 3]) == 0.25


def test_sign_flip_counts_ties_and_handles_zero():
    # d = (1, 1): patterns (+,+) and (-,-) give |mean| 1, the mixed ones 0 -> p = 2/4.
    assert exact_sign_flip_p_value([1, 1]) == 0.5
    # All differences 0: every pattern ties with the observed 0 -> p = 1.
    assert exact_sign_flip_p_value([0, 0, 0]) == 1.0


def test_sign_flip_smallest_possible_p_for_ten_values():
    # Ten positive values of different sizes: only the two all-same-sign patterns are as extreme -> 2/1024.
    assert exact_sign_flip_p_value(range(1, 11)) == pytest.approx(2 / 1024)


def test_sign_flip_rejects_too_many_values():
    with pytest.raises(ValueError):
        exact_sign_flip_p_value(range(21))


def test_holm_example_from_docstring():
    assert holm_adjusted([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_holm_caps_at_one_and_keeps_order():
    assert holm_adjusted([0.5, 0.9]) == pytest.approx([1.0, 1.0])
    assert holm_adjusted([0.001]) == pytest.approx([0.001])


def test_bootstrap_interval_is_reproducible_and_brackets_the_mean():
    values = [0.1, -0.2, 0.3, 0.05, -0.1, 0.2]
    first = bootstrap_mean_interval(values)
    assert first == bootstrap_mean_interval(values)              # fixed seed -> identical
    assert first[0] < sum(values) / len(values) < first[1]
    assert bootstrap_mean_interval([2.0] * 5) == (2.0, 2.0)       # no variation -> zero-width interval


def test_plus_vs_comma_analysis_on_synthetic_results():
    """Two cases where (μ+λ) is always exactly 1 % lower: every difference is -1 %."""
    cases = load_all_cases()[:2]
    results = []
    for case in cases:
        for seed in range(10):
            comma_variance = 0.001 * (1 + seed / 100)
            results.append({"case": case.name, "variant": "mu_comma_lambda", "seed": seed, "final_variance": comma_variance})
            results.append({"case": case.name, "variant": "mu_plus_lambda", "seed": seed,
                            "final_variance": comma_variance - 0.01 * 0.001 * 1.045})   # 1 % of mean(comma) = 1.045e-5
    analysis = plus_vs_comma_analysis(results, cases)
    for row in analysis["cases"]:
        assert row["mean_relative_difference"] == pytest.approx(-0.01)
        assert row["plus_lower_in"] == 10
        assert row["p_value"] == pytest.approx(2 / 1024)
    overall = analysis["overall"]
    assert overall["mean_relative_difference"] == pytest.approx(-0.01)
    assert overall["p_value"] == pytest.approx(0.5)               # only 2 case means: 2 of 4 patterns as extreme
    assert overall["cases_plus_lower"] == 2
