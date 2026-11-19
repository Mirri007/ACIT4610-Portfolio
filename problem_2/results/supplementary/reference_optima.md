# SUPPLEMENTARY: reference minimum-variance portfolios (post-hoc analysis, not a required result)

Reference = exact KKT solution on the support suggested by SLSQP. **Numerically verified, not formally proven**: KKT residuals and the relative duality gap (distance between the reference variance and a weak-duality lower bound) are computed in floating point. Also checked: no final ES run and none of 20,000 random feasible portfolios has a lower variance. Gaps are context for interpreting the ES results; the assignment's conclusions remain relative comparisons between the variants.

| Case | n | Reference variance V* | Assets held | Return constraint active | Max KKT residual | Relative duality gap | Not beaten by ES / random | Mean gap (1+1)-ES | Mean gap (μ+λ)-ES | Mean gap (μ,λ)-ES | Best ES run gap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| port1_alpha025 | 31 | 7.6899822438e-04 | 6 | yes | 8.7e-19 | -1.4e-16 | yes | 14.76 % | 0.01 % | 0.02 % | 0.0001 % |
| port1_alpha050 | 31 | 1.1663242820e-03 | 4 | yes | 2.2e-18 | 1.5e-15 | yes | 30.68 % | 0.00 % | 0.00 % | 0.0000 % |
| port1_alpha075 | 31 | 2.3108535102e-03 | 3 | yes | 1.7e-18 | 5.6e-16 | yes | 17.17 % | 0.00 % | 0.00 % | 0.0000 % |
| port2_alpha025 | 85 | 1.5346933527e-04 | 24 | yes | 2.2e-16 | 1.6e-15 | yes | 20.57 % | 7.07 % | 5.13 % | 2.4665 % |
| port2_alpha050 | 85 | 2.4737146292e-04 | 20 | yes | 8.7e-19 | 2.2e-16 | yes | 50.15 % | 6.14 % | 8.25 % | 2.5846 % |
| port2_alpha075 | 85 | 4.7040565319e-04 | 7 | yes | 2.2e-19 | 4.6e-16 | yes | 118.49 % | 5.65 % | 3.87 % | 0.5780 % |
| port3_alpha025 | 89 | 2.3348446292e-04 | 26 | yes | 3.8e-19 | 4.6e-16 | yes | 25.05 % | 5.79 % | 4.76 % | 2.6706 % |
| port3_alpha050 | 89 | 3.3821102718e-04 | 16 | yes | 8.7e-19 | 1.6e-16 | yes | 38.72 % | 4.74 % | 3.24 % | 1.6057 % |
| port3_alpha075 | 89 | 6.0553876619e-04 | 7 | yes | 2.2e-16 | 7.2e-16 | yes | 39.69 % | 1.15 % | 3.01 % | 0.0473 % |
| port4_alpha025 | 98 | 2.0234947459e-04 | 27 | yes | 4.9e-19 | 5.4e-16 | yes | 46.43 % | 12.20 % | 16.17 % | 8.3550 % |
| port4_alpha050 | 98 | 3.7176207386e-04 | 17 | yes | 6.5e-19 | 8.7e-16 | yes | 94.94 % | 10.62 % | 15.79 % | 4.8206 % |
| port4_alpha075 | 98 | 7.6436277482e-04 | 8 | yes | 2.0e-18 | -7.1e-16 | yes | 109.16 % | 5.59 % | 8.25 % | 2.5989 % |
| port5_alpha025 | 225 | 3.0464069967e-04 | 12 | no | 2.2e-19 | 0.0e+00 | yes | 84.72 % | 15.15 % | 9.81 % | 1.5573 % |
| port5_alpha050 | 225 | 3.3616393093e-04 | 14 | yes | 1.1e-16 | 3.2e-16 | yes | 116.15 % | 17.84 % | 12.23 % | 4.8428 % |
| port5_alpha075 | 225 | 4.5628058940e-04 | 10 | yes | 1.1e-18 | 0.0e+00 | yes | 137.46 % | 16.44 % | 18.44 % | 7.5496 % |

Gap = 100 × (V_ES − V*) / V*. Mean gap = gap of the mean final variance of the 10 runs.
