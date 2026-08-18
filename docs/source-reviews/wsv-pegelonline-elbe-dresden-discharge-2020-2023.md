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
- Predeclared holdout: **1,461 physical UTC comparison days from 2020-01-01 through 2023-12-31**

## Why this source closes a current gap

OpenCatastrophe already admits the CEMS GloFAS historical product as **modelled** river discharge. That manifest explicitly says GloFAS discharge is not a direct river-gauge observation. PEGELONLINE supplies a public gauge observation route that can test one bounded location/time slice without adding a generic hydrology catalogue.

Dresden is selected before target-value inspection because:

- PEGELONLINE exposes a stable station UUID and long-term raw `Q` data;
- authoritative German hydrology metadata report a 53,096 km² drainage area, comfortably above the 500 km² scale used in GloFAS gauge-selection methodology;
- the physical 2020–2023 window is after the documented GloFAS v4 calibration period ending in 2019, so it can serve as a **temporal holdout**. This does not prove that Dresden itself was absent from model calibration; if station overlap exists, results must be labelled a temporal holdout at a potentially calibrated location rather than an independent-site validation.

No target discharge values from the holdout are inspected to choose the location, window, matching rule, aggregation operator or metrics.

## PEGELONLINE scientific semantics

PEGELONLINE describes the webservice values as **ungeprüfte Rohdaten** (unvalidated raw data). The Dresden station page exposes discharge and water level and offers long-term raw discharge downloads from 1 January 2000.

Supporting state hydrology documentation explains that discharge is obtained from observed water level through a continuously monitored stage–discharge relationship. Therefore `Q` should be treated as an observation-derived hydrological quantity, not as a direct volumetric flow-meter measurement.

PEGELONLINE documents two different download-time conventions that must not be conflated. The separate free **daily-file** service states that timestamps are provided year-round in Central European standard time. The **long-term water-level/discharge download** instead uses local legal time; its JSON format carries ISO-8601 timestamps with complete timezone information, including the UTC offset for MEZ/MESZ. This Dresden pilot therefore freezes **long-term JSON** as the target format and converts each explicit source offset to UTC. The CSV long-term representation is not the scientific ingestion format because its simplified local-time strings omit the explicit offset and can be ambiguous around daylight-saving transitions.

### Pre-target REST metadata resolution

Before any holdout `Q` values were inspected, the official PEGELONLINE REST-v2 station metadata for the frozen Dresden UUID was resolved on 2026-08-10 with `includeTimeseries=true` and without requesting `currentMeasurement`. The response identified:

- station number: `501060`;
- station short name / water: `DRESDEN` / `ELBE`;
- WGS84 latitude / longitude: **51.054460 / 13.738832**;
- exactly one discharge time series `Q` with long name `ABFLUSS_ROHDATEN`;
- unit: **m³/s**;
- `equidistance`: **15 minutes**.

For this preregistered pilot, those pre-target metadata freeze the PEGELONLINE source grid to **900 seconds**, hence **96 expected source observations per 24-hour comparison window**. `scripts/parse_pegelonline_metadata.py` makes the provider-metadata interpretation executable and rejects measurement-bearing responses, station-identity drift, Q-semantic drift, non-finite coordinates, ambiguous Q series and sampling intervals that cannot form an exact 24-hour grid.

These resolved values are not a substitute for byte-level acquisition evidence. The exact saved REST metadata request and response must still be fingerprinted with byte size and SHA-256 before target acquisition is considered reproducible. If the preserved provider response does not reproduce the frozen values above, the pilot fails closed for review instead of changing the sampling or station metadata after target inspection.

## Access and rights assessment

The PEGELONLINE webservice/download pages explicitly state that the unvalidated raw data are available under **Datenlizenz Deutschland – Zero – Version 2.0 (DL-DE-Zero-2.0)**.

The official GovData licence text permits commercial and non-commercial copying, modification, combination, transmission and incorporation without restrictions or conditions.

Engineering interpretation:

- commercial use: allowed;
- redistribution/adaptation: allowed;
- attribution: not a licence condition, though provider/station provenance remains scientifically required by OpenCatastrophe;
- repository scope: metadata only;
- at this source review time, no generated long-term discharge download file had been acquired or approved for Git publication; later external receipts do not retroactively alter that review-time statement or authorize Git publication.

## Predeclared GloFAS comparison contract

This contract is part of the admission rationale. It must be changed in a reviewed commit **before** inspecting comparison results, never after seeing skill scores.

### GloFAS slice

Use the already admitted CEMS GloFAS historical source with:

- system version: `version_4_0`;
- hydrological model: `lisflood`;
- product type: `consolidated`;
- variable: `river_discharge_in_the_last_24_hours` (`dis24`);
- physical UTC comparison windows: **`[2020-01-01T00:00:00Z, 2024-01-01T00:00:00Z)`**;
- corresponding end-labelled `dis24` timestamps: **2020-01-02T00:00:00Z through 2024-01-01T00:00:00Z**, exactly **1,461 labels**;
- 0.05° v4.0 grid;
- the official upstream-area ancillary data for the same GloFAS v4.0 cycle.

CEMS model-output documentation defines `dis24` as river discharge averaged over the 24-hour model time step and states that the stored timestamp marks the **end** of that averaging period. The published GloFAS reanalysis methodology likewise describes daily discharge as the average from 00:00 UTC to 00:00 UTC and assigns it to the date at the end of the 24-hour window. Therefore each decoded GloFAS timestamp `T` represents exactly the half-open interval **`[T - 24 hours, T)`**. No empirical lead/lag search or alternate day boundary is permitted.

