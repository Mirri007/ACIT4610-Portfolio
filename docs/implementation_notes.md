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

### 6. Choice of BA settings: what was done, in the order it happened

The assignment leaves the BA settings to us ("Choose and record the BA settings"). All steps took
place on 2026-11-19, in this order.

**Step 1: initial proposal (no data).** Before any code existed, setting A (n=50, m=10, e=3,
nep=40, nsp=20) was proposed as a generic starting point.

**Step 2: timing check.** After implementation, setting A was run once on eil51 and once on ch150,
both neighbourhoods, with **seed 0**, to measure runtime. Seed 0 is one of the experiment seeds.
The results (large gaps, e.g. about 200 % on ch150) were seen, and they prompted the decision to run a
pilot study instead of keeping A. They were not used to compare candidate settings, and A was not chosen.

**Step 3: original pilot (`experiments/tsp_pilot_settings.py`).** This step selected the settings.
- Four settings, A–D, from "many sites and scouts" to "few sites, many recruits per site".
- Instances eil51, kroA100 and ch150; both neighbourhoods; seeds 100–104 (not the experiment seeds).
- Each combination: the same 30,000-evaluation budget.
- Selection rule: the lowest average mean gap over all instances and both neighbourhoods.

| Setting | n | m | e | nep | nsp | Evals/iteration | Avg mean gap (swap) | Avg mean gap (reversal) | Avg mean gap (both) |
|---------|--:|--:|--:|----:|----:|----------------:|--:|--:|--:|
| A | 50 | 10 | 3 | 40 | 20 | 300 | 158.30 % | 103.15 % | 130.73 % |
| B | 20 | 5 | 2 | 50 | 20 | 175 | 118.99 % | 53.58 % | 86.29 % |
| C | 10 | 3 | 1 | 100 | 50 | 207 | 114.57 % | 45.50 % | 80.03 % |
| **D (chosen)** | **6** | **2** | **1** | **100** | **50** | **154** | **103.93 %** | **27.95 %** | **65.94 %** |

**Step 4: the 120 experiment runs** were done with D.

**Step 5: audit.** A review of the selection found these limitations of the original pilot:
- **Instance overlap.** It used 3 of the 6 assignment instances. The settings are independent of
  the evaluation *seeds* but not of the evaluation *instances*.
- **Fairness between the neighbourhoods.** Both neighbourhoods got identical candidates, instances,
  seeds and budgets, and D is best for each neighbourhood separately (table above). D increases the
  advantage of reversal over swap (from A to D, reversal's average gap falls by about 73 %, swap's by
  about 34 %). Reversal beats swap in all 12 pilot comparisons, though, so the conclusion "reversal
  is better" does not depend on the choice of settings.
- **D did not win everywhere.** It won 4 of 6 instance × neighbourhood combinations. On eil51, B won
  with swap (28.73 % vs D's 39.11 %) and C won with reversal (4.74 % vs D's 5.92 %). These
  differences are within about one standard deviation.
- **The selection rule matters.** The average mean gap uses the published optimal *lengths* to put
  instances on a common percentage scale. (The optimal *tours* were never used.) Ranking settings
  within each combination by mean tour length needs no optimal lengths. Under that rule, **C and D
  tie** (average rank 1.83 each). D's advantage comes from the larger instances.
- **D is the edge of the tested range.** It is the most concentrated candidate, so even more
  concentrated settings might do better. We stopped on purpose: fewer sites or no scouts would turn
  the BA into a plain hill climber.
- **Small study.** 4 candidates, 5 seeds.

**Step 6: robustness check (`experiments/tsp_robustness_pilot.py`), done AFTER steps 1–5.**
This check **did not select or change the settings**; it only tested whether D stays competitive
away from the assignment instances.
- Same four settings (imported from the original pilot script), both neighbourhoods, 30,000
  evaluations.
