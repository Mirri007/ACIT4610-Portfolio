# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Loading the OR-Library portfolio datasets and building the 15 test cases (Problem 2).

The data
--------
Each file ``port<k>.txt`` (J.E. Beasley's OR-Library) describes n assets:

    line 1:            n                         number of assets
    next n lines:      mean_return  std_dev       one line per asset (asset 1, 2, ..., n)
    remaining lines:   i  j  correlation          one line per PAIR of assets

Example (port1.txt):  ``31``, then `` .001309 .043208`` (asset 1), ..., then `` 1 2 .562289``.

The pair lines list every pair once with i <= j, including i = j (an asset's correlation with
itself, always 1). So there are n(n+1)/2 pair lines: 496 for n = 31. Asset numbers start at 1,
Python indices at 0, so asset i is stored at index i - 1. Each correlation is stored in BOTH
C[i, j] and C[j, i], because correlation is symmetric (assignment: "Store that correlation in both").

From statistics to a covariance matrix
--------------------------------------
* r (mean returns): the expected return of each asset.
* s (standard deviations): how much each asset's return fluctuates.
* C (correlations): how two assets move together, from -1 (opposite) to +1 (together).
* Covariance:  Sigma_ij = s_i * s_j * C_ij   (assignment formula).
  On the diagonal, Sigma_ii = s_i^2 is each asset's own variance.

Return targets (assignment, "Return Target Calculation")
-------------------------------------------------------
* u = (1/n, ..., 1/n)       the equal allocation (same weight on every asset)
* R_eq = r^T u              its return (= the average of the mean returns)
* r_max = max_i r_i         the best single-asset mean return
* R_min(alpha) = (1 - alpha) * R_eq + alpha * r_max,   alpha in {0.25, 0.50, 0.75}
  alpha = 0 would be the equal-allocation return, alpha = 1 the best single asset. Larger alpha
  = a more demanding target, so fewer portfolios are allowed.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
SOURCE_URL = "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/{name}.txt"

# Dataset name -> (number of assets, number of correlation records), from the assignment table.
DATASETS = {
    "port1": (31, 496),
    "port2": (85, 3655),
    "port3": (89, 4005),
    "port4": (98, 4851),
    "port5": (225, 25425),
}
ALPHAS = [0.25, 0.50, 0.75]


class PortfolioFormatError(ValueError):
    """Raised when a dataset file does not have the expected structure."""


@dataclass
class PortfolioData:
    """
    One validated dataset.

    Attributes
    ----------
    name : str                    e.g. "port1"
    n_assets : int
    mean_returns : (n,) array     r
    std_devs : (n,) array         s
    correlation : (n, n) array    C, symmetric, ones on the diagonal
    covariance : (n, n) array     Sigma = s_i s_j C_ij
    """

    name: str
    n_assets: int
    mean_returns: np.ndarray
    std_devs: np.ndarray
    correlation: np.ndarray
    covariance: np.ndarray


@dataclass
class PortfolioCase:
    """
    One of the 15 test cases: a dataset plus a minimum required return.

    ``name`` follows the pattern used in the assignment, e.g. "port5_alpha050" for port5 with
    alpha = 0.50.
    """

    name: str
    data: PortfolioData
    alpha: float
    equal_allocation_return: float   # R_eq
    max_asset_return: float          # r_max
    best_asset_index: int            # j with r_j = r_max (0-based), used by the return repair
    min_return: float                # R_min(alpha)


def build_covariance(std_devs, correlation):
    """
    Sigma_ij = s_i * s_j * C_ij.

    ``np.outer(s, s)`` is the n x n table whose entry [i, j] is s_i * s_j; multiplying it
    element by element with C gives the covariance matrix in one step.
    """
    return np.outer(std_devs, std_devs) * correlation


def parse_portfolio_text(text, name="dataset", expected_assets=None, expected_records=None):
    """
    Parse and validate the text of one OR-Library portfolio file.

    The file is read LINE BY LINE (blank lines are ignored), and every line must have exactly
    the number of values its section requires. Checking the line structure, not just the total
    count of numbers, means a missing or extra value is reported at the line where it happens
    instead of silently shifting all following numbers. Validation checks:
      1. line 1 holds one positive whole number n (and matches ``expected_assets``);
      2. the next n lines each hold exactly 2 numbers (mean return, standard deviation),
         and all standard deviations are > 0;
      3. every remaining line holds exactly 3 values (i, j, correlation);
      4. the number of those lines is n(n+1)/2 (and matches ``expected_records``);
      5. every i, j is a whole number in 1..n, each unordered pair appears exactly once,
         and every pair (including i = j) is present;
      6. every correlation is in [-1, 1], and every diagonal correlation is exactly 1.

    Returns
    -------
    PortfolioData
    """
    lines = [line.split() for line in text.splitlines() if line.strip()]
    if not lines:
        raise PortfolioFormatError(f"{name}: file is empty")

    # Rule 1: number of assets.
    if len(lines[0]) != 1:
        raise PortfolioFormatError(f"{name}: line 1 must contain only the number of assets")
    try:
        n_assets = int(lines[0][0])
    except ValueError as error:
        raise PortfolioFormatError(f"{name}: first value must be the number of assets") from error
    if n_assets < 1:
        raise PortfolioFormatError(f"{name}: number of assets must be positive")
    if expected_assets is not None and n_assets != expected_assets:
        raise PortfolioFormatError(f"{name}: expected {expected_assets} assets, found {n_assets}")

    # Rule 2: n asset lines with (mean return, standard deviation).
    asset_lines = lines[1:1 + n_assets]
    if len(asset_lines) != n_assets:
        raise PortfolioFormatError(f"{name}: file ends before all {n_assets} asset lines")
    for asset_number, parts in enumerate(asset_lines, start=1):
        if len(parts) != 2:
            raise PortfolioFormatError(
                f"{name}: asset line {asset_number} must contain 'mean_return std_dev', found {parts}"
            )
    try:
        mean_returns = np.array([float(parts[0]) for parts in asset_lines])
        std_devs = np.array([float(parts[1]) for parts in asset_lines])
    except ValueError as error:
        raise PortfolioFormatError(f"{name}: asset lines must contain numbers") from error
    if np.any(std_devs <= 0):
        raise PortfolioFormatError(f"{name}: standard deviations must be positive")

    # Rule 3 and 4: correlation lines with exactly three values, right number of them.
    record_lines = lines[1 + n_assets:]
    for record_number, parts in enumerate(record_lines, start=1):
        if len(parts) != 3:
            raise PortfolioFormatError(
                f"{name}: correlation record {record_number} must contain 'i j correlation', found {parts}"
            )
    n_records = len(record_lines)
    if n_records != n_assets * (n_assets + 1) // 2:
        raise PortfolioFormatError(
            f"{name}: expected n(n+1)/2 = {n_assets * (n_assets + 1) // 2} correlation records, found {n_records}"
        )
    if expected_records is not None and n_records != expected_records:
        raise PortfolioFormatError(f"{name}: expected {expected_records} records, found {n_records}")

    # Rule 5 and 6: fill C, checking indices, duplicates and values.
    correlation = np.full((n_assets, n_assets), np.nan)   # NaN marks "not filled yet"
    for record, (i_token, j_token, value_token) in enumerate(record_lines):
        try:
            i, j, value = int(i_token), int(j_token), float(value_token)
        except ValueError as error:
            raise PortfolioFormatError(f"{name}: record {record + 1} is not 'integer integer number'") from error
        if not (1 <= i <= n_assets and 1 <= j <= n_assets):
            raise PortfolioFormatError(f"{name}: record {record + 1} has asset index outside 1..{n_assets}")
        if not -1.0 <= value <= 1.0:
            raise PortfolioFormatError(f"{name}: record {record + 1} has correlation {value} outside [-1, 1]")
        if i == j and value != 1.0:
            raise PortfolioFormatError(f"{name}: correlation of asset {i} with itself must be 1")
        row, column = i - 1, j - 1                      # 1-based asset numbers -> 0-based indices
        if not np.isnan(correlation[row, column]):
            raise PortfolioFormatError(f"{name}: pair ({i}, {j}) appears more than once")
        correlation[row, column] = value                # store in both places: C is symmetric
        correlation[column, row] = value
    if np.isnan(correlation).any():
        raise PortfolioFormatError(f"{name}: some asset pairs have no correlation record")

    return PortfolioData(
        name=name,
        n_assets=n_assets,
        mean_returns=mean_returns,
        std_devs=std_devs,
        correlation=correlation,
        covariance=build_covariance(std_devs, correlation),
    )


def load_dataset(name):
    """Load and validate one of the five assignment datasets, e.g. ``load_dataset("port1")``."""
    expected_assets, expected_records = DATASETS[name]
    text = (DATA_FOLDER / f"{name}.txt").read_text()
    return parse_portfolio_text(text, name, expected_assets, expected_records)


def case_name(dataset_name, alpha):
    """Consistent case identifier: ("port5", 0.50) -> "port5_alpha050"."""
    return f"{dataset_name}_alpha{int(round(alpha * 100)):03d}"


def build_case(data, alpha):
    """
    Create one test case: compute R_eq, r_max and R_min(alpha) for a dataset.

    ``np.argmax`` returns the FIRST index with the largest mean return. In all five datasets the
    largest mean return belongs to exactly one asset, so there is no ambiguity.
    """
    n = data.n_assets
    equal_weights = np.full(n, 1.0 / n)                     # u_i = 1/n
    equal_allocation_return = float(data.mean_returns @ equal_weights)
    best_asset_index = int(np.argmax(data.mean_returns))
    max_asset_return = float(data.mean_returns[best_asset_index])
    min_return = (1.0 - alpha) * equal_allocation_return + alpha * max_asset_return
    return PortfolioCase(
        name=case_name(data.name, alpha),
        data=data,
        alpha=alpha,
        equal_allocation_return=equal_allocation_return,
        max_asset_return=max_asset_return,
        best_asset_index=best_asset_index,
        min_return=float(min_return),
    )


def load_all_cases():
    """All 15 test cases, ordered port1_alpha025, port1_alpha050, ..., port5_alpha075."""
    cases = []
    for dataset_name in DATASETS:
        data = load_dataset(dataset_name)
        for alpha in ALPHAS:
            cases.append(build_case(data, alpha))
    return cases


def load_case(name):
    """Load one case by its name, e.g. ``load_case("port5_alpha050")``."""
    dataset_name, alpha_part = name.split("_alpha")
    alpha = int(alpha_part) / 100
    if dataset_name not in DATASETS or alpha not in ALPHAS:
        raise ValueError(f"Unknown case {name!r}")
    return build_case(load_dataset(dataset_name), alpha)
