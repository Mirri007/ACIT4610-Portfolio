# Problem 2: (μ+λ)-ES vs (μ,λ)-ES, case-level comparison

**Statistical unit.** The 150 seed pairs come from 15 cases that differ systematically (data, size, target), so they are not 150 independent observations. The main test therefore uses the **case** as the unit: each case contributes the mean of its 10 paired relative differences d = (V_plus - V_comma) / mean(V_comma); negative = (μ+λ) lower. Pairs share the seed, and with the same seed both variants start from the same 10 parents.

## Overall (15 cases)

- Mean of the case means: +0.005 %
- 95 % percentile-bootstrap interval over cases: [-1.309 %, +1.386 %]
- Exact two-sided sign-flip test over the 15 case means (all 32,768 sign patterns): p = 0.994
- (μ+λ) lower on average in 7 of 15 cases

## Within each case (10 paired seeds)

| Case | Mean relative difference | 95 % bootstrap interval | Exact sign-flip p | Holm-adjusted p | Seeds with (μ+λ) lower |
|---|---|---|---|---|---|
| port1_alpha025 | -0.005 % | [-0.027 %, +0.011 %] | 0.8809 | 1.0000 | 4/10 |
| port1_alpha050 | +0.001 % | [+0.000 %, +0.001 %] | 0.0020 | 0.0293 | 0/10 |
| port1_alpha075 | +0.000 % | [+0.000 %, +0.000 %] | 0.0020 | 0.0293 | 0/10 |
| port2_alpha025 | +1.849 % | [+0.115 %, +3.575 %] | 0.0898 | 1.0000 | 3/10 |
| port2_alpha050 | -1.945 % | [-5.300 %, +0.559 %] | 0.2656 | 1.0000 | 7/10 |
| port2_alpha075 | +1.716 % | [-4.163 %, +7.150 %] | 0.5254 | 1.0000 | 2/10 |
| port3_alpha025 | +0.988 % | [-0.523 %, +2.241 %] | 0.2188 | 1.0000 | 3/10 |
| port3_alpha050 | +1.450 % | [-0.070 %, +2.877 %] | 0.1113 | 1.0000 | 2/10 |
| port3_alpha075 | -1.807 % | [-3.602 %, -0.174 %] | 0.0957 | 1.0000 | 7/10 |
| port4_alpha025 | -3.418 % | [-5.292 %, -1.717 %] | 0.0039 | 0.0508 | 9/10 |
| port4_alpha050 | -4.471 % | [-9.544 %, +0.164 %] | 0.1094 | 1.0000 | 7/10 |
| port4_alpha075 | -2.459 % | [-6.051 %, +0.550 %] | 0.2031 | 1.0000 | 8/10 |
| port5_alpha025 | +4.864 % | [+0.624 %, +9.624 %] | 0.0840 | 1.0000 | 5/10 |
| port5_alpha050 | +4.996 % | [-0.951 %, +10.187 %] | 0.1445 | 1.0000 | 3/10 |
| port5_alpha075 | -1.686 % | [-10.023 %, +6.855 %] | 0.7188 | 1.0000 | 6/10 |

## How to read this, and limitations

- An overall p-value far above 0.05 means **no evidence of an overall difference**; it does NOT show the variants are equivalent. Equivalence would need a margin fixed in advance and an interval inside it, which this study did not define.
- The 15 cases are the assignment's fixed benchmark, not a random sample of all portfolio problems; conclusions apply to these cases.
- With only 15 cases (overall) or 10 seeds (within a case), percentile-bootstrap intervals are approximate and tend to be slightly too narrow.
- The sign-flip test assumes that, without a real difference, each difference is symmetric around 0.
- Within-case p-values are adjusted with Holm's method for 15 tests. A significant within-case result can still be practically negligible (check the size of the mean difference).
