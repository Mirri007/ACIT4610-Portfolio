# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_development_log.md.
"""
Distances, tour length (the objective function) and tour validity for the TSP.

Key ideas
---------
* A *tour* is stored as a NumPy array of city **indices** (0-based). Index 0 is TSPLIB city 1.
  Example for 5 cities: ``[0, 3, 1, 4, 2]`` means city 1 -> 4 -> 2 -> 5 -> 3 -> back to city 1.
* The assignment fixes city 1 as the first city. So every tour starts with index 0, and
  the return to city 1 is *not* stored as an extra entry: it is added only when calculating
  the length (the "return leg") and when drawing the route.
* Distances follow the TSPLIB EUC_2D rule: Euclidean distance rounded to the nearest whole
  number, with each edge rounded *before* the edges are added together.
"""

import numpy as np


def compute_distance_matrix(coordinates):
    """
    Build the full table of rounded TSPLIB EUC_2D distances between all pairs of cities.

    Formula (assignment, from TSPLIB documentation section 2.1)::

        d_ij = floor( sqrt( (a_i - a_j)^2 + (b_i - b_j)^2 ) + 0.5 )

    where (a_i, b_i) are the coordinates of city i. Adding 0.5 and rounding down ("floor")
    rounds to the nearest whole number, with exact halves rounded up: 2.5 -> 3, 2.49 -> 2.

    Why not Python's built-in ``round()``? Because ``round(2.5)`` gives 2 ("banker's
    rounding": halves go to the nearest even number). That differs from TSPLIB and would
    make our tour lengths disagree with the published optimal lengths.

    Why compute a matrix once? Each run evaluates 30,000 tours of up to 150 edges. Looking up
    pre-computed distances is much faster than recomputing square roots every time, and it
    guarantees every evaluation uses exactly the same rounded values.

    Parameters
    ----------
    coordinates : numpy.ndarray, shape (n, 2)
        Row i holds the (x, y) coordinates of city index i.

    Returns
    -------
    numpy.ndarray of int64, shape (n, n)
        ``distances[i, j]`` is the rounded distance between city indices i and j.
        It is symmetric (d_ij = d_ji) and zero on the diagonal (d_ii = 0).
    """
    coordinates = np.asarray(coordinates, dtype=float)

    # Broadcasting trick, explained: coordinates[:, None, :] has shape (n, 1, 2) and
    # coordinates[None, :, :] has shape (1, n, 2). Subtracting them gives an (n, n, 2) array
    # whose entry [i, j] is (a_i - a_j, b_i - b_j), i.e. the difference for every pair at once.
    differences = coordinates[:, None, :] - coordinates[None, :, :]

    # Square both differences, add them, take the square root: plain Euclidean distance.
    euclidean = np.sqrt(np.sum(differences ** 2, axis=2))

    # TSPLIB rounding: add 0.5 then round down. Stored as whole numbers (int64), so tour
    # lengths are exact integers with no floating-point error when we add edges together.
    return np.floor(euclidean + 0.5).astype(np.int64)


def tour_length(tour, distances):
    """
    The objective function of Part A: total length of the closed tour.

    Formula (assignment)::

        L(pi) = sum_{i=1}^{n-1} d(pi_i, pi_{i+1})  +  d(pi_n, pi_1)

    The sum covers every leg from one city to the next, and the final term is the
    *return leg* from the last city back to the first (city 1).

    How the code does it: ``np.roll(tour, -1)`` shifts the tour one place to the left, moving
    the first city to the end. Example::

        tour               = [0, 3, 1, 4, 2]
        np.roll(tour, -1)  = [3, 1, 4, 2, 0]

    Pairing the two arrays position by position gives the legs (0,3), (3,1), (1,4), (4,2) and
    (2,0). The last pair is exactly the return leg. ``distances[tour, next_cities]`` looks up
    all those leg lengths at once, and ``.sum()`` adds them. Each leg is already rounded
    (see :func:`compute_distance_matrix`), so we round "each edge before adding".

    Parameters
    ----------
    tour : numpy.ndarray of int
        Permutation of city indices 0..n-1 (starting with 0).
    distances : numpy.ndarray, shape (n, n)
        Output of :func:`compute_distance_matrix`.

    Returns
    -------
    int
        Total tour length. Smaller is better (we are minimising).
    """
    next_cities = np.roll(tour, -1)
    return int(distances[tour, next_cities].sum())


def create_random_tour(number_of_cities, rng):
    """
    Create a uniformly random tour with city 1 (index 0) fixed in the first position.

    This is how scout bees are initialised (assignment: "Initialize scouts with uniformly
    shuffled permutations"). Only the cities after the fixed start are shuffled, so every
    ordering of cities 2..n is equally likely.

    Parameters
    ----------
    number_of_cities : int
    rng : numpy.random.Generator
        The run's random number generator. Using the run's own generator (created from its
        seed) is what makes every run reproducible.

    Returns
    -------
    numpy.ndarray of int64
        For example ``[0, 3, 1, 4, 2]`` for 5 cities.
    """
    other_cities = np.arange(1, number_of_cities)          # indices 1..n-1 (cities 2..n)
    shuffled_others = rng.permutation(other_cities)         # uniform random order
    return np.concatenate(([0], shuffled_others)).astype(np.int64)


def is_valid_tour(tour, number_of_cities):
    """
    Return True if ``tour`` visits every city exactly once and starts with city 1.

    The assignment requires us to "validate that every returned tour contains every city
    once". A valid tour must:
      * have exactly ``number_of_cities`` entries,
      * contain each index 0..n-1 exactly once (a permutation, no repeats, nothing missing),
      * begin with index 0, because city 1 is fixed as the starting city.
    """
    tour = np.asarray(tour)
    if tour.ndim != 1 or len(tour) != number_of_cities:
        return False
    if tour[0] != 0:
        return False
    # Sorting a permutation of 0..n-1 must give exactly [0, 1, ..., n-1].
    return bool(np.array_equal(np.sort(tour), np.arange(number_of_cities)))


def tour_to_city_ids(tour):
    """
    Convert 0-based indices to TSPLIB city ids (1-based) for saving and display.

    Example: ``[0, 3, 1]`` -> ``[1, 4, 2]``.
    """
    return [int(index) + 1 for index in tour]


def closed_route_city_ids(tour):
    """
    Return the route as TSPLIB city ids with city 1 appended at the end, for display only.

    The assignment says to append city 1 "only when displaying the closed route, not as a
    second entry in the permutation". Example: ``[0, 3, 1]`` -> ``[1, 4, 2, 1]``.
    """
    city_ids = tour_to_city_ids(tour)
    return city_ids + [city_ids[0]]
