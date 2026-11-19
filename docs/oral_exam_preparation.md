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
