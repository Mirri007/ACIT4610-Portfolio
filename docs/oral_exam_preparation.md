# Oral Exam Preparation

Personal study notes, **not** part of the submitted report. Each component follows the same
pattern: what it does, how it works, why it was done that way, which requirement it meets, an
example, key parameters, five likely questions with answers, and common mistakes.

---

# Problem 1A: Bees Algorithm for the Travelling Salesman Problem

## Words you need first

| Term | Meaning |
|------|---------|
| **Optimisation problem** | Choose the best option from a huge number of possible options. |
| **Candidate solution** | One possible answer. Here: one order in which to visit the cities. |
| **Objective function** | The rule that gives each candidate a score. Here: total tour length. We **minimise** it (lower = better). |
| **Objective evaluation** | Calculating the score of one candidate once. The budget is 30,000 of these per run. |
| **Permutation** | An ordering in which every item appears exactly once, e.g. (1, 4, 2, 3). |
| **Heuristic / metaheuristic** | A search method that usually finds good solutions quickly but does not guarantee the best one. The BA is a metaheuristic. |
| **Neighbourhood** | All solutions reachable from one solution by one small change ("move"). |
| **Exploitation** | Searching carefully near solutions that are already good (local search). |
| **Exploration** | Searching new, unvisited areas (here: random scouts). |
| **Seed** | The starting number for the random number generator. Same seed → same "random" choices → same run. |
| **Best-so-far** | The best score found up to a given evaluation. It can only improve or stay the same. |
| **Gap** | How far above the optimum a result is, in percent. |

---

## Component 1: TSP data, distances and tour length

Files: `src/tsplib.py`, `src/tsp_tour.py`, `src/tsp_instances.py`

### 1. What it does
It loads the TSPLIB files, checks that they are what the assignment requires, builds a table of
distances between all cities, and computes the length of a tour. Tour length is the objective function.

### 2. How it works, step by step
1. Open the `.tsp.gz` file with `gzip` (decompressing it in memory) and read the lines.
2. The header lines (`NAME : eil51`, etc.) go into a dictionary. After `NODE_COORD_SECTION`, each line
   is `id x y`.
3. Validate the file:
   - required fields present;
   - TYPE = TSP;
   - EDGE_WEIGHT_TYPE = EUC_2D;
   - number of rows = DIMENSION;
   - ids unique and exactly 1..n.
4. Store coordinates so that **row k is city k+1**. Python counts from 0, TSPLIB counts from 1.
5. Build the n × n distance matrix once:
   `d_ij = floor(sqrt((a_i−a_j)² + (b_i−b_j)²) + 0.5)`.
6. Tour length = sum of the distances between consecutive cities **plus the return leg** from the
   last city back to city 1. The code uses `np.roll(tour, -1)` to pair every city with the next one,
   wrapping around at the end.

### 3. Why it was done this way
- **Validation:** a wrong or damaged file would silently corrupt every result, so the code stops with
  a clear message instead.
- **Distance matrix:** each run computes 30,000 tour lengths, so looking distances up is much faster
  than recomputing square roots. It also guarantees that every evaluation uses the same rounded numbers.
- **Integer distances:** whole numbers make tour lengths exact, with no floating-point error.

### 4. Requirements satisfied
A4–A11 in `docs/requirements_checklist.md`:
- the six instances;
- decompress before loading;
- metadata validation;
- the TSPLIB rounding rule;
- rounding each edge before summing;
- the return edge;
- tour validation;
- optimal tours used only for checking.

### 5. Example
Four cities at the corners of a 3 × 4 rectangle: city 1 (0,0), city 2 (3,0), city 3 (3,4), city 4 (0,4).
- Tour 1→2→3→4→1: 3 + 4 + 3 + **4 (return leg)** = **14**.
- Tour 1→3→2→4→1: 5 + 4 + 5 + 4 = **18**. It is longer because it crosses itself.

Rounding: a distance of exactly 2.5 becomes floor(3.0) = **3**. Python's `round(2.5)` would give **2**.

### 6. Important parameters
None to tune. These are fixed rules from the assignment and TSPLIB.

### 7. Likely questions
1. **How do you know your distances are correct?**
   TSPLIB publishes an optimal tour for each instance. Our code computes exactly the published length
   for all six (e.g. 7,542 for berlin52). A test checks this. If the rounding or the return leg were
   wrong, the lengths would not match. We also tested this: a deliberately planted rounding bug and
   a missing-return-leg bug both made tests fail.
2. **Why `floor(x + 0.5)` and not `round()`?**
   TSPLIB rounds halves upward. Python's `round` uses "banker's rounding" (halves go to the nearest
   even number), so `round(2.5) = 2`. That would give different lengths from the published optima.
3. **Why is city 1 not written twice in the tour?**
   The assignment says the permutation lists each city once. The return to city 1 is added only in
   the length calculation and when the route is drawn.
4. **What would happen if the file had 51 rows but DIMENSION said 52?**
   Loading stops with an error naming the problem. There is a test for this.
5. **Did the optimal tours influence the search?**
   No. They are stored only in `tests/` and only test code reads them. The BA only receives the
   distance matrix.

### 8. Common mistakes
- Forgetting the return leg, which makes every tour look shorter than it is.
- Rounding the total instead of each edge.
- Mixing up 0-based indices and 1-based city ids.

---

## Component 2: Neighbourhood moves (swap and segment reversal)

File: `src/tsp_neighbourhoods.py`

