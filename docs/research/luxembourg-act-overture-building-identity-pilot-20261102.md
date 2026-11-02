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

## Original Parquet row-group geography metadata pilot (2026-11-02)

The STAC original filename is a coarse geographic container, not a proof of
individual building footprints. To reduce avoidable provider data access, the
new `research_runners/overture_lu_rowgroup_metadata_v0.py` performs a
**metadata-only**, exact-file-limited preflight on that original 609 MB file.
It rechecks STAC/file headers, then reads only the source Parquet footer,
which is frozen at **1,461,640 bytes** (less than the strict 2 MiB cap).

The code decodes the original Parquet row-group and column-chunk Thrift
CompactProtocol metadata, checks the complete **256 row-group** inventory
and original **5,054,907** row conservation, then screens original numeric
per-row-group `bbox.xmin/xmax/ymin/ymax` **DOUBLE/float64** statistics against
6.129..6.131 E, 49.609..49.611 N.

- **Excluded:** Source metadata prove that no bounding boxes in a
  given group can intersect the query window.
- **Candidate:** Coarse row-group bounds could intersect; a candidate is
  **not** a real city building, nor proof of a feature overlap.
- **Unknown:** Missing, invalid, nonfinite or contradictory bbox statistics
  cannot safely exclude a group; it must remain eligible for a later
  per-row controlled check.

The original provider footer declares Parquet physical type **5 = DOUBLE**, with 8-byte statistics for all four bbox columns. A first full-metadata run incorrectly assumed float32 and conservatively returned all 256 groups as `unknown`; this was fixed before using the results to exclude any source group.\n\nThe first original row group's footer metadata was independently sampled:
**16,234** file rows; `bbox.xmin` 3.890515–3.967390,
`bbox.xmax` 3.890683–3.967666, `bbox.ymin` 48.707302–49.039326,
`bbox.ymax` 48.707397–49.039677. These extrema are outside the
Luxembourg-city query box and safely exclude that **one** group.
That is a strictly original-source **footer finding**, without reading any
row-level polygons or records.

Run only after confirming bounded source-metadata access:

    python -m unittest tests.test_overture_lu_rowgroup_metadata_v0 -v
    python -m research_runners.overture_lu_rowgroup_metadata_v0 --live

