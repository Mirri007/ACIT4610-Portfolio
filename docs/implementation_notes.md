# Implementation Notes

Technical design decisions, parameter selection, validation and key findings. Commands, settings
tables and file layouts are in the README files and are not repeated here.

## Kinds of runs and their seeds

| Kind | Purpose | Seeds |
|---|---|---|
| Required experiments | The reported results (120 TSP, 80 continuous, 450 ES runs; 30,000 evaluations each) | 0–9 |
| Parameter pilots | Choosing the BA settings, before the required runs | 100–104 |
| Robustness check (Problem 1A) | Re-checking the chosen BA setting on other instances, after the required runs | 200–204 |
| Post-hoc diagnostics and supplementary analyses | Explaining results; never part of the required results | 300–310 |
| Preliminary checks (Problem 2) | Smoke test and timing | 900–904 |
| Automated tests | | ≥ 1000 (Problem 2); various (Problem 1) |

---

## Problem 1: Bees Algorithm

### Algorithm
- **Version:** the basic Bees Algorithm of Pham et al. (2006).
  - n scouts; the m best sites are selected and the e best of those are elite.
  - Elite sites receive nep recruits, other selected sites nsp.
  - The remaining n − m bees are fresh random scouts.
  - Neighbourhood shrinking and site abandonment (later BA variants) are not used.
- **Retained solutions:** a site keeps the best of itself and its recruits, and is replaced only by a
  strictly better recruit. Each recruit is one neighbourhood move away from the *original* site.
- **One core for both parts:** `bees_algorithm.py` is shared. Only the random-solution and
  neighbour functions differ, which makes "what changes between discrete and continuous BA" explicit.
- **Evaluation counting:**
  - Every candidate passes through `EvaluationTracker.evaluate`. This includes the initial
    population, every recruit (accepted or rejected) and every scout.
  - The algorithm checks the budget before each candidate, so a run stops at exactly 30,000, even in
    the middle of an iteration.
- **Best-so-far log:** only the evaluations where the best value improved are stored. This is
  lossless, because the curve is constant between improvements. Mean convergence curves average the
  rebuilt curves at every evaluation number.
- **Fair comparison of the two neighbourhoods:** both use the same settings and seeds, and the
  initial population is drawn before any move is used, so for each seed swap and reversal start from
  the identical population.

### Part A (TSP): validation
- Distances follow TSPLIB EUC_2D: floor(√(…) + 0.5), each edge rounded before summing, with the
  return edge included. Python's `round()` is not used, because it rounds 2.5 to 2.
- The published optimal tours (stored only in `tests/`, never read by the algorithm) reproduce the
  published optimal lengths exactly for all six instances.

### Part A: parameter selection
Four candidate settings (A–D) were compared in a pilot on eil51, kroA100 and ch150. Each was run
with both neighbourhoods, seeds 100–104 and 30,000 evaluations. The selection rule was the lowest
average mean gap.

| Setting | n | m | e | nep | nsp | Evaluations / iteration | Avg mean gap |
|---|---|---|---|---|---|---|---|
| A | 50 | 10 | 3 | 40 | 20 | 300 | 130.73 % |
| B | 20 | 5 | 2 | 50 | 20 | 175 | 86.29 % |
| C | 10 | 3 | 1 | 100 | 50 | 207 | 80.03 % |
| **D (chosen)** | **6** | **2** | **1** | **100** | **50** | **154** | **65.94 %** |

D was best for each neighbourhood separately. With a 30,000-evaluation budget, concentrating
recruits on few sites pays off, because random tours are rarely competitive. D still has an elite
site, a second selected site and 4 scouts per iteration.

**Limitations:**
- The pilot used 3 of the 6 test instances, so it is independent of the evaluation seeds but not of
  the instances.
- Ranked by placement instead of average gap, C and D tie.
- D is the edge of the tested range.
- Before the pilot, setting A was timed once with seed 0 (an evaluation seed). These results were not
  used to compare settings.

**Robustness check (after the required runs; not used for selection):** the same four settings on
pr76, rat99 and ch130 with seeds 200–204. D was best in all 6 instance × neighbourhood combinations
(average gap 55.52 % vs 119.99 % for A). The check contains no instance as small as eil51.

### Part A: key findings
- **Segment reversal beats swap on every instance,** and ended shorter in **60 of 60 paired runs**
  (same seed, same initial population).
  - Reversal changes 2 edges and can remove crossings (2-opt).
  - Swap changes up to 4 edges.