### 1. What it does
It creates a *neighbour*: a slightly changed copy of a tour. Recruited bees use it to search near a
good site.

### 2. How it works
1. Pick two different positions at random from 1..n−1. Position 0 is never picked, because city 1
   must stay first.
2. **Swap:** exchange the cities at the two positions.
3. **Reversal:** reverse the order of all cities from the first position to the second, inclusive.
4. Always work on a **copy**, so the site's own tour is not changed.

### 3. Why
- The assignment requires exactly these two moves, with one move per recruited bee.
- Both moves only rearrange cities, so the result is always a valid permutation; no repair is needed.
- Copying matters because many recruited bees start from the same site tour.

### 4. Requirements satisfied
A13 (two versions), A14 (one random move, city 1 fixed), A12/A1 (valid permutations).

### 5. Example (city ids)
- Tour (1, 2, 3, 4, 5, 6), positions 1 and 4:
  - **Swap** → (1, **5**, 3, 4, **2**, 6)
  - **Reversal** → (1, **5, 4, 3, 2**, 6)
- Edges changed:
  - Swap removes up to **four** edges (into and out of both cities) and adds four new ones.
  - Reversal removes only **two** edges (at the ends of the segment). The inside of the segment is
    travelled backwards, which has the same length because distances are symmetric.

### 6. Parameters
None. Positions are chosen uniformly at random.

### 7. Likely questions
1. **Why did reversal perform much better than swap?**
   Reversal changes only two edges, so it is a small, focused change. It is the classic "2-opt" move,
   which can remove a place where the route crosses itself. A swap between two far-apart positions
   usually adds four new edges, often long ones, so most swaps make the tour worse.
   Our results: berlin52 mean gap 7.65 % (reversal) vs 36.06 % (swap); ch150 65.07 % vs 161.33 %.
2. **Can a move break the tour?**
   No. It only rearranges existing entries. Tests check 2,000 random moves for validity and for
   city 1 staying first.
3. **Why must the two positions be different?**
   If they were equal, the move would change nothing, and that would waste an evaluation.
4. **Is there any move that gives the same tour back?**
   Reversing positions 1..n−1 gives the same circle travelled backwards, with the same length.
   It is rare and harmless: it just costs one evaluation.
5. **Why is position 0 excluded?**
   The assignment fixes city 1 as the first city. Excluding position 0 guarantees it never moves.

### 8. Common mistakes
- Modifying the site in place instead of a copy, which secretly changes the parent solution.
- Including position 0.
- Applying several moves per recruited bee (the assignment says one).

---

## Component 3: The Bees Algorithm

File: `src/bees_algorithm.py` (shared core), `src/bees_tsp.py` (TSP connection and settings)

### 1. What it does
It searches for short tours by copying how honey bees forage: some bees explore at random, and more
bees are sent to forage around the best places found.

### 2. How it works, step by step

| Bee language | Optimisation meaning |
|---|---|
| Site / flower patch | A candidate tour |
| Scout bee | A completely random tour (exploration) |
| Selected site | One of the m best tours |
| Elite site | One of the e best (gets the most bees) |
| Recruited bee | One neighbour (one move) of a selected site (exploitation) |

1. **Initialisation:** create n = 6 random tours (city 1 first, the others shuffled) and evaluate them.
2. **Repeat until the budget is used:**
   1. Sort the tours from shortest to longest.
   2. **Site selection:** the best m = 2 tours are selected sites. The very best (e = 1) is the elite site.
   3. **Recruitment:** the elite site gets nep = 100 recruited bees and the other selected site gets
      nsp = 50. Each recruited bee = one random move applied to the site.
   4. **Local search result:** each site keeps the best of itself and its recruits. A neighbour
      replaces the site only if it is **strictly shorter**, so a site never gets worse.
   5. **Global search:** the other n − m = 4 bees are fresh random scouts.
   6. **New population** = 2 retained sites + 4 new scouts.
3. **Stop** as soon as 30,000 evaluations have been used, even in the middle of an iteration.
4. **Return** the best tour ever evaluated (the best-so-far).

### 3. Why this design
- **One shared core** for Part A and Part B: only "make a random solution" and "make a neighbour"
  differ. This shows clearly what is common between discrete and continuous BA.
- **Each recruit starts from the original site,** not from the best neighbour found so far. All
  recruits explore around the same site, as in Pham et al. The site is updated once, after all its
  recruits.
- **Settings chosen by a pilot study:** see Component 5.

### 4. Requirements satisfied
BA1–BA7, A12–A16: the Pham BA, permutation representation, recorded settings, 30,000 evaluations
counted correctly, stopping at the budget, recording of initial/best-so-far/final values, the same
settings and seeds for both versions.

### 5. Example (one iteration with our settings)
- Population sorted: tour lengths [9,000, 9,400, 15,000, 21,000, 22,500, 30,000].
- Elite site (9,000) gets 100 neighbours. The best of them is 8,950 → the site becomes 8,950.
- Selected site (9,400) gets 50 neighbours. None is shorter → it stays 9,400.
- The four worst tours are dropped and replaced by 4 new random tours, e.g. [28,000, 31,000, 26,500, 29,900].
- Next population: [8,950, 9,400, 28,000, 31,000, 26,500, 29,900].
- Evaluations used: 100 + 50 + 4 = **154**.

### 6. Important parameters and their effect