The physical-window definition is intentional: requesting provider labels 2020-01-01 through 2023-12-31 would include a window beginning in 2019 and omit the final physical day of 2023. The executable holdout contract therefore uses the end labels above while preserving the original scientific intent of testing the physical calendar years 2020–2023.

All exact EWDS requests and returned file hashes remain outside Git until separately reviewed.

### Gauge-to-grid matching

The executable metadata-only selector in `scripts/hydrology_grid_matching.py` is the authority for this preregistration:

1. Resolve and freeze the Dresden WGS84 coordinate from the immutable PEGELONLINE station metadata; the pre-target resolution above yields **51.054460 / 13.738832**.
2. Consider candidate GloFAS v4.0 cells whose spherical **great-circle angular distance is <= 0.15°** from that station coordinate.
3. Require absolute relative upstream-area mismatch against the authoritative Dresden drainage area 53,096 km² to be **<= 10%**.
4. Select the eligible cell with minimum absolute relative drainage-area mismatch.
5. Break an exact mismatch tie by minimum great-circle angular distance.
6. Break any remaining exact tie canonically by latitude and then longitude ascending.
7. If no cell satisfies the rule, **fail closed**. Do not expand the radius or relax the 10% threshold after inspecting discharge values.

The historical >=500 km² calibration-scale context remains scientifically relevant but is not a separate executable filter for Dresden: the 10% mismatch gate around 53,096 km² already implies an eligible model upstream area of at least 47,786.4 km². Keeping a second redundant gate would not alter the eligible set.

The 0.15° neighborhood and deterministic tie-break sequence are OpenCatastrophe preregistration rules, not claims that CEMS selected Dresden or its grid cell using this exact procedure.

### Time alignment, observed aggregation and completeness

- Acquire the PEGELONLINE **long-term raw download in JSON format**. Parse its documented ISO-8601 timestamps with the explicit local legal-time UTC offset and convert each source timestamp to UTC. Do not apply the separate daily-file fixed-MEZ convention to this long-term JSON workflow.
- Require the parsed/converted series to cover the exact physical UTC interval **`[2020-01-01T00:00:00Z, 2024-01-01T00:00:00Z)`** before trimming; a provider-facing civil-date request may be broader but may not narrow this UTC coverage.
- Use the pre-target frozen `Q` sampling interval of **15 minutes / 900 seconds**, hence **96 expected observations per 24-hour window**.
- For each GloFAS `dis24` timestamp `T`, use exactly the interval `[T - 24 hours, T)`.
- A comparison day is valid only when at least 90% of the 96 expected regular PEGELONLINE source observations for that exact interval are present and finite. The executable threshold therefore requires at least **87 finite source observations**.
- If the daily source window passes the completeness gate, define observed daily discharge as the **arithmetic mean of all finite `Q` samples on the frozen regular sampling grid within that exact window**. This operator is fixed before holdout inspection to match the GloFAS 24-hour mean-discharge semantics without interpolation or data-dependent time weighting.
- If the completeness gate fails, the observed daily value is unavailable for skill metrics. Do not fill, interpolate or shift the day.
- The GloFAS value must be finite as well for the day to enter paired skill metrics.
- No empirical timestamp shift, alternate day boundary or post-hoc aggregation rule is allowed.

The 90% threshold applies within each 24-hour source window. This pre-registration does not invent an additional whole-holdout coverage threshold; instead, the final result must report the valid-day count and fraction against the fixed **1,461-day denominator**.

### Metrics

Compute over all valid matched days in the frozen holdout:

- modified Kling–Gupta Efficiency (KGE′), matching the objective used in GloFAS v4 calibration/evaluation; the implementation must document the exact equation/reference and must not silently substitute the original KGE formulation;
- Pearson correlation coefficient;
- relative mean bias `(mean_model / mean_observed) - 1`;
- count and fraction of valid comparison days.

Report all metrics whether favourable or unfavourable. A mathematically undefined metric must be reported as not comparable rather than as NaN/Infinity. Do not tune GloFAS parameters, station mapping, date range, filtering or metric definitions using the holdout.

This pilot characterises one model/location/time comparison. It does not establish Germany-wide or global GloFAS validity and does not turn a river-discharge comparison into a flood-inundation validation.

## Requirements before any raw/derived publication

For PEGELONLINE, freeze and fingerprint the exact metadata-only REST request/response used above plus the generated long-term **JSON** `Q` download request/file, source timestamp offsets, byte size and SHA-256. For GloFAS, freeze and fingerprint the exact v4.0 upstream-area ancillary request/file plus the complete EWDS target request, system version and returned target hashes. `scripts/dresden_acquisition_evidence.py` provides the pre-admission byte-identity bridge; obtaining those hashes does **not** itself promote either metadata-only manifest to raw publication. Any daily aggregation or comparison output additionally needs deterministic code/configuration identity and separate rights/derived-artifact review.

## Authoritative public references

- PEGELONLINE station: `https://pegelonline.wsv.de/gast/stammdaten?pegelnr=501060`
- PEGELONLINE REST-v2 Dresden metadata request: `https://pegelonline.wsv.de/webservices/rest-api/v2/stations/70272185-b2b3-4178-96b8-43bea330dcae.json?includeTimeseries=true`
- PEGELONLINE downloads/licence: `https://www.pegelonline.wsv.de/webservice/downloads`
- PEGELONLINE help / long-term download formats and timestamp semantics: `https://pegelonline.wsv.de/gast/hilfe`
- PEGELONLINE REST API documentation: `https://pegelonline.wsv.de/webservice/dokuRestapi`
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
