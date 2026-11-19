<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CAL FIRE FRAP firep25_1: original ArcGIS metadata preflight

**Research-only, 2026-11-01.** This does not admit original features, clear
API terms, fetch data or produce model-ready observations. The associated
source access contract
`access/us.calfire.frap.historical-fire-perimeters.firep25-1.json`
remains `documented_only`, with no network probe authorized.

## Why exact original layer metadata matters

CAL FIRE's authoritative [2026 historical perimeter product page](https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/fire-perimeters)
describes April 2026 edition `firep25_1` through 2025, with changed and removed
fire records and newly supplied Global IDs. The authoritative published
[FRAP current ArcGIS FeatureServer layer 0](https://services.arcgis.com/V6ZHFr6zdgNZuVG0/ArcGIS/rest/services/California_Fire_Perimeters/FeatureServer/0)
is named `California_Fire_Perimeters__all_`, geometry type
`esriGeometryPolygon`, with `OBJECTID` / `GlobalID`,
`YEAR_ = esriFieldTypeSmallInteger`, `INC_NUM` / `UNIT_ID` /
`IRWINID` text and `ALARM_DATE` / `CONT_DATE` ArcGIS date fields.
Its published *view* is Web Mercator (`wkid 102100`, equivalent
`latestWkid 3857`). Other historical or mirrored CAL FIRE layers expose
different schema and CRS conventions (for example `YEAR_` as text or
native-style EPSG 3310), so product names alone do not establish source
byte or shape compatibility.

The official [June 2023 FRAP Fire History Data Dictionary](https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/fire-perimeters)
describes `YEAR_` as Text and documents `INC_NUM` as a locally assigned
emergency-command-center identifier, whereas the *current specific* ArcGIS
layer uses SmallInteger for year. The dictionary and the 2026 ArcGIS
metadata refer to different representations/vintages; do not silently
cast and claim interchangeability. `IRWINID` is a fire identifier;
the new `GlobalID` is a data-record tracking key, not guaranteed
to be an equivalent fire-event identifier.

## Minimal fail-closed proof

`scripts/preflight_calfire_frap_layer_metadata_v0.py` accepts a saved
**original, independently authorized** ArcGIS layer 0 JSON metadata response:

```sh
python scripts/preflight_calfire_frap_layer_metadata_v0.py --input /trusted/local/frap_layer0_metadata.json
```

No source retrieval is implemented. This preflight checks layer `id`,
exact name and geometry, object/global ID field *case*, original
event-time field names, fixed field types (especially numeric `YEAR_`),
Web Mercator view CRS, UTF-8 JSON uniqueness, and 512-KiB maximum.
It rejects feature arrays, geometry payloads, duplicated fields, malformed
date metadata and mismatched layer identities. A successful receipt contains
only the input SHA-256, size, field count and selected field/type identities;
it never publishes feature rows, polygons, addresses, loss amounts or source
raw bytes.

The receipt flags `provider_revision_verified=false`,
`event_to_dins_identity_proven=false`,
`external_source_use_authorized=false` and
`model_data_admitted=false`. It cannot verify whether downloaded metadata
corresponds to frozen `firep25_1` original data bytes; the live service is
mutable. A SHA-256 of saved metadata is not a freeze of source feature
geometry, a release-specific asset or an event crosswalk.

The 20 deterministic synthetic tests in
`tests/test_preflight_calfire_frap_layer_metadata_v0.py` cover correct
metadata-only output, historical text-year drift, old EPSG 3310 views,
temporal field identity, duplicate keys, unexpected geometry and
feature payload rejection.

## Next independent gates

Review the exact feature service terms, source file release and attribution;
freeze original provider byte receipts outside Git; compare feature-level
incident IDs using independently authorized, privacy-safe summaries;
resolve missing and duplicate perimeters. Any DINS building-inspection join
must preserve missingness and distinguish `GlobalID` record identity from
`IRWINID` event identity, with no use of actual personal addresses or policy
records under this contract.