| Parameter | Value | Effect of increasing it |
|---|---:|---|
| n (scouts / population) | 6 | More exploration, but more evaluations spent on random tours |
| m (selected sites) | 2 | Search spread over more tours; less effort per tour |
| e (elite sites) | 1 | More tours get the large recruitment |
| nep (bees per elite site) | 100 | More intensive local search around the very best tour |
| nsp (bees per other selected site) | 50 | More local search around second-best tours |

### 7. Likely questions
1. **What is the difference between elite and selected sites?**
   Both receive recruited bees. Elite sites are the very best of the selected sites and receive more
   bees (100 vs 50). This puts most of the search effort where the solutions are best.
2. **What do the scouts contribute if random tours are so bad?**
   They are the global exploration. They give the algorithm a chance to find a completely different
   region. For the TSP with this budget they rarely win, which is why the pilot study favoured few
   scouts (4 per iteration). Keeping some scouts is what makes it a Bees Algorithm and not a pure
   hill climber.
3. **Can the best solution get worse during a run?**
   No. Selected sites are only replaced by strictly better neighbours, and the best-so-far record
   keeps the best tour ever evaluated. The best-so-far curve can only go down or stay flat; a test
   checks this.
4. **Why does the final iteration end early?**
   30,000 − 6 = 29,994, which is not a multiple of 154. After 194 full iterations, 118 evaluations
   remain: 100 go to the elite site and 18 to the selected site, then the budget is exhausted.
   The assignment explicitly allows this incomplete final iteration.
5. **How did you choose the parameters?**
   With a pilot study comparing four settings on eil51, kroA100 and ch150, using seeds 100–104
   (not the experiment seeds). Concentrating bees on few sites gave about half the gap of the
   "many sites" setting (65.94 % vs 130.73 % average). Be ready to state the limitations honestly:
   - The pilot used three of the six test instances.
   - Ranked by placement instead of average gap, C and D tie.
   - D was the edge of the range we tried.
   - Before the pilot, one timing run of setting A with seed 0 was seen. It made us run a pilot,
     but it was not used to choose.

6. **Doesn't tuning on test instances bias your results?**
   It could, so we checked afterwards. On three different TSPLIB instances (pr76, rat99, ch130)
   with new seeds (200–204), D was best in all six instance × neighbourhood combinations. That
   check came after the experiments and did not change anything; it only confirms that D was not
   just lucky on the test instances.

7. **Was the pilot fair to both neighbourhoods?**
   Yes. Both got the same candidates, instances, seeds and budget, and D was best for each
   neighbourhood separately. Reversal beat swap in every pilot comparison, so "reversal is better"
   does not depend on which setting we chose. D does make the difference larger.

### 8. Common mistakes
- Forgetting to count rejected neighbours as evaluations.
- Letting the recruits walk away from the site (applying moves cumulatively). That is a different
  algorithm.
- Comparing with `<=` instead of `<`. It would still be valid, but sites would drift between
  equal-length tours. We chose strict improvement.

---

## Component 4: Evaluation counting, stopping and best-so-far history

File: `src/evaluation_tracker.py`

### 1. What it does
It counts every objective evaluation, stops the run at exactly 30,000 and records how the best
value improved over time.

### 2. How it works
1. Every candidate is scored by `tracker.evaluate(solution)`. This is the **only** way to score a
   candidate, and it increases the counter by 1.
2. If the new value is strictly lower than the best so far, it records (evaluation number, value)
   and stores a copy of the solution.
3. Before creating each new candidate, the BA asks `budget_exhausted()`. If the answer is yes, it stops.
4. If anything tried to evaluate beyond the budget, an error is raised (a safety net).

### 3. Why
Counting in a single place makes it impossible to forget a candidate. Saving only the improvements
keeps the logs small but exact.

### 4. Requirements satisfied
BA4–BA7, A17: exact budget, counting including rejected candidates, stopping mid-iteration,
recording the initial best, best-so-far history and final best.

### 5. Example
Values evaluated: 900, 950, 850, 870, 860, 800, 820 (7 evaluations).
- Stored history: (1, 900), (3, 850), (6, 800).
- Rebuilt curve: 900, 900, 850, 850, 850, 800, 800.

### 6. Parameters
`max_evaluations = 30,000`.

### 7. Likely questions
1. **How can you prove each run used exactly 30,000 evaluations?**
   Each run saves its count, the code raises an error if a run does not end at exactly 30,000, and
   the table script re-checks all 120 saved runs.
2. **Do rejected neighbours count?**
   Yes. They were evaluated, so they used part of the budget. The assignment says so explicitly.
3. **Why plot against evaluations rather than iterations?**
   Evaluations measure the actual computational effort and are what the budget limits. Iterations
   cost different amounts with different settings, so they would make comparisons unfair.
4. **What is the "initial best value"?**
   The best tour length among the 6 random tours of the initial population. For berlin52 the mean
   initial best was 28,128, against a final mean of 8,119 with reversal.
5. **How is the mean convergence curve made?**
   Each run's history is expanded to one value per evaluation (1 to 30,000), and the 10 curves are
   averaged at each evaluation number.

### 8. Common mistakes
- Counting iterations instead of evaluations.
- Forgetting to count the initial population.
- Overshooting the budget in the last iteration.

---

## Component 5: Experiments and results (what the numbers say)

Files: `experiments/*.py`, results in `problem_1/results/`

### 1. What was run
6 instances × 2 neighbourhoods × 10 seeds (0–9) = **120 runs**, each with exactly 30,000 evaluations.
Every saved tour was re-verified: valid permutation, recomputed length matches, 30,000 evaluations.

