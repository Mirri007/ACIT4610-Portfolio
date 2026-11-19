# ACIT4610 Portfolio 2026: Bees Algorithm and Evolution Strategies

Code, data and results for the ACIT4610 final portfolio (OsloMet, 2026).

| Folder | Contents | Status |
|--------|----------|--------|
| [`problem_1/`](problem_1/README.md) | Bees Algorithm: TSP (Part A) and continuous functions (Part B) | Part A done; Part B not started |
| `problem_2/` | Evolution Strategies for portfolio optimisation | Not started |
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
```

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