- **The gap grows with instance size** (reversal: 5.07 % on eil51 → 65.07 % on ch150).
- **ch150 is budget-limited:** its convergence curve is still falling at 30,000 evaluations.
- Best berlin52 tour: 7,670 (gap 1.70 %), reversal, seed 7. No run found an optimal tour.

### Part B (continuous): design and validation
- **Representation:** real vectors. Scouts are uniform within the bounds.
- **Neighbourhood:** every coordinate + U(−10 %, +10 %) of (upper − lower), then clipped to the
  bounds (the bounds handling).
- **Function checks:**
  - the value at the known minimiser is 0 (within 10⁻¹²);
  - hand-computed points;
  - agreement with a line-by-line transcription of the SFU R reference code at 200 random points per
    function and dimension.
- The known minimisers appear only in the tests, never in the search.

### Part B: parameter selection
- **Pilot:** the same four candidates, at D = 20 (not an experiment dimension), seeds 100–104. The
  selection rule, fixed before the pilot, was the lowest average rank over the four functions.
- **Chosen:** C (n = 10, m = 3, e = 1, nep = 100, nsp = 50; 207 evaluations per iteration).
- **The differences were within about one standard deviation** of run-to-run variation, so the
  settings matter little.
- A post-hoc sensitivity check at D = 10 and 30 (seeds 300–309, five settings from explorative to
  extreme local search) confirmed this: differences mostly within ±1.5 standard deviations, with no
  consistent direction.
- Before the pilot, each case was timed once with seed 0. These results were not used for selection.

### Part B: why the results stay far from 0
- **The neighbourhood is fixed:** every recruit changes all D coordinates by up to ±10 % of the range,
  and the patch never shrinks.
- **Example (Sphere):** f(x + δ) = f(x) + 2x·δ + |δ|², and E|δ|² = D·a²/3 with a = 1.024 (≈ 3.5 for
  D = 10). Once f(x) is small compared with the step size, almost every step overshoots.
- **Measured** (`problem_1/results/supplementary/continuous_diagnostics.md`):
  - at the final solutions, one neighbour improves with probability ≤ 0.0001 on average;
  - the remaining distance to the optimum per coordinate is below the neighbour's spread (Sphere D10:
    0.205 vs 0.591);
  - the unimodal functions make 0.00–0.26 % of their total improvement after evaluation 15,000.
- **Explanatory run outside the assignment's rules** (`NONCOMPLIANT_neighbourhood_size_sweep.md`,
  not a result):
  - ±1 % instead of ±10 % improves Sphere about 87× and Rosenbrock D30 about 29×;
  - but it worsens Rastrigin D10 (36.6 → 45.0) and Ackley D10 (6.0 → 16.9);
  - so no fixed size suits all functions, which is the motivation for neighbourhood shrinking in later
    BA versions.
- **D = 30 is harder than D = 10:** each step changes all coordinates, so steps grow with D while
  helpful directions become rarer.

---

## Problem 2: Evolution Strategies

### Data and model
- **Parser:** reads the files line by line, and checks n, the line structure, n(n+1)/2 correlation
  records (i ≤ j, diagonal included), duplicates, missing pairs, ranges and diagonal = 1. Each
  correlation is stored in C_ij and C_ji.
- **Covariance:** Σ_ij = s_i s_j C_ij. All five matrices are positive definite (smallest eigenvalue
  6.05·10⁻⁶ for port5).
- **Port1 checkpoint:** reproduced exactly (R_eq, V(u), R_min(0.5)).
- **Highest-return asset:** unique in every dataset, so the return repair is well defined.
- **Negative target:** port5_alpha025 has a negative target return (−0.000137), because port5's
  equal-weight return is negative. This is correct under the assignment's formula.

### Design decisions and interpretations
- **Repair before every evaluation:** simplex projection (sorting algorithm for θ), then the return
  repair w = (1 − β)q + βe_j. One evaluator (`PortfolioEvaluator`) repairs, evaluates, counts and
  keeps the archive for all three variants.
- **The repaired weights are the individual:** mutation starts from feasible portfolios, following
  the assignment's wording "add … and repair the child".
- **Two different parents** are chosen per child (uniformly, without replacement).
- **Ties in survivor selection** keep the earlier individual (stable sort; parents before offspring).
- **Final partial batch:** 30,000 = 10 + 428 × 70 + 30. The last 30 children are evaluated and
  archived; no survivor selection follows.