### 2. Main results (from `results/tables/tsp_summary.md`)

| Instance | Optimum | Reversal mean gap | Swap mean gap |
|---|---:|---:|---:|
| eil51 | 426 | 5.07 % | 33.71 % |
| berlin52 | 7,542 | 7.65 % | 36.06 % |
| st70 | 675 | 7.90 % | 59.35 % |
| eil76 | 538 | 9.93 % | 48.98 % |
| kroA100 | 21,282 | 19.83 % | 125.15 % |
| ch150 | 6,528 | 65.07 % | 161.33 % |

- Best berlin52 tour: 7,670 (gap 1.70 %), segment reversal, seed 7.
- No run found an optimal tour.

### 3. Interpretation for the discussion
- **Improvement from initial solutions:** large in every case, e.g. berlin52 from a mean initial best
  of 28,128 down to 8,119 (reversal).
- **Swap vs reversal:** reversal is better on every instance, both in mean gap and in consistency.
  Its standard deviation is lower (berlin52: 324 vs 633).
- **Larger instances:** the gap grows with size (reversal: 5 % on eil51 → 65 % on ch150). The number
  of possible moves grows roughly with n², but the budget is fixed. The ch150 convergence curve is
  still falling at 30,000 evaluations, so ch150 runs are **budget-limited**, not stuck.
- **Early behaviour:** on ch150, swap is slightly ahead for the first ~6,000 evaluations, then
  reversal overtakes it. When the tour is very bad, almost any change helps; later, reversal's
  ability to remove crossings matters more.
- **Runtime:** about 0.5–1.2 s per run, almost independent of size. The Python overhead per
  evaluation dominates.

### 4. Likely questions
1. **Is a 65 % gap on ch150 a failure?**
   It is an unsuccessful case in the sense that the result is far from optimal, but it is explained
   by the fixed budget: the curve is still improving at the end. With the same budget, larger
   instances simply get fewer evaluations per city.
2. **Why are the initial values the same for swap and reversal?**
   For the same seed, the random generator produces the same initial population before any
   neighbourhood move is used. Both versions start identically, which makes the comparison fair.
3. **Why 10 seeds?**
   The assignment requires 10 independent runs. Results vary by seed, so we report the best, mean
   and standard deviation.
4. **How is the gap calculated?**
   100 × (L_BA − L*) / L*, with L* the published optimum. For example, (7,670 − 7,542) / 7,542 × 100
   = 1.70 %.
5. **Are these results reproducible?**
   Yes. Each run is fully determined by its seed. Running the same command gives the same tours and
   lengths; only the measured runtime differs slightly.

---

# Problem 1B: Bees Algorithm for continuous functions

## Words you need first

| Term | Meaning |
|------|---------|
| **Continuous optimisation** | The solution is a list of real numbers that can take any value in a range (not an ordering of cities). |
| **Decision variable / coordinate** | One number in the solution vector x = (x₁, …, x_D). |
| **Dimension D** | How many numbers the vector has (10 or 30 here). |
| **Bounds** | The allowed interval for each coordinate, e.g. [−5.12, 5.12]. |
| **Global minimum** | The lowest value the function can take anywhere (0 for all four functions). |
| **Local minimum** | A point lower than everything *near* it, but not the lowest overall. A search can get stuck there. |
| **Unimodal / multimodal** | One minimum (Sphere) vs. many local minima (Rastrigin, Ackley). |
| **Clipping** | If a coordinate goes outside its bounds, set it to the nearest bound. |
| **Objective error** | Distance from the best possible value. Since the minimum is 0, the error is simply f(x). |

---

## Component 6: The four benchmark functions

File: `src/benchmark_functions.py`

### 1. What it does
It computes the four test functions exactly as defined in the assignment and the SFU library.

### 2. How each works
- **Sphere:** add up the squares of all coordinates. It is a smooth bowl with one bottom at 0.
- **Rosenbrock:** each pair of neighbouring coordinates contributes 100·(x_{i+1} − x_i²)² + (1 − x_i)².
  The bottom is a long, narrow, curved valley; the minimum is at all ones.
- **Rastrigin:** 10·D + Σ(x_i² − 10·cos(2πx_i)). A bowl with regular bumps, so there is a local
  minimum near every point with whole-number coordinates.
- **Ackley:** −20·exp(−0.2·√(mean x²)) − exp(mean cos(2πx)) + 20 + e. It is almost flat far from
  the centre, has many small bumps, and a deep narrow hole at 0.

### 3. Why it was done this way
- Each function is a short formula in NumPy, so it can be compared line by line with the assignment.
- The known minimisers are kept only in the tests, so the search code can never "cheat".

### 4. Requirements satisfied
B1–B7 (functions, bounds, both dimensions, checks at the minimiser and another point, no minimiser
inserted into the search).

### 5. Examples (from the tests)
- Sphere(1, 2, −3) = 1 + 4 + 9 = 14.
- Rosenbrock(1, 2) = 100·(2 − 1)² + 0 = 100.
- Rastrigin(1, 2) = 20 + (1 − 10) + (4 − 10) = 5, because cos(2π·k) = 1 for whole numbers k.
- Ackley(1, …, 1) = 20 − 20·e^−0.2 ≈ 3.6254.

### 6. Parameters
Ackley's constants a = 20, b = 0.2, c = 2π; the bounds; D.

