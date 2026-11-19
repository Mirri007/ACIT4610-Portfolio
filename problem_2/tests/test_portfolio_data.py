# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Tests for dataset parsing, covariance construction and return targets.

Includes the assignment's port1 parser checkpoint and an independent line-by-line parser that
does not share code with src/portfolio_data.py.
"""

import numpy as np
import pytest

from src.portfolio_data import (
    ALPHAS,
    DATA_FOLDER,
    DATASETS,
    PortfolioFormatError,
    build_case,
    case_name,
    load_all_cases,
    load_case,
    load_dataset,
    parse_portfolio_text,
)


def independent_parse(path):
    """Second, deliberately different parser: reads line by line, fills a dict of pairs."""
    lines = [line.split() for line in open(path) if line.strip()]
    n = int(lines[0][0])
    returns = [float(line[0]) for line in lines[1:n + 1]]
    stds = [float(line[1]) for line in lines[1:n + 1]]
    pairs = {}
    for line in lines[n + 1:]:
        i, j, c = int(line[0]), int(line[1]), float(line[2])
        pairs[(i, j)] = pairs[(j, i)] = c
    return n, returns, stds, pairs


TINY_TEXT = """ 2
 .01 .10
 .03 .20
 1 1 1.0
 1 2 .5
 2 2 1.0
