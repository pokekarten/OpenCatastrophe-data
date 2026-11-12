<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original Bavaria HU-BY: first 64 Polygon/GEOS topology canary

**Exact source**: official Bayerische Vermessungsverwaltung, anonymous open
[Oberbayern Hausumringe regional ZIP](https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip),
product-scoped **CC BY 4.0** with
“Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de”
as issuer attribution. Public service ATOM publishes CC BY 4.0;
its dataset ATOM has an independently recorded missing `rights=TODO`
metadata field, and restricted ALKIS WFS / national HU-DE are not
automatically covered.

## Pre-existing actually executed original source receipt

The already verified original first-Polygon source workflow
[43320212959](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43320212959)
proved one original 49,197-byte ranged ZIP member
`hausumringe.shp` and exactly **one** complete original
Polygon (one closed ring, seven points). The original ranged response
SHA-256 is
`8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80`.
The exact original source and science record is in
[the first-Polygon report](by-oberbayern-original-shp-first-polygon-20261112.md),
and its anonymous original-structure receipt is stored in the
insurance Neon **sample #61**.

## Original bounded native and GEOS canary implementation

New runner
`research_runners/by_hausumringe_oberbayern_first64_geos_v0.py`
extends that single source proof from **one** to **64 consecutive
leading** original native Shape records. This is **not random**,
representative or a historical 2020 reference sample.

The runner accepts no caller-provided URL, offset, record count,
region, raw data, credentials or download destination. It issues at
most **one** reviewed anonymous HTTP Range GET,
`bytes=275903-325099` (49,197 B) of exactly the same public BVV
source ZIP. It requires HTTP **206**, exact
`Content-Range bytes 275903-325099/174299765`,
exact file MIME, original member name, source ZIP version/Deflate,
original response SHA-256, and original
`hausumringe.shp` first record SHA-256. The partial raw DEFLATE
is bounded to at most **4 MiB** transient uncompressed data.
No full ZIP, no full 501 MB uncompressed SHP, no original geometry
or source bytes are stored.

Exactly the first 64 native Shape records are parsed in order with
strict record number/size, native Shape 5 Polygon framing
(or explicit Shape 0 Null), bounded polygon-part and point counts,
closed rings, source CRS envelope and per-record bbox conservation.
Each Polygon ring is independently checked for topology using
**Shapely 2.1.2 / GEOS** (`LinearRing.is_simple`,
`LinearRing.is_valid`, individual part `Polygon.is_valid`).
If individual original rings are invalid, the runner records **only
aggregate invalid counts**, rather than silently repairing/removing
them or declaring an entire dataset clean. Ring orientation and
multi-part hole/exterior topology are **not** independently resolved,
so per-part checks must never be represented as full multipolygon
validity. Even if all 64 pass, it says nothing about the remaining
millions of records.

Output is **only** fixed-source original SHAs, anonymous aggregate
record/ring/point counts, GEOS-invalid ring counts,
first-64-record byte digest and explicit negative completeness/vintage
and model admission fields. No source coordinate, polygon bbox,
individual record ID, owner/address, asset feature, full
geometry, raw ZIP or rendered images in logs, Git or Neon.
No library table or model admission automatically updated.

`.github/workflows/by-hausumringe-first64-geos-original.yml`
executes pinned GEOS **synthetic-only tests on PRs**.
Only after CI and manual review/merge to main or explicit trusted
workflow dispatch does the runner perform exactly one real provider
request on an ephemeral runner. **Original source execution subsequently succeeded** on trusted main;
the source-run receipt, limits and Neon research sample are shown next.

## Scientific limits

- The source CRS EPSG:25832 comes from independently verified BVV
  original `.prj`, but those 64 source polygons are not the same
  geometry as the GHSL E2020 32×32 cells.
- The original full archive/SHP SHA-256 and CRC over all 501 MB,
  original survey dates, complete cadastral capture and
  independent building identity are not proved.
- Exact 2020 historical footprints are not available here; current
  public source bytes cannot be used as unconditional 2020 truth.
