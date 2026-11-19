# AI Development Log

This log records how AI tools were used, to support the AI declaration required by the assignment.

Tool: Claude Code (Anthropic), model Claude Opus 5.5.

**Division of roles.**
- **The student directed the project:** set the requirements and working standards, decided when to
  move between stages, confirmed facts from the original assignment PDF, and asked for every review,
  audit and change listed below.
- **The AI (Claude Code)** wrote all the code, tests, experiment scripts and documentation, and ran
  the experiments, following those instructions. About 100 % of the code is AI-generated, and every
  AI-written Python file starts with an `# AI attribution` header.

---

## 1. Instructions received from the student

In chronological order. "Student" = the author of this portfolio.

| # | Date | Instruction from the student (summary) |
|---|------|----------------------------------------|
| S1 | 2026-11-19 | Read the whole assignment PDF and follow it exactly. Write readable, beginner-level code with extensive "why" comments and docstrings. Write tests alongside the code. Never invent results or claim untested things. Prepare oral-exam material. Work in stages and wait for approval between them. First deliver: a requirements checklist, project structure, data/dependency list, Problem 1A plan, risks and test plan. |
| S2 | 2026-11-19 | Confirmed from the original PDF the cases whose names were blank in the text version: TSP convergence plots berlin52 and ch150; TSP route plot berlin52; ES convergence plot port5_alpha050; continuous convergence plot Rastrigin D = 10. Approved a short AI header per file, provided it does not replace the educational comments. Asked for the GitHub repository and an accurate development history. Approved starting Problem 1A. |
| S3 | 2026-11-19 | Stop adding Claude as co-author in Git commits; use the student's Git identity only; short professional commit messages; never rewrite Git history; keep the AI attribution in source headers and in this log. |
| S4 | 2026-11-19 | Before Problem 1B: perform an independent audit of Problem 1A (BA logic, evaluation counting, identical settings for both neighbourhoods, statistics and figures) and explain the parameter pilot and its independence from the evaluation seeds. |
| S5 | 2026-11-19 | Run an additional robustness pilot on three TSPLIB instances that are not among the six required ones, with new seeds, as a check only (it must not replace the settings). Keep the 120 runs unless an actual error is found. Add the audit scripts to the repository. Document the original selection process accurately, including its limitations, without presenting the later pilot as if it came first. Then approved Problem 1B: test all functions carefully and verify exactly 30,000 evaluations per run. |
| S6 | 2026-11-19 | Approved Problem 2. Prioritise quality and understanding over speed. Use separate seeds for preliminary testing, tuning and final experiments. Write comprehensive tests, including independent mathematical checks. Audit thoroughly afterwards. Do not write the report yet. Announced a separate critical review of both problems, especially whether Problem 1B can be improved within the assignment's rules without changing the setup just to get better numbers. |
| S7 | 2026-11-19 | Critical review of the whole project before the report. Specifically: investigate the weak Problem 1B results (convergence, neighbourhood size, parameter sensitivity, compliant improvements); test whether the explanation for the (1+1)-ES stagnation is supported by the saved step-size and convergence data; reassess the (μ+λ) vs (μ,λ) statistics, accounting for the 150 pairs coming from 15 cases, without overstating significance or equivalence; check correctness, repair, counting, fairness, reproducibility and completeness against the PDF. For every proposed improvement state: the weakness, why the change helps, compliance, whether a rerun is needed, and whether it is worth it. **Do not change final results or settings yet.** Also: record the student's instructions clearly in this log. |
| S8 | 2026-11-19 | Approved review recommendations R1–R7 (not R8), with conditions: case-level statistics with the unit, confidence interval and limitations explained; exact optima as supplementary context, independently verified, distinguishing numerical verification from mathematical proof; (1+1) diagnostics separating step-size adaptation from high-dimensional difficulty; 1B neighbourhood diagnostics, with non-±10 % experiments marked supplementary only; corrected docs and exam notes; the 60/60 Part A paired comparison; tests for the new analyses; **no change to algorithms, settings, seeds, final results or required figures** unless a correctness error is found; reproducible scripts with documented dependencies; a clear distinction between mandatory experiments, pilots, post-hoc diagnostics and supplementary analyses, preserving the chronology; rerun all tests and audits and check the repository for inconsistencies; do not start the report. |

---

## 2. Work performed by the AI

| Date | Stage | What the AI did | Following instruction |
|------|-------|-----------------|-----------------------|
| 2026-11-19 | Stage 1: setup | Read the assignment; wrote `requirements_checklist.md`; created the folder structure; downloaded the 11 official datasets; reproduced the port1 parser checkpoint with a throwaway script | S1 |
| 2026-11-19 | Stage 1: GitHub | Created the private GitHub repository `Mirri007/ACIT4610-Portfolio` and pushed the Stage 1 commit | S2 |
| 2026-11-19 | Problem 1A | Wrote all Python code in `problem_1/src/`, `problem_1/experiments/` and `problem_1/tests/`. Planted four deliberate bugs in a scratch copy to check the tests, which led to two extra budget tests. Ran the settings pilot, all 120 experiment runs, and the tables and figures. Wrote `problem_1/README.md`, `implementation_notes.md` and `oral_exam_preparation.md` | S1, S2 |
| 2026-11-19 | Problem 1A audit | Independent audit (own parser, distance and statistics; trace of every evaluation in two real runs): no errors found. Reported the pilot's limitations, including that seed-0 timing results for setting A were seen before the pilot | S4 |
| 2026-11-19 | Problem 1A robustness | Wrote and ran `tsp_robustness_pilot.py` on pr76, rat99, ch130 (seeds 200–204) without changing settings or results. Added `audit_tsp_results.py` and `audit_tsp_trace.py` (both pass; the results audit was shown to fail on a deliberately corrupted copy). Rewrote the settings chronology | S5 |
| 2026-11-19 | Problem 1B | Fetched the SFU R reference code. Wrote the functions, continuous BA, pilot, experiment, table, plot and two audit scripts, and all Part B tests. Disclosed that seed-0 timing runs were seen before the pilot. Ran the pilot (rule fixed in advance), all 80 runs, the audits and 7 planted-bug checks. Wrote the Part B documentation and exam notes | S5 |
| 2026-11-19 | Problem 2 | Wrote all Problem 2 code and 119 tests. Inspected the data structure and covariance eigenvalues. Investigated a runtime anomaly (OpenBLAS threading) and switched the experiments to single-threaded. Planted 12 bugs; one exposed a missing test, which was added. Ran 450 runs, both audits and the analysis. Wrote the README, implementation notes and exam notes | S6 |
| 2026-11-19 | Critical review | Diagnostic analyses with separate seeds (300–309) and reference optima, without changing final results or settings. Wrote the prioritised review in `docs/critical_review.md` | S7 |
| 2026-11-19 | Review implementation | Implemented R1–R7 (not R8). Case-level statistics module and table; reference optima with a KKT certificate, weak-duality bound and random check (SciPy only for candidates); (1+1) diagnostics on all five datasets; 1B diagnostics with the non-compliant sweep kept separate; Part A paired table; 36 new tests; revision notes in the docs and exam notes; fixed an empty-mean warning in the new paired-comparison function and an unclosed-file warning in an existing Problem 2 test. No algorithm, setting, seed, final result or required figure changed | S8 |
