# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
The two neighbourhood moves used by recruited bees in the TSP version of the Bees Algorithm.

What is a "neighbourhood"?
--------------------------
In the Bees Algorithm, recruited bees search *near* a good site. For tours, "near" means
"reachable with one small change". A neighbourhood move is that small change. The assignment
asks for two BA versions that differ only in this move:

* **Swap**: pick two positions and exchange the cities in them.
      [1, 2, 3, 4, 5, 6]  swap positions 1 and 4  ->  [1, 5, 3, 4, 2, 6]
  This changes up to four legs of the tour (the legs into and out of both cities).

* **Segment reversal**: pick two positions and reverse the order of the cities between them
  (inclusive).
      [1, 2, 3, 4, 5, 6]  reverse positions 1..4  ->  [1, 5, 4, 3, 2, 6]
  Because distances are symmetric, the reversed middle part has the same internal length;
  only the two legs at the ends of the segment change. This is the classic "2-opt" move,
  which can remove a crossing between two legs of the route.

Rules from the assignment that both moves follow:
  * Exactly ONE randomly selected move creates each recruited neighbour.
  * City 1 (position 0) never moves, so positions are drawn from 1..n-1 only.
  * The result is still a valid permutation (both moves only rearrange cities).
  * The original site tour is not changed: each move works on a copy, because the same
    site is used again by the next recruited bee.
"""

import numpy as np


def pick_two_different_positions(number_of_cities, rng):
    """
    Choose two different positions uniformly at random from 1..n-1 and return them sorted.

    Position 0 is excluded because city 1 must stay first. The positions are drawn
    "without replacement", so they are always different and the move always changes the tour.

    Returns
    -------
    (int, int)
        ``first_position < second_position``.
    """
    first_position, second_position = rng.choice(
        np.arange(1, number_of_cities), size=2, replace=False
    )
    return int(min(first_position, second_position)), int(max(first_position, second_position))


def swap_move(tour, rng):
    """
    Return a NEW tour in which the cities at two random positions are exchanged.

    Parameters
    ----------
    tour : numpy.ndarray of int
        The site's tour (left unchanged).
    rng : numpy.random.Generator

    Returns
    -------
    numpy.ndarray
        A copy of ``tour`` with one swap applied; city 1 is still in position 0.
    """
    first_position, second_position = pick_two_different_positions(len(tour), rng)
    neighbour = tour.copy()  # copy so the site's own tour is not modified
    neighbour[first_position], neighbour[second_position] = (
        neighbour[second_position],
        neighbour[first_position],
    )
    return neighbour


def reversal_move(tour, rng):
    """
    Return a NEW tour in which the segment between two random positions is reversed.

    The segment includes both chosen positions. With positions i < j, the cities at
    i, i+1, ..., j are written back in the order j, j-1, ..., i.

    Parameters
    ----------
    tour : numpy.ndarray of int
        The site's tour (left unchanged).
    rng : numpy.random.Generator

    Returns
    -------
    numpy.ndarray
        A copy of ``tour`` with one segment reversal applied; city 1 is still in position 0.
    """
    first_position, second_position = pick_two_different_positions(len(tour), rng)
    neighbour = tour.copy()
    # Python slicing: [first : second + 1] covers both end positions; [::-1] reverses it.
    neighbour[first_position:second_position + 1] = neighbour[first_position:second_position + 1][::-1]
    return neighbour


# Lookup table so experiment scripts can choose the move by name ("swap" or "reversal").
NEIGHBOURHOOD_MOVES = {
    "swap": swap_move,
    "reversal": reversal_move,
}
