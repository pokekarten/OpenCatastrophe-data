<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FEMA historical geospatial damage: live aggregate-only source receipt (2026-11-01)

**Scope:** Public FeatureServer layer **0**, service item `e56e3d16fa144684bd532edbf298042c`. Observation date: **2026-11-01**. This receipt contains only *provider-generated aggregate counts and static field metadata*; no feature rows, geometries, building addresses, claims, source rasters, insurer data or source downloads were stored. Counts can change: not a durable file-content hash or an admitted source identity.

**Provider:** FEMA Historical Geospatial Damage Assessment Database, public layer 0: https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0

## Live REST metadata confirmed

| Provider field | Directly checked value |
| --- | --- |
| `serviceItemId` | `e56e3d16fa144684bd532edbf298042c` |
| Layer type | ArcGIS `Feature Layer`; `esriGeometryPoint` |
| Layer EPSG WKID | `32616` (layer's spatial reference; **not** a USGS/DEM or per-building identity) |
| `dateFieldsTimeReference` | `UTC` |
| `editingInfo.dataLastEditDate` | `2021-06-22T13:57:41.394Z` |
| `maxRecordCount` | 2,000 per normal feature query |
| `ASMT_TYPE` coded domain | `MOD` (modeled), `RS` (remote sensing), `FA` (field assessed), `OTH`, `UNK` |
| `DMG_LEVEL` coded domain | `UNK`, `DES`, `MAJ`, `MIN`, `AFF`, `NOD` |
| `DMG_TYPE` coded domain | `UNK`, `EQ`, `FI`, `FL`, `WI`, `IS`, `MUL`, `OTH` |
| `IN_DEPTH` | Nullable double **in feet**; provider warns depth may be measured or modelled |

REST `f=pjson` directly returned the above live values. The layer advertises a last data edit in **2021**, not evidence of coverage of recent catastrophes. A distinct FEMA/Data.gov catalogue product with a newer page date should **not** be silently conflated with this exact 2021 FeatureServer layer.

## Three actual aggregate-only live queries

All requests used HTTP GET with `f=json`, were read-only, returned no individual feature coordinates, and targeted `/FeatureServer/0/query`. Query parameters are given separately to avoid treating a URL string as dataset identity.

1. **Census:** `where=1=1`, `returnCountOnly=true`, `returnGeometry=false`: total **930,839** feature assessments.
2. **Assessment-method aggregation:** `where=1=1`, `groupByFieldsForStatistics=ASMT_TYPE`, `outStatistics=[{"statisticType":"count","onStatisticField":"OBJECTID","outStatisticFieldName":"count_by_method"}]`, `returnGeometry=false`: **MOD 664,294**, **RS 266,545**; `FA`, `OTH` and `UNK` **absent** from returned groups. The two positive counts sum to **930,839**. Zero `FA` is an **observed absence in this layer's public aggregate** at query time, not a global statement about all FEMA field inspections.
3. **Event/method aggregation:** `where=1=1`, `groupByFieldsForStatistics=EVENT_NAME,ASMT_TYPE`, count of `OBJECTID`; returned **20** event/method rows, sum **930,839**. This is not an independent-claim or unique-property count. The largest returned event groups include 2016 Louisiana floods (164,543 `MOD`), 2017 Hurricane Harvey (156,099 `MOD`), 2012 Hurricane Sandy (147,702 `RS`), and 2017 Hurricane Maria (69,294 `RS` plus 72,640 `MOD`).

A subsequent **event-specific read-only aggregate** used `where=EVENT_NAME = '2018 Hurricane Michael'`, `groupByFieldsForStatistics=DIS_NUMBER,EVENT_DATE,ASMT_TYPE,DMG_TYPE`, and a count of `OBJECTID`. It returned precisely three groups:

| Event label | Disaster number | Event date (UTC) | Method | Damage type | Feature assessments |
| --- | --- | --- | --- | --- | ---: |
| 2018 Hurricane Michael | `DR-4339` | 2018-10-10 | `RS` | `WI` (wind) | 1,249 |
| 2018 Hurricane Michael | `DR-4400` | 2018-10-10 | `RS` | `WI` | 917 |
| 2018 Hurricane Michael | `DR-4399` | 2018-10-10 | `RS` | `WI` | 23,682 |
| **Total** | **3 distinct disaster numbers** | | | | **25,848** |

The source-native `EVENT_DATE` is UTC epoch milliseconds `1539129600000`, equivalent to 2018-10-10. Provider `DIS_NUMBER` must be retained as part of the event key: a single event name is **not** a uniquely identified FEMA disaster cohort.

## Scientific consequence and gating decision

- **NO-GO for independent observed/field-assessed damage holdout from this layer as currently published:** `FA=0` across the entire accessible aggregate. `RS` represents remote-sensing interpretation and `MOD` is itself model output; neither is interchangeable with field-observed loss or paid claims.
- **Conditional research candidate**: `DR-4399` / `2018-10-10` / `RS` / `WI` (23,682 assessments) is an explicit *remote-sensing-only* event cohort suitable for a future, separately rights-reviewed aerial-image/roof-damage benchmark. Exact feature times, duplicate keys, actual imagery, hazard mechanism and valid footprint must still be checked. Do **not** infer damage loss ratio, policy coverage, first-floor elevation or any numeric height from this metadata.
- **NO automatic property join:** FeatureServer `OBJECTID`, the three disaster numbers, source points and insured properties are distinct identities. No geocoded building or insurer exposures were linked.
- **Do not overstate currency or external rights:** ArcGIS exposes public access, but precise source-specific reuse and model-consumer scope remain subject to admission review; dates/coverage are historical. Only aggregate metadata and provider codes entered this research document.

The existing synthetic-only code `research_runners/fema_damage_assessment_preflight_v0.py` now enforces the provider's exact assessment/damage-type code domains in addition to explicit event/date/geometry guards. This does **not** claim that locally synthetic `FA` examples exist in the real database.

## Next bounded evidence gates

1. Before any real per-feature retrieval, review rights, service freshness, query limits, stable source-version evidence and justified record/geometry retention (do not commit feature bytes).
2. If justified, audit a tiny fixed **`DR-4399` + UTC 2018-10-10** metadata-only cohort, not the whole Hurricane Michael name group; verify exact event span and `RS`/wind origin.
3. Select one real USGS S1M tile only after current coverage and source work units are confirmed. S1M post-event source/acquisition vintage must not be treated as an observed 2018 pre-event building condition or a damage record.
4. Find **truly independent measured damage** from another rights-compatible dataset before any validation/calibration of vulnerability curves; do not promote RS/MOD comparisons as independent out-of-sample validation.

**Conclusion:** The provider is live and queryable for aggregates, with a major experimental limitation proven by its own counts; no source-data admission, raw-byte acquisition or model-calibration input has occurred.