- No independent GHSL building count, insured building valuation,
  OED account/location export, TIV, event damage or CAT model input
  is authorized; keep research-only and
  `model_input_approved=false`.


## Successful actual original first64 and research Neon #62 — 2026-11-12

**Verified original BVV source run:**
[GitHub Actions #43321672686](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43321672686),
trusted `main` merge commit
`1c42b240a4c26bc859605d59c0ffceb071f255a8` after
[PR #1525](https://github.com/pokekarten/OpenCatastrophe-data/pull/1525).
All source-specific GEOS synthetic tests and full repository CI
(Python 3.11–3.14 plus Berlin) succeeded before merge. The
**actual original 49,197-byte HTTP-206 source Range** was then
fetched once, re-verified against its frozen SHA-256 and decoded
using the official open regional SHP member and GEOS 2.x.

| First-party result | Verified value |
| --- | --- |
| Original real live UTC | 2026-11-12 22:38:03 UTC |
| Original official source | BVV Oberbayern open `hausumringe.shp` member of 174,299,765-byte ZIP |
| Original exact Range | `bytes=275903-325099/174299765` (49,197 bytes) |
| Original ranged response SHA-256 | `8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80` |
| Original first 64 complete sequential Shape records | **64** (64 Polygon type 5; zero NULL shapes) |
| Original Polygon rings checked by GEOS | **64** (one ring per source record; no multi-part records in this excerpt) |
| Original Polygon vertices examined only in transient RAM | **505** |
| GEOS rings with invalid/simple-ring flags | **0** |
| GEOS individual part-Polygon invalid flags | **0** |
| First 64 consecutive raw native record bytes SHA-256 | `366f87b09c803c6f82adc30b295620bd3c8ba038742b63e06782da3fd1c58051` |
| Existing first Polygon research Neon sample | **#61**, original first source record only |
| Additional 64-record aggregate research Neon sample | **#62** (overlaps #61 by one record) |
| Canonical JSONB SHA-256 for Neon #62 | `d71c14e946eff84662328b6061ede7bca162e7b94e018883c63209ec217c6d34` |

The second research sample **#62** was inserted into
`insurance-risk-core.research.source_sample_v0` with
`sample_kind=observed_values`, exact original source response
SHA-256 as above, *explicit*
`overlaps_original_source_sample_id=61` and
`incremental_distinct_original_records_over_sample61=63`.
It is **not** an independent source dataset or distinct raster
spatial extent. It contains only anonymous aggregate counts and
SHA-256 receipts; neither individual building coordinates, native
Polygon vertices/IDs, original ZIP/SHP bytes, individual feature
areas nor rendered geometries were persisted. The original
BVV CC BY 4.0 source attribution is preserved; the dataset ATOM
`rights=TODO` metadata issue is not suppressed.

Independent read-only Neon proof:

```sql
SELECT sample_id,source_id,sample_kind,provider_response_sha256,
       sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
         AS canonical_jsonb_sha256_valid,
       sample_json->>'native_source_records_structurally_decoded' AS native_records,
       sample_json->>'native_source_rings_checked_with_geos' AS geos_rings,
       sample_json->>'geos_invalid_rings' AS invalid_rings,
       sample_json->>'incremental_distinct_original_records_over_sample61' AS incremental_records,
       sample_json->>'overlaps_original_source_sample_id' AS overlap_prior_sample,
       model_input_approved, source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id IN (61,62)
ORDER BY sample_id;
```

**Scientific claim scope:** GEOS checks cover **only 64 first
consecutive records**, a nonrandom and potentially geographically
clustered selection. These are real official 2026-era source
polygons, but neither source-survey vintage, spatial completeness,
multi-part/hole topology for records outside the excerpt, the
2,703,736 indexed features, independent historical 2020 footprints
nor the GHSL E2020 32×32 true-building overlay are established.
One source ZIP response hash is used for both #61 and #62,
explicitly to prevent false counting of independent sources.
The candidate remains `not_admitted` to any scientific/insured
CAT model. `model_input_approved=false` for both research samples.
