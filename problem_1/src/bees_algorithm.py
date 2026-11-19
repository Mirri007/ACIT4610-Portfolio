# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
The Bees Algorithm (BA) of Pham et al. (2006), written once and shared by Part A and Part B.

Plain-English idea
------------------
Honey bees find food efficiently. A colony sends **scout bees** to random places. Scouts that
find good flower patches report back, and more bees are **recruited** to forage near the
best patches. The very best patches get the most bees. Meanwhile some bees keep scouting at
random, so the colony keeps discovering new areas.

Translated to optimisation:

======================  ==============================================================
Bee language            Optimisation meaning
======================  ==============================================================
flower patch / site     a candidate solution (a tour, or a vector of numbers)
nectar quality          objective value (lower tour length / function value = better)
scout bee               a completely random new solution (global exploration)
selected site           one of the m best solutions in the current population
elite site              one of the e best of those m (e <= m); gets the most bees
recruited bee           one neighbour of a site, made by one small random change
                        (local exploitation, the "neighbourhood search")
======================  ==============================================================

One iteration, step by step (Pham et al. 2006, basic version)
-------------------------------------------------------------
Population size n (number of scout bees), m selected sites, e elite sites, nep bees per elite
site, nsp bees per other selected site.

1. Rank the current n solutions from best to worst.
2. **Site selection**: the m best become selected sites; the top e of them are elite sites.
3. **Recruitment + local search**: each elite site receives nep recruited bees, each other
   selected site receives nsp. Each recruited bee is a neighbour of its site (one random
   move). Every neighbour is evaluated.
4. **Retained solutions**: for each selected site, keep the best of {the site itself and all
   its recruited neighbours}. A site is replaced only by a strictly better neighbour, so a
   site never gets worse.
5. **Global scouting**: the remaining n - m bees become fresh random scouts.
6. The new population = m retained site solutions + (n - m) new scouts.

Stopping: the run stops as soon as the evaluation budget (30,000) is used up, even in the
middle of step 3 or 5 ("allowing an incomplete final iteration").

Evaluations per full iteration = e * nep + (m - e) * nsp + (n - m).

Why one shared implementation?
------------------------------
The BA steps above do not depend on what a "solution" is. Only two operations do:
  * how to create a random solution (random tour vs. random vector), and
  * how to create a neighbour (swap/reversal vs. a small numerical change).
These are passed in as functions, which makes explicit what stays common between discrete and
continuous BA and what changes.
"""

from dataclasses import dataclass, asdict


@dataclass
class BeesSettings:
    """
    The Bees Algorithm parameters. Names follow Pham et al. (2006).

    Attributes
    ----------
    n_scouts : int
        n: population size (number of scout bees / sites kept in each iteration).
    n_selected_sites : int
        m: number of best sites that receive recruited bees (m <= n).
    n_elite_sites : int
        e: number of the selected sites treated as elite (e <= m).
    n_bees_elite : int
        nep: recruited bees sent to each elite site.
    n_bees_selected : int
        nsp: recruited bees sent to each non-elite selected site.
    max_evaluations : int
        Evaluation budget per run (30,000 in the assignment).
    """

    n_scouts: int
    n_selected_sites: int
    n_elite_sites: int
    n_bees_elite: int
    n_bees_selected: int
    max_evaluations: int = 30_000

    def check(self):
        """Raise ValueError if the settings break the BA's basic rules (e.g. more elite than selected sites)."""
        if not 1 <= self.n_elite_sites <= self.n_selected_sites <= self.n_scouts:
            raise ValueError("Settings must satisfy 1 <= e <= m <= n")
        if self.n_bees_elite < 1 or self.n_bees_selected < 1:
            raise ValueError("Each selected site needs at least one recruited bee")
        if self.max_evaluations < self.n_scouts:
            raise ValueError("The budget must at least cover the initial population")

    def evaluations_per_iteration(self):
        """e*nep + (m-e)*nsp + (n-m): evaluations used by one complete iteration."""
        return (
            self.n_elite_sites * self.n_bees_elite
            + (self.n_selected_sites - self.n_elite_sites) * self.n_bees_selected
            + (self.n_scouts - self.n_selected_sites)
        )

    def as_dict(self):
        """The settings as a plain dictionary, for saving with every run's results."""
        return asdict(self)


