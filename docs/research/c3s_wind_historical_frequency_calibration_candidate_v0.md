<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# C3S EWS regional windstorm annual-count holdout calibration challenger

Date: 2026-11-04. **Research-only executable method; no real source sample admitted, no official download performed in this work, no Zurich insurer calibration.**

## Source already reviewed in this repository

This work composes, without altering, the existing **official-source annual CSV parser** `research_runners/c3s_wind_annual_summary_v0.py` and research metadata/rights manifest `manifests/copernicus.c3s.european-windstorm-reanalysis.v1.0.json` (metadata approved, **raw data not admitted**). Product DOI [10.24381/bf1f06a9](https://doi.org/10.24381/bf1f06a9), [C3S EWS dataset](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis). The source is a 1940-to-present historical ERA5-based storm-indicator series, not an insurer's losses and not automatically a stochastic windstorm CAT catalogue. This is distinct from C3S WISC's separate 22,980 synthetic storm **footprints**; never confuse that count with years or the source historical count frequency.

The existing C3S source `storm_number` is a regional NUTS annual summary at a **specific threshold and storm-tracking algorithm**; the two tracking algorithms and nested wind-gust thresholds must **never be summed**. The NUTS territorial version is not yet established by source CSV; therefore no building geocoding or company exposure overlay is authorized here.

## Implemented candidate and controls

`research_runners/c3s_wind_frequency_candidate_v0.py` first requires byte-exact SHA256 of the **original C3S CSV**, reuses the unchanged strict CSV parser, then selects one explicit `region × tracking algorithm × gust threshold` and requires **every** annual row including zero-storm years for contiguous non-overlapping train/holdout periods. It estimates one stationary Poisson count intensity `lambda = training event count / training years`, records exact rational numerator/denominator, Poisson probability of at least one event, sample variance / mean dispersion indicator, and independent holdout annual count distribution, Poisson log score and occurrence Brier score. The first model must NOT automatically pass just because the scores are finite; there is no empirical admission acceptance threshold or physical validation yet. The holdout case `lambda = 0` with positive observed events is an explicit *diagnostic failure*, with `holdout_log_likelihood = null` (no NaN/Infinity fraud).

**Scientific exclusions:** Stationarity, homogeneous Poisson counts, one region, event algorithm identity, climate nonstationarity, sample annual dependence, source counting definitions, storm geographies, event dates and event footprints are not independently validated by this fit. The model does not compute insurer exposure or insured gross/net losses; it does not feed count intensity straight into Oasis/NextGen as if it were an admitted event catalogue or shared catastrophe year measure. A single region annual count is not Europe's multi-country joint occurrence frequency, especially not a net Zurich Europe-wind regional frequency.

## Reproduction after a real C3S source has been approved and downloaded

```bash
# Run after separately recording exact C3S request, bytes and SHA256.
PYTHONPATH=. python3 research_runners/c3s_wind_frequency_candidate_v0.py \
  /path/to/original-c3s-ewss-annual-summary.csv \
  --expected-source-sha256 '<EXACT_64_HEX_SHA256_FROM_INDEPENDENT_SOURCE_RECEIPT>' \
  --region DE --algorithm '<EXACT_ALGORITHM_LABEL_FROM_ORIGINAL_CSV>' \
  --threshold-mps 20 \
  --train-start 1980 --train-end 2014 \
  --holdout-start 2015 --holdout-end 2024 \
  --out /tmp/c3s-de-20ms-storm-count-poisson-diagnostic.json
```

The example `DE`, years and threshold are *selection examples only*. The model **fails closed** when any source year is absent or labels do not exist; the raw file has not been checked in the current work. No catalogued *real* lambda or goodness of fit is claimed. Preselect source vintage, algorithm, NUTS unit, threshold and train/holdout spans **before** checking target insurer losses, and use a genuinely held-out source time block; avoid temporal leakage. The original `storm_number` and annual summary count remain different products than individual storm tracks, 72h gust footprint rasters or a vulnerability damage curve.

## Actually executed local synthetic-only tests

```shell
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_c3s_wind_frequency_candidate_v0.py' -v
```

8/8 local test cases PASS using synthetic CSVs **only**; includes correct MLE/holdout, algorithm-scope isolation, zero-year completeness, source SHA mismatch, nested-threshold scientific constraint (delegated upstream), train/holdout separation, zero-lambda unsupported positive holdout and deterministic receipt. Tests use the source parser's exact current bytes copied for a local execution. Exact official `OpenCatastrophe-data` GitHub CI has **not** yet been established; keep PR draft until original HEAD CI succeeds.

## Connection to the Zurich-inspired pilot

Stage 1 (this PR) pins **historical regional storm-count marginal estimation**; Stage 2 acquires **per-storm C3S wind footprints and tracks**, retaining the original physical event/season identity and cross-country hazards; Stage 3 applies **separately sourced asset geography, building taxonomy and valid wind vulnerability**; Stage 4 uses NextGen's strict claims/contract perspectives to generate **insurer gross and outward net OEP/AEP on a scientifically legitimate shared stochastic year sample**, with independently checked exposure marginals. Published Zurich net risk metrics can only be holdout challenges after compatible USD currency, perimeter, reinsurance definition and annual aggregation are matched.

Do not reinterpret a fitted regional marginal annual Poisson count as a stochastic insurer catastrophe model, or import the current independently simulated 10k toy results as observations.
