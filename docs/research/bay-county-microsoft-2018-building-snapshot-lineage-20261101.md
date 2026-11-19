<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hurricane Michael: original Bay County building footprints and pinned Microsoft pre-event release

**Investigated 2026-11-01.** No raw original property features, building geometries, identities, image bytes, source ZIP files or sensitive owner/address data were downloaded or committed. This note is a **source-vintage / licensing audit, not an approved event-era building stock**.

## 1. Official live Bay County building polygons — actual geometry source, but not historical

Original service: https://gis.baycountyfl.gov/arcgis/rest/services/Hosted/FC_BuildingFootprints/FeatureServer/22

This is the county's public **Building Footprints** layer, original `serviceItemId=6b68c1a8d4354fc3b6f38cf41f46b754`, `esriGeometryPolygon`, native projected Florida State Plane `latestWkid=2238`. Its source-native schema includes `objectid`, `roof_type`, `bldgheight`, `numstories`, `lastupdate`, `create_date`; the geometry represents building footprints rather than parcel boundary polygons. The service is **not versioned** and declares `supportsQueryWithHistoricMoment=false`. Thus no official historical time-travel layer was established for October 2018.

Actual original public `/query` responses, each `returnCountOnly=true`, `returnGeometry=false`, `f=json`, no `outFields` or individual geometry:

| Source-native provider query | Original count (2026-11-01) |
| --- | ---: |
| `where=1=1` | **117,646** building footprint polygon features |
| `lastupdate IS NULL` | **117,500** |
| `lastupdate IS NOT NULL` | **146** |
| `lastupdate < timestamp '2018-10-10 00:00:00'` | **146** |
| `create_date < timestamp '2018-10-10 00:00:00'` | **0** |

The counts reconcile: 117,500 + 146 = **117,646**. In particular, **99.88%** of source records lack `lastupdate`; the 146 older timestamps may refer to edit status or a reused field, not evidence of intact 2018 building structures. The zero source `create_date` features before the hurricane **does not prove** those buildings were newly constructed after the storm; it may reflect later service migration/re-import. Database record creation, actual building construction, flight imagery acquisition, geometry digitization and edit dates are different events.

This current county geometry family is a strong **technical building schema** source and can support future analysis with proper provenance; at present it is **NOT an immutable pre-event source**. No original individual roof, date attribute, address or footprint coordinate was examined. Rights and export limits have not been approved.

## 2. Microsoft: exact pre-storm GitHub **published source**, uncertain underlying aerial imagery age

Microsoft announced its roughly 125-million-US-building computer vision dataset on **2018-06-28**, publicly archived in [the contemporary OSM community announcement](https://lists.openstreetmap.org/pipermail/talk-us/2018-June/018653.html). The *original GitHub public repository* `Microsoft/USBuildingFootprints` has a verified commit **`c9fb49b5f7475102b2923ae2c7fc455412c7f0e8`**, authored **2018-10-09 21:48:57 UTC**, before the hurricane's October 10 landfall.

The [exact README at this historical commit](https://github.com/microsoft/USBuildingFootprints/blob/c9fb49b5f7475102b2923ae2c7fc455412c7f0e8/README.md) lists a **Florida V1.1** downloadable asset:
`https://usbuildingdata.blob.core.windows.net/usbuildings-v1-1/Florida.zip`,
and declares **6,903,772** computer-generated statewide building footprint geometries. This is a pinned original publisher claim, **not a county subset, nor a successful original source ZIP download**. One bounded original historical ZIP byte-range request failed with `WEBSITE_ACCESS_ERROR`; no GeoJSON, raw geometry, archive Content-Length, SHA-256 or exact asset object identity was verified.

**Temporal trap:** Microsoft's own original 2018 README says the footprint dates depend on the **multi-vintage Bing imagery composite**, and it cannot provide an exact original photo year for each local building. It is reasonable to call this a building detection **catalogue released before Hurricane Michael**, but **not** to call its individual building outlines dated 2018-10-09 ground truth without source imagery validation. Newer Microsoft V2 ZIPs, updated GeoJSON, or 2025-plus state layers are different vintages and cannot replace this 2018 archive by name.

**Source-specific rights conflict:** the same pinned historic README states **Open Data Commons Open Database License (ODbL)**, while the historical GitHub `LICENSE` text starts **Creative Commons Attribution 4.0 International**. Neither ambiguity should be silently resolved by choosing the more permissive interpretation; this research keeps **commercial redistribution and model training NO-GO** pending source-owner/rights clarification and exact archive identification. The archived repository's `LICENSE` may govern a different content scope than the README data; the existence of two declarations alone does not establish a legal contradiction in granted rights.

## 3. Original source-scoped reproducible admission contract

`research_runners/bay_microsoft_2018_building_vintage_gate_v0.py` exposes exactly two **pure offline validators**:

- `audit_bay_current_footprints()`: exact county source ID, polygon/CRS/roof fields, not-versioned flags and the five count-only receipts. It rejects missing dates, unexpected feature fields, nonconservative count arithmetic or fake historical service support.
- `audit_microsoft_2018_original_readme()`: exact original pre-hurricane GitHub commit and original Florida V1.1 URL/count, both historical rights declarations, and fails closed if caller asserts ZIP bytes or individual photo timestamps were verified.

`tests/test_bay_microsoft_2018_building_vintage_gate_v0.py` tests the source API contract and failures using only **synthetic** projections and original count fixtures, not downloaded source geometries. The original public source reads above support independent authenticity, but **offline tests do not authenticate server responses**.

**Scientific decision:** Bay County's current building polygons and Microsoft's 2018-published footprints are both **non-admitted research candidates**. Neither proves unique pre-hurricane building identities for the seven FEMA `RS/WI` points challenged by the NOAA alpha-mask test, and neither permits damage-curve calibration or synthetic insurer exposure as an admitted historical source. The immediate next gates are lawful original Microsoft Florida V1.1 archive acquisition/sha256 and resolution of its data reuse rights; separately, an authoritative Bay County archived geometry layer with an acquisition date before 2018-10-10 or documented source aerial image vintage.
