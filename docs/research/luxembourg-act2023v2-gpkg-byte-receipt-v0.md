<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT2023v2: original ZIP + GeoPackage metadata receipt

**Scope:** Read-only research, never an approved CAT model input. This extends
`docs/research/luxembourg-bati3d-official-footprint-asset-preflight-v0.md`
with an **executable original-file inspection**, not a new catalogue source.

## Source identity / verified provider claims (2026-11-01)

- Publisher: Luxembourg Administration du cadastre et de la topographie (ACT).
- Official catalogue: https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2023/
- Exact **ACT2023v2**, 2D building footprints GeoPackage ZIP:
  https://data.public.lu/en/datasets/r/d62942ec-0dc8-40e2-9fa4-27841e6e1ac1
- Distribution: https://download.data.public.lu/resources/base-de-donnees-nationale-des-batiments-3d-2023/20260317-160936/act2023v2-buildings3d-footprints.gpkg.zip
- Provider label: **CC0**; listed compressed size: **60.3 MB**; updated
  **2026-03-17**; declared CRS **LUREF LTM / EPSG:2169**.
- Provider explains that the 2D footprints represent the **extent of roofs**
  in 3D buildings, not necessarily the same footprint definition as EUBUCCO.
- The provider page describes unusual **X Northing / Y Easting** axis naming
  for EPSG:2169. A valid EPSG code alone therefore does not prove correct
  coordinate interpretation; no spatial join is authorised by this check.
- The catalogue's `md5` value with multipart-like suffix is **not** accepted
  as a regular independent hash pin.

## Implemented one-shot workflow

The `.github/workflows/luxembourg-gpkg-original-preflight.yml` workflow
runs focused synthetic tests and tries a single **fixed** HTTPS file download
on a GitHub-hosted runner (read-only permissions, time and size bounds).
No provider data are committed or uploaded; any original file is ephemeral.

The source preflight `scripts/luxembourg_gpkg_zip_preflight_v0.py` accepts
one locally downloaded ZIP with an optional **independently known**
`--sha256`:

```bash
python scripts/luxembourg_gpkg_zip_preflight_v0.py \
  --source-zip /private/act2023v2-buildings3d-footprints.gpkg.zip
python -m unittest tests.test_luxembourg_gpkg_zip_preflight_v0 -v
```

It computes original ZIP and extracted GeoPackage SHA-256; rejects malformed,
linked, encrypted, oversized, multi-GPKG, or unsafe ZIP members; validates the
SQLite file header, GPKG application ID, required metadata tables, exact
EPSG:2169 polygon/multipolygon declarations, geometry-column presence and
bounded feature table row counts. The only outputs are schema names, data
counts, file sizes, hashes and explicit blocked-admission flags.

The workflow reports a new SHA-256 as a **receipt of bytes acquired at runtime**,
not verification against a previously known independent source hash; check
`verified_against_independent_prior_sha256`. An unreachable publisher URL
must fail rather than substitute a different vintage.

## Original provider receipt (GitHub Actions; 2026-11-01)

**An actual original-file acquisition and bounded metadata inspection has now
succeeded** in the source workflow, not merely a synthetic test:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41306520956

| Evidence field | Original observed value |
| --- | --- |
| Provider resource | `d62942ec-0dc8-40e2-9fa4-27841e6e1ac1` |
| Exact archive bytes | `63246093` |
| Archive SHA-256 | `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a` |
| Extracted GeoPackage bytes | `157261824` |
| GeoPackage SHA-256 | `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf` |
| Feature table | `ACT2023v2_Buildings3d_Footprints` |
| Declared geometry and EPSG | `MULTIPOLYGON`, `2169` |
| Feature rows | **238189** |
| Declared geometry column | `geom` |

Publisher field names (names only, no actual attribute values):
`id`, `geom`, `buildingid`, `gml_id`, `commune`, `lau2`,
`modelmodificationdate`, `area`, `zmin`.

The first workflow acquired and independently **computed** the original ZIP
hash; it did **not** compare against a pre-existing pin. A follow-up exact-URL
workflow now requires the above observed archive SHA **as its prior pin** and
must fail if the provider revises bytes. The file was read in GitHub's
temporary runner only; no raw geometry, feature IDs or personal data were
uploaded to Git or Neon.

This evidence establishes an actual downloadable Luxembourg building source,
its schema and record count. It does **not** prove geometrical validity,
country-by-country coverage, real building identity, CRS axis order,
source survey vintage, EUBUCCO licence, or CAT admission.

## Critical remaining work

1. Recheck the exact prior ZIP SHA-256 on a second official retrieval and
   preserve a separate immutable checksum/dated provenance receipt when the
   provider updates the source.
2. Independently inspect original SRS WKT / coordinate samples to resolve
   EPSG:2169 axis semantics. This preflight does **not** validate polygon
   geometry topology, survey dates, 2D-vs-roof segmentation or source ID
   stability. File-level licence/attribution and scientific suitability still
   require review.
3. Fetch licensed, version-pinned EUBUCCO v0.2 Luxembourg data separately;
   ACT's CC0 label does **not** transfer to EUBUCCO.
4. Cut small same-place, same-vintage samples **outside Git** and run
   `building_footprint_overlap_v0.py` with the correctly established CRS.
   Quantify manual match precision/recall, one-to-many splits and coverage.
5. Only then consider derived exposure and vulnerability inputs with versioned
   legal and scientific admission. No owner, customer, policy, building record
   or original geometry goes into the lightweight research database in this PR.
