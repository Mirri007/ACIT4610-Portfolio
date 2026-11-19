# Problem 2: comparison of the ES variants

## Mean final variance per case (lowest in bold)

| Case | Assets | (1+1)-ES | (μ+λ)-ES | (μ,λ)-ES | Lowest | (μ+λ) vs (μ,λ): relative difference |
|---|---|---|---|---|---|---|
| port1_alpha025 | 31 | 8.82514e-04 | **7.69104e-04** | 7.69138e-04 | (μ+λ)-ES | -0.00 % |
| port1_alpha050 | 31 | 1.52412e-03 | 1.16633e-03 | **1.16632e-03** | (μ,λ)-ES | +0.00 % |
| port1_alpha075 | 31 | 2.70764e-03 | 2.31085e-03 | **2.31085e-03** | (μ,λ)-ES | +0.00 % |
| port2_alpha025 | 85 | 1.85041e-04 | 1.64321e-04 | **1.61337e-04** | (μ,λ)-ES | +1.85 % |
| port2_alpha050 | 85 | 3.71420e-04 | **2.62571e-04** | 2.67780e-04 | (μ+λ)-ES | -1.95 % |
| port2_alpha075 | 85 | 1.02778e-03 | 4.96985e-04 | **4.88602e-04** | (μ,λ)-ES | +1.72 % |
| port3_alpha025 | 89 | 2.91963e-04 | 2.47014e-04 | **2.44599e-04** | (μ,λ)-ES | +0.99 % |
| port3_alpha050 | 89 | 4.69163e-04 | 3.54230e-04 | **3.49166e-04** | (μ,λ)-ES | +1.45 % |
| port3_alpha075 | 89 | 8.45902e-04 | **6.12484e-04** | 6.23757e-04 | (μ+λ)-ES | -1.81 % |
| port4_alpha025 | 98 | 2.96305e-04 | **2.27044e-04** | 2.35079e-04 | (μ+λ)-ES | -3.42 % |
| port4_alpha050 | 98 | 7.24722e-04 | **4.11228e-04** | 4.30473e-04 | (μ+λ)-ES | -4.47 % |
| port4_alpha075 | 98 | 1.59872e-03 | **8.07052e-04** | 8.27399e-04 | (μ+λ)-ES | -2.46 % |
| port5_alpha025 | 225 | 5.62727e-04 | 3.50800e-04 | **3.34530e-04** | (μ,λ)-ES | +4.86 % |
| port5_alpha050 | 225 | 7.26621e-04 | 3.96134e-04 | **3.77284e-04** | (μ,λ)-ES | +5.00 % |
| port5_alpha075 | 225 | 1.08347e-03 | **5.31314e-04** | 5.40426e-04 | (μ+λ)-ES | -1.69 % |

Cases where each variant has the lowest mean variance: (1+1)-ES: 0, (μ+λ)-ES: 7, (μ,λ)-ES: 8

## Paired per-seed counts (150 pairs = 15 cases x 10 seeds; descriptive only)

These counts describe the data; they are not a significance test, because pairs from the same case are not independent. See es_plus_vs_comma.md for the case-level test.

| Comparison | First lower | Second lower | Equal |
|---|---|---|---|
| (μ+λ)-ES vs (μ,λ)-ES | 66 | 84 | 0 |
| (μ+λ)-ES vs (1+1)-ES | 150 | 0 | 0 |
| (μ,λ)-ES vs (1+1)-ES | 150 | 0 | 0 |
