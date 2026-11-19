# Critical Review of Problems 1A, 1B and 2

Requested by the student on 2026-11-19 (instruction S7 in `ai_development_log.md`). The final
experimental results and algorithm settings were **not changed**. All new evidence comes from
read-only analysis of saved outputs and from **diagnostic runs with seeds 300–309**, which are used
nowhere else. Diagnostic runs were done with temporary scripts. Their outputs are copied verbatim
below; recommendations R2–R4 propose turning them into documented scripts in the repository.

---

## 1. Summary

- **No correctness errors were found.** Evidence:
  - all three audits pass, two of them independent of the project code;
  - 165 + 119 tests pass, and planted bugs are caught;
  - clean-clone reruns reproduce all 650 runs exactly (apart from runtime);
  - every mandatory dataset, run file, log, table and figure is present.
- **Main weaknesses** are in the **analysis and interpretation**, not in the implementation:
  1. The (μ+λ) vs (μ,λ) significance test used the wrong unit of analysis.
  2. Problem 2 had no absolute quality reference, so "all portfolios valid" said nothing about how
     good they are.
  3. The (1+1)-ES stagnation explanation was plausible but untested; it is now **partly confirmed and
     partly corrected**.
  4. The Problem 1B explanation was theoretical; it is now supported empirically.
- **No change to the final algorithms, settings or results is recommended.** In particular, no
  compliant change to Problem 1B gives a consistent improvement (section 2.1).

---

## 2. Findings

### 2.1 Problem 1B: why the results are weak, and can they be improved within the rules?

**Evidence A: the final solutions are frozen.** For each saved final best vector, 4,000 neighbours
were drawn with the assignment's neighbourhood (±10 % of the range on every coordinate, clipped):

| Function | D | P(one neighbour improves) | RMS distance to optimum per coordinate | Neighbour per-coordinate std (a/√3) | Share of total improvement after evaluation 15,000 |
|---|---|---|---|---|---|
| Sphere | 10 | 0.0000 | 0.205 | 0.591 | 0.05 % |
| Sphere | 30 | 0.0001 | 0.427 | 0.591 | 0.26 % |
| Rosenbrock | 10 | 0.0001 | 0.947 | 0.866 | 0.00 % |
| Rosenbrock | 30 | 0.0001 | 1.190 | 0.866 | 0.01 % |
| Rastrigin | 10 | 0.0001 | 1.210 | 0.591 | 2.98 % |
| Rastrigin | 30 | 0.0002 | 1.996 | 0.591 | 5.22 % |
| Ackley | 10 | 0.0000 | 1.365 | 3.784 | 0.00 % |
| Ackley | 30 | 0.0002 | 2.917 | 3.784 | 2.79 % |

At the end of a run, about 1 in 5,000–10,000 neighbours improves. For Sphere and Ackley, the
remaining distance to the optimum is *smaller* than the typical size of one neighbourhood step, so
almost every step overshoots. For the unimodal functions, the second half of the budget produces
almost nothing.

**Evidence B: the BA settings hardly matter.** Five settings, spanning very explorative to extreme
local search, were run at the experiment dimensions with diagnostic seeds 300–309. The table gives
the mean final value, then the ratio to the current setting C, then the difference in units of C's
standard deviation:

