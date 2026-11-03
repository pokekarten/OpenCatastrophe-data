<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin detailed SRGK: bounded original ZIP central-directory inventory

**Research-only.** No archive is downloaded in full; no original TIFF
member/pixel, physical flood depth, insurer exposure, vulnerability
function, loss, CAT model admission or database write is authorized.

## Exact preceding evidence

[Reviewed Berlin source run 41367827781](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41367827781)
confirmed detailed SRGK child Atom
`https://gdi.berlin.de/data/ua_srgk/atom/0.atom`,
full original child XML 3,297 bytes, SHA-256
`144de6b6afcf80f722996934dd690b5e40e9dfa294bc9eb59509a26ffb2a6e7f`,
and exactly three official ZIP products. Each original HEAD returned
HTTP 200 `application/zip` and exact `Content-Length`:

| Event family | Official ZIP filename | Source HTTP size bytes |
| --- | --- | ---: |
| Rare | `wasserstand_seltenes_ereignis.zip` | 132,689,382 |
| Extraordinary | `wasserstand_aussergewoehnliches_ereignis.zip` | 136,928,247 |
| Extreme | `wasserstand_extrem.zip` | 93,562,670 |

Provider child Atom links declare `image/tiff` even though URLs and
HEAD media are ZIP. The source states that **extreme raster data are not
available for all model areas**. Do not treat ZIP availability as
every-area scenario coverage.

The independently official-filter-verified **second** study box is
`[391860,5816840,392060,5817040]` in EPSG:25833, 200 × 200 m,
with 40,000 m² detailed *model-area polygon overlap* in
[original run 41363537076](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41363537076).
This does **not** establish which precise TIFF member is relevant.

## New source-locked central-directory audit

`research_runners/berlin_srgk_depth_zip_central_range_v0.py` uses the
three **exact approved official URLs and above sizes only**. The
separate reviewed workflow first runs adversarial ZIP tests offline;
the original provider work happens only after a workflow-change
merge to `main`, or explicit manual dispatch.

For each ZIP, perform at most **two bounded GETs** with exact
`Range: bytes=start-end` and
`Accept-Encoding: identity`:

1. Read at most 65,557 original tail bytes to find a complete ZIP
   end-of-central-directory (EOCD) record, including any comment.
2. Verify single-disk classic ZIP offsets/member counts and fetch
   at most 262,144 original **central-directory index bytes**, not
   archive member bodies. Parse each central-directory entry with
   explicit lengths and safe member names.

**Total hard transfer limit:** at most
`3 × (65,557 + 262,144) = 983,103 bytes`,
even though full archives total hundreds of megabytes. This step
does not perform ZIP member-range reads or unpack any TIFF.

An HTTP 200 response to a Range request fails **before reading body**:
never fall back to a full download. Also fail on missing/incorrect
206 `Content-Range`, changed source length, partial body,
redirect, compressed transfer, ZIP64/multi-disk flags, encrypted
members, unsupported compression, inconsistent central directory,
unsafe member paths, duplicate names, impossible bounds or caps.
**No safety gate should be weakened to obtain a green workflow.**

Only source-file names (at most 12 `.tif/.tiff` samples per ZIP),
per-entry compressed/uncompressed sizes, aggregate member formats,
full transferred-tail and index-byte SHA-256, source size, retrieved
UTC and scientific nonadmission flags appear in the output.
No original provider ZIP payload bytes or pixel/geometry data are
committed or copied into Neon.

If a provider does not support exact-range ZIP indexes or uses ZIP64,
record the failed gate; a separately reviewed alternative is needed.
No arbitrary URL, unbounded retry, dynamic provider discovery or
automatic full-ZIP fallback.

## Remaining independent model science / reuse gates

- This source-level directory inventory does not prove actual raster
  CRS, water-depth unit, scale, NoData, scenario assumptions,
  physical footprint, event probability or local observation.
- Read authoritative *per member* GeoTIFF headers in a separately
  reviewed bounded source process before matching to the second
  pilot. ZIP central file names are not enough for geography.
- Publisher licence wording has **German Data Licence Zero 2.0**
  and **CC BY 4.0 attribution specifically for Moabit and
  Flughafensee**. Follow per-product/per-area rights, attribution
  and provenance before distributing or importing raster content.
- The BKG KOSTRA signed Int16 source is a **different hazard product**
  whose depth-encoding blocker is tracked in
  [issue #1086](https://github.com/pokekarten/OpenCatastrophe-data/issues/1086).

**Acceptance:** synthetic tests + complete Python 3.11–3.14 / REUSE /
geospatial workflow checks. A successful original source-run must
be documented separately with its precise outcome. Even all green
does **not** authorize real CAT or insurance model input.