### 7. Likely questions
1. **How did you check the functions are correct?**
   In three ways:
   - the value at the known minimiser is 0;
   - values at points worked out by hand are correct;
   - the results agree with a line-by-line copy of SFU's own R code at 200 random points per
     function and dimension.

   Planted bugs (e.g. Ackley with b = 0.25, Rastrigin without the 10·D term) were all caught by
   the tests.
2. **Why is Ackley at 0 not exactly 0 in Python?**
   −20·e⁰ − e¹ + 20 + e should cancel, but floating-point numbers cannot store e exactly, so about
   4·10⁻¹⁶ remains. The tests use a tolerance of 10⁻¹².
3. **Why does Rastrigin have the term 10·D?**
   At x = 0 every cosine is 1, so the sum is −10·D. Adding 10·D makes the minimum exactly 0.
4. **What makes Rosenbrock hard even though it has one minimum?**
   The valley is easy to find but narrow and curved. Steps across the valley are punished by the
   factor 100, so progress along the valley floor is slow.
5. **Where are the known minimisers used?**
   Only in the tests. The search starts from uniform random vectors.

### 8. Common mistakes
- Summing Rosenbrock over all D coordinates instead of D − 1 pairs.
- Forgetting the 10·D term.
- Using different Ackley constants.

---

## Component 7: Continuous Bees Algorithm (representation, neighbourhood, clipping)

File: `src/bees_continuous.py` (plus the same `bees_algorithm.py` as Part A)

### 1. What it does
It runs the **same** Bees Algorithm as Part A, with real-valued vectors instead of tours.

### 2. How it works
1. **Scout:** each coordinate is drawn uniformly at random between its lower and upper bound.
2. **Recruit (neighbour):** for **every** coordinate, draw a change uniformly in
   [−10 %, +10 %] of (upper − lower), add it, then **clip** to the bounds.
3. Selection, recruitment, retention, scouting and stopping are identical to Part A.
4. Settings: n = 10, m = 3, e = 1, nep = 100, nsp = 50, so 207 evaluations per iteration.
   30,000 = 10 + 144 × 207 + 182, so iteration 145 is incomplete.

### 3. Why
- The neighbourhood and the clipping are exactly what the assignment specifies.
- Reusing the BA core makes the discrete/continuous comparison clear: only the representation and
  the move differ.

### 4. Requirements satisfied
B8–B12, BA1–BA7 for Part B.

### 5. Example (Sphere, range 10.24, maximum change 1.024)
Site (5.0, −2.0), random changes (+0.5, −0.3) → (5.5, −2.3). Then 5.5 is above the bound 5.12,
so the neighbour becomes (5.12, −2.3).

### 6. Parameters
n, m, e, nep, nsp as in Part A; the neighbourhood size is fixed at 10 % by the assignment.

### 7. Likely questions
1. **Why do the results not reach 0? Is that a bug?**
   No. The neighbourhood is fixed: every coordinate moves by up to ±10 % of its range in every
   recruit, and the patch never shrinks. For Sphere the expected squared step size is
   D·a²/3 ≈ 0.35·D, about 3.5 for D = 10. Once the site is closer to 0 than a typical step is
   long, almost every random step lands further away. Sphere's mean final values (0.43 at D = 10,
   5.5 at D = 30) show this ceiling. Later BA versions shrink the neighbourhood to fix exactly this.
2. **Why is D = 30 so much harder?**
   Each recruit changes all 30 coordinates at once. The step is longer and it is much less likely
   that all coordinates move in a helpful direction. The search space is also vastly larger for the
   same 30,000 evaluations.
3. **What does clipping do and why is it needed?**
   It puts any coordinate that left its interval back onto the nearest bound, so every evaluated
   vector is inside the allowed region. Tests show clipping happens at both bounds.
4. **What is the same and what is different compared with Part A?**
   - Same: the whole BA loop, site selection, elite and non-elite recruitment, keeping only
     improvements, fresh scouts, evaluation counting, stopping and best-so-far tracking.
   - Different: the representation (vector vs permutation), the scout (uniform vector vs shuffle),
     the move (perturb all coordinates vs swap/reversal), and constraint handling (clipping vs none
     needed).
5. **How were the Part B settings chosen?**
   With a pilot at D = 20 and seeds 100–104, using a rule fixed in advance (lowest average rank).
   C won, but all four settings were within about one standard deviation of each other, so the
   settings matter little here. Before the pilot, one timing run per case with seed 0 was seen;
   it was not used for selection.

### 8. Common mistakes
- Using 10 % of the upper bound instead of the range.
- Changing only one coordinate.
- Forgetting clipping, or using the same random change for all coordinates. All of these were
  planted as bugs and caught by the tests.

---

## Component 8: Part B results (what the numbers say)

From `results/tables/continuous_summary.md` (10 runs each):

| Function | D = 10 mean (best) | D = 30 mean (best) | Mean initial best (D = 10 / 30) |
|---|---|---|---|
| Sphere | 0.4293 (0.1843) | 5.499 (4.556) | 53.58 / 204.1 |
| Rosenbrock | 92.38 (64.31) | 2,472 (1,641) | 368,900 / 2,145,000 |
| Rastrigin | 33.01 (23.14) | 275.6 (245.1) | 133 / 452.5 |
| Ackley | 6.233 (5.122) | 10.55 (10.07) | 20.53 / 20.89 |

**Points for the discussion:**
- **Improvement from the initial population** is large everywhere, e.g. Rosenbrock D = 10 from
  about 369,000 to 92.
