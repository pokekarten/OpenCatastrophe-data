# P-COLD temporal frequency tournament v0 — semantic amendment

Date: 2026-09-08

Status: **POST_RESULT_SEMANTIC_QUALIFICATION / RAW_RECEIPT_PRESERVED / NO_PROMOTION**

Authoritative bounded scientific verdict:

`MIXED / NB2_NLL_ADVANTAGE_SURVIVES_OOS / IID_NB2_PREDICTIVE_ADEQUACY_FALSIFIED / SIMPLE_CALENDAR_TREND_HARMONIC_INSUFFICIENT / SERIAL_NONSTATIONARITY_UNRESOLVED / NO_PROMOTION`

This amendment does not change the frozen source bytes, admissible-event/date rule, model fits, score values, bootstrap values, PIT draws, tail calculations or execution receipt. It qualifies what those already-recorded outputs can support.

## Why an amendment is needed

The raw receipt contains an internal summary field

```text
interpretive_pattern = RESIDUAL_OVERDISPERSION_SUPPORTED_IN_FINAL
```

That field is only a narrow pairwise indicator: in the final period, M3 (calendar mean + NB2) has a positive moving-block NLL improvement over M2 (the same calendar mean + Poisson) and the fitted M3 dispersion is nonzero.

It is **not** the preregistered validation-selection result and must not be read as evidence that M3, NB2, or a stochastic-overdispersion mechanism is predictively adequate.

## Preregistered validation gate

On 2015-01 through 2018-12:

- M1 stationary NB2 versus M0 stationary Poisson: mean monthly NLL improvement `+16.4447151277`, moving-block 95% `[+3.4363466386,+28.6484485462]`;
- M2 calendar Poisson versus M0: `+13.7017323195`, 95% `[+1.0500647144,+25.7207936212]`;
- M3 calendar NB2 versus M0: `+17.4703331239`, 95% `[+3.3402815288,+30.7732494624]`;
- M3 versus M2: `+3.7686008044`, 95% `[+1.7864120112,+5.5900346856]`.

However every challenger fails the predeclared broad calibration guard. The frozen selection receipt therefore records:

```text
passed_challengers = []
winner = M0
```

This means **no challenger passed the preregistered promotion gate**. M0 is the mechanical fallback label, not a claim that stationary Poisson is adequate: M0 itself also fails the reported calibration diagnostics badly.

## Final-period result

On the exact-date admissible final period 2019-01 through 2022-11:

- M0 mean NLL `12.8902031465`;
- M1 stationary NB2 `3.0314281383`;
- M2 calendar Poisson `27.2305314600`;
- M3 calendar NB2 `8.1654944639`.

M1 improves M0 by `+9.8587750082` mean NLL with moving-block 95% `[+2.0337944750,+20.7719845232]`. This is strong evidence that the broad predictive distribution benefits from extra variance relative to stationary Poisson on these held-out months.

It is **not sufficient evidence for iid NB2 adequacy**:

- M1 final randomized-PIT KS statistic is `0.3377816036`, above the frozen `0.30` catastrophic threshold;
- M1 Pearson residual lag-1 autocorrelation is `0.9102925740`;
- Ljung-Box Q12 p-value is approximately `9.6e-33`;
- M1 final Pearson residual variance remains `5.9402352589` rather than near one.

The simple deterministic calendar challenger is also not adequate. M2's training-fitted linear trend + annual harmonic extrapolates extremely poorly in the final period. M3 substantially repairs M2 relative to its Poisson law but does not pass the overall M0 comparison/adequacy gate and remains serially/calibrationally defective.

## Mechanism interpretation

The data support a bounded distinction:

1. **extra predictive variance matters** relative to stationary Poisson;
2. that does **not identify** stationary stochastic overdispersion as the mechanism;
3. the frozen linear trend + annual harmonic is not an adequate deterministic nonstationarity model;
4. strong residual serial dependence and the train/validation/final mean shifts leave regime change, change points, dynamic intensity, event-clustering/contagion, reporting/media process changes, and richer nonstationarity live as challengers.

The training exact-date monthly count mean is `5.2288401254`; validation mean is `20.5416666667`; final mean is `8.3617021277`. This large temporal movement makes static iid interpretation especially weak.

## Secondary tail firewall

The receipt preserves the preregistered fixed-severity annual frequency-only VaR99.5/ES/stop-loss calculations as execution diagnostics. Because **none of the candidate predictive laws passes the declared calibration gate**, those tail numbers are **not admissible as validated risk measures, capital quantities, insurer parameters, or model-selection evidence**. They can only demonstrate that uncertainty-family and temporal-mean choices can make downstream tail outputs diverge materially.

## Data boundary

The exact v3 workbook contains Event IDs 1..3723. The sole extra non-integer `Event ID` cell is the workbook note stating that undisclosed source information is populated with `F`.

Only 3,047 events have an integer occurrence year and an integer occurrence month in 1..12. The frozen rule excludes 676 events with undisclosed/unparseable occurrence date and never imputes them. The exact-date monthly series therefore ends at 2022-11; 2023 is not fabricated as a zero-count year.

## Best next falsification

Freeze before further target inspection a genuinely dynamic frequency challenger, for example:

- Poisson/NB state-space intensity with a latent random walk or AR state;
- predeclared change-point/regime-switching Poisson/NB process;
- self-exciting/event-clustering challenger where economically defensible;
- flexible calendar intensity with regularized spline/change-point state.

Use rolling-origin or untouched later-period evaluation, retain a calibration gate, and ask whether the stationary NB2 NLL advantage disappears once temporal dependence/nonstationarity is modelled directly.

No P-COLD model family, banking-to-insurance transfer, operational-risk default, capital number, NextGen schema/API, or production/regulatory use is promoted by this result.