| Function, D | A (n50 m10 e3) | **C (current)** | D (n6 m2 e1) | E (n2 m1 e1, nep200) | G (n100 m5 e1) |
|---|---|---|---|---|---|
| Sphere 10 | 1.14×, +0.9 sd | 1.00 | 0.99×, −0.1 | 0.98×, −0.1 | 1.23×, +1.5 |
| Sphere 30 | 1.08×, +1.1 | 1.00 | 0.95×, −0.6 | 0.97×, −0.4 | 1.29×, +3.9 |
| Rosenbrock 10 | 0.88×, −0.2 | 1.00 | 0.77×, −0.3 | 1.17×, +0.3 | 0.95×, −0.1 |
| Rosenbrock 30 | 1.01×, +0.1 | 1.00 | 0.84×, −1.0 | 0.80×, −1.2 | 1.16×, +1.0 |
| Rastrigin 10 | 1.00×, +0.1 | 1.00 | 0.88×, −1.4 | 1.20×, +2.3 | 1.00×, −0.0 |
| Rastrigin 30 | 0.99×, −0.1 | 1.00 | 1.04×, +0.4 | 1.01×, +0.1 | 1.04×, +0.4 |
| Ackley 10 | 1.01×, +0.2 | 1.00 | 1.04×, +0.6 | 1.00×, −0.0 | 1.06×, +0.8 |
| Ackley 30 | 1.04×, +1.0 | 1.00 | 0.96×, −0.9 | 1.00×, +0.1 | 1.05×, +1.2 |

No setting is consistently better than C. D gains up to 23 % on some cases and loses on others;
E is worse on Rastrigin D10; many scouts (G) is clearly worse on Sphere D30. The pilot's conclusion
("settings matter little") is confirmed at D = 10 and 30 on independent seeds.

**Evidence C: the fixed neighbourhood size is the binding constraint.** This is a **diagnostic only**:
it violates the assignment's fixed 10 %, and must never be presented as a result. Current settings,
seeds 300–309, mean final value:

| Function, D | 10 % (assignment) | 3 % | 1 % |
|---|---|---|---|
| Sphere 10 | 0.4185 | 0.0357 | 0.0048 |
| Sphere 30 | 5.625 | 0.533 | 0.071 |
| Rosenbrock 10 | 107.1 | 23.8 | 7.5 |
| Rosenbrock 30 | 2,795 | 191.6 | 95.7 |
| Rastrigin 10 | 36.6 | 52.2 | 45.0 |
| Rastrigin 30 | 268.3 | 271.0 | 210.9 |
| Ackley 10 | 6.03 | 3.11 | 16.92 |
| Ackley 30 | 10.38 | 16.41 | 19.92 |

- Smaller patches help the unimodal functions enormously (Sphere about 90×).
- Smaller patches *hurt* the multimodal ones: Ackley D10 gets 3× worse at 1 %, because small steps
  cannot leave the flat outer region or local minima.
- So **no fixed size is best for all functions**. This is the exploration–exploitation trade-off that
  later BA versions address with neighbourhood shrinking, which the assignment's fixed ±10 % does
  not allow.

**Conclusion for 1B.**
- The weak results are mainly explained by the assignment-specified fixed neighbourhood, not by our
  settings or by an implementation error.
- There is no compliant change that improves results consistently. Changing the settings now would
  be tuning on noise, would require a new pilot and a full rerun, and would risk exactly what the
  student wants to avoid: "better-looking numbers".
- The right improvement is to **document the evidence**, not to change the algorithm.

### 2.2 Problem 2: is the (1+1)-ES stagnation explanation supported?

**Reference optima.** For every case the exact minimum variance V\* was computed: SLSQP, then an
exact solution of the KKT equations on the active set, then a check of all KKT conditions. Because the
problem is convex, this **certifies global optimality**. All 15 cases were certified, and no ES run
went below V\*.

