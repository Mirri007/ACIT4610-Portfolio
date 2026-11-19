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

#### 5b. Empirical evidence (post-hoc diagnostics, added after the critical review)

`supplementary/continuous_diagnostics.py`, outputs in `results/supplementary/`. Diagnostic seeds
300–309; the required results are unchanged.

- **Frozen final solutions (compliant).** At the saved final vectors, one assignment neighbour
  improves with probability ≤ 0.0001 on average (max 0.0005). For Sphere and Ackley, the remaining
  RMS distance to the optimum per coordinate (Sphere D10: 0.205; Ackley D10: 1.37) is smaller than
  the neighbour's per-coordinate standard deviation (0.591; 3.78). For the unimodal functions,
  0.00–0.26 % of the total improvement happens after evaluation 15,000.
- **Settings sensitivity (compliant, D = 10 and 30).** Five settings, from explorative to extreme
  local search, differ mostly within about ±1.5 standard deviations of the current setting, without a
  consistent direction (best case: D on Rosenbrock D10, 0.77×; worst: many scouts on Sphere D30,
  1.29×, +3.9 sd). This confirms the pilot at the experiment dimensions: **the settings are not the
  bottleneck.**
- **Neighbourhood size (NOT assignment-compliant, explanatory only).** With ±1 % instead of ±10 %,
  Sphere improves about 87× (D10: 0.42 → 0.0048) and Rosenbrock D30 about 29×. But Ackley D10 gets
  worse (6.0 → 16.9) and Rastrigin D10 too (36.6 → 45.0): small steps cannot leave local minima or the
  flat outer region. **No single fixed size suits all functions**, which is the motivation for
  neighbourhood shrinking in later BA versions. The assignment fixes ±10 %, so this was not used.

**Conclusion:** the weak Part B results are explained mainly by the assignment-specified fixed
neighbourhood. No compliant change (settings) gives a consistent improvement, so the algorithm and
settings were kept unchanged.

### 6. Runtime

Measured on an Apple M2 with Python 3.11.1: single runs took 0.21–1.12 s, group means (function × D) were 0.22–0.47 s, and the total search time for all 80 runs was 27.5 s.

### 7. Reproducibility check (performed 2026-11-19)

1. Cloned the GitHub repository at commit `eef146c` into an empty folder, created a fresh virtual
   environment and installed `requirements.txt`. All 165 tests passed, and the single-run command
   from the README worked.
2. Re-ran all 80 Part B runs with `--overwrite`. All 80 results were identical to the committed ones
   in every field except `runtime_seconds`.
3. The regenerated summary table differed only in the runtime column.
4. All four audit scripts (`audit_tsp_results`, `audit_tsp_trace`, `audit_continuous_results`,
   `audit_continuous_trace`) returned exit code 0.

---

## Problem 2: Evolution Strategies for portfolio optimisation

### 1. Structure

- `portfolio_data.py`: parse and validate the files, build Σ, compute targets, define the 15 cases.
- `portfolio_model.py`: return, variance, simplex projection, repair, tolerances.
- `portfolio_evaluator.py`: repair + evaluate + count + archive, shared by all three variants.
- `es_one_plus_one.py` and `es_population.py`: the variants.
- `run_es.py`: one run → one result record.

As in Problem 1, all evaluations pass through a single method (`PortfolioEvaluator.evaluate`), so
counting, repair and archiving are identical for all three variants.

### 2. Data validation (2026-11-19)

All five files have exactly n(n+1)/2 correlation records with i ≤ j and no duplicates (the diagonal
is included and always 1). All correlations lie in [−1, 1]. The parser checks all of this **line by
line**.

A first token-based version accepted the file as one stream of numbers. A test exposed that a wrong
asset count then shifts every following number; it was still rejected, but with a misleading message.
The line-based version reports the exact faulty line.

All five covariance matrices are positive definite (smallest eigenvalue 6.05e−6 for port5), so no
portfolio can have negative variance. The highest-return asset is unique in every dataset, so the
return repair always uses a well-defined asset.

### 3. Design decisions and interpretations

- **The repaired portfolio is the individual.** The ES stores the repaired, feasible w (not the raw
  z) and mutates from it. This follows the assignment's wording: "add … to each weight and repair the
  child"; "retain the child". Every individual is therefore feasible. (Storing the raw z and repairing
  only for evaluation would be the alternative, sometimes called Baldwinian repair.)
