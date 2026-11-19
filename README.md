# ACIT4610 Portfolio 2026: Bees Algorithm and Evolution Strategies

Code, data and results for the ACIT4610 final portfolio (OsloMet, 2026).

| Folder | Contents | Status |
|--------|----------|--------|
| [`problem_1/`](problem_1/README.md) | Bees Algorithm: TSP (Part A) and continuous functions (Part B) | Parts A and B done and audited |
| [`problem_2/`](problem_2/README.md) | Evolution Strategies for portfolio optimisation | Done and audited |
| `docs/` | Requirements checklist, implementation notes, AI development log, exam notes | |

## Requirements

- Python 3.11 (developed with 3.11.1)
- numpy 1.26.4, matplotlib 3.9.2, pytest 8.3.3 (pinned in `requirements.txt`)

## Installation

```bash
git clone https://github.com/Mirri007/ACIT4610-Portfolio.git
cd ACIT4610-Portfolio
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Running

Each problem is run from its own folder. Exact commands, settings, seeds and output files are
listed in each problem's README:

```bash
cd problem_1
python -m pytest                                   # automated tests
python -m experiments.run_tsp_experiments          # all 120 TSP runs
python -m experiments.make_tsp_tables              # summary tables
python -m experiments.make_tsp_plots               # figures
python -m experiments.run_continuous_experiments   # all 80 continuous-function runs
python -m experiments.make_continuous_tables
python -m experiments.make_continuous_plots

cd ../problem_2
python -m pytest
python -m experiments.run_es_experiments           # all 450 ES runs
python -m experiments.make_es_tables
python -m experiments.make_es_plots
```

## Audits

Independent re-checks of the saved results (exit code 0 = all checks passed). Run from the problem folder:

| Folder | Command | What it checks |
|---|---|---|
| `problem_1` | `python -m experiments.audit_tsp_results` | All 120 TSP runs and the summary table, with its own parser and distance code (no project imports) |
| `problem_1` | `python -m experiments.audit_tsp_trace` | Logs every evaluation of 2 real runs and rebuilds the Bees Algorithm rules |
| `problem_1` | `python -m experiments.audit_continuous_results` | All 80 continuous runs and the summary table, with its own copy of the SFU formulas (no project imports) |
| `problem_1` | `python -m experiments.audit_continuous_trace` | Logs every evaluation of 3 real runs and rebuilds the rules, including the ±10 % neighbourhood |
| `problem_2` | `python -m experiments.audit_es_results` | All 450 ES runs and the summary table, in plain Python (no project imports, no NumPy) |
| `problem_2` | `python -m experiments.audit_es_trace` | Logs every evaluation of 6 full runs and rebuilds the rules of all three ES variants |

## Kinds of work in this repository

| Kind | Where | Status |
|---|---|---|
| Required experiments, tables and figures | `problem_*/experiments/`, `problem_*/results/{raw,convergence,tables,figures}/` | The assignment's results |
| Parameter pilots | `problem_1/experiments/*pilot*.py` | Chose the BA settings before the final runs |
| Audits | `problem_*/experiments/audit_*.py` | Independent re-checks of saved results |
| Post-hoc diagnostics and supplementary analyses | `problem_*/supplementary/`, `problem_*/results/supplementary/` | Added after the critical review; explain results, never replace them |

Supplementary analyses need one extra package: `python -m pip install -r requirements-supplementary.txt`
(SciPy, used only for a reference solver in Problem 2). See `docs/critical_review.md` and the problem READMEs.

## Data sources

All original data files are included unmodified.

- **TSPLIB** (G. Reinelt, Heidelberg University):
  `https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/<name>.tsp.gz` for eil51, berlin52, st70,
  eil76, kroA100 and ch150, stored in `problem_1/data/tsplib_original/`.
- **OR-Library portfolio data** (J.E. Beasley):
  `https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/port<k>.txt` for k = 1..5, stored in `problem_2/data/`.

## Use of AI

Code in this repository was generated with AI assistance (Claude Code, Anthropic). Every
AI-generated Python file starts with an `# AI attribution` header. See
[`docs/ai_development_log.md`](docs/ai_development_log.md) for what was generated at each stage.
