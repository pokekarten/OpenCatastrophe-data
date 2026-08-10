<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: PEGELONLINE Dresden discharge, 2020–2023 holdout

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/wsv.pegelonline.elbe-dresden-discharge.2020-2023.json`
- Provider: Wasserstraßen- und Schifffahrtsverwaltung des Bundes (WSV) / PEGELONLINE
- Station: DRESDEN / ELBE, number `501060`
- Immutable PEGELONLINE station UUID: `70272185-b2b3-4178-96b8-43bea330dcae`
- Variable: raw discharge `Q`, m³/s
- Predeclared holdout: **2020-01-01 through 2023-12-31**

## Why this source closes a current gap

OpenCatastrophe already admits the CEMS GloFAS historical product as **modelled** river discharge. That manifest explicitly says GloFAS discharge is not a direct river-gauge observation. PEGELONLINE supplies a public gauge observation route that can test one bounded location/time slice without adding a generic hydrology catalogue.

Dresden is selected before target-value inspection because:

- PEGELONLINE exposes a stable station UUID and long-term raw `Q` data;
- authoritative German hydrology metadata report a 53,096 km² drainage area, comfortably above the 500 km² scale used in GloFAS gauge-selection methodology;
- the 2020–2023 window is after the documented GloFAS v4 calibration period ending in 2019, so it can serve as a **temporal holdout**. This does not prove that Dresden itself was absent from model calibration; if station overlap exists, results must be labelled a temporal holdout at a potentially calibrated location rather than an independent-site validation.

No target discharge values from the holdout are inspected to choose the location, window, matching rule, aggregation operator or metrics.

## PEGELONLINE scientific semantics

PEGELONLINE describes the webservice values as **ungeprüfte Rohdaten** (unvalidated raw data). The Dresden station page exposes discharge and water level and offers long-term raw discharge downloads from 1 January 2000.

Supporting state hydrology documentation explains that discharge is obtained from observed water level through a continuously monitored stage–discharge relationship. Therefore `Q` should be treated as an observation-derived hydrological quantity, not as a direct volumetric flow-meter measurement.

The PEGELONLINE download documentation states that file timestamps use Central European standard time throughout the year. Any comparison with GloFAS UTC time must therefore convert source timestamps explicitly; daylight-saving assumptions must not be introduced.

The newer PEGELONLINE/HYDAS metadata interfaces expose the time-series resolution/equidistance as metadata. The Dresden `Q` sampling interval must therefore be frozen from the retrieved time-series metadata before target values are loaded; no interval is hard-coded from a generic PEGELONLINE example.

## Access and rights assessment

The PEGELONLINE webservice/download pages explicitly state that the unvalidated raw data are available under **Datenlizenz Deutschland – Zero – Version 2.0 (DL-DE-Zero-2.0)**.

The official GovData licence text permits commercial and non-commercial copying, modification, combination, transmission and incorporation without restrictions or conditions.

Engineering interpretation:

- commercial use: allowed;
- redistribution/adaptation: allowed;
- attribution: not a licence condition, though provider/station provenance remains scientifically required by OpenCatastrophe;
- repository scope: metadata only;
- no generated download file has been acquired or approved for Git publication.

## Predeclared GloFAS comparison contract

This contract is part of the admission rationale. It must be changed in a reviewed commit **before** inspecting comparison results, never after seeing skill scores.

### GloFAS slice

Use the already admitted CEMS GloFAS historical source with:

- system version: `version_4_0`;
- hydrological model: `lisflood`;
- product type: `consolidated`;
- variable: `river_discharge_in_the_last_24_hours` (`dis24`);
- date range: 2020-01-01 through 2023-12-31;
- 0.05° v4.0 grid;
- the official upstream-area ancillary data from the same GloFAS product documentation.

CEMS model-output documentation defines `dis24` as river discharge averaged over the 24-hour model time step and states that the stored timestamp marks the **end** of that averaging period. The published GloFAS reanalysis methodology likewise describes the daily discharge as the average from 00:00 UTC to 00:00 UTC and assigns it to the date at the end of the 24-hour window. Therefore, after decoding the GloFAS timestamp `T` to UTC, this pilot fixes the comparison interval to the half-open window **`[T - 24 hours, T)`**. No empirical lead/lag search or alternate day boundary is permitted.

All exact EWDS requests and returned file hashes remain outside Git until separately reviewed.

### Gauge-to-grid matching

1. Resolve the Dresden WGS84 coordinate from PEGELONLINE station metadata using the immutable UUID.
2. Consider GloFAS river cells within 0.15° of that coordinate.
3. Require model upstream area >= 500 km².
4. Require relative drainage-area mismatch against the authoritative Dresden value 53,096 km² to be <= 10%. This is an OpenCatastrophe pre-registration rule informed by the explicit `<10%` real-versus-model drainage-area consistency criterion documented for GloFAS v5 calibration stations; it is not evidence that GloFAS v4 selected Dresden or any other v4 calibration station using that same threshold.
5. Select the eligible cell with minimum absolute relative drainage-area mismatch; break an exact tie by shortest geodesic distance to the station.
6. If no cell satisfies the rule, **fail closed**. Do not expand the radius or relax the 10% threshold after inspecting discharge values.

The matching rule is a project pre-registration, not a claim that CEMS itself selected the same Dresden grid cell.

### Time alignment, observed aggregation and completeness

- Convert PEGELONLINE timestamps from documented year-round Central European standard time to UTC.
- Freeze the PEGELONLINE `Q` sampling interval from the retrieved source time-series metadata before loading target values.
- For each GloFAS `dis24` timestamp `T`, use exactly the interval `[T - 24 hours, T)`.
- A comparison day is valid only when at least 90% of the expected regular PEGELONLINE source observations for that exact interval are present and finite.
- If the daily source window passes the completeness gate, define observed daily discharge as the **arithmetic mean of all finite `Q` samples on the frozen regular sampling grid within that exact window**. This operator is fixed before holdout inspection to match the GloFAS 24-hour mean-discharge semantics without interpolation or data-dependent time weighting.
- If the completeness gate fails, the observed daily value is unavailable for skill metrics. Do not fill, interpolate or shift the day.
- The GloFAS value must be finite as well for the day to enter paired skill metrics.
- No empirical timestamp shift, alternate day boundary or post-hoc aggregation rule is allowed.

The 90% threshold applies within each 24-hour source window. This pre-registration does not invent an additional whole-holdout coverage threshold; instead, the final result must report the count and fraction of valid matched days.

### Metrics

Compute over all valid matched days in the frozen holdout:

- modified Kling–Gupta Efficiency (KGE′), matching the objective used in GloFAS v4 calibration/evaluation; the implementation must document the exact equation/reference and must not silently substitute the original KGE formulation;
- Pearson correlation coefficient;
- relative mean bias `(mean_model / mean_observed) - 1`;
- count and fraction of valid comparison days.

Report all metrics whether favourable or unfavourable. Do not tune GloFAS parameters, station mapping, date range, filtering or metric definitions using the holdout.

This pilot characterises one model/location/time comparison. It does not establish Germany-wide or global GloFAS validity and does not turn a river-discharge comparison into a flood-inundation validation.

## Requirements before any raw/derived publication

For PEGELONLINE, freeze the generated long-term download request/file, source timestamps, source time-series metadata including the sampling interval/equidistance, byte size and SHA-256. For GloFAS, freeze the complete EWDS request, system version, upstream-area ancillary identity and returned hashes. Any daily aggregation or comparison output needs deterministic code/configuration identity and separate rights/derived-artifact review.

## Authoritative public references

- PEGELONLINE station: `https://pegelonline.wsv.de/gast/stammdaten?pegelnr=501060`
- PEGELONLINE downloads/licence: `https://www.pegelonline.wsv.de/webservice/downloads`
- PEGELONLINE REST API: `https://pegelonline.wsv.de/webservice/dokuRestapi`
- PEGELONLINE/HYDAS API documentation: `https://www.pegelonline.wsv.de/webservice/dokuHydasapi`
- DL-DE-Zero-2.0: `https://www.govdata.de/dl-de/zero-2-0`
- Dresden drainage-area support: `https://www.umwelt.sachsen.de/umwelt/infosysteme/hwims/portal/web/wasserstand-pegel-501060`
- GloFAS historical product: `https://ewds.climate.copernicus.eu/datasets/cems-glofas-historical`
- CEMS model-output variable/time semantics: `https://confluence.ecmwf.int/display/CEMS/Model+Output`
- GloFAS reanalysis methodology and daily discharge semantics: `https://essd.copernicus.org/articles/12/2043/2020/`
- GloFAS v4 release details: `https://confluence.ecmwf.int/spaces/CEMS/pages/388505179/GloFAS+v4.0`
- GloFAS v4 calibration data/matching rationale: `https://confluence.ecmwf.int/spaces/CEMS/pages/340755424/GloFAS+v4+calibration+data`
- GloFAS v4 calibration methodology and KGE′ objective: `https://confluence.ecmwf.int/spaces/CEMS/pages/340755426/GloFAS+v4+calibration+methodology+and+parameters`
- GloFAS v5 calibration-station drainage-area consistency criterion: `https://confluence.ecmwf.int/spaces/CEMS/pages/673567677/GloFAS+v5+calibration+data`