- **No run gets close to the global minimum.** This is explained by the fixed neighbourhood.
- **Higher dimension** is clearly harder for every function.
- **Rastrigin convergence (D = 10)** keeps improving slowly in steps; the min–max band shows large
  run-to-run differences in when improvements happen.
- **Ackley at D = 30** ends around 10.5 in every run (small std 0.28): all runs stall at a similar
  level.
- **Discrete vs continuous:**
  - In Part A, one move changes only a few edges, so the search can make small, precise changes.
  - In Part B, every move changes all coordinates by a fixed amount, which limits precision.

---

# Problem 2: Evolution Strategies for portfolio optimisation

## Words you need first

| Term | Meaning |
|------|---------|
| **Portfolio / weights w** | How the budget is split over n assets; w_i is the fraction in asset i (0.25 = 25 %). |
| **Expected return R(w) = rᵀw** | The weighted average of the assets' mean returns. |
| **Variance V(w) = wᵀΣw** | Our risk measure and the **objective** (lower = less risky). |
| **Standard deviation s_i** | How much asset i's return fluctuates. Variance = std². |
| **Correlation C_ij** | How assets i and j move together: +1 together, 0 unrelated, −1 opposite. |
| **Covariance matrix Σ** | Σ_ij = s_i·s_j·C_ij. Diagonal = each asset's own variance. |
| **Diversification** | Combining assets that do not move together lowers total variance. |
| **Constraint** | A rule a solution must satisfy (w ≥ 0, Σw = 1, R(w) ≥ R_min). |
| **Feasible** | Satisfies all constraints (here: within the 1e−8 tolerances). |
| **Probability simplex** | All vectors with non-negative entries that sum to 1 (= all valid budget splits). |
| **Projection** | Moving a point to the nearest point of a set. |
| **Evolution Strategy (ES)** | An evolutionary algorithm for real numbers: Gaussian mutation, a step size σ that adapts, selection. |
| **Step size σ** | The standard deviation of the random mutation: how far children move from parents. |
| **Self-adaptation** | Each individual carries its own σ values, which are mutated and inherited; good σ survive with good solutions. |
| **Plus / comma selection** | Survivors chosen from parents + children (plus), or children only (comma). |
| **Archive** | A separate record of the best valid solution ever evaluated. |

---

## Component 9: Data, covariance and return targets

File: `problem_2/src/portfolio_data.py`

### 1. What it does
It reads each OR-Library file, checks it, builds the correlation and covariance matrices, and
computes the three return targets per dataset (15 cases).

### 2. How it works
1. Line 1 = n. Next n lines = mean return and std of each asset.
2. Remaining lines = "i j correlation" for every pair with i ≤ j, including i = j (always 1).
   n(n+1)/2 lines in total (496 for n = 31).
3. Store each correlation in C[i−1, j−1] **and** C[j−1, i−1]. The files are 1-based and Python is 0-based.
4. Σ = s_i·s_j·C_ij for all pairs: `np.outer(s, s) * C`.
5. R_eq = mean of r (return of equal weights 1/n); r_max = largest r_i;
   R_min(α) = (1 − α)·R_eq + α·r_max for α = 0.25, 0.50, 0.75.

### 3. Why
- Strict validation (line structure, counts, duplicates, ranges, diagonal = 1) prevents silently wrong
  matrices.
- The targets lie between "equal weights" and "best single asset", so a larger α means a harder
  return requirement.

### 4. Requirements
E1–E7, including the port1 checkpoint (R_eq = 0.003504064516129, V(u) = 0.001130937943724,
R_min(0.5) = 0.007184532258065), reproduced exactly in a test.

### 5. Example
port1, assets 1 and 2: s₁ = 0.043208, s₂ = 0.040258, C₁₂ = 0.562289 →
Σ₁₂ = 0.043208 × 0.040258 × 0.562289 ≈ 0.000978.

### 6. Parameters
α ∈ {0.25, 0.50, 0.75}.

### 7. Likely questions
1. **Why store the correlation twice?**
   The file lists each pair once (i ≤ j), but correlation is symmetric. The variance formula uses
   both Σ_ij and Σ_ji.
2. **How did you validate the parser?**
   - The port1 checkpoint values from the assignment.
   - A second, independent parser in the tests gives identical numbers for all five files.
   - The covariance is symmetric and positive definite, with the diagonal equal to s².
   - Broken files are rejected, one test per rule.
3. **What does positive definite mean, and why check it?**
   Every non-zero portfolio has variance > 0. If Σ were not positive definite, some portfolios would
   have negative "variance", which is impossible, and the optimiser could exploit it.
4. **Why does α = 0.75 give a higher variance?**
   The return must be closer to the best single asset, so the portfolio must concentrate more on
   high-return, usually riskier, assets. Fewer allocations are allowed, and the minimum variance rises.
5. **What is a case name?**
   For example `port5_alpha050`: dataset port5, α = 0.50.

### 8. Common mistakes
- Filling only half of C.
- Forgetting to subtract 1 from the indices.
- Using standard deviation instead of variance as the objective. (The assignment says variance throughout.)

---

## Component 10: Repair (simplex projection + return repair) and feasibility

File: `problem_2/src/portfolio_model.py`

### 1. What it does
It turns any vector produced by mutation or recombination into a valid portfolio before its variance
is computed.

### 2. How it works
1. **Simplex projection:** q_i = max(z_i − θ, 0) with θ such that Σq = 1.
   θ is found by sorting z from largest to smallest and testing how many of the largest entries
   stay positive.
