<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First insurer Europe-wind CAT: C3S × CLIMADA × NextGen research contract

Date 2026-11-04. **Engineering specification only — neither original C3S source bytes nor a CLIMADA/NextGen native hazard-loss calibration were executed.** No Zurich asset-location, CAT tower, or PML is inferred from this document.

## Independently verifiable external sources

- [C3S Enhanced Windstorm Service official data](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis) (DOI 10.24381/bf1f06a9): tracks (6-hour CSV), 72-hour event maximum 10 m wind-gust footprints (NetCDF4 at 0.25° ERA5 or 0.016° downscaled), regional annual summary counts (CSV). Gust thresholds are 0 / 15.6 / 20 / 25 m/s; region units NUTS0/1/2; algorithms TempestExtremes and TRACK. The source updates monthly; product version 1.0 is **not** an immutable raw-file identity.
- [Official C3S Product User Guide](https://confluence.ecmwf.int/spaces/CKB/pages/462911116/Windstorm+tracks+and+footprints+derived+from+reanalysis+over+Europe+between+1940+to+present+Product+User+Guide): regional storm count is the number of storm *decontaminated* footprints intersecting one region at one threshold. Do not add counts across overlapping regions, across nested thresholds, or across algorithms. Full-domain and decontaminated footprints are distinct products.
- [CLIMADA 6.1.0 Impact Function Calibration API](https://climada-python.readthedocs.io/en/stable/api/climada/climada.util.calibrate.html): `climada.util.calibrate.base.Input` takes hazard, exposure, observed impact data, an impact-function creator, a model-output projection, a cost function and bounds. Bayesian and event-ensemble optimizers can estimate parameters and variation. Since v6.0.1 the cost function expects NumPy and optional data weights: explicitly pin the implementation version.
- [Riedel, Kropf and Schmid, JOSS 2024](https://doi.org/10.21105/joss.06755): peer-reviewed implementation of the CLIMADA impact-function calibration module. It needs **observed event-level impacts** compatible with source hazard and exposure; annual group net AEL/PML is not a proxy for event-level claims.

## Four source contracts — never collapse the evidence layers

1. `C3S_COUNT_V0`: pin exact original CSV bytes, SHA256, retrieval selectors, NUTS vintage, one region, one algorithm, one threshold, calendar train/holdout. Reuse `c3s_wind_annual_summary_v0.py` plus PR #1308 `c3s_wind_frequency_candidate_v0.py` for **count-rate diagnostic only**. It does not create a stochastic physical event catalogue.
2. `C3S_EVENT_V0`: independently pin each storm's original track, physical event identity/date, decontaminated NetCDF gust map, time windows, grid/CRS/unit and raw SHA256. A NUTS summary count is not an asset-level hazard field. Never silently merge different tracking algorithms or split one shared storm into one event per country.
3. `EXPOSURE_AND_IMPACT_V0`: building coordinates, occupancy/structural class, replacement/contents/BI value, independently stated insurance penetration and policy hypotheses; separate historic event-specific **observed losses** with exact claim basis, geography, time, currency and rights. Physical building stock is **not** Zurich's actual insured portfolio. Absent impact observations are a hard block for vulnerability **calibration**.
4. `ANNUAL_EVENT_FINANCE_V0`: globally shared physical-event IDs, chronology, annual sampling measure including zero-event years, per-asset GUL, original policy insured gross, outward Cat XL / inward reinsurance, retro and retained net. Keep asset-level gross separate from insured original gross; prevent intragroup double-counting; independently test exact `gross = net + cessions` at each economic boundary.

## Scientific experiment and holdouts

Use an explicit, independently validated historical count catalogue to compare possible annual event-number models (Poisson is a hypothesis, not automatic truth; measure overdispersion, dependence and trend). Calibrate occupancy/peril-specific CLIMADA `ImpactFuncSet` against disjoint **physical storm** train/holdout event groups and independent historical impact data; NEVER randomly split pixels of the same storm across train/holdout. Record model release, optimizer seed, parameter bounds, cost function, receipt hashes and validation errors. A single fitted observed mean does not prove the tail, uncertainty or storm clustering.

The currently runnable synthetic NextGen PR #280 10k-year *independent* challenger is a financial/numerical oracle, not the native F5/CLIMADA/Oasis engine. Its new caller-supplied world-ID audit detects omission of synthetic quiet years but cannot by itself verify source frequency, vulnerability, risk geography or downstream regulatory capital. Its initial F5 wind mode uses **Bernoulli ≤ 1 event per peril/year**, not an empirical Poisson multi-occurrence catalogue.

Zurich's 2025 Europe wind USD **net** AEL and annual aggregate 100-year PML must be evaluated only as external post-fit holdouts after verified corporate/peril/country perimeter, FX/year basis, insurance treaty rights and source uncertainty are resolved. Do **not** fit the source hazard or invented insurer TIV to force these disclosed net values.

## Promotion gates (all presently open)

- [ ] Download, pin and license-review exact C3S annual CSV / track / NetCDF assets, including provenance and annual zero-event domain.
- [ ] Verify source NUTS vintage and storm event/year identity; validate selected event gust footprints independently (for example against DWD station observations at matching times).
- [ ] Obtain a geographically plausible synthetic asset inventory and *separate* admitted event-level historic impact observations with legally usable rights.
- [ ] Pin CLIMADA release, validate synthetic grid-to-asset overlap plus impact-function unit tests, train/holdout and uncertainty diagnostics.
- [ ] Generate a **scientifically admissible** physical shared annual event process, preserving multi-storm years, temporal ordering and spatial cross-country dependence; reject unsupported hours/reinstatement assumptions.
- [ ] Execute authentic full private NextGen Source → Original → Inward → Retro → Gross/Net AEP/OEP model and independent reference, with all CI and strict numeric gates.

Neither raw C3S acquisition, actual CLIMADA `Input` optimization, Oasis/OpenQuake original models nor real insurer return-period output is claimed here.
