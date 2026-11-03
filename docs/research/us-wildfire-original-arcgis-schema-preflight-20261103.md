<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# US wildfire original ArcGIS layer schema: bounded preflight 2026-11-03

**Status: native provider metadata observed; executable schema check research-only; original source dataset rows/bytes unexamined.**

The [merged 2026 wildfire crosswalk](us-wildfire-identity-audit-executable-v0.md) consumes simplified, caller-prepared small CSV projections, **not direct ArcGIS data**. This new preflight validates the **original native field types, layer numbers, EPSG:4269 CRS and point/polygon geometry** against pinned caller-supplied original-service metadata JSON. It closes a concrete source-mapping risk without claiming an actual provider-asset download.

## Publisher-original live service documentation (reviewed 2026-11-03)

| Observation | Official layer | Native field / type | Research projection |
| --- | --- | --- | --- |
| USFS FPA FOD Seventh Edition original point event record | [EDW current edition layer 0](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0) | `fod_id` / Integer | `fpa_record_id` (not ephemeral `objectid`) |
| USFS FPA FOD optional MTBS link | Same layer | `mtbs_id` / String | `mtbs_id` |
| USFS FPA FOD discovery year | Same layer | `fire_year` / SmallInteger | `fire_year` |
| MTBS 2024 burned-area **polygon** | [EDW MTBS layer 82](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/82) | `perim_id` / String | `mtbs_component_id` (*candidate only; uniqueness/nullability not yet proven*) |
| MTBS 2024 polygon event ID | Same layer | `fire_id` / String | `mtbs_id` |
| MTBS 2024 polygon event year | Same layer | `year` / SmallInteger | `fire_year` |
| MTBS 2024 polygon class | Same layer | `fire_type` / String | `event_kind` (*requires reviewed vocabulary mapping*) |

**Version identity warning:** The USFS `EDW_FireOccurrenceCurrentEdition_01` URL is a *mutable current-edition alias* currently advertising Seventh Edition `FPA_FOD_20260615`. The MTBS year-specific layer 82 is an official 2024 **subset** but its service contents can be refreshed or historically reprocessed; 2026 updates have changed MTBS historical product values. Neither URL nor layer ID is an immutable **asset** identifier. Verify original archive and output SHA-256 separately before original data or scientific model admission.

**Different MTBS layer types:** [2024 point locations layer 83](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/83) has `FIRE_ID` and `FIRE_TYPE` but does *not* advertise `YEAR` in the native point schema. `IG_DATE` is a date in the point service, whereas in the polygon service it may be an integer; never assume point/polygon native fields are interchangeable. `FIRE_NAME`, `IRWINID`, `MAP_ID` and `PERIM_ID` are not alternative replacements for the MTBS `FIRE_ID` event key.

## How to run the offline gate

Retrieve the two authoritative *metadata JSON* snapshots (do not fetch all fire features) from the exact **predefined official URLs**:

- `https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0?f=pjson`
- `https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/82?f=pjson`

Keep them outside the public repository. Record fetch UTC, HTTP status, response MIME, Content-Length, redirects, exact endpoint and SHA-256 digest in a private evidence receipt. Do not publish a full original record response.

```sh
python -m research_runners.us_wildfire_original_arcgis_metadata_v0 \
  --fpa-metadata /private/fpa-layer-0-metadata.json \
  --fpa-sha256 PINNED_SHA256_OF_EXACT_FILE \
  --mtbs-metadata /private/mtbs-layer-82-metadata.json \
  --mtbs-sha256 PINNED_SHA256_OF_EXACT_FILE
```

The runner supports two small JSON snapshots, each at most 2 MB. It strictly checks duplicate JSON and field keys, expected typed columns, source layer number/name, geometry type, and the reported spatial reference. It fails closed on any schema drift; extra provider fields remain permitted.

Passing means **only that supplied metadata are structurally compatible** with the documented research projection. It does **not** authenticate that the caller obtained the bytes from the original provider, resolve alternate field definitions in archived GPKG/SQLite, confirm uniqueness of `perim_id`, validate `FIRE_TYPE` categories, prove source rights, map real events, or approve catastrophe/insurance loss models. No data is fetched or saved into Neon.

## Next isolated gates

1. Pin provider-original archive edition and MTBS 2026 Q3 post-reprocessing product/bundle byte identity, not only live metadata; obtain official field dictionaries and typed `FIRE_TYPE` vocabulary.
2. Run a bounded **authorized** source record preflight and count null/duplicate `FOD_ID`, `MTBS_ID`, `FIRE_ID`, `PERIM_ID` without publishing identifiers or site coordinates.
3. Compare historical fire year, point-to-polygon location/date, and complex-fire multiplicity as review evidence. Never merge on same fire name, loose spatial proximity or same state/day.
4. Only after scientific and rights review, use explicit versioned transformations for CAT frequency calibration, simulated ground-up losses and NextGen financial contracts.
