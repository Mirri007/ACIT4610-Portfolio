# Requirements Compliance Matrix

Each technical requirement of the assignment (ACIT4610 Final Group Project 2026), with its
implementation, the evidence that it is met, and the verification status. "Verified" means the
evidence was checked by the automated tests, the independent audit scripts and/or the saved outputs.
Paths are relative to the problem folder unless stated otherwise.

## General

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| G1 | One GitHub repository, separate folder per problem | `problem_1/`, `problem_2/` | Repository structure | Verified |
| G2 | Clean Python code with inline documentation of the algorithmic logic | Docstrings and comments in all modules | Source files | Verified |
| G3 | README with step-by-step installation, dependencies and how to run on the data | `README.md`, `problem_1/README.md`, `problem_2/README.md`; `requirements.txt` (pinned versions) | Clean-clone installation and runs | Verified |
| G4 | Code is executable, loads the data and generates the outputs | Experiment, table and plot scripts | Clean-clone reproduction of all 650 runs and tables (identical except runtime) | Verified |
| G5 | Scripts reproduce the reported experiments and figures | `experiments/run_*`, `make_*_tables`, `make_*_plots` | Commands in the READMEs | Verified |
| G6 | AI-produced code clearly marked | Attribution header in every AI-generated source file | `docs/ai_declaration.md` | Verified |

## Problem 1: Bees Algorithm, common rules

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| BA1 | Bees Algorithm of Pham et al. (2006) | `src/bees_algorithm.py` (shared by Parts A and B) | `audit_tsp_trace`, `audit_continuous_trace` rebuild every iteration | Verified |
| BA2 | Permutation (Part A) and real vector (Part B) representations | `src/tsp_tour.py`, `src/bees_continuous.py` | Tests | Verified |
| BA3 | Choose and record the BA settings for each part | `TSP_BEES_SETTINGS`, `CONTINUOUS_BEES_SETTINGS`; selection by pilot studies | `problem_1/README.md`; `docs/implementation_notes.md` | Verified |
| BA4 | 30,000 objective evaluations per run | `EvaluationTracker` (single counting point) | Tests; audits of all 200 saved runs | Verified |
| BA5 | Count the initial population, recruits and scouts, including rejected candidates | `EvaluationTracker.evaluate` | Tests with an independent call counter; trace audits | Verified |
| BA6 | Stop at the budget; incomplete final iteration allowed | Budget check before every candidate | Tests (budget ending during recruitment and scouting); trace audits | Verified |
| BA7 | Record initial best, best-so-far history and final best solution | Saved per run (JSON + convergence CSV) | `audit_tsp_results`, `audit_continuous_results` | Verified |

