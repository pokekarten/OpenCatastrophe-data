<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NRW LoD2 OGC API metadata canary (2026-11-08)

## Source and independent boundary

- Official provider landing page: https://ogc-api.nrw.de/3dg/v1
- Exact collection page: https://ogc-api.nrw.de/3dg/v1/collections/building
- Official AdV service metadata (2026-09-08): https://www.distributions.informationgrid.eu/trefferanzeige?docuuid=bde30228-a718-45a8-9518-1e17e47c0187
- GovData source catalogue: https://data.gov.de/suche/daten/3d-gebaudemodell-nw-lod28b9df
- Canonical non-admitted candidate: `landscape/sources-nrw-lod2-ogcapi-20261108.json`

The publicly accessible provider HTML collection page was inspected on 2026-11-08:
- Collection name: `building` (display title `Gebäude`).
- Provider-advertised feature count: **11,605,500**. This is not an independently downloaded/verified feature count.
- Collection metadata advertises a temporal extent **2025-01-30 to 2025-03-20**.
- The collection presents storage CRS **EPSG:5555** and lists other supported reference systems including EPSG:25832 and EPSG:4326. This is **not evidence** that a chosen response's coordinates use EPSG:4326 by default.
- Provider landing page and collection page both refer to `Datenlizenz Deutschland – Zero – Version 2.0`.
- Separately, the official AdV metadata names ALS/DGM1 vintage 2019–2025 and ALKIS footprint reference 2025-07-01. The mismatched temporal concepts are **not resolved**: publication/valid-time fields, source vintages and individual object timestamps must not be combined or silently treated as one consistent `as_of` date.

None of these observations identifies insured assets, confirms 11.6 million usable exposure buildings, proves a historic event-time building state, or validates roof material, year built, physical occupancy, replacement cost or actual R+V policyholder location.

## Original provider JSON observation (2026-11-08)

A separate read-only web scrape of the **fixed official collection JSON URL** returned
`application/json` with **3,707 original response-body bytes** and SHA-256
`48279601eb25b24343ad809586bb802295d47a6e4983d0e105c73232b296fd88`.
This is an **external HTTP fetch**, not a run of `probe_nrw_lod2_api_metadata_v0.py --live`;
the Python command's end-to-end HTTP receipt is still outstanding.

The parsed original JSON fields (metadata only) were:

| Field | Observed value |
| --- | --- |
| `id` | `building` |
| `collectionType` / `itemType` | `3d-container` / `feature` |
| `itemCount` | `11605500` (provider-reported, not independently counted) |
| `storageCrs` | `http://www.opengis.net/def/crs/EPSG/0/5555` |
| Spatial extent CRS | `http://www.opengis.net/def/crs/OGC/0/CRS84h` |
| Spatial bounding-box dimensionality | Six ordinates: 3D lon, lat and height |
| `extent.temporal.interval` | `2025-01-30T00:00:00Z` to `2025-03-20T00:00:00Z` |
| Advertised `items` representations | `application/gml+xml`, `application/city+json`, `application/city+json-seq`, `model/gltf-binary`, `text/html` |
| Advertised `items` GeoJSON representation | None in this metadata snapshot |

The new checker deliberately rejects changed `collectionType`, `itemType`, CRS,
non-3D spatial envelopes or loss of both CityJSON and CityGML support. It reports
only reviewed metadata, checksums and booleans. An absent GeoJSON `items` link is
**not proof the service can never provide GeoJSON**, but it prevents assuming one
without an explicit format probe. The 3D bounding-box CRS (CRS84h) is different
from storage CRS (EPSG:5555): do not use one to interpret the other's coordinates.

The downloaded JSON body is **not in Git**. A tool-mediated metadata fetch does
not validate feature availability, completeness, geometry correctness, licensing
of API automation or insurance-model use.

## Official queryables schema discovery (2026-11-08; metadata only)