| Case | V\* | Assets in optimum | Mean gap (1+1) | Mean gap (μ+λ) | Mean gap (μ,λ) | Best single ES run |
|---|---|---|---|---|---|---|
| port1_alpha025 | 7.68998e−4 | 6 | 14.76 % | 0.01 % | 0.02 % | 0.0001 % |
| port1_alpha050 | 1.16632e−3 | 4 | 30.68 % | 0.00 % | 0.00 % | 0.0000 % |
| port1_alpha075 | 2.31085e−3 | 3 | 17.17 % | 0.00 % | 0.00 % | 0.0000 % |
| port2_alpha025 | 1.53469e−4 | 24 | 20.57 % | 7.07 % | 5.13 % | 2.47 % |
| port2_alpha050 | 2.47371e−4 | 20 | 50.15 % | 6.14 % | 8.25 % | 2.58 % |
| port2_alpha075 | 4.70406e−4 | 7 | 118.49 % | 5.65 % | 3.87 % | 0.58 % |
| port3_alpha025 | 2.33484e−4 | 26 | 25.05 % | 5.79 % | 4.76 % | 2.67 % |
| port3_alpha050 | 3.38211e−4 | 16 | 38.72 % | 4.74 % | 3.24 % | 1.61 % |
| port3_alpha075 | 6.05539e−4 | 7 | 39.69 % | 1.15 % | 3.01 % | 0.05 % |
| port4_alpha025 | 2.02349e−4 | 27 | 46.43 % | 12.20 % | 16.17 % | 8.36 % |
| port4_alpha050 | 3.71762e−4 | 17 | 94.94 % | 10.62 % | 15.79 % | 4.82 % |
| port4_alpha075 | 7.64363e−4 | 8 | 109.16 % | 5.59 % | 8.25 % | 2.60 % |
| port5_alpha025 | 3.04641e−4 | 12 | 84.72 % | 15.15 % | 9.81 % | 1.56 % |
| port5_alpha050 | 3.36164e−4 | 14 | 116.15 % | 17.84 % | 12.23 % | 4.84 % |
| port5_alpha075 | 4.56281e−4 | 10 | 137.46 % | 16.44 % | 18.44 % | 7.55 % |

(The return constraint is active at the optimum in 14 of 15 cases; port5_alpha025 is the exception.)

New facts this reveals:
- **The population ES find the exact optimum on port1** (all 31 assets is a small problem), and come
  within 1–18 % on average elsewhere. The gap grows with the number of assets.
- **(1+1) ends 15–137 % above the optimum.** The problem is convex, so there are **no local optima**:
  the stagnation cannot be a "local optimum trap". It must come from the search dynamics.
- **The optima are sparse (3–27 assets).** (1+1) final portfolios hold on average 19.5 (port1) to
  111 (port5) assets. This supports the sparsity part of the earlier explanation.

**Correlation in the saved data** (150 runs, 500-evaluation windows from the step-size logs):

| σ at start of window | Windows | Mean relative variance improvement per window |
|---|---|---|
| ≥ 10⁻³ | 161 | 24.2 % |
| 10⁻⁴–10⁻³ | 255 | 3.39 % |
| 10⁻⁵–10⁻⁴ | 800 | 0.69 % |
| 10⁻⁶–10⁻⁵ | 1,703 | 0.11 % |
| 10⁻⁷–10⁻⁶ | 2,152 | 0.013 % |
| < 10⁻⁷ | 3,929 | 0.0016 % |

The median evaluation at which σ first drops below 10⁻⁴ is 1,000; the archive is within 1 % of its
final value at a median of 3,890. Progress collapses as σ shrinks. This is only a correlation:
a hard landscape could cause both.

**Causal test 1: prevent the collapse** (diagnostic variants, NOT the assignment's (1+1); seeds
300–304; mean gap to V\*):

| Case | As specified (floor 10⁻⁸) | σ floor 10⁻⁴ | σ floor 10⁻³ | Fixed σ₀, no adaptation |
|---|---|---|---|---|
| port1_alpha050 | 25.76 % | 11.03 % | 2.95 % | 0.02 % |
| port3_alpha050 | 34.37 % | 13.36 % | 7.04 % | 9.31 % |
| port5_alpha050 | 122.59 % | 85.35 % | 76.40 % | 86.94 % |

**Causal test 2: why does σ collapse?** The probability that one mutation + repair improves, measured
at the saved stagnated (1+1) solutions (seed 0), 3,000 samples per σ:

