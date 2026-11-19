<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT BD-Adresses: original publisher metadata and geocoding pilot boundary

**Review:** 2026-11-04. **Candidate:** `lu.act.bd-adresses.georeferenced-address-points.2026`. **Status:** original-publisher documentation checked, **not** data-byte verified, not admitted.

## Original source identities

- Official data portal: https://data.public.lu/en/datasets/adresses-georeferencees-bd-adresses/
- Official ACT explanation: https://act.public.lu/content/act/fr/parcelles-residences/registre-adresses.html
- **GeoJSON resource** (stable portal resource ID `7b58cf20-cbb0-4970-83f7-53a277f691b8`): https://data.public.lu/en/datasets/r/7b58cf20-cbb0-4970-83f7-53a277f691b8
- **CSV resource** (stable portal resource ID `5cadc5b8-6a7d-4283-87bc-f9e58dd771f7`): https://data.public.lu/en/datasets/r/5cadc5b8-6a7d-4283-87bc-f9e58dd771f7
- **Shapefile ZIP** (stable resource ID `2a17ddc2-b961-45ce-83a2-be751d3af9b8`): https://data.public.lu/en/datasets/r/2a17ddc2-b961-45ce-83a2-be751d3af9b8
- Underlying official **CACLR** national place/street/house-number register: https://data.public.lu/en/datasets/registre-national-des-localites-et-des-rues/

This ACT BD-Adresses resource is **not** the previously registered CACLR textual registry. CACLR identifies official addresses **without coordinates**, whereas BD-Adresses enriches a subset with points. Both are the same official provider's lineage and are **not independent geographic observations**. The official INSPIRE address product can be another presentation of ACT cadastral data; do not count it as an independent holdout.

## Rights, timing and exact-file semantics

- The official BD-Adresses **dataset page advertises CC0**. This is evidence for a *candidate* rights review, not a completed per-file/revision approval for OpenCatastrophe redistribution, commercial model input or blending with other providers.
- Provider lists GeoJSON points, CSV (LUREF X/Y plus WGS84 latitude/longitude) and a Shapefile in LUREF `EPSG:2169`. Verify actual GeoJSON CRS and column axis semantics from exact bytes and independent control points before comparing to `EPSG:4326`.
- The publisher's portal has been indexed with **different last-update dates** (2026-08-10 for a cached page/asset snapshot and newer 2026-10 listings elsewhere). Never silently use a generic `latest` filename: fix exact resource URL, observed UTC retrieval timestamp, size, publisher-supplied MD5, original computed SHA-256 and source-vintage before any use.
- A community-enriched `luxembourg-addresses.csv` listed separately on the same page is a **third-party OSM derivative (ODbL)**, not an ACT CC0 file. Do not inherit the main dataset license for it or use that derivative as independent truth against OSM/Pelias/Photon.

## Scientific and entity-matching constraints

ACT states that address-point location may be placed manually, or synthesized from the parcel centroid or largest-building centroid. The point is **not** guaranteed to be the physical building entrance. Multiple addresses can have identical points; many CACLR addresses have no georeferenced point. Cadastral/geodetic offsets versus LUREF are disclosed by the publisher.

Consequently:
1. Preserve original ACT address source identifiers and geometric placement-method information where available; never mistake address ID, parcel ID and footprint/building ID for the same key.
2. The existing `ACT2023v2`, EUBUCCO government-sourced polygons, national cadastral footprint and BD-Adresses may share upstream geometry. A small address-point distance is **not independent validation** of these polygons.
3. Address-to-footprint matching must explicitly distinguish `building`, `parcel`, `building_part`, `unit`, `unknown`, and one-to-many / many-to-one. A house number is not one insured exposure; a building centroid is not the policy risk address.
4. Do not promote these coordinates to property value/TIV, vulnerability, policy inclusion or physical asset identity without independent original-source and scientific review.

## Access route caution

