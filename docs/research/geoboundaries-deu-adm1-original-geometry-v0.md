<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original geoBoundaries Germany ADM1 GeoJSON — exact-source geometry gate

## Source identity (distinct from metadata-only API access)

An earlier source receipt in
[docs/GEOBOUNDARIES_DEU_ADM1_METADATA_PROBE_V0.md](../GEOBOUNDARIES_DEU_ADM1_METADATA_PROBE_V0.md)
bound the public geoBoundaries `gbOpen DEU/ADM1` metadata endpoint to
`boundaryID=DEU-ADM1-10402087`, year represented **2021**, the
Federal Agency for Cartography and Geodesy and an original attribution
licence (Datenlizenz Deutschland – Namensnennung – 2.0).
The geoBoundaries collection also requires CC BY 4.0 attribution;
both source and collection-level licence/provenance obligations remain.

The exact authoritative asset reference in the reviewed metadata was:

- Published URL: `https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/DEU/ADM1/geoBoundaries-DEU-ADM1.geojson`
- Immutable Git tree revision: `9469f09`
- Authoritative Git-LFS pointer at that revision: `132 bytes`;
  it contains the original **Git-LFS SHA-256**
  `56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682`
  and original length **6,254,151 bytes**.
- GeoJSON content delivery URL at the *same pinned revision*:
  `https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/9469f09/releaseData/gbOpen/DEU/ADM1/geoBoundaries-DEU-ADM1.geojson`.
- Official API rights/usage guidance: https://www.geoboundaries.org/api.html
- Upstream licence source:
  https://www.govdata.de/dl-de/by-2-0

GitHub's normal text/blob API can return only the **132-byte LFS pointer**,
not 6.25 MB of polygons. Counting the pointer as an imported geometry dataset
would be a serious error. The SHA-256 in this independent Git-LFS pointer
is an exact original-asset identity; do not replace it with an unchecked
`latest`, an inferred Git blob SHA or the metadata-response hash.

## Implemented scoped audit

`research_runners/geoboundaries_deu_adm1_original_geojson_v0.py` reads
a **local original file** and never downloads anything itself. Before
JSON parsing it requires exact source byte count, exact SHA-256 and rejects
LFS pointers. It then validates:

1. Strict duplicate-free UTF-8 GeoJSON FeatureCollection with **16** features.
2. Feature `shapeID` and `shapeName` uniqueness,
   `shapeGroup=DEU`, `shapeType=ADM1`.
3. Polygon/MultiPolygon-only OGC-valid, non-empty, nonzero-area geometry.
4. Bounded vertices, finite positions, WGS84 longitude-latitude national
   extent sanity gate and supported embedded CRS metadata (if present).
5. Pairwise overlapping polygon areas above a conservative diagnostic
   threshold of `1e-8` square degrees must **fail**. Boundary-touch
   topological intersection is not automatically an overlap.
6. Report **aggregated evidence only**, including feature/vertex counts,
   coarse bounding box, maximal inter-feature overlap and original SHA.
   No provider feature coordinates/IDs, source files, or derived GIS layer
   are committed to Git or an application database.

The separate source-specific
`.github/workflows/geoboundaries-deu-adm1-original-geometry.yml`
performs synthetic tests on a pull request, and **one exact original
provider asset acquisition** on the first main push of its workflow file
(or explicit manual workflow dispatch). External bytes reside only inside
the job's temporary private directory and are deleted at exit. This is
an intentionally bounded source review, separate from the existing
metadata-only access contract. The workflow does **not** generalize that
contract to country-wide crawling, perpetual downloads, or commercial
redistribution. No scheduled provider requests.

To examine a separately, lawfully acquired exact original file locally:

```bash
python -m pip install -r requirements-eu-flood-spatial.txt
python -m unittest tests.test_geoboundaries_deu_adm1_original_geojson_v0 -v
python -m research_runners.geoboundaries_deu_adm1_original_geojson_v0 \\
  --original-geojson /local/secure/geoBoundaries-DEU-ADM1.geojson
```

## Remaining prerequisites before physical CAT data use

The output is a **quality receipt, not a geometry ingestion contract**.
It neither makes buildings locatable nor creates insured values. Prior to
joining with EUBUCCO / GHSL / OSM / insurer exposures:

- Confirm whether the provider coordinates, source period and names are
  the appropriate legal and temporal reference for the exposure year.
- Establish crosswalks from geoBoundaries `shapeID/shapeISO` to current
  official state codes and NUTS versions; never join solely by labels.
- Validate geodetic area/coverage/completeness with an independent national
  boundary reference; a valid GeoJSON polygon is not proof of complete
  or authoritative coverage. Do not treat square degrees as m².
- Freeze a separate explicit rights-reviewed ingestion manifest and store
  original/derived geometry under the **CAT** datastore only. Keep it
  physically separate from Pokémon holdings and production models.

The first real geometry audit's GitHub Actions URL, source hashes, and any
observed original-source scientific blockers should be documented after the
first run rather than assuming the source will pass.

## Verified full original geometry, first-party live receipt — 2026-11-01

The exact pinned **6,254,151-byte** original GeoJSON was downloaded from the
reviewed commit and all implemented geometry/identity integrity checks passed
in [GitHub Actions run 41313687185](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41313687185),
main commit `2675046142011145bb6ed4426fce6b4c51c0535b`.
This is a trusted execution receipt rather than synthetic test evidence.

Observed original-source aggregate facts (not inferred from metadata alone):

| Field | Verified result |
| --- | --- |
| Original SHA-256 | `56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682` |
| Original bytes | 6,254,151 |
| Feature / unique ID / unique name counts | 16 / 16 / 16 |
| OGC valid polygonal geometries | All 16 |
| Total polygon coordinate positions | 143,969 |
| Material inter-feature polygon overlap | None at the stated threshold |
| WGS84 coordinate bbox (rounded to 0.001°) | [5.866, 47.270, 15.042, 55.059] |
| CRS metadata | Present and accepted |
| Source year | 2021 (reviewed source metadata; not re-dated) |
| Provider bytes persisted to Git | No |
| Geometry admitted to CAT model | No |

The original 2021 data are real and checked, but a complete independent
national administrative border coverage/completeness comparison and
version-safe official NUTS crosswalk remain outstanding. The next adapter
may build an explicit **isolated CAT-only staging index** for local spatial
queries, retaining both source and collection attribution, without silently
modifying a production or Pokémon-related database.