- **Two *different* parents** are chosen for each child (uniformly, without replacement). With the
  same parent twice, recombination would just copy it.
- **Ties in survivor selection** keep the earlier individual (stable sort; parents before offspring).
- **Incomplete final batch.** 30,000 = 10 + 428 × 70 + 30. The 30 children of the last batch are
  evaluated and can enter the archive, but no survivor selection follows, because no further
  generation would use it.
- **Order of random draws per child:** choose parents, then Z₀, then Z_i (n numbers), then the
  mutation normals (n numbers). For the same seed, (μ+λ) and (μ,λ) draw identically during
  initialisation, so they start from the **same 10 parents**. The audit checks this. It makes the
  per-seed comparison between plus and comma *paired*.
- **Single-threaded BLAS in the experiment scripts.** In a preliminary measurement (seeds 900–904),
  OpenBLAS multi-threading made port5 runs about twice as slow and erratic (e.g. 4.77 s vs 2.66 s for
  repeats of the same run), with bit-identical results. Runtime is a reported metric compared between
  variants, so the experiments run single-threaded. Problem 1 is unaffected, because it uses no BLAS
  operations.

### 4. Seeds and tuning

- **Final seeds 0–9:** used only for the 450 reported runs.
- **Seeds 900–904:** used for the smoke test and timing measurements.
- **Seeds ≥ 1000:** used inside the tests.

No parameter was tuned: μ, λ, the initial step sizes, the step-size bounds, the 1/5-rule factors,
τ and τ' are all fixed by the assignment.

### 5. Verification

- **Tests:** 119 automated tests. Highlights:
  - the port1 checkpoint;
  - the assignment's A/B example;
  - variance against an explicit double loop;
  - simplex projection against an independent bisection method, plus the closest-point property;
  - repair feasibility on all 15 cases;
  - a rebuilt (1+1) step-size sequence, with the mutation noise standardised to N(0, 1);
  - rebuilt plus/comma selection;
  - Z₀ shared within a child, checked statistically through the real child-creation code.
- **Planted bugs:** 12 were planted. 11 were caught at first; the twelfth (Z₀ drawn per coordinate)
  exposed a missing test, which was added, and it is now caught.
- **Audits:**
  - `audit_es_results` (plain Python, no project code): all 450 runs and the 45 summary rows pass.
    It was shown to fail when a single weight is changed by 1e−7.
  - `audit_es_trace`: six full-budget runs (three variants × port5_alpha050 and port1_alpha075,
    seed 0) are rebuilt rule by rule and reproduce the saved results exactly.

### 6. Results in brief (details in `problem_2/results/tables/`)

- All 450 final allocations are feasible (10/10 valid runs in every case), and no invalid candidate
  was ever evaluated.
- **(1+1)-ES is worst in all 150 paired comparisons** against both population variants.
- **(μ+λ) vs (μ,λ):** the lowest mean in 7 vs 8 cases. With the **case as the statistical unit**
  (`es_plus_vs_comma.md`):
  - the mean of the 15 case-mean relative differences is +0.005 % (95 % bootstrap interval −1.31 %
    to +1.39 %);
  - an exact sign-flip test gives p = 0.994, so there is **no evidence of an overall difference**;
  - this does **not** show the variants are equivalent;
  - within cases the direction varies: (μ+λ) is lower on all three port4 cases, (μ,λ) on port5 at
    α = 0.25 and 0.50. After the Holm correction, only the two port1 cases with α ≥ 0.50 remain
    significant, and there the difference is 0.001 % (both reach the reference optimum).

  *Revision note:* the first version of this section reported a sign test over the 150 seed pairs
  (p = 0.165). It was replaced after the critical review (section "Post-hoc review" below), because
  pairs from the same case are not independent.
- **Convergence (port5_alpha050):**
  - The population variants improve steeply up to about 5,000 evaluations, then slowly.
  - (1+1) improves faster in the first ~1,500 evaluations but flattens by ~5,000.

### 7. Why the (1+1)-ES stagnates

#### 7a. Explanation as first written (before the post-hoc diagnostics), kept for the chronology

**Observations:**
- **Step size collapse.** Its success rate averaged 18.8 % (range 14.2–19.9 %), i.e. slightly
  *below* 1/5 throughout. So the 1/5 rule shrinks σ almost continuously, and 126/150 runs end with
  σ < 10⁻⁷ (the bound is 10⁻⁸).