- **Instances not in the assignment set:** pr76, rat99 and ch130. Optimal lengths are from TSPLIB's
  best-known list; pr76 and ch130 are also confirmed by their published optimal tours in a test.
- **New seeds:** 200–204.

| Setting | Avg mean gap (swap) | Avg mean gap (reversal) | Avg mean gap (both) | Avg rank (1 = best) |
|---|--:|--:|--:|--:|
| A | 147.61 % | 92.37 % | 119.99 % | 4.00 |
| B | 116.81 % | 42.77 % | 79.79 % | 3.00 |
| C | 105.69 % | 35.29 % | 70.49 % | 2.00 |
| **D** | **90.04 %** | **21.01 %** | **55.52 %** | **1.00** |

Result: **D was best in every one of the 6 instance × neighbourhood combinations**, under both
selection rules and for each neighbourhood separately (full table: `results/tables/tsp_robustness_pilot.md`).

The difference from the original pilot is that D lost only on eil51, the smallest instance (51
cities), and by margins within the noise. The robustness instances have 76–130 cities. A plausible
explanation: on a small instance, 30,000 evaluations are enough for several settings to approach a
local optimum, so they finish close together. On larger instances the budget becomes the
bottleneck, and concentrating recruits on the best sites pays off. Limitation of the check: it
contains no instance as small as eil51/berlin52, so it does not test D in that range.

**Interpretation.** With 30,000 evaluations, concentrating recruited bees on a few good sites works
best. Fresh random tours are almost never competitive with an improved site, so evaluations spent on
many scouts or weak sites are mostly wasted. D still contains every BA component: an elite site, a
non-elite selected site and 4 random scouts per iteration. The settings are a reasonable, checked
choice, not a proven optimum.

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

---

## Problem 1B: Bees Algorithm for continuous functions

### 1. What is shared with Part A and what changes

The BA loop (`src/bees_algorithm.py`) and the evaluation tracker are **exactly the same code** as in
Part A. Only the problem-specific parts change (`src/bees_continuous.py`):

| | Part A (TSP) | Part B (functions) |
|---|---|---|
| Solution | permutation of cities | vector of D real numbers |
| Scout (random solution) | shuffle cities 2..n | each coordinate uniform in [lower, upper] |
| Recruit (neighbour) | one swap or one segment reversal | every coordinate + uniform change in ±10 % of (upper − lower), then clip to bounds |
| Constraint handling | not needed (moves keep a permutation) | clipping to the bounds |
| Objective | tour length (integer) | function value (real; minimum 0) |

### 2. Function validation

`tests/test_benchmark_functions.py` checks each function in three independent ways:
- at the known minimiser (0 within 1e-12);
- at hand-calculated points (e.g. Ackley at the all-ones vector = 20 − 20·e^−0.2 = 3.6253849…);
- against a line-by-line Python copy of the SFU R reference code
  (https://www.sfu.ca/~ssurjano/Code/spherefr.html, rosenr.html, rastrr.html, ackleyr.html, fetched
  2026-11-19), at 200 random points per function and dimension and at the bound corners.

The known minimising vectors are stored only in the tests, never in `src/`.

### 3. Choice of BA settings: what was done, in the order it happened (2026-11-19)

**Step 1: timing check (disclosure).** With provisional settings (D from Part A), all 8
function/dimension cases were run once with **seed 0**, an experiment seed, to measure runtime, and
the results were seen. This repeated the Part A mistake of looking at an experiment seed before
selection. It was not used in the selection below, but it happened before the settings were fixed.

**Step 2: pilot (`experiments/continuous_pilot_settings.py`), with the design and selection rule
written into the script before it was run.**
- The same candidates A–D as in Part A.
- Dimension **D = 20**, which is not an experiment dimension. All four functions are required, so
  only the dimension could differ.
- Seeds 100–104.
- Rule: lowest average rank over the four functions. Ranks are used because the functions have very
  different scales.