@dataclass
class Bee:
    """A solution together with its objective value (so it never has to be re-evaluated)."""

    solution: object
    value: float


def run_bees_algorithm(tracker, create_random_solution, create_neighbour, settings, rng):
    """
    Run the Bees Algorithm until the evaluation budget is used up.

    Parameters
    ----------
    tracker : EvaluationTracker
        Scores candidates, counts evaluations and records the best-so-far history.
        ALL evaluations go through ``tracker.evaluate``.
    create_random_solution : callable(rng) -> solution
        Makes one random solution (used for the initial population and for fresh scouts).
    create_neighbour : callable(solution, rng) -> new solution
        Applies one small random change to a copy of ``solution`` (local search).
        It must not modify ``solution`` itself.
    settings : BeesSettings
    rng : numpy.random.Generator
        The run's random generator, created from the run's seed. Every random choice in the
        run comes from this one generator, so the same seed always gives the same run.

    Returns
    -------
    dict
        ``initial_best_value``: best value in the initial population.
        ``iterations_started``: number of iterations begun (the last may be incomplete).
        The final best solution and history are read from ``tracker``.
    """
    settings.check()
    number_of_scouts_per_iteration = settings.n_scouts - settings.n_selected_sites

    # ---- Initialisation: n scout bees visit n random sites. -----------------------------
    # Each one costs one evaluation. The initial population counts toward the budget.
    population = []
    for _ in range(settings.n_scouts):
        solution = create_random_solution(rng)
        population.append(Bee(solution, tracker.evaluate(solution)))

    # The assignment asks us to record the best value of the initial population, so we can
    # measure how much the search improved on it.
    initial_best_value = tracker.best_value

    iterations_started = 0
    while not tracker.budget_exhausted():
        iterations_started += 1

        # ---- Step 1-2: rank sites and select the m best (the first e are elite). ---------
        # Python's sort is "stable": bees with equal values keep their previous order. This
        # makes tie-breaking deterministic, which helps reproducibility.
        population.sort(key=lambda bee: bee.value)
        selected_sites = population[:settings.n_selected_sites]

        new_population = []

        # ---- Step 3-4: recruit bees to each selected site and keep the best per site. ---
        for site_rank, site in enumerate(selected_sites):
            # Elite sites (rank 0 .. e-1) get more recruited bees than the other selected
            # sites. This spends more of the budget near the most promising solutions.
            if site_rank < settings.n_elite_sites:
                recruits_for_this_site = settings.n_bees_elite
            else:
                recruits_for_this_site = settings.n_bees_selected

            best_bee_at_site = site  # start from the site itself
            for _ in range(recruits_for_this_site):
                if tracker.budget_exhausted():
                    break  # stop exactly at the budget, even mid-iteration
                # Each recruit is ONE random move away from the ORIGINAL site (not from the
                # best neighbour found so far). All recruits explore around the same site.
                neighbour = create_neighbour(site.solution, rng)
                neighbour_value = tracker.evaluate(neighbour)
                # Keep the neighbour only if it is strictly better. A rejected neighbour
                # still used one evaluation (counted inside tracker.evaluate).
                if neighbour_value < best_bee_at_site.value:
                    best_bee_at_site = Bee(neighbour, neighbour_value)

            # The retained solution for this site moves into the next population.
            new_population.append(best_bee_at_site)

        # ---- Step 5: the remaining n - m bees scout new random sites. -------------------
        # These replace the population's worse solutions. They are the BA's global
        # exploration: a chance to find a better region than the current sites.
        for _ in range(number_of_scouts_per_iteration):
            if tracker.budget_exhausted():
                break
            solution = create_random_solution(rng)
            new_population.append(Bee(solution, tracker.evaluate(solution)))

        # ---- Step 6: the new population is used in the next iteration. -------------------
        population = new_population

    return {
        "initial_best_value": initial_best_value,
        "iterations_started": iterations_started,
    }
