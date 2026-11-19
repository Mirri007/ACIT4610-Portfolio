# Problem 2: Portfolio Optimisation with Evolution Strategies

Three ES variants, (1+1)-ES, (μ+λ)-ES and (μ,λ)-ES, minimise portfolio variance subject to a
long-only budget constraint and a minimum expected return, on 5 OR-Library datasets × 3 return
targets = 15 cases. All three variants are implemented, tested, run and audited.

All commands are run from **this folder** (`problem_2/`) after installing the dependencies
(see the main [README](../README.md)).

## Folder layout

| Path | Contents |
|------|----------|
| `data/port1.txt` … `port5.txt` | Original OR-Library files, unmodified |
| `src/portfolio_data.py` | Line-by-line parser with validation, covariance Σ_ij = s_i s_j C_ij, return targets, the 15 cases |
| `src/portfolio_model.py` | Expected return, variance (objective), simplex projection, return-target repair, feasibility tolerances |
| `src/portfolio_evaluator.py` | Repairs + evaluates + counts every candidate; keeps the best-valid archive |
| `src/es_one_plus_one.py` | (1+1)-ES with the 1/5th success rule |
| `src/es_population.py` | (μ+λ)-ES and (μ,λ)-ES: recombination, self-adaptation, survivor selection |
| `src/run_es.py` | Runs one variant on one case with one seed; **budget, seed lists, variant labels** |
| `src/statistics_tools.py` | Exact sign-flip test, bootstrap interval, Holm correction (used for the plus/comma comparison) |
| `supplementary/` | Post-hoc diagnostics and supplementary analyses (**not** required results; see below) |
| `experiments/` | Experiment, table, figure and audit scripts |
| `tests/` | Automated tests |

## Data

| File | Assets n | Correlation records | Source |
|------|---------:|--------------------:|--------|
| port1.txt | 31 | 496 | https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/port1.txt |
| port2.txt | 85 | 3,655 | https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/port2.txt |
| port3.txt | 89 | 4,005 | https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/port3.txt |
| port4.txt | 98 | 4,851 | https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/port4.txt |
| port5.txt | 225 | 25,425 | https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/port5.txt |

File format description: https://people.brunel.ac.uk/~mastjjb/jeb/orlib/portinfo.html.

Return targets: R_min(α) = (1 − α)·R_eq + α·r_max with α ∈ {0.25, 0.50, 0.75}. Case names are
`port<k>_alpha<025|050|075>`, e.g. `port5_alpha050`.

The port1 parser checkpoint is reproduced by a test: R_eq = 0.003504064516129,
V(u) = 0.001130937943724, R_min(0.50) = 0.007184532258065.

## Repair (applied to every candidate before evaluation)

1. Project z onto the probability simplex: q_i = max(z_i − θ, 0), with θ chosen so Σq = 1
   (sorting algorithm, implemented in `project_onto_simplex`).
2. If R(q) < R_min: w = (1 − β)·q + β·e_j, where j is the highest-return asset and
   β = (R_min − R(q)) / (r_max − R(q)). Otherwise w = q.

Every final solution is checked against w_i ≥ −1e−8, |Σw − 1| ≤ 1e−8 and R(w) ≥ R_min − 1e−8.

## Parameters (all fixed by the assignment; nothing was tuned)

| | (1+1)-ES | (μ+λ)-ES | (μ,λ)-ES |
|---|---|---|---|
| Parents / offspring | 1 / 1 | μ = 10 / λ = 70 | μ = 10 / λ = 70 |
| Initial weights | U[0, 1] per weight, then repair | same, for each of the 10 parents | same |
| Step size | one scalar σ, initial 0.1/√n | one σ per weight, initial 0.1/√n | same |
| Step-size update | ×exp(1/3) on success, ×exp(−1/12) on failure (1/5 rule) | σ'_i = σ_r,i·exp(τ'Z₀ + τZ_i), τ' = 1/√(2n), τ = 1/√(2√n) | same |
| Step-size bounds | [1e−8, 1.0] | [1e−8, 1.0] | [1e−8, 1.0] |
| Recombination | none | two different parents chosen uniformly at random; weights averaged, step sizes geometric mean | same |
| Survivor selection | child replaces parent only if variance strictly lower | best 10 of parents + offspring | best 10 of offspring only |
| Evaluations per run | 1 + 29,999 trials = 30,000 | 10 + 428 × 70 + 30 = 30,000 | same |

Interpretation choices (not specified by the assignment):
- The two parents for recombination are *different* individuals.
- Ties in survivor selection keep the earlier individual.
- After the incomplete final batch of 30 children, no survivor selection is done (the run ends; the
  30 children are still evaluated and archived).

