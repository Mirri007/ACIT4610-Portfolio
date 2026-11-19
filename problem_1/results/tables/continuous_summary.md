# Part B: Bees Algorithm on benchmark functions (10 runs per row, 30,000 evaluations per run)

Values are final best objective values f(x); the global minimum of every function is 0, so these are the objective errors. Std = sample standard deviation (ddof = 1). Runtime = wall-clock seconds of the search.

| Function | D | Runs | Mean initial best | Best | Mean | Std | Median | Mean runtime (s) |
|---|---|---|---|---|---|---|---|---|
| sphere | 10 | 10 | 53.58 | 0.1843 | 0.4293 | 0.1314 | 0.4158 | 0.220 |
| sphere | 30 | 10 | 204.1 | 4.556 | 5.499 | 0.785 | 5.252 | 0.223 |
| rosenbrock | 10 | 10 | 3.689e+05 | 64.31 | 92.38 | 20.59 | 88.82 | 0.349 |
| rosenbrock | 30 | 10 | 2.145e+06 | 1641 | 2472 | 496.2 | 2532 | 0.339 |
| rastrigin | 10 | 10 | 133 | 23.14 | 33.01 | 6.204 | 33.54 | 0.309 |
| rastrigin | 30 | 10 | 452.5 | 245.1 | 275.6 | 26.43 | 270.5 | 0.444 |
| ackley | 10 | 10 | 20.53 | 5.122 | 6.233 | 0.5497 | 6.226 | 0.466 |
| ackley | 30 | 10 | 20.89 | 10.07 | 10.55 | 0.2797 | 10.69 | 0.402 |
