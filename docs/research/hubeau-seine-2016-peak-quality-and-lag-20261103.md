<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# 2016 Seine flood: original quality-coded peak is not a calibration target

**Date: 2026-11-03. Status: independently executed research and provider-API semantics, NOT source/model admission.** This is a causal follow-up to merged [source usability #1205](https://github.com/pokekarten/OpenCatastrophe-data/pull/1205), which already verified all 94 daily records against live Hub'Eau. It does not re-commit the observations. Neither the 2016 flood footprint nor the 2016 insured building inventory is validated by these checks.

## Original external provider semantics

The authoritative [Hub'Eau Hydrométrie API](https://www.data.gouv.fr/dataservices/hubeau-hydrometrie) documents `obs_elab`, daily mean flow `QmnJ`, and discharge in litres/second. Its live API v2.0.1 responses retrieved on 2026-11-03 for the exact station/day peaks explicitly give:

| Station/day | Provider QmnJ | Status (provider label) | Qualification (provider label) | Method (provider label) |
| --- | ---: | --- | --- | --- |
| `F447000302` / **2016-06-03** | 1,299,307 litres/s = **1,299.307 m³/s** | code 12, `Donnée pré-validée` | code 12, **`Douteuse` (doubtful)** | code 8, `Calculée` |
| `F700000103` / **2016-06-04** | 1,745,481 litres/s = **1,745.481 m³/s** | code 16, `Donnée validée` | code 20, `Bonne` (good) | code 4, **`Reconstituée` (reconstructed)** |

The official one-day provider queries used the exact reviewed URL shape:
- `https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab?code_entite=F447000302&date_debut_obs_elab=2016-06-03&date_fin_obs_elab=2016-06-03&grandeur_hydro_elab=QmnJ&size=1`
- `https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab?code_entite=F700000103&date_debut_obs_elab=2016-06-04&date_fin_obs_elab=2016-06-04&grandeur_hydro_elab=QmnJ&size=1`

The additional exact 7-day Ponthierry request for 1–7 June returned all seven records with status=12 `Donnée pré-validée`, qualification=12 `Douteuse`, method=8 `Calculée`. The source labelled these fields explicitly; no speculative SANDRE code interpretation is needed. Requests were made through a connected web-content intermediary, *not an independently hash-authenticated original-byte acquisition*. Source bytes and station coordinates were **not** stored in the repository.

The independently published [HydroPortail station synthesis for Paris-Austerlitz](https://hydro.eaufrance.fr/stationhydro/F700000103/impression-synthese) lists daily mean discharge maximum **1,750,000 litres/s** on 4 June 2016. It also separately lists **instantaneous flow maximum 1,800,000 litres/s on 3 June**: these **must never be interchanged**. That station summary notes **strong local influence throughout the year**. The reported daily maximum is rounded compared with the precise API/QmJ sample and is a context consistency check, not byte-parity proof.

## Executed Neon evidence

Two `SELECT`-only scripts were independently run against the existing CAT-only Neon `insurance-risk-core` project, `insurance` database, default main branch **before being committed**:

1. [Peak qualification and method gate](../../research_runners/sql/hubeau_2016_peak_quality_gate_v0.sql) returned:

| Stored station | Days | Doubtful | Prevalidated / Validated | Peak day | Peak flow, m³/s | Highest quality-20 flow, m³/s | Highest validated AND quality-20 flow |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `F447000302` | 47 | 7, **all 1–7 June** | 47 / 0 | 2016-06-03 | 1299.307 | **777.998** (outside highest flood days; *not a substitute for peak*) | **NULL** |
| `F700000103` | 47 | 0 | 0 / 47 | 2016-06-04 | 1745.481 | 1745.481 | 1745.481 |

Ponthierry gate = `PEAK_DOUBTFUL_NOT_CALIBRATION`. Paris gate = `PEAK_NON_DIRECT_METHOD_REVIEW` because the validated, good-quality peak is **reconstructed** rather than a confirmed direct discharge measurement. On **both** rows `rights_cleared_rows=0`, `event_verified_rows=0`, `model_admitted_rows=0`: `RESEARCH_ONLY_SOURCE_GATES_OPEN`.

2. [Cross-station lag sensitivity](../../research_runners/sql/hubeau_2016_lag_sensitivity_v0.sql) returned correlations between daily mean discharges, where lag L is Paris day minus Ponthierry day:

| Calendar lag L, days | Paired days (levels) | QmnJ Pearson level correlation | Correlation of day-to-day changes |
| ---: | ---: | ---: | ---: |
| -2 | 45 | 0.8084 | 0.5006 |
| -1 | 46 | 0.9351 | 0.6976 |
| 0 | 47 | 0.9924 | 0.9399 |
| 1 | 46 | 0.9582 | 0.8165 |
| 2 | 45 | 0.8444 | 0.5097 |

This is **only descriptive**. For example the raw observed highest QmnJ days differ by +1 calendar day, while both level and first-difference contemporaneous correlations are highest at lag 0 on this finite 47-day window. This does **not** measure or prove physical flood-wave travel time. Correlation of temporally autocorrelated river flows may be inflated by the shared event hydrograph. Ponthierry's seven doubtful days overlap the event peak, so quality-20-only sensitivity excludes the highest stage and is **not an unbiased true-peak estimator**.

## Scientific and licensing consequences

- Do not calibrate flood depth or an asset vulnerability curve against the doubtful Ponthierry peak or against a contemporaneous/lagged correlation from this window. A 2016 flood-depth raster, independently verified geometry and hydraulic boundary conditions are required.
- The Paris peak is a reconstructed, good-quality, validated **daily mean**; it is neither a direct instantaneous discharge observation nor an insured loss or building inundation depth.
- These two stations differ in river context and local influence. A day difference in peak date is not by itself an elapsed flow-travel time, and station-level rates must not be equated with a local parcel flood depth.
- Source records may change after retrieval; retain API version and exact query plus future frozen original-response SHA-256 for scientific reproducibility. A live semantic query and stored 64-digit SHA format are not provider-byte authentication.
- `original_licence_reuse_reviewed=false` on all 94 stored observations at this review: neither successful HTTP retrieval nor public API documentation alone authorizes commercial CAT-model ingestion or release under our native admission contract.
- **No writes to Neon, no provider original data bytes in Git, no rights change, no production/insured-loss claims**. These are reproducible research-only SQL checks, not user-data or portfolio processing.

## Next scientific input needed

A **separate independently reliable 2016 high-water-stage or inundation-depth reference**, ideally station rating curves, timestamped stage and source-verified observed flood polygons in the correct 2016 AOI, with geometry topology and rights separately checked. If the Ponthierry original historical discharge peak is to be used, seek an authoritative corrected series or provider explanation and freeze its exact source version rather than silently converting `Douteuse` to `Bonne`. Then a rights-cleared 2016-vintage building inventory, vulnerability functions and independent validation are needed before GUL modelling.

## Reproduction

Execute the two SQL scripts **read-only** in Neon `insurance-risk-core / insurance / main`. They return only aggregate station/date/quality diagnostics and do not export the underlying daily series. Their live results were compared to the exact provider fields and public HydroPortail synthesis. Before merging this PR, run the repository definition-of-done `python scripts/check_all.py` on the exact PR head; green tests verify code quality, not hydrologic sufficiency.