All three variants keep a separate archive of the best valid allocation (including initialisation),
which is what each run returns. The archive is never used to choose parents.

## Seeds

| Purpose | Seeds |
|---|---|
| Final experiments (all 450 reported runs) | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 |
| Preliminary smoke tests and runtime measurements | 900–904 |
| Automated tests | ≥ 1000 |
| Post-hoc diagnostics (supplementary) | 300–305 (310 for random-portfolio check) |
| Parameter tuning | none needed (all parameters fixed by the assignment) |

## Commands

```bash
# Automated tests (about 10 seconds)
python -m pytest

# One single test case: port1, alpha = 0.50, (1+1)-ES, seed 0
python -m experiments.run_es_experiments --cases port1_alpha050 --variants one_plus_one --seeds 0

# Full experiment: 15 cases x 3 variants x 10 seeds = 450 runs
# (total search time 10.5 minutes on an Apple M2)
python -m experiments.run_es_experiments

# Tables and figures from the saved results
python -m experiments.make_es_tables
python -m experiments.make_es_plots

# Audits (exit code 0 = passed)
python -m experiments.audit_es_results   # independent re-check of all 450 runs + summary (plain Python, no project code)
python -m experiments.audit_es_trace     # logs every evaluation of 6 full runs and rebuilds each variant's rules
```

Finished runs are skipped when the experiment is restarted; add `--overwrite` to re-run them.

The experiment and trace scripts run NumPy's linear algebra **single-threaded** (set at the top of
the script). In a preliminary measurement (seeds 900–904), multi-threading made port5 runs about twice
as slow and their runtimes erratic, while the results were bit-for-bit identical. Since runtime is
compared between the variants, stable single-threaded timing is used. Tests run correctly either way.

## Outputs

| File | Contents |
|------|----------|
| `results/raw/es/<case>_<variant>_seed<seed>.json` | One file per run: settings, target, best valid weights, return, variance, feasibility, runtime, evaluations, archive history, step sizes / population-best history |
| `results/convergence/es/<case>_<variant>_seed<seed>.csv` | Archive best-so-far log: `evaluation, archive_best_variance` (one row per improvement) |
| `results/raw/es_all_runs.csv` | All 450 runs in one table, including weights |
| `results/tables/es_summary.csv` / `.md` | Required summary: case, assets, target return, best/mean variance, std, feasible runs, mean runtime (45 rows) |
| `results/tables/es_comparison.md` | Variants side by side per case; paired per-seed comparisons |
| `results/tables/es_analysis.md` | Stagnation, sparsity, constraint activity, (1+1) step sizes |
| `results/tables/es_plus_vs_comma.md` | (μ+λ) vs (μ,λ) with the **case** as statistical unit: exact sign-flip tests, bootstrap intervals, Holm correction, limitations |
| `results/figures/es_convergence_port5_alpha050.png` | **Required** convergence plot: mean archive best variance vs evaluations, three variants |
| `results/figures/es_comma_population_vs_archive_port5_alpha050.png` | Supplementary: (μ,λ) population best vs archive |
| `results/figures/es_step_sizes_port5_alpha050.png` | Supplementary: (1+1) step-size adaptation |
| `results/es_experiment_log.txt` | Console log of the full experiment |

Variance is w^TΣw in squared return units (returns in the data are decimal fractions per period).
The results describe relative performance of the ES variants on historical data only; they say
nothing about future investment performance.

## Supplementary analyses (post hoc; not part of the required experiments)

Added after the critical review (`docs/critical_review.md`). They change no algorithm, setting, seed,
required result or required figure. Outputs go to `results/supplementary/` only.

| Kind | Script | What it does | Seeds |
|---|---|---|---|
| Supplementary analysis | `supplementary/reference_optima.py` | Minimum-variance portfolio per case: SLSQP candidate, exact KKT solve, KKT residuals, weak-duality bound, checks against all ES runs and 20,000 random portfolios; gap of each ES variant. **Numerically verified, not formally proven.** Context only: the assignment's conclusions stay relative | 310 (random check) |
| Post-hoc diagnostic | `supplementary/one_plus_one_diagnostics.py` | Why (1+1) stagnates: association in saved data, interventions with **modified (1+1) versions (not the assignment's algorithm)**, success-probability probe, step-size vs dimension decomposition | 300–305 |

Setup and commands (from `problem_2/`; the reference optima need SciPy):

```bash
python -m pip install -r ../requirements-supplementary.txt   # adds scipy==1.17.1
python -m supplementary.reference_optima          # about 30 s; run this first
python -m supplementary.one_plus_one_diagnostics  # about 3 minutes; uses the reference optima
```

Outputs: `results/supplementary/reference_optima.md/.csv`, `reference_optima_weights.json`,
`one_plus_one_diagnostics.md/.json`.