- **Early stagnation.** Median: within 1 % of its final variance after 3,890 evaluations, yet tiny
  "improvements" continue until evaluation 29,997.
- **Not sparse.** Its final portfolios hold on average 67.6 assets with weight > 10⁻⁶, against
  14.7 / 14.6 for (μ+λ) / (μ,λ). The low-variance portfolios found by the population variants are
  sparse.

**Explanation (consistent with the data, not proven):**
- A weight reaches exactly 0 only when mutation pushes it below θ, so that the projection cuts it off.
- With one shared σ that has already shrunk, the many small weights can no longer be removed, and
  (1+1) stays in a too-diversified region.
- The repair also creates kinks: weights are cut at 0, and the return is pinned exactly at R_min in
  48/150 (1+1) runs versus 124/150 for (μ+λ). Near a kink, smaller steps do not raise the success
  rate towards 1/2 as they would on a smooth function. The 1/5 rule therefore keeps shrinking σ. This
  is a known weakness of the 1/5 success rule on constrained problems.
- The population ES has a separate step size per weight, recombination (averaging two sparse
  parents), and selection among 70 children. That lets it keep moving weights to 0.

#### 7b. Corrected explanation after the post-hoc diagnostics (`results/supplementary/one_plus_one_diagnostics.md`)

The diagnostics used diagnostic versions of (1+1) (a higher σ floor or a fixed σ) with seeds 300–304,
a probe of the success probability at the saved stagnated solutions, and the numerically verified
reference optima. **The problem is convex, so there are no local optima: the stagnation must come
from the search dynamics.** Two effects can be distinguished.

1. **Step-size adaptation (the 1/5 rule) — confirmed as a cause.**
   - At the stagnated solutions, the probability that one mutation improves stays **below 0.2 at
     every tested σ** (10⁻⁸ to 10⁻²; at most 0.181), on all five datasets. So the 1/5 rule is
     *forced* to keep shrinking σ.
   - On a smooth function with no active constraints, tiny steps would succeed about half the time;
     here 0.10–0.18. This is consistent with the kinks created by the repair.
   - Preventing the collapse removes **80–100 % of the gap** to the optimum for n ≤ 98 (e.g. port1:
     25.8 % → 0.02 %; port4: 94.0 % → 17.1 %). There, (1+1) then performs roughly like the
     population ES.
2. **Difficulty of searching with one isotropic step size in many dimensions — a second cause that
   dominates for n = 225.**
   - On port5, preventing the collapse removes only 38 % of the gap (122.6 % → 76.4 %, against
     15.0 % for the population ES).
   - At the stagnated port5 point (120 % above the optimum), not one of 3,000 mutations with
     σ ≥ 10⁻⁶ improved, although improving directions must exist in a convex problem. A single σ
     shared by 225 weights almost never produces one.
   - The population ES avoid this with per-weight step sizes, recombination and 70 children per
     generation.

**Caveats:**
- the datasets differ in more than their size;
- the "collapse prevented" value is the best of three diagnostic versions chosen afterwards (optimistic);
- 5 seeds per setting;
- the diagnostic versions are not the assignment's algorithm.

The sparsity observation (7a) still holds: the reference optima hold 3–27 assets, while (1+1) holds
about 20 (port1) to 111 (port5).

### 8. Limitations and weaknesses (to mention in the report)

1. **Absolute quality (originally missing, now supplementary).** The assignment limits conclusions
   to relative performance. After the critical review, numerically verified reference optima were
   added as **supplementary context** (`results/supplementary/reference_optima.md`): population ES
   0.00–18.4 % above the optimum on average, (1+1) 14.8–137.5 %. These numbers are context for
   stagnation and problem size, not a change to the required comparison.
2. **Interpretation choices** in section 3 (distinct parents, tie-breaking, Lamarckian repair, no
   selection after the last partial batch) could slightly change results under other readings.
3. **Comparisons with (1+1) are not paired.** (1+1) starts from a single random portfolio, while the
   population variants start from 10, so their initial best values differ. The 150/150 result makes
   this immaterial for the conclusion.
4. **Statistical comparison of plus and comma.** The original pooled sign test was replaced by a
   case-level analysis. Remaining limitations:
   - only 15 cases (fixed benchmarks, not a random sample) and 10 seeds per case;
   - approximate bootstrap intervals;
   - no equivalence margin defined, so equivalence cannot be claimed.