- **Paired comparison of plus and comma:** for the same seed, (μ+λ) and (μ,λ) start from the same 10
  initial parents.
- **No tuning:** all ES parameters are fixed by the assignment.
- **Single-threaded linear algebra:** OpenBLAS multi-threading made runtimes about twice as slow and
  erratic, with identical results, so the experiments run single-threaded to make runtime comparable.

### Key findings
- All 450 final allocations are valid, and no invalid candidate was ever evaluated.
- **(1+1)-ES is worse than both population variants in all 150 paired comparisons.**
- **(μ+λ) vs (μ,λ)** (`es_plus_vs_comma.md`):
  - The case is the statistical unit, because the 150 seed pairs come from 15 cases and are not
    independent.
  - Mean of the case-mean relative differences +0.005 % (95 % bootstrap interval −1.31 % to +1.39 %);
    exact sign-flip test p = 0.994. **There is no evidence of an overall difference.**
  - Equivalence is not shown: no margin was defined in advance, and within-case intervals reach
    about ±10 %.
  - Within cases, (μ+λ) is lower on port4 and (μ,λ) on port5 at α ≤ 0.5. After the Holm correction
    only the port1 cases with α ≥ 0.50 remain significant, with a negligible 0.001 % difference.
- **Comma selection** can lose the best individual, because all parents are discarded each
  generation. In one port5 run the population best got worse in 193 of 428 generations, while the
  archive, which only accepts strictly better valid allocations, never got worse.

### Why the (1+1)-ES stagnates
Evidence: saved step-size logs, post-hoc diagnostics with seeds 300–304
(`problem_2/results/supplementary/one_plus_one_diagnostics.md`) and the reference optima below. The
problem is convex, so there are no local optima; the stagnation comes from the search dynamics.

1. **Step-size adaptation.**
   - The success rate stays just below 1/5 (18.8 % on average), so the 1/5 rule shrinks σ throughout
     (126/150 runs end with σ < 10⁻⁷).
   - At the stagnated solutions no tested step size (10⁻⁸ to 10⁻²) reaches 20 % success (at most
     0.181), so the rule is forced to shrink σ. The repair's kinks (weights cut at 0, return pinned at
     R_min) keep even tiny steps at 10–18 % success, instead of about 50 % on a smooth function.
   - In diagnostic versions that prevent the collapse, 80–100 % of the gap to the optimum disappears
     for n ≤ 98.
2. **High dimension.**
   - For port5 (n = 225), preventing the collapse removes only 38 % of the gap.
   - A single isotropic step size for 225 weights almost never produces an improving mutation (0 of
     3,000 for σ ≥ 10⁻⁶ at the stagnated point).
   - The population ES avoid this with per-weight step sizes, recombination and 70 children per
     generation.

**Caveats:** the datasets differ in more than size; the diagnostic versions are not the assignment's
algorithm; 5 seeds per setting.

### Reference optima (supplementary context)
- **Method:** minimum-variance portfolios computed per case. SLSQP proposes a candidate; the KKT
  equations are then solved exactly on its support.
- **Checks:**
  - KKT residuals ≤ 2.2·10⁻¹⁶;
  - weak-duality gap at rounding level;
  - not beaten by any ES run or by 20,000 random portfolios.
- **Status:** a numerical verification, not a formal proof (floating point).
- **Results:** population ES 0–18 % above the optimum on average (optimal on port1); (1+1) 15–137 %.
  The optimal portfolios hold 3–27 assets, while (1+1) holds about 20–111.
- The assignment's conclusions remain relative comparisons between the variants.

### Limitations
- Conclusions are relative between the variants and based on historical data.
- The interpretation choices above could slightly change results under other readings.
- (1+1) is not paired with the population variants (it has a different initialisation); with 150/150
  this does not affect the conclusion.
- The feasible-run rate is 10/10 everywhere by construction of the repair, so it cannot separate the
  variants.
- Runtimes come from one machine (Apple M2, Python 3.11.1).

---

## Verification and reproducibility
- **Automated tests:** 171 (Problem 1) and 137 (Problem 2). They pass with warnings treated as errors.
- **Planted errors:** deliberately introduced bugs were detected by the tests; missing tests found
  this way were added.
- **Independent audits:** each problem has one audit that re-checks the saved results without using
  project code, and one that rebuilds the algorithm rules from logged evaluations.
- **Reproduction:** all 650 runs and every table were reproduced exactly (apart from runtime) from a
  clean clone of the repository.
