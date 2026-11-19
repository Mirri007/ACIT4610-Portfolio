# Implementation Notes

Design decisions, with the reasoning behind them. Useful when writing the report's
implementation section and when preparing for the oral exam.

---

## Problem 1A: Bees Algorithm for the TSP

### 1. Which BA version?

The basic Bees Algorithm of Pham et al. (2006):

1. n scouts are placed at random sites and evaluated.
2. Each iteration, the sites are ranked. The m best are *selected*, and the best e of those are *elite*.
3. Each elite site gets nep recruited bees and each other selected site gets nsp. Each recruited bee
   is one neighbourhood move away from its site.
4. Each selected site keeps the best of itself and its recruits (it never gets worse).
5. The other n − m bees become new random scouts.
6. Stop when the evaluation budget is used up.

**Not included:**
- *Neighbourhood shrinking* (`ngh`): in the TSP a move is "one swap / one reversal", so there is no
  numeric patch size to shrink.
- *Site abandonment*: this comes from later BA versions, not the 2006 paper the assignment cites.

### 2. One BA core for Part A and Part B

`src/bees_algorithm.py` contains the BA loop once. The problem-specific parts are passed in as
functions: "make a random solution" and "make a neighbour". This shows directly what changes
between discrete and continuous BA (representation, random solution, neighbourhood move) and what
stays the same (site selection, recruitment, retention, scouting, budget, best-so-far).

### 3. Evaluation counting

All candidates are scored through `EvaluationTracker.evaluate`. It:
- counts the evaluation, including rejected neighbours;
- updates the best-so-far;
- raises an error if the budget would be exceeded (a safety net).

The BA checks `budget_exhausted()` before every new candidate, so a run stops at exactly 30,000,
even in the middle of recruitment or scouting. Tests check:
- a budget that ends during recruitment;
- a budget that ends during scouting;
- a budget equal to the initial population;
- the full 30,000-evaluation run.

An independent counter inside the objective function confirms that no evaluation goes uncounted.

### 4. Best-so-far logging

Only the evaluations where the best value improved are stored. This is lossless: the value is
constant between improvements, so the full curve can be rebuilt with
`expand_history_to_every_evaluation`. The mean convergence curve is the average of the 10 rebuilt
curves at every evaluation number. That works because every run uses exactly the same budget.

### 5. Same seed → same initial population for both neighbourhoods

Each run uses one `numpy.random.default_rng(seed)`. The initial population is drawn before any
neighbourhood move is used, so for a given seed **swap and reversal start from identical scouts**.
The equal "Mean initial best" values for both versions in `tsp_summary.md` show this, and a test
checks it. Both versions therefore get the same start, the same settings and the same budget.

### 6. Choice of BA settings (pilot study)

The assignment leaves the BA settings to us. Four settings were compared with
`experiments/tsp_pilot_settings.py`:
- instances eil51, kroA100 and ch150;
- both neighbourhoods;
- seeds 100–104, which are **different from the experiment seeds 0–9**, so the reported results
  were not tuned on their own seeds.

Average mean gap over the pilot instances and both neighbourhoods (from `results/tables/tsp_pilot_settings.csv`):

| Setting | n | m | e | nep | nsp | Evals/iteration | Avg mean gap |
|---------|--:|--:|--:|----:|----:|----------------:|-------------:|
| A | 50 | 10 | 3 | 40 | 20 | 300 | 130.73 % |
| B | 20 | 5 | 2 | 50 | 20 | 175 | 86.29 % |
| C | 10 | 3 | 1 | 100 | 50 | 207 | 80.03 % |
| **D (chosen)** | **6** | **2** | **1** | **100** | **50** | **154** | **65.94 %** |

**Interpretation.** With only 30,000 evaluations, the search gains most from concentrating recruited
bees on a few good sites. Fresh random tours are almost never competitive with an improved site, so
evaluations spent on many scouts or many weak sites are mostly wasted. D still contains every BA
component: an elite site, a non-elite selected site and 4 random scouts per iteration. We did not
concentrate further, because a single site with no scouts would no longer be a Bees Algorithm, just
a hill climber.

**Limitations.**
- The pilot is small (5 seeds, 4 settings).
- D was not the best everywhere: on eil51 with swap, C was better (33.66 % vs 39.11 %).
- The settings are a reasonable choice, not a proven optimum.

### 7. Validation of distances

- The published optimal tour of each instance (TSPLIB `.opt.tour.gz`, stored only in `tests/`)
  reproduces the published optimal length exactly for all six instances (test
  `test_published_optimal_tours_have_published_lengths`).
- Rounding uses `floor(x + 0.5)`, not Python's `round()`, which rounds 2.5 down to 2.

### 8. Runtime

Measured on the development machine (Apple M2, Python 3.11.1): 0.52–1.15 s per run, with group
means (instance × neighbourhood) of 0.54–0.77 s. The total search time for all 120 runs was 71.2 s. Runtime hardly changes with instance size: per evaluation, the Python overhead
of creating and copying a candidate dominates the cost of summing 51–150 distances.

### 9. Reproducibility check (performed 2026-11-19)

1. Cloned the GitHub repository into an empty folder, created a fresh virtual environment, and ran
   `pip install -r requirements.txt` (numpy 1.26.4, matplotlib 3.9.2, pytest 8.3.3). All 94 tests passed.
2. Re-ran all 120 runs with `--overwrite`. All 120 result files were **identical** to the committed
   ones in every field except `runtime_seconds`.
3. The regenerated summary table differed only in the "Mean runtime" column.
