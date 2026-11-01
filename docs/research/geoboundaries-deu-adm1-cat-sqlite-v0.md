<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Local isolated CAT geography SQLite staging — geoBoundaries DEU ADM1

This utility turns the **verified original** 2021 geoBoundaries DEU ADM1
GeoJSON into a 16-polygon *local* CAT-only spatial index. It does not ingest
buildings, insured assets, claim records, market values or hazard event tracks.
See [original geometry quality receipt](geoboundaries-deu-adm1-original-geometry-v0.md)
for the live full-source SHA and observed geometry facts.

## Usage (explicit, separate CAT location)

```bash
python -m pip install -r requirements-eu-flood-spatial.txt
python -m unittest tests.test_geoboundaries_deu_adm1_cat_sqlite_v0 -v

# 'source.geojson' must be the full, original pinned Git-LFS data object.
# File content SHA-256 must be 56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682.
mkdir -p /secure/cat-data/staging
python -m research_runners.geoboundaries_deu_adm1_cat_sqlite_v0 \\
  --original-geojson /secure/source.geojson \\
  --output /secure/cat-data/staging/deu-adm1-2021.cat.sqlite
```

`/secure` is an illustrative **user-controlled existing folder**, not a
repository or connected persistent service. The script does not create remote
databases or silently register CAT datasets as production-ready. The SQLite
output must use an absolute `*.cat.sqlite` path outside the Git checkout;
the script refuses to overwrite existing files. It atomically constructs a
fresh file with a distinct SQLite `application_id=0x43415431` and version 1.
A separate schema marker is mandatory before queries. These safeguards
prevent accidental reuse of unrelated Pokémon or insurer databases.

## Stored content and rights

- A single `source_provenance` record with 2021, boundary identity,
  original SHA/length, pinned asset link, original German
  **Datenlizenz Deutschland – Namensnennung – 2.0** attribution and
  geoBoundaries **CC BY 4.0** collection attribution.
- The exact 16 source polygons as local WKB along with their original
  `shapeID`, `shapeName`, and optional `shapeISO` (no invented crosswalk).
- The `admin1_bbox` SQLite RTree spatial filter, used **only for candidate
  lookup**; actual point assignment must pass an independent Shapely
  point-within/covered-by-polygon check.
- Boundary points matching multiple states must return an explicit
  ambiguity error. Outside-location points return `None`. Coordinates
  must be finite WGS84 longitude/latitude.

This is not a claimed official NUTS mapping, nor proof of land completeness
or legal national border authority. The 2021 boundary vintage must never be
silently joined to a different NUTS year or to current insurance locations
without documenting vintage/crosswalk effects. Source data and any local
spatial assignments are retained **only** in the explicitly selected CAT
staging file; no provider original bytes or staged SQLite files are committed
to Git or uploaded as workflow artifacts.

## Reproducible source-data smoke check

The dedicated original-geometry workflow runs synthetic tests on PRs. A
single workflow revision merge on `main`, or manual dispatch, fetches the
exact 6,254,151-byte original file and verifies its SHA/geometry. It then
creates an **ephemeral** `*.cat.sqlite` file, checks schema/provenance/RTREE,
and resolves two fixed known **test points** (Munich and Berlin) to
different ADM1 source polygons. Both original file and derived database are
deleted after the run. They are not production CAT database writes.

The source's first isolated CAT SQLite run should be documented only after
a real full-source GitHub Actions execution reports success. Scientific
model admission still requires explicit data-governance and exposure-schema
review.

## Verified first-party full-source CAT index run — 2026-11-01

The complete source-pinned original GeoJSON was used in a real GitHub Actions
run [41314234471](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41314234471)
at main commit `672f88c945c4352978427bf0dff881aee7b5b9a7`.
Both reviewed spatial-regression and SQLite integration steps succeeded:
**16 synthetic tests passed**, then an independently acquired **6,254,151-byte**
original source was SHA-256 checked against
`56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682`.
The original comprised 16 OGC-valid features and 143,969 coordinates.

The first-party stage printed:

- `separate_cat_staging_file_created=true`
- `indexed_polygons=16`, `db_application_id=1128354865`
- `represented_year=2021`
- `source_sha256=56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682`
- `provider_bytes_committed_to_repository=false`
- `model_input_admitted=false`

The subsequent real-source spatial smoke test printed:
`PASS: Munich and Berlin each resolve to distinct DEU ADM1 source polygons`.

This confirms a *working local, ephemeral* 2021 Germany ADM1 CAT spatial
staging construction and exact point join on original data. The SQLite
file was deleted after the test and is **not** a persistent shared CAT
database. No NUTS crosswalk, actual insurer exposure, or worldwide
coverage is implied.