2. **Return repair:** if R(q) < R_min, mix q with "all money in the best asset j":
   w = (1 − β)q + βe_j, β = (R_min − R(q)) / (r_max − R(q)). This gives exactly R(w) = R_min.
3. **Feasibility check:** w_i ≥ −1e−8, |Σw − 1| ≤ 1e−8, R(w) ≥ R_min − 1e−8.

### 3. Why
- The assignment prescribes this repair.
- Repair (instead of rejection or penalties) means every evaluated portfolio is valid, so the ES can
  simply compare variances.
- Projection is the *smallest* change that makes z non-negative and summing to 1. The return repair
  moves only as far towards the best asset as needed.

### 4. Requirements
E8–E11.

### 5. Examples
- Projection: z = (0.3, 0.2, −0.5) → θ = −0.25 → q = (0.55, 0.45, 0).
- Return repair: r = (2 %, 6 %, 10 %), R_min = 4 %, q = (0.8, 0.2, 0) has R(q) = 2.8 %.
  β = (0.04 − 0.028)/(0.10 − 0.028) = 1/6, so w = (2/3, 1/6, 1/6) with R(w) = 4 %.

### 6. Parameters
Tolerance 1e−8.

### 7. Likely questions
1. **Why is the result of the return repair still on the simplex?**
   It is a weighted average (weights 1 − β and β, both between 0 and 1) of two portfolios that are
   both non-negative and sum to 1.
2. **Why exactly R_min after repair?**
   Return is linear: R(w) = (1 − β)R(q) + β·r_max = R(q) + β(r_max − R(q)) = R_min.
3. **How did you test the projection?**
   - Hand examples.
   - Comparison with a completely different algorithm (bisection on θ) on 300 random vectors.
   - The closest-point property: no random simplex point is closer to z.
   - Applying the projection twice changes nothing.
4. **Why tolerances?**
   Floating-point arithmetic rounds, e.g. a sum of 0.9999999999999999. The tolerances accept
   rounding but reject real violations; tests check both sides of every bound.
5. **Does the repair influence the search?**
   Yes, strongly. It cuts weights to exactly 0 and pins the return at R_min. This creates "kinks" in
   the landscape, which is part of why the (1+1)-ES stagnates (Component 13).

### 8. Common mistakes
- Normalising by dividing by the sum (that is not a projection, and fails with negative entries).
- Using the asset with the largest *weight* instead of the largest *return* in step 2.

---

## Component 11: (1+1)-ES and the 1/5th success rule

File: `problem_2/src/es_one_plus_one.py`

### 1. What it does
It keeps one parent portfolio and, 29,999 times, creates one mutated child. The child replaces the
parent only if it has strictly lower variance.

### 2. How it works
1. Parent = repair(uniform [0, 1] random weights). σ = 0.1/√n.
2. Child = repair(parent + σ·N(0, 1) per weight). One evaluation.
3. If V(child) < V(parent): replace the parent, and σ ← σ·e^(1/3) (about ×1.40).
   Otherwise σ ← σ·e^(−1/12) (about ×0.92). Keep σ in [1e−8, 1].

### 3. Why
These are the assignment's rules. The two factors balance exactly at a success rate of 1/5:
p/3 − (1 − p)/12 = 0 ⇔ p = 1/5. More successes → bigger steps; fewer → smaller steps.

### 4. Requirements
E12–E14, E21–E23.

### 5. Example
σ = 0.01. A success gives 0.01 × 1.3956 = 0.0140; a failure gives 0.01 × 0.9200 = 0.0092.
Four failures and one success: 0.01 × 0.92⁴ × 1.3956 ≈ 0.0100. Unchanged on average, as intended.

### 6. Parameters
σ₀ = 0.1/√n, factors e^(1/3) and e^(−1/12), bounds [1e−8, 1].

### 7. Likely questions
1. **Why does the (1+1)-ES perform worst everywhere?**
   - Its success rate stayed slightly below 1/5 (18.8 % on average), so σ shrank throughout.
     126/150 runs ended with σ < 10⁻⁷.
   - It reached within 1 % of its final value after a median of 3,890 evaluations and then stagnated.
   - Its portfolios keep about 68 assets, while the population ES finds sparse portfolios with about
     15 assets. With one tiny σ, small weights can no longer be pushed to 0.
2. **Why σ₀ = 0.1/√n?**
   A mutation changes all n weights. Its total length grows like σ·√n, so dividing by √n keeps the
   initial total step about 0.1 for any n.
3. **What is "plus" about (1+1)?**
   The parent competes with its child, so the parent's variance never gets worse (elitism).
4. **How did you verify the implementation?**
   From a log of a real run, we rebuilt every accept/reject decision and the full σ sequence. Then
   (candidate − parent)/σ was checked to be standard normal: mean −0.0002, std 0.9997 on port5.
   Planted bugs in the factors, σ₀ or the acceptance rule were all caught.
5. **Is the step-size collapse a bug?**
   No. The trace confirms the rules are followed exactly. It is a known weakness of the 1/5 rule on
   constrained problems: near constraint boundaries, smaller steps do not raise the success rate
   enough.

### 8. Common mistakes
- Accepting equal or worse children.
- Updating σ only on success.
- Forgetting the clamp.

---

## Component 12: Population ES, (μ+λ) and (μ,λ)

File: `problem_2/src/es_population.py`

### 1. What it does
It keeps 10 parents, each with weights and its own step size per weight, creates 70 children per
generation, and keeps the 10 best.