The official portal describes historic REST `/geocode/search` and `/geocode/reverse` endpoints, with results containing a WGS84 `geomlonlat`, LUREF `geom`, address IDs and coarse-to-house-number `accuracy` codes. However the portal marks one endpoint *unavailable*, and the third-party/mapping `Geoportal V4 API` requires ACT access authorization for domain use. These older descriptions are **not** proof of live anonymous API availability. Prefer the version-pinned public CSV/GeoJSON metadata for pilot planning until a minimal, authorized provider canary is independently proven.

The independent Luxembourg OGC API at https://features.geoportail.lu/collections?f=json is publicly discoverable and lists numerous layers, but a BD-Adresses feature collection was **not** identified in the reviewed metadata. Do not invent a working endpoint by assuming one exists.

## Next falsifiable experiment

Use the existing `scripts/geocode_evidence_quality_v0.py` with 20–50 strictly bounded cases. First freeze one licensed, actually retrieved ACT address resource and an **independently sourced** reference for positional error; a same-ACT footprint is a linkage challenge, not a truth holdout. Compare Pelias and Photon on pinned source snapshots; count no-result, ambiguous, coarse and known shared-lineage outcomes, and validate coordinate transformations via two independent LUREF/WGS84 control points. Store no public household address list or raw source bytes. Record a provider receipt/hashes before any promotion. The current PR does **not** perform this experiment.

## Executed live original-publisher metadata inspection (2026-11-04)

The actual uData **resource API** was fetched individually, without requesting any original address CSV/GeoJSON/ZIP bytes. This exposed a **newer 2026-11-02 release** than the 2026-10-12 version still visible in a cached dataset page snapshot. The API serializes checksum as `checksum: {type: "md5", value: "..."}`, names the asset with `title`, and supplies `filesize`, `last_modified` and exact versioned `url`. The earlier 2026-10-12 MD5 values must **not** be applied to the November bytes.

| Fixed original resource | Versioned path suffix | Publisher MD5 (not original SHA-256) | API filesize (bytes) | Last modified (UTC) |
| --- | --- | --- | ---: | --- |
| `7b58cf20-cbb0-4970-83f7-53a277f691b8` GeoJSON | `20261102-033136/addresses.geojson` | `16d7e4e2ccf735fea7ca0db26378281b` | 80,901,702 | 2026-11-02 03:31:37 |
| `5cadc5b8-6a7d-4283-87bc-f9e58dd771f7` CSV | `20261102-033122/addresses.csv` | `946114c1a24b49471b580bc225e4cb25` | 28,209,815 | 2026-11-02 03:31:23 |
| `2a17ddc2-b961-45ce-83a2-be751d3af9b8` SHP ZIP | `20261102-033150/addresses-shp.zip` | `3b1bb33c8c1a4fc2bbd95d5fb6317d29` | 19,700,240 | 2026-11-02 03:31:51 |

Official resource JSON endpoint template (read-only):
`https://data.public.lu/api/1/datasets/56fd16fa855e9b6a1088f552/resources/{fixed_resource_uuid}/`.

**Implementation:** `scripts/probe_lu_bd_adresses_metadata_v0.py` fixes those exact three resource IDs, paths, MD5s and file-size bands. By default it performs **no** network request; `--live` explicitly permits three bounded metadata JSON GETs, blocks redirects, rejects filename/origin/version/checksum drift and never fetches the linked source files. The script's offline deterministic test suite has 11 synthetic tests; run `python -m unittest discover -s tests -p 'test_probe_lu_bd_adresses_metadata_v0.py' -v`. A separate live run **from the project's executable environment** remains required: the live API was inspected through a browser-independent public web retrieval, not the newly committed Python probe.

No actual source-file SHA-256, row count, schema validation, CRS numeric transform, record privacy check, license signoff, or model input approval has been established. The `extras["check:available"]` in uData's resource metadata is historical availability monitoring, **not** proof of a fresh original-file download. When publisher uploads a new version, the frozen canary should deliberately fail until the new release receives its own review.
