# AI Development Log

This log records how AI tools were used, to support the AI declaration required by the assignment.

Tool: Claude Code (Anthropic), model Claude Opus 5.5.

| Date | Stage | What the AI did | What the student did |
|------|-------|-----------------|----------------------|
| 2026-11-19 | Stage 1: setup | Read the assignment, wrote `requirements_checklist.md`, created the folder structure, downloaded the 11 official datasets, reproduced the port1 parser checkpoint with a throwaway script | Provided the assignment and project instructions; to review and approve the plan |
| 2026-11-19 | Stage 1: GitHub | Created the private GitHub repository `Mirri007/ACIT4610-Portfolio` and pushed the Stage 1 commit | Approved the plan and asked for the repository |
| 2026-11-19 | Stage 2: Problem 1A | Wrote all Python code in `problem_1/src/`, `problem_1/experiments/` and `problem_1/tests/` (100 % AI-generated; every file has an attribution header); planted four deliberate bugs in a scratch copy to check that the tests catch them, which led to two extra budget tests; ran the settings pilot study, all 120 experiment runs, and the tables and figures; wrote `problem_1/README.md`, `implementation_notes.md` and `oral_exam_preparation.md` | Confirmed the required plot cases (berlin52 and ch150 convergence, berlin52 route); to review the code, results and notes |
| 2026-11-19 | Problem 1A audit | Independent audit (own parser, distance and statistics; trace of every evaluation in two real runs): no errors found. Reported the pilot's limitations, including that seed-0 timing results for setting A were seen before the pilot | Reviewed the audit; asked for a robustness check, audit scripts in the repo and accurate documentation |
| 2026-11-19 | Problem 1A robustness | Wrote `tsp_robustness_pilot.py` and ran it on pr76, rat99, ch130 (seeds 200–204) after the 120 runs, without changing settings or results; added `audit_tsp_results.py` and `audit_tsp_trace.py` (both pass; the results audit was shown to fail on a deliberately corrupted copy); rewrote the settings chronology in `implementation_notes.md` | Approved Problem 1A subject to these checks |