### 2. How it works (per child)
1. Choose two **different** parents at random.
2. Weights: average of the two parents. Step sizes: geometric mean √(σ⁽¹⁾σ⁽²⁾).
3. Self-adaptation: σ'_i = σ_i·exp(τ'·Z₀ + τ·Z_i), with τ' = 1/√(2n) and τ = 1/√(2√n).
   Z₀ is one number for the whole child; Z_i is one per coordinate. Clamp to [1e−8, 1].
4. Mutate with the **new** σ': z_i = w_i + σ'_i·N_i, then repair and evaluate.
5. After 70 children:
   - **plus:** best 10 of 10 parents + 70 children;
   - **comma:** best 10 of the 70 children only.

Budget: 10 + 428 × 70 + 30 = 30,000, so the last batch has 30 children.

### 3. Why
- Recombination mixes good portfolios and smooths out noise.
- A step size per weight allows different scales for different assets.
- Self-adaptation lets selection tune the step sizes: children whose σ' happened to suit the problem
  produce better portfolios, survive, and pass on their σ'.
- Comma selection forgets old parents. That lets the step sizes keep adapting and can escape a stuck
  population, at the cost of sometimes losing the best individual.

### 4. Requirements
E15–E23.

### 5. Example
- Parents' σ = (0.01, 1.0) and (1.0, 0.04): geometric means (0.1, 0.2).
- With τ' = 0.2, τ = 0.5, Z₀ = 1, Z = (0, −1): σ' = (0.1·e^0.2, 0.2·e^−0.3) = (0.122, 0.148).

### 6. Parameters
μ = 10, λ = 70 (a 1:7 ratio, a classic choice), τ', τ, σ₀ = 0.1/√n, bounds [1e−8, 1].

### 7. Likely questions
1. **Why can the population best get worse under comma selection, while the archive cannot?**
   - Comma discards all parents every generation. If all 70 children are worse than the best parent,
     the new best is worse. This happened in 193 of 428 generations in one port5 run (supplementary
     figure).
   - The archive is a separate record that only changes when something strictly better appears, so
     the reported result never gets worse.
   - The archive is never used to choose parents.
2. **Why the geometric mean for step sizes?**
   Step sizes act multiplicatively. The geometric mean of 0.01 and 1 is 0.1 (halfway on a log scale);
   the arithmetic mean 0.505 would let the larger value dominate.
3. **What do Z₀ and Z_i do?**
   - Z₀ makes the whole child bolder or more careful at once.
   - Z_i lets individual coordinates differ.
   - A test checked through the real code that Z₀ is shared. The coordinates' log-step changes are
     correlated by τ'²/(τ'² + τ²) ≈ 0.155 for n = 31.
4. **Which is better, plus or comma?**
   - On these data, no clear difference: (μ,λ) had the lower mean in 8 of 15 cases and (μ+λ) in 7.
   - (μ,λ) was lower in 84 of 150 seed pairs, a sign test p = 0.165, so not significant.
   - Per case, the differences are at most 5 %.
   - Both clearly beat (1+1), in 150/150 pairs.
5. **Why are plus and comma comparable seed by seed?**
   With the same seed they start from the same 10 parents, because initialisation draws the same
   random numbers. The audit verifies this.

### 8. Common mistakes
- Mutating with the old σ instead of σ'.
- Drawing Z₀ per coordinate.
- Letting comma selection include parents.
- Using the archive as a parent.

All of these were planted as bugs and caught by the tests.

---

## Component 13: Evaluation counting, archive and results (Problem 2)

Files: `portfolio_evaluator.py`, `run_es.py`, `experiments/*`

### 1. What it does
`PortfolioEvaluator.evaluate` repairs, computes the variance, counts, and updates the archive with
the best *valid* portfolio (strictly lower variance), starting from the very first evaluation.

### 2. Results to remember (450 runs, all feasible)

| | (1+1)-ES | (μ+λ)-ES | (μ,λ)-ES |
|---|---|---|---|
| Cases with lowest mean variance | 0 | 7 | 8 |
| Paired wins vs (1+1) | – | 150/150 | 150/150 |
| Median evaluations to reach within 1 % of final | 3,890 | 13,072 | 13,493 |
| Mean assets held (weight > 1e−6) | 67.6 | 14.7 | 14.6 |

On port5_alpha050 the final mean variances are 7.27e−4, 3.96e−4 and 3.77e−4.

### 3. Likely questions
1. **How do you know each run used exactly 30,000 evaluations?**
   - Every run saves its count, and `run_es_on_case` raises an error otherwise.
   - The independent audit re-checks all 450 runs.
   - The trace audit rebuilds 10 + 428 × 70 + 30 for the population variants.
2. **What does "valid run" mean, and why are all runs valid?**
   Valid means the returned allocation meets the three tolerances. The repair guarantees it, and the
   evaluator counts any invalid candidate: there were none.
3. **Why compare variants on evaluations rather than time or generations?**
   - Evaluations are the fixed budget and the expensive step.
   - A (1+1) trial and a population generation cost very different numbers of evaluations, so
     generations would not be fair.
   - Runtime is reported separately.
4. **Can you say how good the best portfolios are in absolute terms?**
   Not from these experiments. The assignment limits conclusions to relative performance, and we did
   not compute the exact optimum. This is a stated limitation.
5. **Why was BLAS set to single-threaded?**
   Multi-threading made the runtimes about twice as slow and erratic, with identical results.
   Runtime is a compared metric, so stable timing was needed.
