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

## New bounded native and GEOS canary — unexecuted on original until main

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
request on an ephemeral runner. First real original outcome is **not
claimed** by this plan until that trusted source job and its numeric
receipts are directly inspected.

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
