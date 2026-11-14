<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Open GIS and geocoding tools: source research and OpenCatastrophe integration

**Review:** 2026-11-04. **Status:** non-admission research, no external geospatial assets or model-input approvals.  
**Canonical discovery:** [sources-open-geospatial-toolchain-20261104.json](../../landscape/sources-open-geospatial-toolchain-20261104.json); the paired Markdown is **generated**, not separately maintained.  
**Existing, overlapping work:** [GIS/geocoding foundations draft PR #1239](https://github.com/pokekarten/OpenCatastrophe-data/pull/1239), [cross-domain GIS sources draft PR #1238](https://github.com/pokekarten/OpenCatastrophe-data/pull/1238), [Overture building crosswalk draft PR #1107](https://github.com/pokekarten/OpenCatastrophe-data/pull/1107).

## Executive technical decision

Use an **offline-first, source-pinned geospatial resolution pipeline**. Do not build a proprietary global geocoder, scrape a public search API or add a second canonical building inventory to the public repository. Maintain OpenCatastrophe-data as reference/licence/provenance/transform-code authority, not a raw spatial warehouse. Persist permitted original spatial data in an authorized versioned object store and controlled PostGIS/Neon branches, separately from customer exposure and policy data. OpenCatastrophe computes peril-specific ground-up losses; NextGen owns policy, insurer, treaty, retro and capital semantics.

## Collision check and prior art

Draft **#1239 already registers** OpenAddresses, GeoNames, Who's On First, Microsoft TEMPO, OpenLandMap soil, Pelias and Photon; this note does not re-register those candidates or duplicate its generated `sources-gis-geocoding-foundations-20261104.md`. The current main has `scripts/building_id_enrichment_v0.py` for exact *same-namespace* IDs, `scripts/building_footprint_overlap_v0.py` for bounded polygon intersection diagnostics, a documented `access/geoboundaries.gbopen.json` administrative source, and existing OpenCat/NextGen synthetic handoff research. The planned ten software tool entries here are complementary workflow candidates, not ten new datasets or ten CAT models. No source/model admission and no live geocoder performance evaluation are claimed.

## Upstream evidence: primary project documents

| Component | Official evidence | License / rights boundary | Best integration decision |
| --- | --- | --- | --- |
| Pelias (already #1239) | [project](https://github.com/pelias/pelias), [supported data sources](https://github.com/pelias/documentation/blob/master/data-sources.md) | MIT engine, but OSM/ODbL, OpenAddresses source-specific, GeoNames/attribution and WOF upstream rules differ | Preferred candidate for a later **multi-source** self-hosted geocoder |
| Photon (already #1239) | [project](https://github.com/komoot/photon) | Apache-2.0 engine; demo API is limited/throttled; OSM data ODbL | Candidate autocomplete/reverse geocoding challenger, not a new address census |
| OpenAddresses (already #1239) | [source catalogue](https://github.com/openaddresses/openaddresses) | CC0 source-definition JSON does **not** relicense each provider's address records | Address reference input, item-level licensing/attribution required |
| GeoNames and WOF (already #1239) | [GeoNames export](https://www.geonames.org/export/), [WOF licenses](https://whosonfirst.org/docs/licenses/) | Independent attribute/source terms; WOF records carry source-specific lineage | Gazetteer, multilingual place crosswalk and administrative context |
| Nominatim | [software and mixed licenses](https://github.com/osm-search/Nominatim), [public API policy](https://operations.osmfoundation.org/policies/nominatim/) | Component GPL variants; OSM data ODbL. Public OSMF service: no systematic queries, no autocomplete, maximum 1 request/sec; longer bulk use restricted further | Self-hosted **benchmark**, not global public-API production dependency |
| libpostal | [project/licence](https://github.com/openvenues/libpostal) | MIT software; exact statistical model asset/lineage separately recorded | Local parsing/normalization, never proof of geolocation |
| DuckDB Spatial | [Spatial docs](https://duckdb.org/docs/stable/core_extensions/spatial/overview), [GDAL integration](https://duckdb.org/docs/stable/core_extensions/spatial/gdal) | Core MIT; inspect installed spatial and bundled driver dependency notices | Large versioned GeoParquet/COG metadata screening and offline analytics; not canonical insurance state |
| PostGIS | [official GPL FAQ](https://postgis.net/documentation/faq/gpl-license/) | GPLv2 software; normal DB operations do not alone require releasing a client app | Reuse existing separated insurance PostGIS research branch for exact geometry joins |
| H3 | [upstream](https://github.com/uber/h3) | Apache-2.0 implementation; no input data included | Coarse global screening and accumulations, never exact parcel/footprint identity |
| QGIS | [upstream](https://github.com/qgis/QGIS) | GPL-2.0-or-later and independently licensed layers/plugins | Human-adjudicated spatial QC plus scripted receipts |
| GDAL/OGR | [official licence and dependency warning](https://gdal.org/en/stable/license.html) | Generally MIT source; binaries/drivers can impose distinct terms | Batch vector/raster transforms with explicit CRS, vertical datum, scale/NoData |
| MapLibre GL JS | [upstream](https://github.com/maplibre/maplibre-gl-js) | BSD-3-Clause software; map tiles and styles have separate rights | Optional NextGen front-end to inspect permissible risk and uncertainty layers |
| PMTiles | [upstream](https://github.com/protomaps/PMTiles) | BSD-3-Clause implementations, CC0/public-domain specification; tileset retains original data rights | Versioned public **display** archive, not analytical loss input |
| GeoServer | [upstream and licence](https://github.com/geoserver/geoserver) | GPL software, protected layer/endpoint rights require review | Later only when WMS/WFS/OGC serving is necessary |

**Additional dataset authority already present:** Overture [buildings and ODbL provenance](https://docs.overturemaps.org/guides/buildings/), [licensing](https://docs.overturemaps.org/attribution/) and the repo's own [2026-10-21 GERS review](overture-2026-10-21-buildings-gers-identity-rights-boundary-20261103.md). No vendor, software engine or geocoder is itself a replacement cost, an insured location, a hazard intensity raster, or a validated treaty exposure.

## Practical architecture and provenance

1. **Acquisition:** Select *one* licensed provider snapshot/area, capture original provider URL, release, asset identifier, SHA-256, format, CRS, rights, access date and upstream source family; keep original bytes outside public Git. For official cadastral/address imports, record original address-to-building versus address-to-unit granularity.
2. **Parsing and location candidates:** Preserve exact raw input in the authorized private runtime; normalize with version-pinned libpostal only for lookup. Obtain forward candidates via locally controlled Pelias and optionally self-hosted Nominatim/Photon; log data-source family, source-object ID, provider/import version, returned point precision and rank, but never pretend a geocoder confidence number is a calibrated building-match probability.
3. **Authoritative geometry:** Match address point to admitted building footprint first when available; evaluate `ST_Covers` / point-in-polygon and proximity only with documented CRS and address-placement semantics. Then compare polygons through existing Shapely/STRtree IoU diagnostics; quarantine units/parcel IDs, overlapping alternatives, split/merge, demolished/added buildings and possible roofprint-versus-footprint differences. Verify Overture GERS membership separately, not by UUID shape.
4. **Geography and hazard:** Assign official boundary vintage with existing geoBoundaries and local registers. Use exact raster interpolation/cell area/depth units and geodetic/vertical references for hazard overlays. Use H3 for acceleration/aggregates only; it must never replace point/polygon proof or incorrectly spread losses to all buildings in a cell.
5. **Consumers:** OpenCatastrophe receives independently admitted, hashed asset and peril geometry for ground-up calculations; NextGen receives distinct insurance contracts and terms plus **shared physical event/world IDs**. Multi-peril overlap must not double count per-asset combined ground-up; a map tile never enters an actuarial simulation.

### Suggested versioned crosswalk diagnostic contract

The **prospective, private-runtime-only** candidate row should carry:
`source_record_id, source_object_id, source_family, source_release, original_asset_sha256, geometry_crs, geometry_sha256, object_kind (address/parcel/building/part/unit), address_parser_version, geocoder_engine_version, geocoder_index_source_snapshot, candidate_point_method, point_precision, matched_building_source_id, matched_building_id, candidate_count, polygon_iou, distance_m, temporal_overlap, match_status, uncertainty_reason, rights_scope`.

These are **proposed fields**, not a deployed schema or mandate to store address text in public Git. A successful join must not silently create a new insured exposure unit, TIV or commercial-use entitlement.

## Bounded falsifiable pilot

**Region:** Luxembourg, with one exact licensed municipal/cadastral footprint version and independently pinned official address points; only use demonstrably shareable nonpersonal references or wholly synthetic fixtures while rights are unresolved. Compare Pelias vs self-hosted Nominatim/Photon against **the same input snapshot**, not distinct OSM/OA indexes, so software effects are separable from source effects. Pilot design:

- **Truth set:** 20–50 independently checked public/non-sensitive address-point-to-building cases, including high-rise units, missing house number, rural farms, building parts, multi-address buildings and demolished/new footprints. If authentic addresses cannot be redistributed, store only aggregate quality metrics and hashes here.
- **Metrics:** candidate recall@1/@3, median/p95 positional error (metres), unique building match rate, false building matches, null/ambiguous rate, urban/rural and old/new stratification, source-family dependence, runtime and memory. Holdout cases selected independently of thresholds and parser tuning.
- **Failure tests:** coordinate axis swap, inconsistent EPSG, wrong raster NoData, point on polygon boundary, 1-to-many / many-to-1, shared OSM–Overture lineage mislabelled independent, data from a later time than the historic hazard event, mixed building/unit IDs, duplicated source object IDs, and ODbL-unsupported export.
- **Acceptance:** inspect all false matches; accept a mapping only under a predeclared error budget and with separately approved data rights. Unknown rights or ambiguous candidates remain `not_admitted`. Report sampled coverage and error, never claim world completeness from one country.

## Execution order and collision control

**P0:** Merge/review existing #1239 without duplicating its seven candidates. Compare tool binaries and official license/source pages above.  
**P1:** Test an offline libpostal string parser plus candidate lookup with wholly synthetic addresses; no public OSMF Nominatim API.  
**P2:** Extend existing `building_footprint_overlap_v0.py` only after a false-match benchmark, then test one licensed original Luxembourg building/address asset against Overture GERS and official cadastral geometry under a bounded exact-asset receipt. Avoid editing files already owned by #1107.  
**P3:** Use DuckDB Spatial in acquisition/preflight and existing PostGIS for versioned spatial relation storage. Add H3 accumulation and MapLibre/PMTiles display after numerical joins are independently validated.  
**P4:** Contract-test the OpenCat → NextGen handoff with distinct physical assets, peril components, combined losses and policy terms; no elevation or geocoder output should manufacture financial assumptions.

## Evidence and implementation status

Verified: original project documentation and software/data license boundaries from references above; main repository workflows and existing Overture/identity work; open #1239/#1238/#1107 collision surfaces. The accompanying new source shard records **ten workflow/tool candidates** with `rights_review_status=not_reviewed`, `scientific_review_status=not_reviewed`, `admission_status=not_admitted` even where a software license has been identified, because this metadata is not an asset rights/admission approval.

Not verified or performed: production self-hosted installs, live original-address/footprint downloads, empirical matching accuracy, source-file redistribution rights, repository-wide GitHub CI/exact-head checks, Neon writes, real insurer portfolios, calibrated CAT/NextGen simulations.