5. **Runtime** is from one machine (Apple M2), single-threaded. Absolute times will differ elsewhere;
   ratios between the variants are more meaningful.
6. **Feasible-run rate is 10/10 everywhere.** The repair guarantees feasibility by construction, so
   this column cannot discriminate between the variants.
7. **Historical data.** Results say nothing about future investment performance.

### 9. Reproducibility check (performed 2026-11-19)

1. Cloned the repository at commit `154bfe2` into an empty folder, created a fresh virtual
   environment and installed `requirements.txt`. All 119 Problem 2 tests passed, and the
   single-case command from the README worked.
2. Re-ran all 450 runs with `--overwrite`. All 450 results were identical to the committed ones in
   every field except `runtime_seconds`.
3. The regenerated comparison and analysis tables were identical.
4. `audit_es_results` and `audit_es_trace` both passed.


---

## Post-hoc review, diagnostics and supplementary analyses (2026-11-19, after all final experiments)

**Chronology.** All required experiments (120 + 80 + 450 runs) were finished, audited and reproduced
first. Then:
1. The student requested a critical review (S7). It used temporary scripts, and its findings are in
   `docs/critical_review.md`.
2. The student approved recommendations R1–R7 (S8). They were implemented as documented scripts
   with tests.

**No algorithm, setting, seed, final result or required figure was changed. No correctness error was
found.**

| Category | Purpose | Seeds | Location |
|---|---|---|---|
| Required experiments | Results of the portfolio | 0–9 | `problem_*/experiments/run_*`, `results/raw`, `tables`, `figures` |
| Parameter pilots (before the final runs) | Choose BA settings | 100–104 | `problem_1/experiments/*pilot*` |
| Post-hoc robustness check (Part A) | Check the chosen setting on other instances | 200–204 | `problem_1/experiments/tsp_robustness_pilot.py` |
| Post-hoc diagnostics | Explain results (1B neighbourhood, (1+1) stagnation) | 300–310 | `problem_*/supplementary/` |
| Supplementary analysis | Reference optima for Problem 2 (context only) | 310 (random check) | `problem_2/supplementary/reference_optima.py` |
| Preliminary checks (Problem 2) | Smoke test, timing | 900–904 | not saved as results |
| Tests | | ≥ 1000 (P2), various (P1) | `tests/` |

**What was added:**
- **R1:** case-level statistics for (μ+λ) vs (μ,λ) (`src/statistics_tools.py`, `es_plus_vs_comma.md`),
  replacing the pooled sign test.
- **R2:** numerically verified reference optima (`reference_optima.md`): KKT residuals ≤ 2.2e−16,
  relative duality gaps at rounding level (|gap| ≤ 1.6e−15, three of them slightly negative because of
  rounding). Not beaten by any ES run or 20,000 random portfolios. Not a formal proof (floating point).
- **R3:** (1+1) diagnostics (`one_plus_one_diagnostics.md`); the explanation was corrected in Problem 2 §7b.
- **R4:** Part B diagnostics (`continuous_diagnostics.md`; the non-compliant sweep is in
  `NONCOMPLIANT_neighbourhood_size_sweep.md`); see Problem 1B §5b.
- **R6:** paired swap-vs-reversal table (`tsp_paired_comparison.md`): reversal shorter in 60/60 pairs.
- **R7:** tests for all new analysis functions, among them:
  - the diagnostic (1+1) and the 10 % diagnostic neighbourhood reproduce the official algorithms
    exactly;
  - the KKT solve matches two analytically solved problems;
  - the certificate rejects a wrong support.

  Totals now: 171 tests (Problem 1) and 137 tests (Problem 2).
- **Fixes made during this work (test hygiene; no effect on any result):**
  - the new paired-comparison function averaged an empty list (a warning) when given results
    for only some instances; it now uses only the instances present;
  - running the tests with warnings treated as errors revealed that the independent parser in
    `problem_2/tests/test_portfolio_data.py` (written with the original Problem 2 code) left data
    files open (`ResourceWarning`); it now uses `with open(...)`.

  Both test suites now pass with `-W error`.

Dependency: SciPy 1.17.1 (`requirements-supplementary.txt`) is needed only to *find* the
reference-optimum candidates; all checks use NumPy.