| Case | σ = 1e−8 | 1e−7 | 1e−6 | 1e−5 | 1e−4 | 1e−3 | 1e−2 |
|---|---|---|---|---|---|---|---|
| port1_alpha050 | 0.146 | 0.151 | 0.083 | 0.053 | 0.048 | 0.042 | 0.048 |
| port3_alpha050 | 0.123 | 0.032 | 0.009 | 0.006 | 0.005 | 0.002 | 0.001 |
| port5_alpha050 | 0.157 | 0.008 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

(The same probe at the certified optimum gives 0.000, as it must.)

**Verdict on the explanation.** It is **partly supported, and needs one correction.**

- **Supported:**
  - At the stagnated points, **no step size gives the 20 % success the 1/5 rule aims for** (the
    maximum is 0.157), so the rule is *forced* to keep shrinking σ.
  - On a smooth function with no active constraints, tiny steps would succeed about 50 % of the time.
    The observed 12–16 % fits the kinks created by the repair: weights cut at 0, return pinned at R_min.
  - Preventing the collapse removes most of the gap on port1 and port3, so the **collapse is a real
    cause** there.
- **Correction:**
  - On port5 (225 assets), avoiding the collapse helps only partly (123 % → 76–87 %).
  - At a point 116 % above the optimum, **no** mutation with σ ≥ 10⁻⁶ improved in 3,000 tries,
    although improving directions must exist (convex problem).
  - So the second cause is that **one shared, isotropic step size cannot find the narrow set of
    improving directions in 225 dimensions under the repair**. The population ES avoid this with
    per-weight step sizes, recombination and 70 children per generation.
  - The earlier explanation (implementation notes, Problem 2 §7) presented σ collapse plus sparsity
    as the mechanism without testing it. For large n it overstates the role of σ.

### 2.3 Problem 2: (μ+λ) vs (μ,λ), corrected statistics

The earlier sign test pooled 150 seed pairs as if independent. They come from **15 cases** that differ
systematically, so the case is the right unit. Re-analysis on the saved results:

- **Unit = case (15 cases).**
  - Mean relative difference (plus − comma)/comma: +0.005 %, 95 % bootstrap CI [−1.30 %, +1.37 %].
  - Exact sign-flip randomisation test: **p = 0.994**.
  - Plus is lower in 7 of 15 cases.
  - **No evidence of an overall difference.**
- **Within each case (10 paired seeds; same initial parents).** Exact sign-flip test per case, with a
  Holm correction for 15 tests:
  - Significant after correction: only port1_alpha050 and port1_alpha075. There the difference is
    0.001 %: both variants reach the certified optimum, and comma is marginally more precise. It has
    **no practical relevance**.
  - port4_alpha025 favours plus (9/10 seeds, −3.4 %, unadjusted p = 0.004), but after the Holm
    correction p = 0.051, so it is not significant at the 5 % level.
- **The direction depends on the dataset.**
  - port4: plus better in all three cases (−2.5 % to −4.5 %).
  - port5 α = 0.25 / 0.50: comma better (about +5 %).
  - The others are mixed. With 10 seeds per case these cannot be separated from noise.
- **Equivalence cannot be claimed.** Within-case confidence intervals reach ±10 %, and no equivalence
  margin was defined in advance.

**Correct statement for the report:** "We found no evidence that either population variant is better
overall (case-level exact test p = 0.99). There are signs of dataset-dependent differences (port4
favoured plus, port5 at α ≤ 0.5 favoured comma), but with 10 runs per case they are not conclusive,
and the results do not show the variants to be equivalent either."

### 2.4 Problem 1A

- No issues found; the audits pass.
- Additional evidence: with the same seed, both neighbourhoods start from the identical initial
  population, and **segment reversal ends shorter than swap in 60 of 60 paired runs**. The
  "reversal is better" conclusion therefore needs no significance test to be convincing.

### 2.5 Correctness, counting, fairness, reproducibility (all parts)

