# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
The four continuous benchmark functions of Part B, with their search bounds.

What is a benchmark function?
-----------------------------
A mathematical function whose lowest point (global minimum) is already known. Optimisation
algorithms are tested on such functions because we can measure exactly how close they get.
Here every function has its global minimum value 0, so the final objective value of a run IS its
error (assignment: "the final objective value is the objective error").

Each function takes a vector x = (x_1, ..., x_D) of D real numbers ("decision variables") and
returns one number. D is the dimension (10 or 30 in the experiments). Each coordinate must stay
within the function's bounds [lower, upper].

Definitions follow the assignment and the Simon Fraser University (SFU) Virtual Library of
Simulation Experiments by Surjanovic and Bingham (https://www.sfu.ca/~ssurjano/). The tests
compare these functions with a line-by-line Python copy of SFU's R reference code.

Note: the known minimising vectors (all zeros / all ones) are deliberately NOT stored here.
They appear only in the tests, so the search code cannot use them (assignment: "Do not insert
known minimizing vectors into the search").
"""

import numpy as np


def sphere(x):
    """
    Sphere function:  f(x) = sum_{i=1}^{D} x_i^2

    The simplest benchmark: a smooth bowl with a single minimum ("convex, unimodal").
    Every coordinate contributes its square, so f is 0 only when all coordinates are 0.
    Bounds: x_i in [-5.12, 5.12]. Global minimum f(0, ..., 0) = 0.
    """
    x = np.asarray(x, dtype=float)
    return float(np.sum(x ** 2))


def rosenbrock(x):
    """
    Rosenbrock function:  f(x) = sum_{i=1}^{D-1} [ 100 (x_{i+1} - x_i^2)^2 + (1 - x_i)^2 ]

    Each term links two neighbouring coordinates. The minimum lies at the bottom of a long,
    narrow, curved valley (along x_{i+1} = x_i^2): finding the valley is easy, but moving
    along it to the minimum is hard, because steps that leave the valley are punished by the
    factor 100.
    Bounds: x_i in [-5, 10]. Global minimum f(1, ..., 1) = 0.

    How the code pairs neighbours: x[:-1] is (x_1, ..., x_{D-1}) and x[1:] is (x_2, ..., x_D),
    so position i of the two arrays holds x_i and x_{i+1}.
    """
    x = np.asarray(x, dtype=float)
    current = x[:-1]
    following = x[1:]
    return float(np.sum(100.0 * (following - current ** 2) ** 2 + (1.0 - current) ** 2))


def rastrigin(x):
    """
    Rastrigin function:  f(x) = 10 D + sum_{i=1}^{D} [ x_i^2 - 10 cos(2 pi x_i) ]

    A bowl (the x_i^2 part) covered with regular "egg-box" bumps (the cosine part). The cosine
    creates a local minimum near every point with whole-number coordinates, so there are very
    many local minima in which a search can get stuck ("multimodal").
    Why 10 D? cos(0) = 1, so at x = 0 the sum is -10 D; adding 10 D makes the minimum exactly 0.
    Bounds: x_i in [-5.12, 5.12]. Global minimum f(0, ..., 0) = 0.
    """
    x = np.asarray(x, dtype=float)
    dimension = x.size
    return float(10.0 * dimension + np.sum(x ** 2 - 10.0 * np.cos(2.0 * np.pi * x)))


def ackley(x):
    """
    Ackley function:

        f(x) = -20 exp( -0.2 sqrt( (1/D) sum x_i^2 ) ) - exp( (1/D) sum cos(2 pi x_i) ) + 20 + e

    Term 1 depends on the root-mean-square distance from 0: far away it is almost 0, so the
    outer region is nearly flat. Term 2 adds many small cosine bumps (local minima). Near the
    centre both terms fall steeply into a narrow hole. "+ 20 + e" (e = exp(1)) shifts the
    function so that the minimum is exactly 0: at x = 0, term 1 = -20 and term 2 = -e.
    Constants a = 20, b = 0.2, c = 2 pi as in the assignment and the SFU reference code.
    Bounds: x_i in [-32.768, 32.768]. Global minimum f(0, ..., 0) = 0
    (in floating point the result at 0 is about 4.4e-16 rather than exactly 0).
    """
    x = np.asarray(x, dtype=float)
    dimension = x.size
    root_mean_square = np.sqrt(np.sum(x ** 2) / dimension)
    mean_cosine = np.sum(np.cos(2.0 * np.pi * x)) / dimension
    return float(-20.0 * np.exp(-0.2 * root_mean_square) - np.exp(mean_cosine) + 20.0 + np.e)


# name -> (function, lower bound, upper bound). The same bounds apply to every coordinate.
BENCHMARK_FUNCTIONS = {
    "sphere": (sphere, -5.12, 5.12),
    "rosenbrock": (rosenbrock, -5.0, 10.0),
    "rastrigin": (rastrigin, -5.12, 5.12),
    "ackley": (ackley, -32.768, 32.768),
}
