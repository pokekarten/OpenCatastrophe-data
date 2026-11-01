<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT2023v2 to EUBUCCO: original GeoPackage schema / bounded window gate

**State as of 2026-11-01:** offline preflight software implemented; **official
ACT2023v2 ZIP has not been downloaded or inspected** in this execution environment.
This document makes no claims about actual provider layer names, IDs, counts or
exact byte SHA-256.

## Verified original-product constraints

- Publisher catalogue: <https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2023/>
- The listed 2D GeoPackage resource ID is
  `d62942ec-0dc8-40e2-9fa4-27841e6e1ac1`, updated **2026-03-17**.
- Official resource download:
  <https://download.data.public.lu/resources/base-de-donnees-nationale-des-batiments-3d-2023/20260317-160936/act2023v2-buildings3d-footprints.gpkg.zip>.
- Dataset catalogue says **CC0**, 60.3 MB **compressed**, and **EPSG:2169**.
  The original survey contains roof extents derived from **June–September 2023
  aerial images** and includes roofs of buildings with footprints above 20 m².
  These polygons are **roof extents**, which may differ from ground-level
  cadastral or EUBUCCO footprints. The listed 2026 update is a processing
  release, not the building construction year.
- The publisher specifically describes LUREF LTM EPSG:2169 axis semantics as
  `X = Northing`, `Y = Easting`. **Do not silently infer XY order** using a
  generic EPSG:3035 reprojection. Confirm storage XY with known geographic
  control locations and an audited sample *before* spatial matching.
- EUBUCCO v0.2 technical documentation:
  <https://docs.eubucco.com/v0.2/data-format/> and
  <https://dev-docs.eubucco.com/v0.2/license/>.
  EUBUCCO reports source-level `geometry_source` and `geometry_source_id`,
  separate observed/merged/modelled attributes, and ODbL 1.0 with listed
  noncommercial/share-alike exceptions in other regions (Abruzzo/Prague).
  Confirm the **exact Luxembourg source lineage and extract licence** before
  using it; a second product could reuse the same original input.
- Previous PR #908 provides the bounded GeoJSON footprint overlap diagnostic,
  and overlapping PR #911 provides independently version-pinned ZIP integrity
  checks. This work does **not duplicate** either procedure.

## Two-stage offline receipt (after actual authorised acquisition)

First run `research_runners/luxembourg_bati3d_zip_preflight_v0.py`
from PR #911 against an independently recorded original ZIP SHA-256.
That tool emits `gpkg_sha256` but **does not** prove inner schema, CRS,
sample accuracy, building rights or model admission.

After safely obtaining/extracting that **exact** inner .gpkg into a local
working directory outside Git or the Neon metadata database, inspect the
actual layer list, original building IDs, count, GeoPackage `application_id`
and EPSG CRS using:

```bash
python research_runners/luxembourg_gpkg_schema_window_v0.py \
    --gpkg /private/working/act2023v2-buildings3d-footprints.gpkg \
    --expected-gpkg-sha256 <gpkg_sha256-from-verified-original-zip>
```

Read the returned **actual** layer names, field names and SRS ID rather than
guessing the schema. The program rejects malformed GeoPackages, mismatched
expected SHA, unknown EPSG metadata or missing polygon feature layers. It
reports aggregate data counts, not original building IDs.

Only once the original **building ID field**, geographic window and **true
stored axis order** have been reviewed, permit a bounded local sample:

```bash
python research_runners/luxembourg_gpkg_schema_window_v0.py \
  --gpkg /private/working/act2023v2-buildings3d-footprints.gpkg \
  --expected-gpkg-sha256 <verified-extracted-gpkg-sha256> \
  --layer <exact-layer-name> \
  --id-column <actual-verified-building-id-column> \
  --native-epsg2169-bbox <x-min> <y-min> <x-max> <y-max> \
  --limit 250 \
  --permit-local-research-export \
  --output-local /private/working/act-sample.geojson
```

The optional spatial export requires a GeoPackage RTree, less than or equal
to 1500 candidate rows, valid polygon or multipolygon geometries, unique
source IDs and an output file that does **not** already exist. Output GeoJSON
retains the **native source XY coordinates**, without an embedded CRS
declaration: call downstream spatial tooling with `--right-crs EPSG:2169`
only *after* independently verifying native coordinate order. Other missing
layers or unmatched bounding windows result in no output, not guesses.

**No real foreign-source rows/geometry** should be committed or uploaded to
Neon. Large source bytes belong in a separate authorised versioned object
store. The read-only insurance Neon registry continues to hold only source
metadata and Git file/checksum lineage.

## Why this does not yet constitute a confirmed building match

A 2023 roof-derived polygon against an older EUBUCCO ground footprint is
not necessarily an error: overhangs, dormers, roof annexes, commercial
structures and split/merge building definitions can reduce IoU. The first
real data success criterion is a **manual gold-standard sample** stratified
by urban/rural and rooftop complexity, with overlap thresholds calibrated
and original provider/source lineage retained. A large overlap alone
cannot establish actual building identity, construction year, material,
occupancy, insured values or policy cover.
