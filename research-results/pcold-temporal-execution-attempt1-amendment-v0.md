# P-COLD temporal execution attempt 1 — numerical amendment

Date: 2026-09-08

Status: `PRE_SCORE_NUMERICAL_FAILURE / NO_VALIDATION_OR_FINAL_SCORE_EMITTED / SCIENTIFIC_CONTRACT_UNCHANGED`

FFBK preregistration: `pokekarten/FFBK#1462`.

Public runner attempt:

- repository: `pokekarten/OpenCatastrophe-data`;
- branch: `research-run/pcold-v3-source-lock-20260908-sol56`;
- workflow head: `00bd32b3775711040472039637e4f41651d765e7`;
- run: `34218311906`;
- job: `102035238322`;
- exact frozen scientific script blob before repair: `5478be979c628191204b35fac05244b7e0eee544`;
- pre-target compile + focused synthetic controls: PASS, 5/5;
- failure location: `fit_models()` while optimizing training-only M3 NB2 calendar model;
- failure: optimizer encountered `NaN` from the numerical expression `y * log1p(-p)` when very small `alpha` made `p = r/(r+mu)` round to exactly 1 and `y=0` produced floating-point `0 * -inf`.

No validation or final log score, bootstrap interval, PIT, coverage, residual diagnostic, dispersion attribution, annual VaR/ES, stop-loss metric, winner, or research classification was emitted or committed by attempt 1. The durable result-commit step was skipped.

The workbook had already passed the independent source-lock and date-quality gates and was read by the runner before the training optimizer failed. Therefore a repaired execution must **not** be described as a pristine first byte-open. It is a continuation of the prospectively frozen experiment after a pre-score numerical implementation failure.

## Permitted repair

Replace only the unstable but algebraically equivalent NB2 term

```text
y * log(1 - r/(r+mu))
```

with the stable identity

```text
y * (log(mu) - log(r+mu))
```

and compute the `r log p` contribution as

```text
-r * log1p(mu/r)
```

No likelihood family, parameterization, parameter domain, Poisson boundary, optimizer, source bytes, event/date rule, partition, trend/harmonic specification, bootstrap, PIT seed, calibration gate, final evaluation rule, or secondary tail definition may change.

A focused regression control must demonstrate that the repaired expression is finite at the existing lower-alpha search boundary and converges numerically to the Poisson log PMF there before any repaired target execution is accepted.
