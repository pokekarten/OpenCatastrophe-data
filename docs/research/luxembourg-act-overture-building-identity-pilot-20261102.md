<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT 2026 / Overture 2026 building identity pilot

**Research-only. No confirmed real cross-provider individual building matches yet.**

## Two official original source families

Luxembourg ACT GeoBase Buildings (release **2026-10-01**, declared EPSG:2169): original ZIP SHA-256
6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3;
extracted GPKG SHA-256 ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676.
The previously verified ACT original has **230,353 source polygon features**. Source and licence:
https://data.public.lu/en/datasets/bd-l-geobase/ and
https://github.com/pokekarten/OpenCatastrophe-data/pull/1087 .

Overture Buildings (release **2026-10-21.0**, WGS84 lon/lat) are stored as GeoParquet under
s3://overturemaps-us-west-2/release/2026-10-21.0/theme=buildings/type=building/ .
The first two globally listed objects have verified metadata-only receipts in PR #1107;
**neither is known to cover Luxembourg**. Full file SHA-256 and individual original source rows
are not yet verified. Overture licensing/attribution: https://docs.overturemaps.org/attribution/ .

## Provider-confirmed Luxembourg-city candidate file (2026-11-02)

The official [Overture STAC item 00226](https://stac.overturemaps.org/2026-10-21.0/buildings/building/00226/00226.json) was fetched directly, not inferred from the first world files. Its **source-file bounding box** is
longitude **3.8891329765 to 6.5342741013** and latitude **48.7070693970 to 50.8007278442**.
This box intersects our explicit Luxembourg-city research query window longitude **6.129 to 6.131** and latitude **49.609 to 49.611**. Nearby STAC item files 00224–00225, 00227–00233 were screened by their published bounds; the 00226 item is the directly supported candidate for the query window. This is **file extent evidence only**: a file bbox does not prove that any actual polygon intersects the small research box.

Exact S3 object:
https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/release/2026-10-21.0/theme=buildings/type=building/part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet

The provider STAC item reports **609,459,333 original bytes**, **5,054,907 rows** in **256 row groups**. Separate public source HTTP byte ranges verified its first and last **PAR1** magic bytes, original Parquet footer length **1,461,640 bytes**, and a bounded 8,192-byte metadata-footer prefix. Independently decoded the actual Parquet metadata header: version **2**, **5,054,907** rows and **63** nested schema nodes (root 24 children), agreeing with STAC. Original feature data pages and whole-file SHA-256 were **not read or checked**.

For this first **Luxembourg-city pilot only**, the pairing code now requires this exact part-00226 file key rather than accepting arbitrary worldwide Parquet files, and an extra negative test rejects a different syntactically valid file. This key pin is a provider metadata receipt, **not** a claim that individual locally supplied records have been source-byte authenticated. Real region geometry and actual spatial sample content remain outstanding.

## Reproducible original-provider file receipt (metadata only)

The reviewed script research_runners/overture_luxembourg_stac_receipt_v0.py
independently retrieves the exact official STAC item 00226, requires its
frozen 2026-10-21 release, published source file URL, source size,
5,054,907 original rows, 256 STAC-reported row groups and bounding-box
intersection with the small Luxembourg-city research window.

It then asks the actual S3 object for only **4 + 8 + 8,192 = 8,204**
file bytes using exact HTTP 206 ranges. It checks constant ETag across
the three independent ranges, Parquet PAR1 header/trailer, and parses the
original footer-prefix metadata version 2 / 63 schema elements / 5,054,907
rows. It never reads individual original building feature pages or
downloads the full 609 MB file. An S3 ETag is NOT a verified full-file SHA256.

    python -m research_runners.overture_luxembourg_stac_receipt_v0 --live
    python -m unittest tests.test_overture_luxembourg_stac_receipt_v0 -v

The new GitHub workflow .github/workflows/overture-luxembourg-stac-original-file.yml
runs mock-only tests on PRs; it permits the exact public original metadata probe
only on manual workflow_dispatch or after a reviewed workflow-file push on main.
It never logs provider feature rows or writes to Neon. The original S3 source
file metadata was independently checked in this research turn using public
HTTP range responses; full exact-head GitHub CI must pass before merging.

**No national ACT/Overture feature identity has yet been proven.** The original
S3 part file overlaps the research region but its STAC bbox does not prove
any actual per-row geometry overlaps the region. A reviewed bounded original
feature sample, verified original file SHA256, geodetic frame review, GERS
registry evidence, and source-specific reuse rights remain outstanding.

## Isolated insurance Neon metadata readback

The exact newly discovered part-00226 original source-file receipt was inserted
**only** into the existing nonproduction Neon branch
overture-buildings-metadata-pilot-20261102 (ID br-bold-unit-baf2smqf),
table research.overture_original_building_file_probe_v0.
The independent original S3 ListObjectsV2 receipt reports
LastModified **2026-10-21T17:46:03Z**, original size **609,459,333 bytes** and
multipart ETag **a4a0d16d3ca5f460b2626facb71daae5-10** (not a SHA-256).

Live isolated-branch SQL verification now returns **three** metadata source
receipts in total (worldwide parts 00000, 00001 and the Luxembourg-city
candidate part 00226), with **15,059,017 provider-reported file rows** in
those three objects and **zero** source-rights, actual-row-import,
insurer-exposure or CAT-input approvals. The number is the sum of original
**file rows**, not country building count or deduplicated insured structures.

The production insurance branch does **not** have the experimental receipt
table, and still has **zero** admitted original raw files and real insured
exposure units. The Pokémon project was not accessed. The idempotent,
nonproduction-only reproduction SQL is versioned at
research_runners/sql/overture_buildings_metadata_receipts_v0.sql.
This STAC/S3 audit does not admit geometry into a loss model.

## What the new joined-screen code does

The offline script research_runners/luxembourg_act_overture_identity_preflight_v0.py
accepts a strict JSON projection of **up to 64 ACT and 64 Overture features**, with a maximum
**256 KiB** local input, exact pinned original release and ACT hash *claims*, one original
Overture part key, source families, and Polygon/MultiPolygon coordinates. No source fetching,
no Git/raw geometry upload, no Neon write and no insurer valuation is performed.

An ACT feature carries source_id plus its native EPSG:2169 geometry.
An Overture feature carries gers_id, source_families and EPSG:4326 geometry.
The script transforms Overture lon/lat to the ACT EPSG:2169 national grid using
pyproj always_xy and screens source topology, coordinate envelope, physical area, duplicate
IDs and exact source key/version. It computes planar intersection-over-union in projected
square metres and accepts only reciprocal one-to-one **geometric candidates** with IoU >= 0.75.
A 0.01 m² minimum positive overlap suppresses numerical slivers from coordinate round trips;
one-to-many and many-to-one cases are quarantined, and a no-match applies **only** to the
supplied source slice. The public output is aggregate-only: no building identifiers or
coordinates, only counts, sample SHA, and explicit false admission/provenance flags.

**Scientific caveats:** ACT 2026-10-01 predates the LUREF2025 2026-10-31 reference-frame
change. Transformation does not certify source epoch/physical location accuracy.
A UUID does not confirm GERS registry membership. Overture may use upstream geometry lineage
also present in ACT/OSM, so overlap does not establish independent ground truth.
This is NOT a rights approval, insured property, TIV, CAT vulnerability input or certified
national building stock.

## Specific next original-data acquisition step

Use the official Overture DuckDB spatial bbox method to query a small reviewed Luxembourg
research area and retain the actual returned per-feature **filename**. The source query
uses the frozen 2026-10-21.0 buildings partition and these bounding predicates:

    WHERE bbox.xmin < 6.131 AND bbox.xmax > 6.129
      AND bbox.ymin < 49.611 AND bbox.ymax > 49.609
    LIMIT 25

This is **only a suggested query, not an executed acquisition**. LIMIT bounds returned rows,
not Parquet bytes read. The source may span many objects; separate per-file provenance is
mandatory rather than attaching arbitrary output to the first globally listed file.
See https://docs.overturemaps.org/getting-data/duckdb/ .

On the ACT side, verify the original ZIP/GPKG with the existing full-source
checksum/geometry gate in PR #1087, retain original IDs/coordinates only in ephemeral
private input, and quarantine the previously identified 66 self-intersecting source polygons.
Build a small same-area source-pair JSON projection, then run:

    python -m research_runners.luxembourg_act_overture_identity_preflight_v0 --input /tmp/lu-act-overture-research-only.json
    python -m unittest tests.test_luxembourg_act_overture_identity_preflight_v0 -v

No real ACT/Overture source pair has yet passed this join. ACT hash strings in a JSON envelope
are not proof the individual supplied ACT rows came from the hashed original; Overture whole
file hash/rights still need independent verification. **No permission to load geometry
into the insurance production Neon database or mix with the Pokémon database.**
