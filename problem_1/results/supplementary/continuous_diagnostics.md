# POST-HOC DIAGNOSTICS: Problem 1B (assignment-compliant parts A and B; not required results)

## A. Final solutions under the assignment's ±10 % neighbourhood (saved final runs, seeds 0–9)

| Function | D | P(one neighbour improves): mean | max | RMS distance to optimum per coordinate | Neighbour per-coordinate std (a/√3) | Median share of improvement after evaluation 15,000 |
|---|---|---|---|---|---|---|
| sphere | 10 | 0.00005 | 0.00025 | 0.205 | 0.591 | 0.05 % |
| sphere | 30 | 0.00008 | 0.00050 | 0.427 | 0.591 | 0.26 % |
| rosenbrock | 10 | 0.00005 | 0.00025 | 0.947 | 0.866 | 0.00 % |
| rosenbrock | 30 | 0.00010 | 0.00050 | 1.190 | 0.866 | 0.01 % |
| rastrigin | 10 | 0.00003 | 0.00025 | 1.210 | 0.591 | 2.98 % |
| rastrigin | 30 | 0.00008 | 0.00025 | 1.996 | 0.591 | 5.22 % |
| ackley | 10 | 0.00000 | 0.00000 | 1.365 | 3.784 | 0.00 % |
| ackley | 30 | 0.00010 | 0.00050 | 2.917 | 3.784 | 2.79 % |

4,000 neighbours per final vector (probe seed 306).

## B. Settings sensitivity (assignment-compliant: ±10 % neighbourhood, 30,000 evaluations; seeds 300–309)

Cell = mean final value (ratio to the current setting C; difference in units of C's standard deviation).

| Function | D | A (n50 m10 e3 nep40 nsp20, explorative) | C (n10 m3 e1 nep100 nsp50, CURRENT) | D (n6 m2 e1 nep100 nsp50) | E (n2 m1 e1 nep200 nsp1, extreme local search) | G (n100 m5 e1 nep20 nsp10, many scouts) |
|---|---|---|---|---|---|---|
| sphere | 10 | 0.478 (1.14×; +0.9 sd) | 0.4185 (1.00×; +0.0 sd) | 0.4143 (0.99×; -0.1 sd) | 0.4114 (0.98×; -0.1 sd) | 0.5157 (1.23×; +1.5 sd) |
| sphere | 30 | 6.075 (1.08×; +1.1 sd) | 5.625 (1.00×; +0.0 sd) | 5.365 (0.95×; -0.6 sd) | 5.469 (0.97×; -0.4 sd) | 7.264 (1.29×; +3.9 sd) |
| rosenbrock | 10 | 93.97 (0.88×; -0.2 sd) | 107.1 (1.00×; +0.0 sd) | 82.22 (0.77×; -0.3 sd) | 125 (1.17×; +0.3 sd) | 101.2 (0.95×; -0.1 sd) |
| rosenbrock | 30 | 2822 (1.01×; +0.1 sd) | 2795 (1.00×; +0.0 sd) | 2340 (0.84×; -1.0 sd) | 2238 (0.80×; -1.2 sd) | 3252 (1.16×; +1.0 sd) |
| rastrigin | 10 | 36.77 (1.00×; +0.1 sd) | 36.61 (1.00×; +0.0 sd) | 32.22 (0.88×; -1.4 sd) | 44.02 (1.20×; +2.3 sd) | 36.49 (1.00×; -0.0 sd) |
| rastrigin | 30 | 266.3 (0.99×; -0.1 sd) | 268.3 (1.00×; +0.0 sd) | 278.7 (1.04×; +0.4 sd) | 271.2 (1.01×; +0.1 sd) | 279.3 (1.04×; +0.4 sd) |
| ackley | 10 | 6.109 (1.01×; +0.2 sd) | 6.028 (1.00×; +0.0 sd) | 6.298 (1.04×; +0.6 sd) | 6.013 (1.00×; -0.0 sd) | 6.394 (1.06×; +0.8 sd) |
| ackley | 30 | 10.82 (1.04×; +1.0 sd) | 10.38 (1.00×; +0.0 sd) | 9.983 (0.96×; -0.9 sd) | 10.42 (1.00×; +0.1 sd) | 10.9 (1.05×; +1.2 sd) |
