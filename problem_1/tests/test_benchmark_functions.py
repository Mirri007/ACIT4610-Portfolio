# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Tests for the Part B benchmark functions.

Three independent kinds of evidence:
  1. Known minimiser -> value 0 (within a small floating-point tolerance).
  2. Hand-calculated values at other points (worked out in the comments).
  3. Agreement with a line-by-line Python copy of the SFU reference R code, at many random
     points in both experiment dimensions. The copy below uses plain loops and Python's math
     module, deliberately written differently from the NumPy implementation.

The known minimising vectors appear ONLY here (never in src/), so the search cannot use them.
"""

import math

import numpy as np
import pytest

from src.benchmark_functions import BENCHMARK_FUNCTIONS, ackley, rastrigin, rosenbrock, sphere

# Known global minimisers (assignment: 0-vector for Sphere/Rastrigin/Ackley, 1-vector for Rosenbrock).
KNOWN_MINIMISER = {
    "sphere": lambda d: np.zeros(d),
    "rosenbrock": lambda d: np.ones(d),
    "rastrigin": lambda d: np.zeros(d),
    "ackley": lambda d: np.zeros(d),
}
TOLERANCE = 1e-12


# ---------------------------------------------------------------- SFU reference code, transcribed
# Source: https://www.sfu.ca/~ssurjano/Code/spherefr.html, rosenr.html, rastrr.html, ackleyr.html
def sfu_sphere(xx):                      # spheref <- function(xx) { sum(xx^2) }
    return sum(value ** 2 for value in xx)


def sfu_rosen(xx):                       # xi <- xx[1:(d-1)]; xnext <- xx[2:d]
    d = len(xx)                          # sum(100*(xnext-xi^2)^2 + (xi-1)^2)
    return sum(100 * (xx[i + 1] - xx[i] ** 2) ** 2 + (xx[i] - 1) ** 2 for i in range(d - 1))


def sfu_rastr(xx):                       # 10*d + sum(xx^2 - 10*cos(2*pi*xx))
    d = len(xx)
    return 10 * d + sum(value ** 2 - 10 * math.cos(2 * math.pi * value) for value in xx)


def sfu_ackley(xx, a=20, b=0.2, c=2 * math.pi):
    d = len(xx)
    sum1 = sum(value ** 2 for value in xx)
    sum2 = sum(math.cos(c * value) for value in xx)
    term1 = -a * math.exp(-b * math.sqrt(sum1 / d))
    term2 = -math.exp(sum2 / d)
    return term1 + term2 + a + math.exp(1)


SFU_REFERENCE = {"sphere": sfu_sphere, "rosenbrock": sfu_rosen, "rastrigin": sfu_rastr, "ackley": sfu_ackley}


# ---------------------------------------------------------------- 1. known minimisers

@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
@pytest.mark.parametrize("dimension", [10, 30])
def test_value_at_known_minimiser_is_zero(name, dimension):
    function = BENCHMARK_FUNCTIONS[name][0]
    assert abs(function(KNOWN_MINIMISER[name](dimension))) < TOLERANCE


def test_ackley_at_zero_is_only_rounding_error():
    # -20*exp(0) - exp(1) + 20 + e should be 0; floating point leaves about 4.4e-16.
    value = ackley(np.zeros(10))
    assert 0 <= value < 1e-15


# ---------------------------------------------------------------- 2. values worked out by hand

def test_sphere_by_hand():
    # 1^2 + 2^2 + (-3)^2 = 1 + 4 + 9 = 14
    assert sphere([1, 2, -3]) == 14


def test_rosenbrock_by_hand():
    # D = 2, x = (1, 2): 100*(2 - 1^2)^2 + (1 - 1)^2 = 100
    assert rosenbrock([1, 2]) == 100
    # D = 3, x = (0, 0, 0): two terms, each 100*0 + (1-0)^2 = 1 -> total 2 (= D - 1)
    assert rosenbrock([0, 0, 0]) == 2


def test_rastrigin_by_hand():
    # Whole-number coordinates: cos(2*pi*k) = 1, so each term is k^2 - 10, and 10*D cancels the -10s.
    # x = (1, 2): 20 + (1 - 10) + (4 - 10) = 5 = 1^2 + 2^2
    assert rastrigin([1, 2]) == pytest.approx(5, abs=1e-12)
    # x = (0.5,): cos(pi) = -1 -> 10 + 0.25 + 10 = 20.25
    assert rastrigin([0.5]) == pytest.approx(20.25, abs=1e-12)


def test_ackley_by_hand():
    # All coordinates 1: sqrt(mean(x^2)) = 1 and mean(cos(2*pi)) = 1, so
    # f = -20*exp(-0.2) - e + 20 + e = 20 - 20*exp(-0.2) = 3.6253849384403627
    assert ackley(np.ones(10)) == pytest.approx(20 - 20 * math.exp(-0.2), abs=1e-12)
    assert ackley(np.ones(30)) == pytest.approx(3.6253849384403627, abs=1e-12)


# ---------------------------------------------------------------- 3. agreement with SFU reference code

@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
@pytest.mark.parametrize("dimension", [10, 30])
def test_matches_sfu_reference_at_random_points(name, dimension):
    function, lower, upper = BENCHMARK_FUNCTIONS[name]
    rng = np.random.default_rng(2026)
    for _ in range(200):
        x = rng.uniform(lower, upper, size=dimension)
        expected = SFU_REFERENCE[name](list(x))
        assert function(x) == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
def test_matches_sfu_reference_at_bound_corners(name):
    # Every coordinate at the lower bound, then every coordinate at the upper bound.
    function, lower, upper = BENCHMARK_FUNCTIONS[name]
    for value in (lower, upper):
        x = np.full(10, value)
        assert function(x) == pytest.approx(SFU_REFERENCE[name](list(x)), rel=1e-12)


# ---------------------------------------------------------------- bounds and general properties

def test_bounds_match_the_assignment():
    assert BENCHMARK_FUNCTIONS["sphere"][1:] == (-5.12, 5.12)
    assert BENCHMARK_FUNCTIONS["rosenbrock"][1:] == (-5.0, 10.0)
    assert BENCHMARK_FUNCTIONS["rastrigin"][1:] == (-5.12, 5.12)
    assert BENCHMARK_FUNCTIONS["ackley"][1:] == (-32.768, 32.768)


@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
def test_values_are_non_negative_inside_bounds(name):
    # Global minimum 0 means no point can score below 0 (up to rounding).
    function, lower, upper = BENCHMARK_FUNCTIONS[name]
    rng = np.random.default_rng(5)
    for _ in range(500):
        assert function(rng.uniform(lower, upper, size=30)) > -1e-12


@pytest.mark.parametrize("name", list(BENCHMARK_FUNCTIONS))
def test_returns_a_plain_float(name):
    function = BENCHMARK_FUNCTIONS[name][0]
    assert isinstance(function(np.ones(10)), float)