## Problem 1, Part A: TSP

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| A1 | Permutation with each city once; city 1 fixed first, appended only for display | `create_random_tour`, `is_valid_tour`, `closed_route_city_ids` | Tests; all 120 saved tours re-validated | Verified |
| A2 | Objective: consecutive legs plus the return leg | `tour_length` | Hand-worked test (14 vs 10 without return leg) | Verified |
| A3 | Six TSPLIB instances (eil51 426, berlin52 7542, st70 675, eil76 538, kroA100 21282, ch150 6528), decompressed before loading | `data/tsplib_original/*.tsp.gz`, `read_text_file` (gzip) | Tests load all six | Verified |
| A4 | Validate NAME, TYPE (= TSP), DIMENSION, EDGE_WEIGHT_TYPE (= EUC_2D), NODE_COORD_SECTION, row count, unique ids | `src/tsplib.py` | One test per rule | Verified |
| A5 | d_ij = floor(√(…) + 0.5); each edge rounded before summing, including the return edge | `compute_distance_matrix`, `tour_length` | Rounding tests; published optimal tours reproduce all six optima | Verified |
| A6 | Optimal tours only for checking distances, never for initialising or guiding the BA | Stored only in `tests/reference_optimal_tours/` | No reference outside `tests/` | Verified |
| A7 | Uniformly shuffled initial scouts | `create_random_tour` | Uniformity test | Verified |
| A8 | Two versions: swap and segment reversal; one random move per recruit; city 1 fixed | `src/tsp_neighbourhoods.py` | Tests; trace audit | Verified |
| A9 | Same settings and seed list for both versions | One settings object; seeds 0–9 | Audit: identical settings and initial populations | Verified |
| A10 | 10 seeds × 6 instances × 2 versions = 120 runs | `experiments/run_tsp_experiments.py` | 120 files in `results/raw/tsp/` | Verified |
| A11 | Per run: final length, gap, runtime, evaluation count | Saved per run | `results/raw/tsp_all_runs.csv` | Verified |
| A12 | Gap(%) = 100 (L_BA − L\*) / L\* | `percentage_gap` | Test; audit | Verified |
| A13 | Summary table: instance, cities, optimum, best, mean, std, mean gap, mean runtime | `make_tsp_tables.py` | `results/tables/tsp_summary.md` | Verified |
| A14 | Convergence plots (berlin52, ch150): mean best-so-far over 10 runs, both versions, optimum marked | `make_tsp_plots.py` | `results/figures/tsp_convergence_berlin52.png`, `tsp_convergence_ch150.png` | Verified |
| A15 | Route plot of the shortest tour over both versions and all runs (berlin52), labelled with neighbourhood, seed, length, gap, start city; return leg drawn | `make_tsp_plots.py` | `results/figures/tsp_route_berlin52.png` (reversal, seed 7, 7,670, 1.70 %) | Verified |

## Problem 1, Part B: Continuous optimisation

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| B1 | Sphere, Rosenbrock, Rastrigin, Ackley with the specified bounds; D = 10 and 30 | `src/benchmark_functions.py` | Tests | Verified |
| B2 | Check each function at its minimiser and another point against the SFU definitions | `tests/test_benchmark_functions.py` | Minimisers, hand values, transcription of the SFU R code at random points | Verified |
| B3 | Known minimisers never inserted into the search | Minimisers only in tests | Source files | Verified |
| B4 | Scouts uniform within the bounds | `create_random_vector` | Uniformity test | Verified |
| B5 | Neighbour: independent U(−10 %, +10 %) of the range per coordinate, clipped to the bounds | `create_neighbour_vector` | Tests; trace audit of every recruit | Verified |
| B6 | Record settings for site selection, recruitment and scouting | `CONTINUOUS_BEES_SETTINGS` | `problem_1/README.md` | Verified |
| B7 | 10 seeds × 4 functions × 2 dimensions = 80 runs, full budget | `experiments/run_continuous_experiments.py` | 80 files in `results/raw/continuous/`; audit | Verified |
| B8 | Per run: final value, best vector, runtime, evaluations | Saved per run | `results/raw/continuous_all_runs.csv` | Verified |
| B9 | Summary table: function, D, best, mean, std, mean runtime | `make_continuous_tables.py` | `results/tables/continuous_summary.md` | Verified |
| B10 | Convergence plot, Rastrigin D = 10, axis transformation labelled | `make_continuous_plots.py` | `results/figures/continuous_convergence_rastrigin_D10.png` (log y-axis) | Verified |
| B11 | Boxplots of final values at D = 30, four panels in one figure, labelled axes | `make_continuous_plots.py` | `results/figures/continuous_boxplots_D30.png` | Verified |

## Problem 1: deliverables

| ID | Requirement | Evidence | Status |
|---|---|---|---|
| P1D1 | Original TSPLIB instances and source URLs in the repository | `data/tsplib_original/`; `problem_1/README.md` | Verified |
| P1D2 | Raw per-run results and best-so-far logs (seeds, values, evaluations, runtime, tours/vectors) | `results/raw/`, `results/convergence/` | Verified |
| P1D3 | README: dependency versions, all BA settings, seed lists, data locations, commands for one run and the full set | `problem_1/README.md` | Verified |

