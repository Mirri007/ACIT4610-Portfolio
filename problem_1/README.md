# Problem 1: Bees Algorithm

Part A (TSP) and Part B (continuous functions) are implemented, tested, run and audited.

All commands below are run from **this folder** (`problem_1/`) after installing the
dependencies (see the main [README](../README.md)).

## Folder layout

| Path | Contents |
|------|----------|
| `data/tsplib_original/` | The six original TSPLIB files (`.tsp.gz`), unmodified |
| `data/tsplib_robustness_pilot/` | pr76, rat99, ch130 from the same TSPLIB source, used **only** for the robustness check |
| `src/tsplib.py` | Loads a `.tsp.gz` file and validates NAME, TYPE, DIMENSION, EDGE_WEIGHT_TYPE, NODE_COORD_SECTION, row count, unique ids |
| `src/tsp_tour.py` | Rounded EUC_2D distance matrix, tour length (incl. return leg), random tours, tour validation |
| `src/tsp_neighbourhoods.py` | Swap move and segment-reversal move |
| `src/evaluation_tracker.py` | Counts every objective evaluation, enforces the budget, records the best-so-far history |
| `src/bees_algorithm.py` | The Bees Algorithm (shared by Part A and Part B) |
| `src/benchmark_functions.py` | Sphere, Rosenbrock, Rastrigin, Ackley and their bounds |
| `src/bees_continuous.py` | Runs the BA on one function: random vectors, ±10 % neighbourhood with clipping; **Part B settings and seeds** |
| `src/bees_tsp.py` | Runs the BA on one TSP instance; **Part A settings and seeds** |
| `src/tsp_instances.py` | Instance names, city counts, optimal lengths, file paths, source URLs |
| `experiments/` | Scripts that run experiments and build tables/figures |
| `tests/` | Automated tests (`tests/reference_optimal_tours/` holds published optimal tours, used **only** by tests) |
| `results/` | All outputs (see below) |

## Part A: data

| Instance | Cities | Optimal length L* | Source |
|----------|-------:|------------------:|--------|
| eil51 | 51 | 426 | https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/eil51.tsp.gz |
| berlin52 | 52 | 7,542 | https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/berlin52.tsp.gz |
| st70 | 70 | 675 | https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/st70.tsp.gz |
| eil76 | 76 | 538 | https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/eil76.tsp.gz |
| kroA100 | 100 | 21,282 | https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/kroA100.tsp.gz |
| ch150 | 150 | 6,528 | https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/ch150.tsp.gz |