An explicit read-only [GitHub research workflow](https://github.com/pokekarten/OpenCatastrophe-data/blob/research/overture-building-crosswalk-preflight-20261102/.github/workflows/overture-lu-rowgroup-metadata.yml)
checks the public pinned STAC and original Parquet footer. It does
**not** decode geometries, original row IDs or insurance values; only
aggregate candidate/excluded/unknown group counts may be logged. A
separate full official provider sample and national ACT/Overture polygon
join remain the next steps. Do not infer an exact city/country building
count or source rights approval from row-group statistics.

## Real original source geometry and cross-source pilot results (2026-11-02)

**This section supersedes the earlier planning-only statements below.**

**Actual original Overture polygons.** [GitHub source run 41497879623](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41497879623) passed, including 9/9 source-free tests. A direct S3 Arrow range-based read used exactly original **row group 182** of Overture part 00226 and projected only `bbox` and `geometry` columns. The source-group file contains **19,095** rows; the selected columns report **1,583,294 compressed bytes** (a source column budget, *not an HTTP transfer cap*). In the tiny 6.129–6.131 E, 49.609–49.611 N research window, **69** original rows had bounding boxes intersecting and **69** source polygons also had **positive true geometric intersection**; **0** of those candidate polygons were malformed or had invalid topology. A geodesic footprint-area sample (first 64 valid polygons only, not every source feature) had median **142.24 m²**. No original Overture IDs, WKB, coordinates, customer data, or object-level geometry were persisted or emitted.

The row-group preflight [run 41497156085](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41497156085) also passed the full original footer reading after fixing the Parquet DOUBLE-vs-FLOAT width. Original row group 182 was **the only** group not excluded by the file's 256 source-group geographic bbox statistics: 255 excluded, 1 candidate, 0 unknown, with 19,095 candidate-group *source rows* and 5,035,812 source rows in excluded groups. It is **not** a city-wide count and not a national completeness proof.

**Actual ACT x Overture spatial crosswalk.** [First end-to-end original-source workflow 41498511267](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41498511267) **PASS**, with all 11 original-independent synthetic tests. This job obtained the immutable official ACT GeoBase 2026-10-01 Buildings ZIP, verified the original whole-ZIP SHA-256 and extracted original GeoPackage SHA-256 using the canonical source gate, scanned all **230,353 ACT original objects** and quarantined the known **66 invalid polygon topologies**. Within the same small research window it found:

| Original-source research metric | Observed |
| --- | ---: |
| ACT 2026 source polygon footprints with positive window intersection | **139** |
| Overture 2026 source polygon footprints with positive window intersection | **69** |
| ACT x Overture polygon overlap pairs at EPSG:2169 planar IoU ≥ 0.75 | **5** |
| Reciprocal one-to-one *geometric candidates* | **5** |
| ACT features with many-to-one / one-to-many ambiguous matches above threshold | **0** |
| ACT source features without a >=0.75 match in this supplied research window | **134** |
| Overture source features without a >=0.75 match in this supplied research window | **64** |

These are **real original polygon geometry comparison observations**, not five independently verified physical building identities, legal source joins, insured locations, TIV, or exposure admissions. In particular, neither ACT's 139 nor Overture's 69 is a complete, independently validated count of buildings in Luxembourg City or a defensible national source coverage ratio. Possible causes for low reciprocal match counts include different polygon segmentation, source lineage, coordinate frame/epoch, generalization, and the strict 0.75 threshold; these hypotheses require measured tests rather than assumptions.

The original provider ZIP and GeoPackage are ephemeral in the GitHub runner; provider WKB, source IDs and geometry coordinates are not emitted to logs or stored in Git or Neon. A research-only **aggregate receipt** was written to isolated CAT Neon branch `br-bold-unit-baf2smqf` under `research.lu_act_overture_original_city_pair_receipt_v0`, plus an Overture-only geometry receipt under `research.overture_lu_city_one_group_geometry_receipt_v0`. Reproducible isolated SQL scripts are in `research_runners/sql/`. Confirmed **0** source-licence approvals, policyholder mappings, model admissions or persisted provider geometry. Production insurance Neon and the Pokémon database remain untouched.

**Next scientific investigation:** `research_runners/luxembourg_act_overture_original_city_pair_v0.py` now additionally computes **aggregate per-source best-IoU histograms**, separating no positive overlap, under 0.25, 0.25–0.50, 0.50–0.75 and ≥0.75. The follow-up **full original-source** [GitHub run 41499209669](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41499209669) **PASSED**, including **13/13** source-free regression tests. Across **139 ACT** and **69 Overture** source polygons in the small pilot window, it measured **282 source-polygon pairs with positive intersecting area**, of which **5** reached IoU >= 0.75 and reciprocal one-to-one candidate status.

The **best ACT overlap per Overture polygon**, not a verified source identity, was: **6** no positive polygon contact; **6** best IoU under 0.25; **33** between 0.25 and 0.50; **19** between 0.50 and 0.75; **5** at least 0.75 (sum **69**). The symmetric **best Overture overlap per ACT polygon** was: **3** no contact; **72** under 0.25; **40** between 0.25 and 0.50; **19** between 0.50 and 0.75; **5** at least 0.75 (sum **139**). These are distributions of geometric footprint resemblance only, not recall, precision, confirmed building population, source-independent validation, a license determination, or any insurer attribution. The mismatch is compatible with differing segmentation/generalization/source epochs; these causal explanations still require targeted source lineage and controlled evidence before reducing threshold or joining individual buildings. Retain all low-score/ambiguous cases for research, not automatic deduplication.

## Original Overture upstream family lineage in the city window (2026-11-02)

The exact original [GitHub source lineage run 41500090059](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41500090059)
**passed**, including **8/8** synthetic no-network tests. It read only
the `bbox` and `sources` fields from the already pinned exact Overture
source Parquet part 00226, original row-group 182, and selected the **69**
source rows whose `bbox` intersects the Luxembourg-city pilot window.

**Original per-row upstream dataset presence:** **64** source polygons
list `OpenStreetMap`; **5** list `Microsoft ML Buildings`. There were
**0** sampled city rows with missing original source lists and **0** with
multiple distinct upstream datasets. The original source license tags
show `ODbL-1.0` for **69** source rows.

These are reported provider metadata categories, **not** an independent
audit of individual source licenses, attribution completeness, or survey
accuracy. Overture's dataset-level ODbL licence and downstream
derivative/database obligations still require legal review. Neither
individual `sources.record_id`, original feature IDs, coordinates, raw
source-lineage records nor building WKB were logged or written to Git/Neon.
The aggregation is *not* a declaration that all 69 polygons represent
distinct insured buildings.

An important next causal check is the cross-tabulation of **which of the
five stricter ACT–Overture geometric match candidates** came from each
upstream dataset. Do not attribute those five matches to OSM or Microsoft
before that further exact-source comparison is verified.

## Source families of the five strict ACT–Overture original geometric candidates

The exact-source [GitHub run 41500592616](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41500592616) **PASSED**, with **16/16** synthetic offline tests and complete ACT full-original SHA verification. It used the same Overture part 00226, source row-group 182 and validated source `sources.dataset` labels in transient memory, preserving correspondence between the 69 real Overture city-window polygons and their individual source metadata **without exporting any source IDs or geometry**.

Among the **five reciprocal ACT–Overture geometric candidate polygons at EPSG:2169 IoU >=0.75**, the matching Overture source labels were: **OpenStreetMap = 5**, **Microsoft ML Buildings = 0**, `unknown_or_multiple = 0`. This exactly conserves the five strict shape candidate pairs. Source-family totals for the broader 69 Overture city polygons remain **64 OpenStreetMap** and **5 Microsoft ML Buildings** (original source-lineage audit #41500090059).

This is a causal **source attribution observation**, not proof that OpenStreetMap and ACT have independent original surveys, share a publisher ID, preserve stable GERS registry membership, or represent five identical physical buildings. It does **not** permit merging polygons, assigning insurer claims, generating replacement values, using copyrighted derivative data commercially without rights review, or treating the 75% IoU cutoff as calibrated identity confidence.

Only the aggregate counts and the original run URL were added to the existing **isolated** Neon CAT research receipt, where `insurance_CAT_model_input_approved = false` is constrained and confirmed. Neither provider features nor original WKB, IDs, coordinates, or OSM record IDs were committed or stored.

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
