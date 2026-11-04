<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg official ACT address-to-building spatial candidate challenge (2026-11-04)

**Research only: source bytes independently pinned; no address/building identity, rights/science admission or insurance exposure.**

## Original data receipts and fixed same-window study

**ACT BD-Adresses 2026-11-02** official CSV: https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/20261102-033122/addresses.csv
28,209,815 bytes, 179,768 original address rows, computed full SHA-256 f163ed856200eedd8b501da2d7787e01ee373be1a55a4d79abcf57c96982a99c. Provider MD5 and 13-field original schema verified in merged PR #1260.

**ACT BD-L-GeoBase Buildings 2026-10-01** official ZIP: https://download.data.public.lu/resources/bd-l-geobase/20261001-010523/buildings-20261001.zip
Original ZIP SHA-256 6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3, extracted GeoPackage SHA-256 ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676, full original 230,353 building object rows. The existing exact-source ZIP CRC/geometry-layer/identifier QA is reused.

**Fixed geographic experiment**: the same 100 x 100 metre Luxembourg city EPSG:3035 square around the previously published 6.1319 E, 49.6116 N reference as previous triple-original building comparisons, 50 metre half-width. Previous source proof found exactly 107 GeoBase building polygons in that window; no sample window is selected from a result-driven search. The November address data are **32 days newer** than the October buildings.

## Bounded executable diagnostic

- research_runners/lu_act_address_geobase_original_window_v0.py: requires the exact original CSV hash, full original GeoBase ZIP/GPKG receipts and 13-field CSV layout. Reuses the existing RTree spatial window sampler for the single official GeoBase Buildings layer.
- Select address points by projected EPSG4326 -> EPSG3035 inside the frozen same-area window. Compare each official EPSG2169 east/north point with original EPSG2169 GeoBase polygon in metric coordinates. The two coordinate variants in the address data were previously checked for internal transform agreement.
- Classes are one containing polygon candidate, multiple containing polygons, interior plus boundary, boundary-only, or no polygon. Only aggregate nearest-distance metrics for points outside all buildings and counts of ambiguous many-address-per-polygon candidate relationships are exposed.
- Original CSV, GeoPackage, polygon sample and individual matches exist only in the isolated runner filesystem and are deleted after execution. A candidate is **not** a building, insurable asset, household, policy, TIV, financial loss or hazard measure.
- Exact original SHA-256 for both data products, predeclared 107 polygon count, strict schema, positive valid polygons, original RTree, 400-per-source local cap and full classification conservation all fail closed on drift.
- Both source products originate from ACT. Common origin prevents claiming independent building location ground truth; differing observation dates also prevent assertions of unchanged asset stock.

## Reproduction and scientific limits

Dedicated original-source GitHub workflow in .github/workflows/luxembourg-act-address-geobase-original-window.yml is scoped to the three changed code/CI paths, uses pinned pyproj 3.7.2 and Shapely 2.1.2, fetches only the two frozen source objects and publishes no original asset or source geometry artifact. The synthetic unit test can be run with:

python -m unittest discover -s tests -p 'test_lu_act_address_geobase_original_window_v0.py' -v

Twelve synthetic tests cover a sole interior candidate, overlapping polygons, boundary and hole handling, many addresses in one footprint, invalid topology and missing input. The original pair was subsequently executed on an exact-head GitHub runner; see the empirical aggregate evidence below.

The next scientific gate is a genuinely independent, manually adjudicated control set with original source lineage, address placement method, multi-unit buildings, cadastral changes, footprint segmentation, survey date and source rights. No model-input admission, insurer risk identity or independent coordinate error has been established.


## Executed two-original-source spatial result, 2026-11-04

**Exact-head original source run:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41812143721 (successful, 12/12 synthetic tests also passed).

The runner freshly downloaded both pinned original objects, verified their full national SHA-256 receipts, checked original ZIP/GeoPackage metadata and feature counts, then selected points and polygons in the previously frozen same 100 x 100 m EPSG:3035 square. Source feature IDs, point coordinates, geometries, linked pairs and individual address strings remained unpublished.

| Full original data / bounded window | Verified count |
| --- | ---: |
| Original 2026-11-02 BD-Adresses national address rows | **179,768** |
| Original 2026-10-01 GeoBase national building object rows | **230,353** |
| BD-Adresses points in the frozen city-centre window | **51** |
| GeoBase2026 building polygons in the SAME window | **107** |
| Address points strictly inside exactly one original building polygon | **51** |
| Address points inside multiple building polygons | 0 |
| Address point inside one polygon while touching another | 0 |
| Address points only touching a building boundary | 0 |
| Address points outside all sampled building polygons | 0 |
| Original address ID repeat excess within this local window | 0 |
| Polygons with exactly one uniquely contained sampled address | **37** |
| Polygons with two or more uniquely contained sampled addresses | **6** |
| Sampled polygons with no uniquely contained address in this **window** | **64** |
| Distinct polygons with 2+ uniquely contained addresses | **6** |
| Address points in those 6 polygons | **14** |

**Conservation:** 51 = 51 + 0 + 0 + 0 + 0. These are **observed candidate relationships**, not 51 independently validated physical building identities. The independent repeated original-source runner now directly counts 37 polygons with one sampled address and 6 with multiple, hence 43 of 107 original polygons have at least one uniquely contained sampled address point. **The other 64 polygons only lack a uniquely contained point in this 100 m window:** these polygon geometries merely *intersect* the window and may have entrances/addresses outside it, or may be non-addressed entities. This result is not a national building-address coverage rate or proof that 64 buildings lack addresses.

**Interpretation / limits:** ACT may place an address at a largest-building or parcel centroid using its own cadastral geometry. The 100% polygon-interior relationship is likely affected by that shared upstream source and is **not independent location validation**, an insurer exposure coverage ratio, a proof that all 107 buildings are addressed, or evidence of no missing/incorrect buildings. Six of the polygons contain more than one address, directly warning against address-to-building 1:1 modelling. Address date 2026-11-02 and building date 2026-10-01 differ; no building-stock change conclusion follows from this diagnostic.

The printed original SHA-256s matched the prior independently established receipts. No raw address/building data or individual match was uploaded as an artifact, no model inputs or insurer records were admitted, and the public repository retains only source-reference metadata, QA code and aggregate evidence.
