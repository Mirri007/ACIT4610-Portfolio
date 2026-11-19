# Problem 1: Bees Algorithm

Part A (TSP) is implemented, tested and run. Part B (continuous functions) is not started yet.

All commands below are run from **this folder** (`problem_1/`) after installing the
dependencies (see the main [README](../README.md)).

## Folder layout

| Path | Contents |
|------|----------|
| `data/tsplib_original/` | The six original TSPLIB files (`.tsp.gz`), unmodified |
| `src/tsplib.py` | Loads a `.tsp.gz` file and validates NAME, TYPE, DIMENSION, EDGE_WEIGHT_TYPE, NODE_COORD_SECTION, row count, unique ids |
| `src/tsp_tour.py` | Rounded EUC_2D distance matrix, tour length (incl. return leg), random tours, tour validation |
| `src/tsp_neighbourhoods.py` | Swap move and segment-reversal move |
| `src/evaluation_tracker.py` | Counts every objective evaluation, enforces the budget, records the best-so-far history |
| `src/bees_algorithm.py` | The Bees Algorithm (shared by Part A and Part B) |
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

Settings were chosen with a pilot study on different seeds (100–104):
`python -m experiments.tsp_pilot_settings` → `results/tables/tsp_pilot_settings.csv`
(reasoning in [docs/implementation_notes.md](../docs/implementation_notes.md)).

## Part A: commands

```bash
# Run the automated tests (about 6 seconds)
python -m pytest

# One single run (berlin52, segment reversal, seed 0), about 0.6 seconds
python -m experiments.run_tsp_experiments --instances berlin52 --neighbourhoods reversal --seeds 0

# The full Part A experiment: 6 instances x 2 neighbourhoods x 10 seeds = 120 runs
# (total search time was 71 s on an Apple M2)
python -m experiments.run_tsp_experiments

# Tables and figures from the saved results
python -m experiments.make_tsp_tables
python -m experiments.make_tsp_plots
```

Finished runs are skipped when the experiment is restarted; add `--overwrite` to re-run them.

## Part A: outputs

| File | Contents |
|------|----------|
| `results/raw/tsp/<instance>_<neighbourhood>_seed<seed>.json` | One file per run: settings, seed, initial best, final best length, gap, runtime, evaluations, iterations, final tour (city ids, starting at city 1), best-so-far history |
| `results/convergence/tsp/<instance>_<neighbourhood>_seed<seed>.csv` | Best-so-far log: `evaluation, best_so_far_length`, one row per improvement (value constant until the next row) |
| `results/raw/tsp_all_runs.csv` | All 120 runs in one table, including final tours |
| `results/tables/tsp_summary.csv` / `.md` | Required summary table (instance, cities, optimum, best, mean, std, mean gap, mean runtime) |
| `results/tables/tsp_pilot_settings.csv` | Pilot study used to choose the settings |
| `results/figures/tsp_convergence_berlin52.png`, `tsp_convergence_ch150.png` | Mean best-so-far vs evaluations, both neighbourhoods, optimum marked |
| `results/figures/tsp_route_berlin52.png` | Shortest berlin52 tour over all 20 runs, with return leg and labels |
| `results/tsp_experiment_log.txt` | Console log of the full experiment run |

Gap(%) = 100 · (L_BA − L*) / L*, where L_BA is the final best valid tour length of the run.