| Check | Evidence | Result |
|---|---|---|
| Mathematics | TSP lengths reproduce all published optima; functions match the SFU reference code; variance matches an explicit double sum; projection matches bisection; port1 checkpoint exact; QP optima certified | Correct |
| Feasibility repair | 450/450 final portfolios feasible; 0 invalid evaluations; repaired returns exactly R_min when the repair acts | Correct |
| Evaluation counting | Exactly 30,000 in all 650 runs; traces rebuild 6 + 194×154 + 118 (1A), 10 + 144×207 + 182 (1B), 1 + 29,999 and 10 + 428×70 + 30 (2) | Correct |
| Fairness | Identical settings/seeds per comparison; identical initial populations for swap/reversal and plus/comma (verified); (1+1) not paired with the population variants (documented; 150/150 makes it immaterial) | Fair |
| Reproducibility | Clean clones from GitHub reproduce all 120 + 80 + 450 runs exactly except runtime | Reproducible |
| Completeness | All 17 mandatory items present (datasets, 650 run files and logs, 3 summary tables, 6 required figures, READMEs) | Complete |
| AI marking | Every non-empty Python file has the header; log updated | Complete |

---

## 3. Prioritised recommendations

| # | Priority | Recommendation | Rerun of final experiments? | Worth it? |
|---|---|---|---|---|
| R1 | High | Replace the pooled sign test with the clustered analysis (2.3) in the code, tables and documentation | No | Yes |
| R2 | High | Add the certified reference optima and gap table as a supplementary Problem 2 analysis | No | Yes |
| R3 | High | Add the (1+1) causal diagnostics (2.2) as a labelled script + table, and correct the explanation | No (diagnostic runs only, ~1 min) | Yes |
| R4 | High | Add the 1B diagnostics (2.1) as a labelled script + table; keep algorithm and settings | No (diagnostic runs only, ~8 min) | Yes |
| R5 | Medium | Correct the outdated claims in implementation notes, exam notes and READMEs (list in section 4) | No | Yes (required if R1–R4 are done) |
| R6 | Medium | Add the paired swap-vs-reversal comparison (60/60) to the Part A tables | No | Yes, cheap |
| R7 | Medium | Add tests for the new statistical helpers (exact sign-flip test, KKT certificate) | No | Yes, if R1–R2 are done |
| R8 | Low | Small hygiene: a one-line AI header comment in `pytest.ini`; mention in the README that the audits exist | No | Optional |
| – | Not recommended | Changing 1B settings; neighbourhood shrinking or site abandonment in 1B; σ floors or other changes to the specified ES; any rerun of final experiments | – | No |

### R1: Clustered plus-vs-comma statistics
- **Weakness:** `make_es_tables.py` reports a sign test over 150 pairs as if they were independent.
  They are clustered in 15 cases, so the p-value (0.165) is not valid for an overall claim. The
  current docs describe this as "not significant", which happens to be right, for the wrong reason.
- **Why the change helps:** it gives a valid overall test (case = unit), shows within-case evidence
  with a multiple-testing correction, and reveals the dataset-dependent pattern that the pooled test
  hides. It also stops the report from overstating either a difference or equivalence.
- **Compliance:** this is analysis of the required comparison; the assignment asks us to "compare the
  three ES variants using achieved variance, variability …".
- **Rerun:** no; only the table script and docs.
- **Worth it:** yes. It is cheap and directly affects a conclusion in the report.

### R2: Certified reference optima (supplementary)
- **Weakness:** "all portfolios valid" says nothing about quality. Without a reference we cannot tell
  that the population ES are optimal on port1 but up to 18 % above the optimum on port5, or that
  (1+1) is up to 137 % above.
- **Why the change helps:** it turns "relatively better" into an interpretable scale. It shows that
  the problem has no local optima, which is essential for explaining stagnation. It also shows how the
  gap grows with problem size, which the assignment asks us to discuss.
