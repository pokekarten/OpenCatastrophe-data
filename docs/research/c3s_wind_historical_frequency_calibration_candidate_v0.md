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

## 2026-11-05 scientific correction: incomplete calendar year and zero-count dispersion

The [official C3S dataset catalogue](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis) documents a **monthly-updated** ERA5 windstorm service, with *annual* regional indicators; the [publisher's product user guide](https://confluence.ecmwf.int/spaces/CKB/pages/462911116/Windstorm+tracks+and+footprints+derived+from+reanalysis+over+Europe+between+1940+to+present+Product+User+Guide) identifies `storm_number` as the annual count of storm footprints intersecting a NUTS region above the explicitly selected threshold. The [original ECMWF catalogue STAC listing](https://cds.climate.copernicus.eu/stac-browser/collections/sis-european-wind-storm-reanalysis) inspected on 2026-11-05 advertised coverage **1940-02-01 through 2026-04-04**. Neither **1940** (source starts in February) nor **2026** (unfinished year) can be treated as one fully observed calendar-year count without independent coverage proof; missing months are not observed zero-storm months.

**Conservative fail-closed research-v0 rule:** This version accepts **only the calendar years 1941–2025** as training or holdout boundaries, even if the received original CSV already contains `1940` or `2026` rows. The code does not extrapolate partial years or silently prorate them to full years. Extending either boundary requires a **new independently dated, complete source-coverage receipt and a reviewed revision**. These fixed versioned cutoffs do not claim that historical 2025 CSV source bytes have been acquired or that their release/vintage is scientifically approved.

If all training-year event counts are zero, the Poisson MLE rate is exactly zero, but the sample-variance-to-mean ratio is **undefined (0/0)**. The research receipt now records `train_variance_to_mean_ratio: null` and `train_dispersion_ratio_defined: false`, not a misleading zero implying adequate dispersion. If positive storms occur in the independent holdout, `holdout_log_likelihood` remains `null` with an explicit diagnostic failure; neither case is a calibrated CAT model. Separate synthetic-only tests challenge both the unfinished-year boundary and the zero-mean cases.

**Still unproven:** original provider annual-summary CSV bytes, NUTS vintage/joins, track IDs, multi-region common physical storm identity, dependent/severe hazard event footprints, calibrated vulnerability and insurer Gross/Net AEP/OEP. The full exact-head CI must pass before technical review, and technical success is **not source/science admission**.


## 2026-11-05 — original CDS form verified and safe acquisition prepared

**Direct metadata verification (not a CSV download):** The current ECMWF [C3S EWS STAC collection](https://cds.climate.copernicus.eu/api/catalogue/v1/collections/sis-european-wind-storm-reanalysis) was fetched; its linked [original download form](https://object-store.os-api.cci2.ecmwf.int/cci2-prod-catalogue/resources/sis-european-wind-storm-reanalysis/form_412cb1af4fc7a078f99700f0647e24bbd7681c2d43c9b03949e251b351318b63.json) and [conditional selection constraints](https://object-store.os-api.cci2.ecmwf.int/cci2-prod-catalogue/resources/sis-european-wind-storm-reanalysis/constraints_3fd6d9cc11e6b4a27abbea37af4c05e698f7ee392c514786a767c330e8dec470.json) were accessed independently. The annual summary branch's verified provider selectors are:

    {"product":"windstorm_summary_indicator","variable":["all"],"tracking_algorithm":["hodges","tempestextremes"]}

The provider form also exposes event_aggregation, year/month/day, footprint resolution and spatial extent; **these belong to different product branches**. There is no verified annual summary per-region/year selector; the full original provider CSV must be acquired and only then locally filtered by year, algorithm, region and threshold. The two tracking algorithms are not additive physical storms.

Added an offline-safe, opt-in intake script at research_runners/c3s_ews_annual_original_acquisition_v0.py: by default it only prints the exact provider request; --execute requires an existing user-controlled, licensed and authenticated CDS API environment. For a future original response it accepts a source CSV or a one-CSV ZIP, conserves separate raw package and CSV member SHA-256 values, checks the original ten-column scientific schema, refuses package overwrite, refuses raw data under Git, rejects login HTML, non-CSV ZIPs, ambiguous ZIP members and source schema drift. Its output is always a **non-admitted research receipt**, never a fitted regional windstorm model.

    # Offline safe request inspection (no network, secrets or licence acceptance):
    PYTHONPATH=. python3 research_runners/c3s_ews_annual_original_acquisition_v0.py

    # ONLY after manual licence acceptance and local CDS token configuration:
    python3 -m pip install 'cdsapi>=0.7.7'
    PYTHONPATH=. python3 research_runners/c3s_ews_annual_original_acquisition_v0.py --execute --out-dir /private/local-c3s-original-downloads

Per [CDS API setup](https://cds.climate.copernicus.eu/how-to-api), the actual data download requires an individual personal-access token and **manual acceptance of that specific dataset's terms**. In this work no user credentials were obtained, no terms were accepted on the user's behalf, no authenticated data retrieval was executed, and no original C3S annual CSV bytes were downloaded. Metadata inspection does not bypass the download rights gate.

**Next actual source gate:** authorized download, external original ZIP/CSV SHA-256 receipt, strict CSV schema verification and independent per-year completeness / NUTS-version review. Until then the physical event catalogue, multi-region covariance, actual insured exposures, calibration and NextGen insurer gross/net/AEP/OEP claims remain blocked. Keep PR draft and scientific admission false.