Files are read directly from the `.gz` archives (decompressed in memory with Python's `gzip`).
Distances: `d_ij = floor(sqrt((a_i - a_j)^2 + (b_i - b_j)^2) + 0.5)`, each edge rounded before summing,
return edge included.

## Part A: Bees Algorithm settings

The same settings and seeds are used for both neighbourhood versions and all six instances.

| Setting | Symbol | Value |
|---------|--------|------:|
| Scout bees (population size) | n | 6 |
| Selected sites | m | 2 |
| Elite sites | e | 1 |
| Recruited bees per elite site | nep | 100 |
| Recruited bees per other selected site | nsp | 50 |
| Fresh random scouts per iteration | n − m | 4 |
| Evaluations per full iteration | e·nep + (m−e)·nsp + (n−m) | 154 |
| Evaluation budget per run | | 30,000 |
| Seeds | | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 |

30,000 evaluations = 6 (initial population) + 194 full iterations × 154 (= 29,876) + 118 in an
incomplete 195th iteration. Every candidate counts, including rejected neighbours.

Neighbourhoods: **swap** (exchange the cities at two random positions) and **reversal** (reverse the
segment between two random positions). Each recruited bee = one random move from its site; city 1 never moves.

Settings were chosen with a pilot study (eil51, kroA100, ch150; seeds 100–104). A robustness
check run *afterwards* on three non-assignment instances (pr76, rat99, ch130; seeds 200–204) did not
change the settings, and D was best there in every combination. The full chronology and limitations
are in [docs/implementation_notes.md](../docs/implementation_notes.md), section 6.

## Part A: commands

```bash
# Run the automated tests (about 10 seconds)
python -m pytest

# One single run (berlin52, segment reversal, seed 0), about 0.6 seconds
python -m experiments.run_tsp_experiments --instances berlin52 --neighbourhoods reversal --seeds 0

# The full Part A experiment: 6 instances x 2 neighbourhoods x 10 seeds = 120 runs
# (total search time was 71 s on an Apple M2)
python -m experiments.run_tsp_experiments

# Tables and figures from the saved results
python -m experiments.make_tsp_tables
python -m experiments.make_tsp_plots

# Settings pilot (how the settings were chosen) and the later robustness check (about 1 minute each)
python -m experiments.tsp_pilot_settings
python -m experiments.tsp_robustness_pilot

# Audits (exit code 0 = passed, 1 = problems found and listed)
python -m experiments.audit_tsp_results   # independent re-check of all 120 saved runs + summary table
python -m experiments.audit_tsp_trace     # logs every evaluation of 2 real runs and rebuilds the BA logic
```

Finished runs are skipped when the experiment is restarted; add `--overwrite` to re-run them.

**What the audits do.**
- `audit_tsp_results` imports no project code. It re-reads the original data, recomputes every tour
  length with its own distance code, and checks permutations, settings, evaluation counts, gaps and
  histories. It also recomputes the summary table with Python's `statistics` module.
- `audit_tsp_trace` runs the real algorithm with logging and checks, iteration by iteration, that the
  elite site (best tour) gets 100 recruits, the second-best gets 50, sites keep only improvements,
  4 scouts follow, and the run stops at exactly 30,000 evaluations.

## Part A: outputs

| File | Contents |
|------|----------|
| `results/raw/tsp/<instance>_<neighbourhood>_seed<seed>.json` | One file per run: settings, seed, initial best, final best length, gap, runtime, evaluations, iterations, final tour (city ids, starting at city 1), best-so-far history |
| `results/convergence/tsp/<instance>_<neighbourhood>_seed<seed>.csv` | Best-so-far log: `evaluation, best_so_far_length`, one row per improvement (value constant until the next row) |
| `results/raw/tsp_all_runs.csv` | All 120 runs in one table, including final tours |
| `results/tables/tsp_summary.csv` / `.md` | Required summary table (instance, cities, optimum, best, mean, std, mean gap, mean runtime) |
| `results/tables/tsp_pilot_settings.csv` | Pilot study used to choose the settings |
| `results/tables/tsp_robustness_pilot.csv` / `.md` | Later robustness check on pr76, rat99, ch130 (not used for selection) |
| `results/tables/tsp_paired_comparison.md` | Seed-by-seed swap vs reversal (same seed = same initial population) |
| `results/figures/tsp_convergence_berlin52.png`, `tsp_convergence_ch150.png` | Mean best-so-far vs evaluations, both neighbourhoods, optimum marked |
| `results/figures/tsp_route_berlin52.png` | Shortest berlin52 tour over all 20 runs, with return leg and labels |
| `results/tsp_experiment_log.txt` | Console log of the full experiment run |

Gap(%) = 100 · (L_BA − L*) / L*, where L_BA is the final best valid tour length of the run.

## Part B: functions

| Function | Bounds (every coordinate) | Global minimum |
|----------|---------------------------|----------------|
| Sphere | [−5.12, 5.12] | f(0, …, 0) = 0 |
| Rosenbrock | [−5, 10] | f(1, …, 1) = 0 |
| Rastrigin | [−5.12, 5.12] | f(0, …, 0) = 0 |
| Ackley (a = 20, b = 0.2, c = 2π) | [−32.768, 32.768] | f(0, …, 0) = 0 |

Formulas follow the assignment and the SFU Virtual Library (Surjanovic & Bingham,
https://www.sfu.ca/~ssurjano/). No data files are needed. Dimensions D = 10 and D = 30.

## Part B: Bees Algorithm settings

| Setting | Symbol | Value |
|---------|--------|------:|
| Scout bees (population size) | n | 10 |
| Selected sites | m | 3 |
| Elite sites | e | 1 |
| Recruited bees per elite site | nep | 100 |
| Recruited bees per other selected site | nsp | 50 |
| Fresh random scouts per iteration | n − m | 7 |
| Evaluations per full iteration | e·nep + (m−e)·nsp + (n−m) | 207 |
| Evaluation budget per run | | 30,000 |
| Neighbourhood | | each coordinate + U(−10 %, +10 %) of (upper − lower), then clipped to bounds |
| Seeds | | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 |

30,000 evaluations = 10 (initial population) + 144 full iterations × 207 (= 29,808) + 182 in an incomplete
145th iteration. Scouts are uniform random vectors inside the bounds.

Settings were chosen with a pilot study at D = 20 (not an experiment dimension) and seeds 100–104,
using a selection rule fixed in advance (lowest average rank over the four functions). The differences
between candidate settings were within about one standard deviation, so the settings matter little
here; see [docs/implementation_notes.md](../docs/implementation_notes.md), Problem 1B section 3.

## Part B: commands

```bash
# One single run (Rastrigin, D = 10, seed 0), about 0.3 seconds
python -m experiments.run_continuous_experiments --functions rastrigin --dimensions 10 --seeds 0

# The full Part B experiment: 4 functions x 2 dimensions x 10 seeds = 80 runs
# (total search time was 28 s on an Apple M2)
python -m experiments.run_continuous_experiments

# Tables and figures from the saved results
python -m experiments.make_continuous_tables
python -m experiments.make_continuous_plots

# Settings pilot (80 runs, under a minute)
python -m experiments.continuous_pilot_settings

# Audits (exit code 0 = passed)
python -m experiments.audit_continuous_results   # independent re-check of all 80 runs + summary (no project imports)
python -m experiments.audit_continuous_trace     # logs every evaluation of 3 real runs and rebuilds the BA logic
```

## Part B: outputs

| File | Contents |
|------|----------|
| `results/raw/continuous/<function>_D<D>_seed<seed>.json` | One file per run: settings, seed, bounds, initial best, final best value, final best vector, runtime, evaluations, iterations, best-so-far history |
| `results/convergence/continuous/<function>_D<D>_seed<seed>.csv` | Best-so-far log: `evaluation, best_so_far_value`, one row per improvement |
| `results/raw/continuous_all_runs.csv` | All 80 runs in one table, including final vectors |
| `results/tables/continuous_summary.csv` / `.md` | Required summary table (function, D, best, mean, std, mean runtime; plus mean initial best and median) |
| `results/tables/continuous_pilot_settings.csv` / `.md` | Pilot study used to choose the settings |
| `results/figures/continuous_convergence_rastrigin_D10.png` | Mean best-so-far vs evaluations, Rastrigin D = 10, log-scale y-axis (labelled) |
| `results/figures/continuous_boxplots_D30.png` | Boxplots of final values, four functions at D = 30, four panels |
| `results/continuous_experiment_log.txt` | Console log of the full experiment run |

Since every global minimum is 0, each final objective value is the run's objective error.

## Kinds of runs and their seeds

| Kind | Purpose | Seeds |
|---|---|---|
| Required experiments | The 120 TSP runs and 80 continuous runs reported as results | 0–9 |
| Parameter pilots | Choosing the BA settings (Part A: eil51/kroA100/ch150; Part B: D = 20) | 100–104 |
| Post-hoc robustness check (Part A) | Checking the chosen setting on pr76/rat99/ch130; did not change anything | 200–204 |
| Post-hoc diagnostics (Part B) | Explaining the Part B results (below) | 300–309 (probe 306) |
| Automated tests | Correctness checks only (budgets, validity, reproducibility); not used to choose settings or report results | various, including 0–9 |

## Supplementary diagnostics for Part B (post hoc; not part of the required experiments)

Script `supplementary/continuous_diagnostics.py` (added after the final experiments, to explain the Part B results):

- **Part A of the script (compliant):** at the saved final solutions, the probability that one
  assignment neighbour improves, the distance to the optimum compared with the neighbourhood size,
  and the share of improvement made in the second half of the budget.
- **Part B of the script (compliant):** sensitivity to five BA settings, all with the assignment's ±10 %
  neighbourhood, at D = 10 and 30.
- **Part C of the script (NOT assignment-compliant, explanatory only):** the same BA with ±3 % and ±1 %
  neighbourhoods. Written to a separate file, `NONCOMPLIANT_neighbourhood_size_sweep.md`; never a result.

```bash
python -m supplementary.continuous_diagnostics   # about 8 minutes
```

Outputs: `results/supplementary/continuous_diagnostics.md/.json` and
`results/supplementary/NONCOMPLIANT_neighbourhood_size_sweep.md/.json`.