## Problem 2: Evolution Strategies

| ID | Requirement | Implementation | Evidence | Status |
|---|---|---|---|---|
| E1 | All five OR-Library files (31/85/89/98/225 assets; 496/3,655/4,005/4,851/25,425 records) | `data/port1.txt` … `port5.txt` | Parser counts; tests | Verified |
| E2 | Parse returns, standard deviations and correlations (stored in C_ij and C_ji, 1-based indices) | `src/portfolio_data.py` (line-by-line validation) | Independent-parser test | Verified |
| E3 | Σ_ij = s_i s_j C_ij; R(w) = rᵀw; objective V(w) = wᵀΣw | `build_covariance`, `expected_return`, `portfolio_variance` | Double-loop test; the assignment's A/B example | Verified |
| E4 | Targets R_min(α) = (1 − α)R_eq + αr_max, α ∈ {0.25, 0.50, 0.75}; 15 cases | `build_case`, `load_all_cases` | Tests | Verified |
| E5 | port1 checkpoint (R_eq, V(u), R_min(0.5)) | — | Test reproduces all three values | Verified |
| E6 | Repair before evaluation: simplex projection, then return repair with β | `project_onto_simplex`, `repair_portfolio`, `PortfolioEvaluator` | Hand examples; comparison with bisection; feasibility on all cases | Verified |
| E7 | Final solutions within the tolerances (w_i ≥ −10⁻⁸, abs(Σw − 1) ≤ 10⁻⁸, R(w) ≥ R_min − 10⁻⁸) | `feasibility_violations` | 450/450 feasible (independent audit) | Verified |
| E8 | (1+1)-ES: uniform init + repair; Gaussian mutation; strict acceptance; σ₀ = 0.1/√n; 1/5 rule (e^(1/3), e^(−1/12)); σ ∈ [10⁻⁸, 1] | `src/es_one_plus_one.py` | Trace test and trace audit rebuild the σ sequence | Verified |
| E9 | (μ+λ) and (μ,λ): μ = 10, λ = 70; recombination of two random parents (mean weights, geometric-mean σ); self-adaptation with τ' = 1/√(2n), τ = 1/√(2√n), shared Z₀; clamped σ | `src/es_population.py` (two *different* parents chosen) | Unit and statistical tests; trace audit | Verified |
| E10 | Survivor selection: plus from parents ∪ offspring; comma from offspring only | `select_survivors` | Selection rebuilt from logged runs | Verified |
| E11 | Separate archive of the best valid allocation, including initialisation; not used for parent selection | `PortfolioEvaluator` | Trace audit | Verified |
| E12 | Same cases, repair, 10 seeds and 30,000 evaluations for all variants (450 runs); count every evaluation; final batch may be smaller (included in the archive) | `experiments/run_es_experiments.py` | 450 files in `results/raw/es/`; 10 + 428 × 70 + 30 rebuilt by the trace audit | Verified |
| E13 | Per run: best valid allocation, expected return, variance, runtime | Saved per run | `results/raw/es_all_runs.csv` | Verified |
| E14 | Summary table (15 cases × 3 variants): case, assets, target, best and mean variance, std, feasible-run rate, mean runtime; statistics over valid runs, runtime over all runs | `make_es_tables.py` | `results/tables/es_summary.md` | Verified |
| E15 | Convergence plot (port5_alpha050): mean archive best variance vs evaluations, all variants on one plot | `make_es_plots.py` | `results/figures/es_convergence_port5_alpha050.png` | Verified |
| E16 | Consistent variant labels and case identifiers | Labels (1+1)-ES, (μ+λ)-ES, (μ,λ)-ES; cases `portk_alphaXXX` | Tables and figures | Verified |
| E17 | README: setup, dependencies and versions, dataset sources, seeds, parameters, commands for one case and the full set | `problem_2/README.md` | — | Verified |