- **Compliance:** the assignment says to "limit conclusions to relative performance among the tested
  ES variants". The gaps must therefore be presented as **context and diagnosis**, not as claims about
  absolute ES quality or investment advice. With that framing it is a supplementary analysis, not a
  change to the experiment.
- **Rerun:** no.
- **Cost:** it needs SciPy as an *analysis-only* dependency (`requirements-analysis.txt`; the core
  experiments stay NumPy + Matplotlib). The KKT certificate makes the result independent of trusting
  the solver.
- **Worth it:** yes. This is the single most informative addition.

### R3: (1+1) stagnation diagnostics
- **Weakness:** the current explanation was untested and, as section 2.2 shows, overstates the role of
  σ for large n.
- **Why the change helps:** it turns a hypothesis into evidence: a correlation, an intervention and a
  probe. It gives a precise two-part answer for the exam: (i) the repair creates kinks where no step
  size reaches 20 % success, so the 1/5 rule must shrink σ; (ii) in 225 dimensions, a single isotropic
  σ rarely finds improving directions even without the collapse.
- **Compliance:** the diagnostic variants (σ floors, fixed σ) are **not** assignment variants. They
  must be labelled as diagnostics and never mixed into the results tables.
- **Rerun:** no final reruns; about 1 minute of diagnostic runs with seeds 300–304.
- **Worth it:** yes. The assignment explicitly requires discussing stagnation and step-size adaptation.

### R4: Problem 1B diagnostics, with no algorithm change
- **Weakness:** the docs' explanation (a theoretical Sphere argument plus the pilot) was not backed by
  measurements at the actual experiment dimensions.
- **Why the change helps:** Evidence A–C shows, from data, why the results are weak, that settings do
  not fix it, and that neighbourhood size is decisive. This answers the student's question honestly.
- **Compliance:** analysis is compliant. The 3 % / 1 % sweep violates the fixed 10 % and is allowed
  **only** as clearly labelled explanatory evidence, never as a result.
- **Rerun:** no final reruns; about 8 minutes of diagnostic runs with seeds 300–309.
- **Worth it:** yes. **Changing 1B's settings is not worth it:** there is no consistent gain (within
  about ±1.5 sd, mixed signs), it would need a new pilot and a full rerun, and it would be tuning on noise.

### R5: Outdated statements to correct
Listed in section 4. They are needed so that notes, README and report agree with the new evidence.

### R6: Paired comparison for Part A
- **Weakness:** the summary table compares swap and reversal only through means and standard deviations.
- **Why it helps:** the 60/60 paired result (same initial population) is the strongest, simplest
  evidence for the main Part A conclusion.
- **Compliant**, **no rerun**, **worth it** (a few lines in `make_tsp_tables.py`).

### R7: Tests for new helpers
Any statistical function used for a reported conclusion should be tested against hand-worked
examples, e.g. a sign-flip test on a tiny vector where all 2^k patterns can be listed by hand, and a
KKT certificate on a 2-asset problem with a known solution. Worth it if R1–R2 are done.

### R8: Hygiene (low priority)
- `pytest.ini` files have no AI header line, and the empty `__init__.py` files contain no code.
- `save_json_safely` and `expand_history` exist in both problem folders. That is acceptable, because
  the folders are separate packages; merging them would add complexity, not remove it.

---

## 4. Statements in the current documentation that are now outdated or imprecise

