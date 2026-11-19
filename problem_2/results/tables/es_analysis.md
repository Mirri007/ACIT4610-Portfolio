# Problem 2: analysis statistics (all 15 cases x 10 seeds per variant)

| Variant | Runs with return constraint active (R = R_min) | Mean assets with weight > 1e-6 | Median evaluation reaching within 1 % of final variance | Median evaluation of last archive improvement |
|---|---|---|---|---|
| (1+1)-ES | 48/150 | 67.6 | 3890 | 29997 |
| (μ+λ)-ES | 124/150 | 14.7 | 13072 | 25673 |
| (μ,λ)-ES | 98/150 | 14.6 | 13493 | 25266 |

(1+1)-ES success rate: mean 0.188, min 0.142, max 0.199; runs ending with step size below 1e-7: 126/150.

The comparison of (μ+λ) and (μ,λ) is in es_plus_vs_comma.md (case-level analysis).