"""


# ---------------------------------------------------------------- assignment checkpoint (port1)

def test_port1_checkpoint_values_from_the_assignment():
    data = load_dataset("port1")
    n = data.n_assets
    u = np.full(n, 1 / n)
    assert data.mean_returns @ u == pytest.approx(0.003504064516129, abs=1e-15)
    assert u @ data.covariance @ u == pytest.approx(0.001130937943724, abs=1e-15)
    case = build_case(data, 0.50)
    assert case.min_return == pytest.approx(0.007184532258065, abs=1e-15)


# ---------------------------------------------------------------- the five real datasets

@pytest.mark.parametrize("name", list(DATASETS))
def test_dataset_sizes_match_assignment_table(name):
    data = load_dataset(name)
    assert data.n_assets == DATASETS[name][0]
    assert data.mean_returns.shape == data.std_devs.shape == (data.n_assets,)
    assert data.covariance.shape == (data.n_assets, data.n_assets)


@pytest.mark.parametrize("name", list(DATASETS))
def test_parser_agrees_with_independent_parser(name):
    data = load_dataset(name)
    n, returns, stds, pairs = independent_parse(DATA_FOLDER / f"{name}.txt")
    assert n == data.n_assets
    assert np.array_equal(data.mean_returns, returns)
    assert np.array_equal(data.std_devs, stds)
    for (i, j), c in pairs.items():
        assert data.correlation[i - 1, j - 1] == c


@pytest.mark.parametrize("name", list(DATASETS))
def test_correlation_and_covariance_properties(name):
    data = load_dataset(name)
    C, S, s = data.correlation, data.covariance, data.std_devs
    assert np.array_equal(C, C.T)                          # symmetric
    assert np.all(np.diag(C) == 1.0)                       # each asset perfectly correlated with itself
    assert np.array_equal(S, S.T)
    assert np.allclose(np.diag(S), s ** 2, rtol=1e-15)     # diagonal = each asset's own variance
    # Positive definite: no portfolio can have negative variance.
    assert np.linalg.eigvalsh(S).min() > 0


def test_covariance_entry_by_hand_port1():
    # From port1.txt: asset 1 std .043208, asset 2 std .040258, correlation(1, 2) = .562289
    data = load_dataset("port1")
    assert data.covariance[0, 1] == pytest.approx(0.043208 * 0.040258 * 0.562289, rel=1e-15)
    assert data.covariance[1, 0] == data.covariance[0, 1]


# ---------------------------------------------------------------- cases and targets

def test_fifteen_cases_with_consistent_names():
    cases = load_all_cases()
    assert len(cases) == 15
    assert [case.name for case in cases[:3]] == ["port1_alpha025", "port1_alpha050", "port1_alpha075"]
    assert cases[-1].name == "port5_alpha075"
    assert case_name("port5", 0.5) == "port5_alpha050"


@pytest.mark.parametrize("case", load_all_cases(), ids=lambda case: case.name)
def test_target_formula_and_ordering(case):
    r = case.data.mean_returns
    assert case.equal_allocation_return == pytest.approx(r.mean(), rel=1e-14)
    assert case.max_asset_return == r.max()
    assert r[case.best_asset_index] == r.max()
    expected = (1 - case.alpha) * r.mean() + case.alpha * r.max()
    assert case.min_return == pytest.approx(expected, rel=1e-14)
    # The target lies strictly between the equal-allocation return and the best asset's return.
    assert case.equal_allocation_return < case.min_return < case.max_asset_return


def test_targets_increase_with_alpha():
    data = load_dataset("port2")
    targets = [build_case(data, alpha).min_return for alpha in ALPHAS]
    assert targets == sorted(targets)


def test_load_case_by_name():
    case = load_case("port5_alpha050")
    assert case.data.n_assets == 225 and case.alpha == 0.5
    with pytest.raises(ValueError):
        load_case("port6_alpha050")


# ---------------------------------------------------------------- broken files are rejected

def test_tiny_valid_file():
    data = parse_portfolio_text(TINY_TEXT)
    assert data.correlation.tolist() == [[1.0, 0.5], [0.5, 1.0]]
    assert data.covariance[0, 1] == pytest.approx(0.10 * 0.20 * 0.5)


@pytest.mark.parametrize(
    "broken_text, message",
    [
        ("", "empty"),
        ("two\n", "number of assets"),
        (" 2 3\n .01 .10\n", "line 1 must contain only"),
        # n says 3 assets but only 2 asset lines: the first correlation line is read as asset 3
        # and rejected because it has 3 values instead of 2.
        (TINY_TEXT.replace(" 2\n .01", " 3\n .01", 1), "asset line 3 must contain"),
        (TINY_TEXT.replace(" .03 .20", " .03"), "asset line 2 must contain"),
        (TINY_TEXT.replace(" .03 .20", " .03 abc"), "must contain numbers"),
        (TINY_TEXT.replace(" 2 2 1.0\n", ""), "n\\(n\\+1\\)/2"),
        (TINY_TEXT.replace(" 2 2 1.0\n", " 2 2\n"), "record 3 must contain"),
        (TINY_TEXT.replace(" 2 2 1.0\n", " 1 2 .5\n"), "more than once"),
        (TINY_TEXT.replace(" 2 2 1.0\n", " 3 3 1.0\n"), "outside 1..2"),
        (TINY_TEXT.replace(" 1 2 .5", " 1 2 1.5"), "outside \\[-1, 1\\]"),
        (TINY_TEXT.replace(" 2 2 1.0", " 2 2 0.9"), "must be 1"),
        (TINY_TEXT.replace(" .01 .10", " .01 -.10"), "positive"),
    ],
)
def test_broken_files_are_rejected(broken_text, message):
    with pytest.raises(PortfolioFormatError, match=message):
        parse_portfolio_text(broken_text)


def test_missing_pair_is_rejected():
    # Right number of records, but (1, 2) replaced by a duplicate diagonal -> pair (1, 2) missing.
    text = TINY_TEXT.replace(" 1 2 .5", " 1 1 1.0")
    with pytest.raises(PortfolioFormatError, match="more than once"):
        parse_portfolio_text(text)


def test_wrong_expected_counts_are_rejected():
    with pytest.raises(PortfolioFormatError, match="expected 3 assets"):
        parse_portfolio_text(TINY_TEXT, expected_assets=3)
    with pytest.raises(PortfolioFormatError, match="expected 4 records"):
        parse_portfolio_text(TINY_TEXT, expected_records=4)
