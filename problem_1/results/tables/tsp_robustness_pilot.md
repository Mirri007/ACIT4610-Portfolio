# Part A: parameter robustness check on non-assignment instances

Performed after the settings were chosen and the 120 runs were finished; it did not change the settings.
Instances: pr76, rat99, ch130. Seeds: 200-204. 30,000 evaluations per run.

| Setting | Avg mean gap, swap (%) | Avg mean gap, reversal (%) | Avg mean gap, both (%) | Avg rank (1 = best) |
|---|---|---|---|---|
| A_n50_m10_e3_nep40_nsp20 | 147.61 | 92.37 | 119.99 | 4.00 |
| B_n20_m5_e2_nep50_nsp20 | 116.81 | 42.77 | 79.79 | 3.00 |
| C_n10_m3_e1_nep100_nsp50 | 105.69 | 35.29 | 70.49 | 2.00 |
| D_n6_m2_e1_nep100_nsp50 | 90.04 | 21.01 | 55.52 | 1.00 |

Per instance and neighbourhood (mean gap % ± sample std over 5 seeds):

| Instance | Neighbourhood | A_n50_m10_e3_nep40_nsp20 | B_n20_m5_e2_nep50_nsp20 | C_n10_m3_e1_nep100_nsp50 | D_n6_m2_e1_nep100_nsp50 |
|---|---|---|---|---|---|
| pr76 | swap | 91.24 ± 6.27 | 70.00 ± 14.14 | 68.61 ± 6.92 | 55.11 ± 12.26 |
| pr76 | reversal | 41.66 ± 5.40 | 14.05 ± 2.49 | 9.51 ± 2.69 | 6.07 ± 2.19 |
| rat99 | swap | 133.53 ± 7.42 | 112.75 ± 18.69 | 103.83 ± 10.23 | 86.99 ± 9.82 |
| rat99 | reversal | 83.75 ± 9.13 | 34.80 ± 2.44 | 30.82 ± 2.78 | 18.10 ± 2.88 |
| ch130 | swap | 218.06 ± 11.58 | 167.67 ± 11.33 | 144.63 ± 8.89 | 128.02 ± 12.09 |
| ch130 | reversal | 151.70 ± 6.09 | 79.46 ± 6.85 | 65.54 ± 8.53 | 38.85 ± 4.35 |