| Setting | Sphere | Rosenbrock | Rastrigin | Ackley | Average rank |
|---|---|---|---|---|---|
| A (n50 m10 e3 nep40 nsp20) | 2.52 (4) | 786.7 (2) | 145.2 (1) | 8.898 (4) | 2.75 |
| B (n20 m5 e2 nep50 nsp20) | 2.415 (2) | 807 (4) | 145.6 (2) | 8.587 (1) | 2.25 |
| **C (n10 m3 e1 nep100 nsp50), chosen** | 2.287 (1) | 695.7 (1) | 158.6 (4) | 8.684 (2) | **2.00** |
| D (n6 m2 e1 nep100 nsp50) | 2.443 (3) | 793.7 (3) | 148.1 (3) | 8.82 (3) | 3.00 |

(Mean final value over 5 seeds; rank within the function in brackets.)

**Limitation: the settings hardly matter here.** For every function, the difference between the
best and worst setting is at most about one standard deviation of the run-to-run variation:

| Function | Best − worst mean | Spread ÷ average std |
|---|---|---|
| Sphere | 0.233 | 0.88 |
| Rosenbrock | 111 | 0.59 |
| Rastrigin | 13.5 | 0.91 |
| Ackley | 0.311 | 1.03 |

So C was chosen correctly by the rule, but with 5 seeds the four settings cannot be told apart
statistically. This is different from Part A, where the differences were large. A likely reason is
section 5: the fixed ±10 % neighbourhood limits the precision of every setting in the same way.

Settings used: **n = 10, m = 3, e = 1, nep = 100, nsp = 50**, so 207 evaluations per iteration.
30,000 = 10 initial + 144 full iterations (29,808) + 182 in an incomplete 145th iteration
(100 + 50 + 32 recruits, no scouts).

### 4. Experiments and verification

80 runs (4 functions × D ∈ {10, 30} × seeds 0–9), each with exactly 30,000 evaluations.
- `make_continuous_tables` re-evaluates every saved vector.
- `audit_continuous_results` (no project imports) re-evaluates every vector with its own SFU
  transcription and recomputes the table.
- `audit_continuous_trace` rebuilds three real runs iteration by iteration and checks that every one
  of the 28,982 recruits per run is within ±10 % of the range of its site and inside the bounds.
- Seven deliberately planted bugs were all caught by the tests: wrong constants in each function,
  10 % of the upper bound instead of the range, no clipping, and one shared change for all coordinates.

### 5. Why no function gets close to 0: the fixed neighbourhood

The assignment fixes the neighbourhood: **every** coordinate changes by up to ±10 % of the range in
every recruit, and the patch never shrinks. Near a minimum, this makes further progress very
unlikely.

Example with Sphere:
- f(x + δ) = f(x) + 2·x·δ + |δ|².
- With each δ_i uniform in [−a, a] and a = 1.024, the expected size of the random step is
  E|δ|² = D·a²/3 ≈ 0.35·D, i.e. about 3.5 for D = 10 and 10.5 for D = 30.
- A neighbour is better only if 2·x·δ < −|δ|². Once f(x) is small compared with the step size,
  almost every random step lands further away.

The search therefore stalls at a level set by the patch size: mean Sphere results are 0.43 (D = 10)
and 5.5 (D = 30). Later BA versions shrink the neighbourhood as a site stops improving
("neighbourhood shrinking"), which would allow much more precision. That is not part of the
assignment's specified neighbourhood, so we did not use it.

The same reasoning explains why **D = 30 is much harder than D = 10** for every function: the step
changes all D coordinates at once, so its expected size grows with D, while the chance that all
coordinates move in helpful directions shrinks.

### 6. Runtime

Measured on an Apple M2 with Python 3.11.1: single runs took 0.21–1.12 s, group means (function × D) were 0.22–0.47 s, and the total search time for all 80 runs was 27.5 s.