A separate read-only original-JSON metadata fetch found the provider's
[queryables schema](https://ogc-api.nrw.de/3dg/v1/collections/building/queryables?f=json),
content type `application/schema+json` (JSON Schema draft 2020-12).
It advertises **15 queryable property names**, but no building features were downloaded:

| Field(s) | Provider schema type | CAT exposure interpretation / caveat |
| --- | --- | --- |
| `gml_id`, `name` | string | Technical record identifier and optional building name, **not** insured account or policy ID |
| `bbox` | geometry-polygon | Indexed spatial envelope, **not** verified roof footprint or a policy location |
| `measuredHeight` | number | Building height difference in meters between provider-defined high and low reference points; not number of floors |
| `storeysAboveGround` | integer | Above-ground storey count; availability/accuracy per feature untested |
| `roofType` | string | Encoded AdV roof-form class, with [official value list](https://repository.gdi-de.org/schemas/adv/citygml/Codelisten/RoofTypeTypeAdV.xml); **not** roof covering/material or damage resistance |
| `creationDate` | date string | Record creation date; **not** construction year without independent definition and crosswalk |
| `function` | string | Encoded AdV building-function class via [official value list](https://repository.gdi-de.org/schemas/adv/citygml/Codelisten/BuildingFunctionTypeAdV.xml); not guaranteed insurance occupancy |
| `address.ThoroughfareName`, `address.ThoroughfareNumber`, `address.PostalCode`, `address.LocalityName` | arrays | Public building-address fields; not source of insurer holdings, not necessary for a first synthetic location experiment |
| `consistsOfBuildingPart.measuredHeight`, `consistsOfBuildingPart.storeysAboveGround`, `consistsOfBuildingPart.roofType` | arrays | Building-part properties; multiple values do **not** imply a uniform whole-building attribute |

A separate original [sortables schema](https://ogc-api.nrw.de/3dg/v1/collections/building/sortables?f=json)
has `additionalProperties=false` and **does not list named sortable fields**:
do not build deterministic pagination or deduplication on an assumed provider sort key.

**Scientific outcome:** a small legally reviewed pilot may test roof-form and building-height *attribute coverage* and crosswalks, separately from structural building identity, construction age, roof material, replacement value, insurer geography and historical event-time exposures. Schema availability is not proof of field completeness, distribution, physical accuracy or scientific model readiness.

## Bounded executable metadata proof

Run offline synthetic regression tests, requiring no network or credentials:

```sh
python -m unittest discover -s tests -p test_probe_nrw_lod2_api_metadata_v0.py -v
```

The optional *single* live metadata probe, for a developer with authorized network access:

```sh
python scripts/probe_nrw_lod2_api_metadata_v0.py --live
```

It requests only the fixed HTTPS `/3dg/v1/collections/building?f=json` collection metadata URL, accepts HTTP 200 JSON, rejects redirects and non-JSON/feature payloads, and caps the response at 131,072 bytes. It reports only metadata byte SHA-256, collection identity, optional advertised count, presence of declared extent, status flags and timestamp. Provider JSON bytes, addresses, building IDs, geometries, coordinates and feature rows are never included in the receipt or committed.

**Execution boundary:** the initial six test methods passed in a local Linux Python environment with synthetic fixtures; later additional CRS/3D negative regression cases were added on a follow-up branch and require exact-head CI confirmation. The actual JSON metadata URL **has not yet been executed by the Python probe**, although the original JSON metadata response was independently obtained and examined through a read-only web scrape as documented above. Neither route grants rights, data admission, model validation or commercial use.

## Next causally required gates

1. Run this exact metadata probe against the original collection JSON; record HTTP/media-type status and checksum only. On errors preserve the failure rather than adding unreviewed fallback endpoints.
2. Review exact live OGC API terms/request constraints and exact product/vintage licence, then separately authorize *one bounded* spatial sample, if needed.
3. For any approved original sample, preserve source-supplied CRS, feature ID, source timestamps and independent raw hashes outside Git. Do not treat `numberMatched` from metadata as extracted row completeness.
4. Prove synthetic locations ↔ geometry joins using known source geometry/CRS and event-date support, then map building taxonomy, value assumptions and wind peril/vulnerability with independent held-out checks.
5. Only after a complete event/period/sample world and legitimate financial assumptions, consider Oasis gross/insured/net and OEP/AEP.

No source-data bytes or confidential insurance inputs belong in this repository.