| Location | Current statement | Should become |
|---|---|---|
| `implementation_notes.md`, Problem 2 §6 | "(μ,λ) lower in 84 of 150 seed pairs; sign test p = 0.165, not a significant difference" | Clustered analysis (2.3): case-level p = 0.99; dataset-dependent pattern; neither difference nor equivalence shown |
| `implementation_notes.md`, Problem 2 §7 | Explanation "consistent with the data, not proven" | Partly confirmed: collapse forced by success < 1/5 at every σ, causal on port1/3; a second cause for large n (isotropic σ in 225 dimensions) |
| `implementation_notes.md`, Problem 2 §8 item 1 | "No absolute quality measure" | Resolved if R2 is accepted (supplementary certified optima) |
| `implementation_notes.md`, Problem 2 §6 | "On port1 both reach practically the same value" | "Both reach the certified optimum on port1" |
| `es_analysis.md` / `make_es_tables.py` | Pooled sign test | Clustered tests (R1) |
| `oral_exam_preparation.md`, Component 11 Q1 and Q5 | σ collapse as the full explanation | Two-part explanation (2.2) |
| `oral_exam_preparation.md`, Component 12 Q4 | "sign test p = 0.165, so not significant" | Clustered result and correct wording (2.3) |
| `oral_exam_preparation.md`, Component 13 Q4 | "Not from these experiments" (absolute quality) | Gaps to certified optima as context (if R2 is accepted) |
| `implementation_notes.md`, 1B §5 | Theoretical argument only | Add Evidence A–C (2.1) |

---

## 5. Items that remain the student's responsibility (from the PDF)

- **The report:** 3,000–7,500 words, PDF, Group No, member name, repository link, no code, captions
  for every figure, the AI declaration with an approximate percentage (about 100 % of the code is
  AI-generated), seeds of the illustrated route (berlin52: reversal, seed 7), and how gaps were
  calculated.
- **GitHub:** add the lecturer as a collaborator, and clarify the week-44 and weekly-report exceptions.
- **Disclosures to keep in the report:**
  - the settings chronology for 1A and 1B (seed-0 timing runs seen before the pilots);
  - interpretation choices in Problem 2 (distinct parents, repaired weights stored, tie-breaking, no
    selection after the final partial batch);
  - single-threaded timing.

---

## 6. Implementation status (added after instruction S8)

The student approved R1–R7 (instruction S8) and later R8 (S9). Implemented as documented, tested scripts. The numbers in
sections 2.1–2.3 above come from the temporary review scripts; the official, reproducible numbers are
in the files listed below.

| Recommendation | Status | Official output |
|---|---|---|
| R1 case-level statistics | Done; the pooled sign test was removed from the tables | `problem_2/results/tables/es_plus_vs_comma.md` (identical to section 2.3) |
| R2 reference optima | Done; adds a weak-duality bound and a 20,000-portfolio random check to the KKT certificate | `problem_2/results/supplementary/reference_optima.md` (identical V\*) |
| R3 (1+1) diagnostics | Done; extended from 3 to all 5 datasets for the step-size vs dimension decomposition | `problem_2/results/supplementary/one_plus_one_diagnostics.md` |
| R4 1B diagnostics | Done; the non-compliant sweep has its own file | `problem_1/results/supplementary/continuous_diagnostics.md`, `NONCOMPLIANT_neighbourhood_size_sweep.md` |
| R5 documentation | Done; superseded statements are kept with revision notes | `docs/implementation_notes.md`, `docs/oral_exam_preparation.md`, READMEs |
| R6 Part A paired table | Done (60/60) | `problem_1/results/tables/tsp_paired_comparison.md` |
| R7 tests | Done (Problem 1: 171 tests, Problem 2: 137 tests) | `problem_*/tests/test_supplementary.py`, `problem_2/tests/test_statistics_tools.py` |
| R8 hygiene | Approved later (S9) and done: AI comment in both `pytest.ini` files; "Audits" section in the main README | `problem_*/pytest.ini`, `README.md` |

Differences from the review's preliminary numbers:
- **1B Evidence A:** the official script draws neighbours in a fixed, sorted order with its own probe
  seed (306). The improvement probabilities therefore differ slightly: mean ≤ 0.00010 and max 0.0005,
  instead of the review's "0.0000–0.0002". The conclusion is unchanged.
- **1B Evidence B and C:** reproduced exactly.
- **The (1+1) intervention on port1/port3/port5 and the probe on those cases:** reproduced exactly;
  port2 and port4 were added.
