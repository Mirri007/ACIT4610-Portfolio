# POST-HOC DIAGNOSTICS: (1+1)-ES stagnation (not part of the required experiments)

Modified (1+1) versions below are diagnostic tools, not the assignment's algorithm. Diagnostic seeds 300–304; probes use the saved seed-0 final solutions. Gaps are relative to the numerically verified reference optima (reference_optima.md).

## Q1. Association in the saved final runs (150 runs, 500-evaluation windows)

| σ at window start | Windows | Mean relative improvement per window | Median |
|---|---|---|---|
| ≥ 1e-3 | 161 | 24.1837 % | 22.04942 % |
| 1e-4 – 1e-3 | 255 | 3.3941 % | 2.51790 % |
| 1e-5 – 1e-4 | 800 | 0.6855 % | 0.44655 % |
| 1e-6 – 1e-5 | 1703 | 0.1066 % | 0.05101 % |
| 1e-7 – 1e-6 | 2152 | 0.0134 % | 0.00570 % |
| < 1e-7 | 3929 | 0.0016 % | 0.00046 % |

Median evaluation at which σ first falls below 1e-4: 1000; below 1e-5: 2500; below 1e-6: 4750. Median evaluation at which the archive is within 1 % of its final value: 3890. (Association only: a difficult landscape could cause both.)

## Q2. Intervention: mean gap to the reference optimum (seeds 300–304, α = 0.50)

| Case | n | as specified (floor 1e-8) | floor 1e-4 | floor 1e-3 | fixed sigma0 (no adaptation) |
|---|---|---|---|---|---|
| port1_alpha050 | 31 | 25.76 % | 11.03 % | 2.95 % | 0.02 % |
| port2_alpha050 | 85 | 50.26 % | 14.77 % | 5.43 % | 7.71 % |
| port3_alpha050 | 89 | 34.37 % | 13.36 % | 7.04 % | 9.31 % |
| port4_alpha050 | 98 | 94.03 % | 45.74 % | 17.13 % | 17.44 % |
| port5_alpha050 | 225 | 122.59 % | 85.35 % | 76.40 % | 86.94 % |

## Q3. Probability that one mutation + repair improves the saved stagnated (1+1) solution

| Case | Gap of probed point | σ = 1e-08 | σ = 1e-07 | σ = 1e-06 | σ = 1e-05 | σ = 1e-04 | σ = 1e-03 | σ = 1e-02 | Same probe at reference optimum (max) |
|---|---|---|---|---|---|---|---|---|---|
| port1_alpha050 | 26.0 % | 0.146 | 0.151 | 0.083 | 0.053 | 0.048 | 0.042 | 0.048 | 0.000 |
| port2_alpha050 | 43.6 % | 0.154 | 0.152 | 0.082 | 0.020 | 0.007 | 0.003 | 0.000 | 0.000 |
| port3_alpha050 | 38.6 % | 0.116 | 0.031 | 0.007 | 0.011 | 0.005 | 0.001 | 0.001 | 0.000 |
| port4_alpha050 | 92.9 % | 0.099 | 0.081 | 0.040 | 0.032 | 0.025 | 0.014 | 0.014 | 0.000 |
| port5_alpha050 | 120.4 % | 0.181 | 0.005 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

3,000 samples per σ (standard error ≤ 0.009). The 1/5 rule stops shrinking σ only where the success rate reaches 0.2.

## Q4. Step-size adaptation vs high-dimensional difficulty (mean gap to the reference optimum)

| Case | n | (1+1) as specified | (1+1) with collapse prevented (best of 3 diagnostic versions) | Part of the gap removed by preventing the collapse | Population ES (saved final runs) |
|---|---|---|---|---|---|
| port1_alpha050 | 31 | 25.76 % | 0.02 % | 100 % | 0.00 % |
| port2_alpha050 | 85 | 50.26 % | 5.43 % | 89 % | 7.20 % |
| port3_alpha050 | 89 | 34.37 % | 7.04 % | 80 % | 3.99 % |
| port4_alpha050 | 98 | 94.03 % | 17.13 % | 82 % | 13.20 % |
| port5_alpha050 | 225 | 122.59 % | 76.40 % | 38 % | 15.04 % |

Caveats: the datasets differ in more than their size; the best of three diagnostic versions is selected after seeing the results (optimistic); 5 seeds per setting; the population-ES column uses the final seeds 0–9.
