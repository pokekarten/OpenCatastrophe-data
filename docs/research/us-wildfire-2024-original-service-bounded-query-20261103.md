<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# US wildfire 2024 original service: bounded read-only field/value receipt (2026-11-03)

**Observed original-service read-only responses; research-only.** No source dataset was downloaded, no complete provider asset SHA-256 was pinned, no private database was written, and no original event identifiers, coordinates or records are reproduced here. Queries used the publisher's publicly documented ArcGIS REST services via a web extraction client; response bytes were not retained or hashed as an original asset receipt. Response record counts are deliberately small **sample counts, not population statistics**.

## Provider endpoints and observed replies

1. [FPA FOD 2024 layer](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/2024), via REST `/query` with `where=1=1`, `outFields=fod_id,mtbs_id,fire_year`, `returnGeometry=false`, `resultRecordCount=3`, `f=pjson`: **3 features**, requested field types integer/string/small-integer, `exceededTransferLimit=true`.
2. [MTBS 2024 burned-area boundaries layer 82](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/82), via `/query` with `where=1=1`, `outFields=fire_id,year,fire_type,perim_id`, `returnGeometry=false`, `resultRecordCount=3`: **3 features**, field types string/small-integer/string/string, `exceededTransferLimit=true`.
3. Same FPA FOD service, layer **0**, selecting `mtbs_id IS NOT NULL AND fire_year = 2024` and at most **10 rows**: **10 rows returned**; all 10 have nonempty MTBS IDs, **10 distinct MTBS IDs**, all had `fire_year=2024`, `exceededTransferLimit=true`. This query actively filters to a non-null subset; **10/10 does not imply a 100% national match rate**.
4. Same MTBS 2024 layer **82**, one equality lookup `fire_id = <one original FPA-supplied MTBS_ID>` (the actual ID is not repeated here), up to 5 rows: **one matching boundary**, `year=2024`, `fire_type=Wildfire`, but **`perim_id` is null**. This is an *observed service ID-match in a single case*, not validation of all events or a contractual occurrence.
5. Same MTBS 2024 layer **82**, `where=1=1`, `outFields=fire_id,year,fire_type,perim_id,map_id`, `returnGeometry=false`, `resultRecordCount=25`: **25 rows**, `exceededTransferLimit=true`; **25 nonempty `fire_id`**, **25 distinct `fire_id` within sample**; **2 nonempty `perim_id`**, **25 nonempty `map_id`** with 25 distinct values **within sample**; all row years 2024. Both `Wildfire` and `Prescribed Fire` occur in sampled `fire_type`.

## Correction to the original schema import assumptions

- **Confirmed defect:** `PERIM_ID` is advertised as a String field in the original MTBS 2024 polygon schema but is **not reliably populated**. It must **not** become the mandatory `mtbs_component_id` of the existing offline crosswalk. The safe metadata map explicitly sets this conversion to `null`.
- `MAP_ID` was nonempty and distinct in these 25 rows but is **not yet documented as globally unique, stable across MTBS releases or appropriate for distinct multi-polygon event components**; do not promote it automatically either.
- **Verified narrow original-ID bridge:** The FPA `MTBS_ID` and MTBS `FIRE_ID` match for one selected 2024 record, not proof of a one-to-one population join. Keep FPA `FOD_ID` separately as the record primary identifier.
- `FIRE_TYPE` has original textual values `Wildfire` and `Prescribed Fire`, which cannot be copied verbatim into the offline research runner's controlled `wildfire`/`prescribed`/`unknown` without an explicit, versioned and audited vocabulary transform. Map absent, changed or unrecognized values to **unknown**, never to wildfire by default.
- These live ArcGIS endpoints can change. Without original archive bytes, published source release, original metadata/record snapshot hashes and a licensed bounded sample pipeline, this receipt proves only that the APIs responded at the time of access and the sample fields existed.

## Next research gates

1. Seek publisher meaning of `MAP_ID`, `PERIM_ID`, `FIRE_ID` and their null/uniqueness guarantees from an original field dictionary; include record-vs-polygon fan-out from a bounded 2024 sample after access rights are reviewed.
2. Build a deterministic **private** source-to-research transformation, with an externally pinned original byte receipt and explicit `fire_type` dictionary. Reject missing component identity rather than selecting a transient GIS `OBJECTID`.
3. Distinguish pilot-year sample matching from population event-frequency statistics; sample selection deliberately biases toward populated `MTBS_ID`.
4. Keep rights, scientific fitness, source data admission, hazard-to-vulnerability mapping, loss and policy calculations blocked pending independent evidence.
