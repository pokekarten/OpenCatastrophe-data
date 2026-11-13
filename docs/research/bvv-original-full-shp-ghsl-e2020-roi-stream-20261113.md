<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bavaria HU-BY full original SHP stream → frozen GHSL E2020 ROI (2026-11-13)

## Research objective and admission status

Implement the **first source-complete, bounded-memory, original-publisher
Hausumringe geometry inventory for the exact previously decoded
GHS-BUILT-S/V E2020 32×32 native grid window** in the Munich region.
**Verified original source outcome:** the new trusted-main original
full-SHP member run **succeeded** on 2026-11-13; its original full-member
CRC/SHA, geometry/ROI aggregates and Neon research sample #94 are
recorded in the source acceptance section below. This is not the
SHA of the *entire ZIP archive*, a historical 2020 footprint truth,
a unique insured-building census or an approved CAT model input.

Previous actual provenance:
- JRC original BUILT-S/V [#43309743505](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43309743505), independently
  reproduced by GDAL/LibTIFF [#43317950827](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317950827);
  research-only Neon original aggregate samples #49 / #50
- BVV original first Polygon [#43320212959](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43320212959)
  and first64 GEOS geometry QA [#43321672686](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43321672686);
  overlapping original research samples #61 and #62
- Existing original BVV Oberbayern ZIP, EPSG:25832 `.prj`,
  original DBF record count, original full 2,703,736-record SHX index
  chain and its min/max record content sizes

**Official product license:** Bayerische Vermessungsverwaltung
Hausumringe Bayern **CC BY 4.0** (commercial reuse with source
attribution and modification notice). Credit:
**Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de**.
See [official BVV Open Data rights](https://www.geodaten.bayern.de/odd/m/3/html/nutzungsbedingungen.html)
and [product description](https://www.ldbv.bayern.de/mam/ldbv/dateien/hausumringe-by_datenformatbeschreibung.pdf).
The linked dataset ATOM still has the `<rights>TODO</rights>`
metadata placeholder; the higher-ranking official product license
and source scope are not changed by this experiment. No protected
ALKIS WFS, national HU-DE or individual building owner data are used.

## Original full-member I/O contract

The workflow `.github/workflows/bvv-original-full-shp-ghsl-roi.yml`
is **synthetic/offline only on pull requests**. After successful
repository CI, trusted `main` or an explicitly dispatched trusted
`main` event may perform **one contiguous source-object coverage as a frozen sequence
of at most 20 bounded HTTP 206 ranged GETs**, each at most **8 MiB**
(never one long-lived 166 MB response). There are no retries,
redirects, credentials, URL parameters, discovered URLs, pagination,
or automatic model registration. Each individual segment requires
its own exact HTTP-206 response, exact source Range, file length,
MIME, encoding, identity URL, and consistent source ETag/Last-Modified
metadata. Segment contents are released before expensive GEOS work,
so the provider is never left on a 5-minute idle response.

| Property | Exact reviewed original proof |
| --- | --- |
| Original official ZIP | `https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip` |
| Full original ZIP object bytes | **174,299,765** (only member read) |
| Exact logical original byte coverage (starts with 45-byte ZIP local header) | **bytes=275903-166448183**, partitioned into contiguous non-overlapping 8 MiB or smaller ranges |
| Exact aggregate provider bytes over validated 206 responses | **166,172,281 bytes**, each individual response size separately verified |
| Original member | `hausumringe.shp`, DEFLATE, not all four ZIP files |
| Full compressed original SHP member bytes | **166,172,236** |
| Full decoded native SHP bytes | **501,212,696** |
| Original ZIP-directory member CRC32 | `55540a66` (must be recomputed over **all** decoded native bytes) |
| Source native records from separately verified original SHX/DBF | **2,703,736** |
| Verified original SHX smallest/largest Polygon content size | **112 / 10,284 bytes** |
| Original HTTP Range prefix SHA-256 (first 49,197 received bytes) | `8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80` |
| Native SHP header SHA-256 (first 100 decoded bytes) | `f312c12beea148041db5ebf9727ad2aca59e036bef4665aae47402008f02bb09` |

The Python standard-library streaming source parser strictly checks
original **HTTP 206 on every bounded source segment**, exact adjacent
Content-Ranges/full archive size, each segment's exact byte count and
cross-request `ETag`/`Last-Modified` consistency when provided,
the original local ZIP member header and **all 2,703,736 sequential
original Shape records**, stream end-of-file, complete decompressed
file-length SHA-256 and CRC32 against the original ZIP header/central
directory. An input block is at most 65,536 bytes, the DEFLATE output
chunk at most 131,072 bytes, and the residual source record byte
buffer is capped. No 174 MB archive or 501 MB decoded source is
written to disk, Neon or GitHub artifacts. The runner only returns
SHA-256 hashes and anonymous numeric statistics, not source
coordinates, geometry, individual IDs or raster pixel values.

This is a **full native original SHP member scan**, *not* the same as
the full **ZIP** SHA-256 (original DBF/SHX/PRJ and central directory
remain separately evidenced) or proof that the source's cadastral
inventory is exhaustive beyond what its publisher asserts.

## Frozen original JRC study window

The source ROI is derived programmatically from the already SHA-pinned
original JRC BUlLT-S/V GeoTIFF pixel scale and tiepoint (EPSG:4326),
the unchanged top-left **col=22973,row=4899**, and exactly **32×32**
30-arcsecond cells.

Approximate native geographic envelope:

```text
min longitude: 11.440416643747994
min latitude:  48.007916676356096
max longitude: 11.707083309358438
max latitude:  48.27458334194954
```

The 4 geographic edges are densified with 32 segments each, then
reprojected into the independently original-file-verified BVV CRS
**ETRS89 / UTM 32N, EPSG:25832**, using pinned PROJ.
Never treat 30 arcseconds as exactly 100 metres, or perform
area arithmetic in square degrees.

All original native Polygon frames are checked in source order; only
features whose source bbox overlaps the frozen projected ROI are
transiently reconstructed as Shapely geometries. For ROI candidates,
validate bounded rings, finite UTM points, source bbox, ESRI shell/
hole orientation, closure and GEOS topology. A malformed or ambiguous
ROI geometry **blocks the source-completeness assertion** rather than
quietly deleting or repairing it. Each intersecting feature is clipped
to the ROI in metres. The runner reports both:

- sum of areas across original clipped polygons (may double-count
  overlapping official shapes);
- area of their transient GEOS union, with overlap difference.

It reports aggregate candidate and intersecting-record counts.
The uncompressed source frame SHA/CRC and complete record count must
pass **before** declaring complete ROI coverage for *this exact
original archive*. Neither individual geometries nor complete
raw rasters are retained; no loss/TIV/asset locations are created.

The source's original `main` attempt
[Actions 43468044298](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43468044298)
failed **closed** at its original safety limit of 100,000 ROI
Polygon features: `BLOCKED: original ROI feature budget exceeded`.
It did **not** complete the 166 MB compressed original source
scan or verify original full-member CRC, so no total-inventory claim,
Neon sample or scientific exposure result can be derived from that
failed attempt.

The original-source pressure is addressed by an **exact GEOS
hierarchical union in bounded 2,048-feature transient batches**.
Each completed batch is merged into a binary-carry geometric union
accumulator. This preserves exact (not merely summed) ROI union
area without keeping all original individual polygons, and prevents
unbounded per-source feature lists. No silent truncation, feature
dropping or false complete-ROI flag is allowed. The accumulated
union is checked for GEOS validity after every merge and final
combination. A 24-level geometry-union budget remains fail-closed.
Synthetic regression tests include six overlapping polygons spread
over multiple forced-small union batches. Only the corrected
**new trusted-main original run** can establish full-member
CRC/SHA, total 2,703,736 original native records and ROI
area/count statistics; they must not be inferred from PR tests.

## Real second provider attempt failed closed: long-lived HTTP transport

[Original GitHub Actions #43469127363](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43469127363)
ran on reviewed main commit
`1dd6687a4e91c51fa142615a5a953cb7811c0abb` and
passed the new hierarchical union's offline synthetic tests. It did
**not** complete the original full-member source transfer. The
bounded main-only research progress log confirmed:

| Original progress | Sequential native record frames | ROI bbox candidates |
| --- | ---: | ---: |
| First | **250,000** | **0** |
| Second | **500,000** | **10,192** |
| Third | **750,000** | **110,974** |
| Fourth | **1,000,000** | **274,649** |

After approximately 5 minutes of real-source work, the provider
response ceased before the entire fixed HTTP Range was delivered:
`BLOCKED: original ZIP Shape range truncated` (exit 2).
There is **no verified complete SHP CRC, full file hash, all-record
count, regional building exposure or ROI area** from this attempt.
The 274,649 figure is an **intermediate ROI bbox candidate count**,
not the count of actual clipped ground-truth buildings and must not
be reused as final inventory. No Neon observed sample was inserted
for this failed run.

**Reasoned failure class:** one long-lived original **166 MB**
HTTP-206 response stayed open during time-intensive GEOS union and
record parsing; the source stream ended before the file was complete.
This does not establish that the official file is corrupt, nor
that its geometries failed validity.

**Transport correction:** the original member is now fetched as
**20 exact adjacent provider HTTP-206 segments**, at most 8 MiB
each. The same continuous raw DEFLATE frame is processed in memory
across the segment boundaries; each segment is fully received,
checked and its network connection closed before processing. On
each segment the source URL, exact Range, Content-Length, original
file size, MIME, no HTTP re-encoding and cross-segment
ETag/Last-Modified identity are checked. There are no retries or
skipped/re-read byte intervals. A byte-counting reader must prove
full logical coverage of **166,172,281** bytes. The existing
49,197-byte original source SHA, full-member original CRC32
`55540a66`, total **2,703,736** native records and complete SHA
are still mandatory. PRs test this on tiny fabricated segmented
byte streams, including source revision changes and truncated
segments; the new real main outcome is **not yet known**.

## Scientific interpretation and next evidence gate

This is a **current-era 2026** HU-BY original cadastral source versus
**2020** JRC GHSL modelled built-up surface and building volume,
not a temporally aligned building-inventory ground truth.
HU-BY includes certain built structures as well as ordinary buildings.
Even source-complete ROI extraction cannot prove that each record is
a unique/insurable building, that the geometries have unchanged
2020 vintage, or that GHSL values have calibrated bias.

After the actual original main source step succeeds:

1. Inspect the full original compressed SHP SHA-256, complete
   uncompressed SHP SHA-256 and CRC, all original record counts,
   ROI union/overlap and original source timestamps.
2. Store a **new, explicitly time-mismatched, research-only aggregate
   source receipt** in Neon only if all original byte/rights/ROI gates
   pass. The receipt must include overlaps with existing sample
   #61/#62, no original polygons or pixel values, and preserve
   `model_input_approved=false`.
3. Separately develop a cell-wise, source-aligned area-weighted
   GHSL-versus-BVV spatial study with temporal/footprint uncertainty.
   Do not claim a validated CAT model or adjust insurer TIV now.

Failure, provider rate limiting, a source format change or source
budget overruns must be recorded as **BLOCKED**. The original
validated-20-segment provider workflow has **now successfully run
on trusted main**; the exact scope and provenance are recorded below.


## Actual full original HU-BY SHP success — verified 2026-11-13

**Trust boundary and result:** [Actions original source run
#43471636096](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43471636096),
source code on reviewed `main` commit
`3542e75d931377c70ec9eda5ad6339a4c5302a2f`,
produced **SUCCESS**. All offline source-specific and repository
tests passed before the merge of
[PR #1545](https://github.com/pokekarten/OpenCatastrophe-data/pull/1545).
The real issuer original full SHP member was then read in
**20 exact adjacent and individually verified anonymous HTTP 206
source ranges**, 8 MiB or smaller. Source validators remained
consistent across segments. The entire unchanged single original
raw DEFLATE member was decoded and checked by one continuous SHA-256
and CRC32 stream (not twenty independent small SHPs).

| Accepted original publisher/source evidence | Verified result |
| --- | ---: |
| Official public product | Bavarian HU-BY Oberbayern region Shapefile, CC BY 4.0 |
| Real original UTC | 2026-11-13 17:29:18 UTC |
| Exact ranged original source ZIP byte coverage | `bytes=275903-166448183/174299765` |
| Individually verified contiguous 206 requests | **20** |
| Full original compressed SHP Deflate bytes | **166,172,236** |
| Full original compressed-member SHA-256 | `22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615` |
| Original native uncompressed SHP bytes | **501,212,696** |
| Full original native SHP SHA-256 | `977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c` |
| Computed CRC32 vs original ZIP local/directory record | **`55540a66` matches** |
| Complete original Shape records and Polygon type-5 frames | **2,703,736 / 2,703,736** |
| Largest native record content bytes | **10,284**, equals independently verified SHX maximum |
| Study polygon projected area EPSG:25832 | **588,514,088.109 m²** |
| Original municipal Polygon bbox candidates overlapping ROI bbox | **431,083** |
| Original source Polygon records actually intersecting clipped ROI | **417,565** |
| Invalid original ROI polygon rings / native reconstructed polygons | **0 / 0** |
| Original clipped individual footprint area sum | **56,871,811.455 m²** |
| Original footprint union area, no double counting | **56,791,644.170 m²** |
| Actual overlap difference | **80,167.285 m²** |
| Exact GEOS union batches | **204**, active final levels **4** |

**Independent prior full-original source-byte corroboration:**
the compressed source SHA-256 **and** complete uncompressed native
SHP SHA-256 above exactly match prior original, separate
[WSF2019 vs BVV execution #43317649994](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317649994),
previously stored in insurance Neon research metadata samples
**#56** and **#57**. They are *repeat observations of the same
official source file*, not additional independent cadastral datasets.
The current full source analysis also includes the original
first64 samples #61 and #62, rather than generating new independent
building counts.

**Neon successfully received the research aggregate** into
`insurance-risk-core.research.source_sample_v0`:

- `sample_id=94`, `source_id=de.bayern.hausumringe`,
  `sample_kind=observed_values`;
- `provider_response_sha256=22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615`
  names **the full compressed original SHP Deflate member bytes**,
  *not* a full ZIP hash and *not* the 20-segment concatenation with
  the 45-byte local header;
- canonical PostgreSQL JSONB SHA-256
  `c32c7336571d820d0b73813cdb58afcff50d105f2899640d4ab5214b35165482`;
- exact native full-SHP original CRC/SHA, each source segment
  count, area union, bbox candidate and 417,565 intersecting Polygon
  aggregate, original source workflow/commit, and links to overlapping
  earlier source receipts #56/#57 and #61/#62;
- `research_only=true`, `model_input_approved=false`,
  `source_byte_persistence_authorized=false` and the product-specific
  **BVV HU-BY CC BY 4.0** attribution unchanged. Source dataset
  ATOM `rights=TODO` is still documented.

A safe read-only source integrity replay:

```sql
SELECT sample_id,source_id,sample_kind,provider_response_sha256,
       sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
         AS canonical_sample_hash_valid,
       sample_json->>'original_full_native_records_checked' AS full_source_records,
       sample_json->>'original_full_decoded_shape_sha256' AS full_native_sha256,
       sample_json->>'roi_original_polygon_records_intersecting' AS roi_polygons,
       sample_json->>'roi_original_polygon_areas_union_m2' AS union_m2,
       model_input_approved,source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id=94 AND source_id='de.bayern.hausumringe';
```

**Scientific boundaries:** This proves *source-native coverage for
exactly this original BVV Oberbayern SHP file* and one fixed projected
research ROI, not complete geospatial coverage of all possible
structures or all Germany. The 417,565 native polygons are
*not* 417,565 insurable buildings. The public source is
current-era cadastre; **its actual building survey dates are
unverified**. The JRC GHSL source corresponds to **E2020**,
so no historical 2020 ground-truth validity/accuracy, insurer TIV
or CAT-model admission follows. The complete original **ZIP archive**
SHA-256 remains unverified (DBF/SHX/PRJ independently probed),
even though the full compressed and native original **SHP member**
SHAs and ZIP-declared SHP CRC32 have been verified.


## 2026-11-13 additional original HTTP transport regressions and bounded response retry

The **successful previously verified original BVV main source run**
[43471636096](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43471636096)
and Neon research sample **#94** remain unchanged and fully valid
for their exact original source epoch. However, two subsequent
**independent main source accesses** encountered transport failures
without any source evidence of changed native bytes:

- [Paired original GHSL/BVV source research run
  43483336611](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43483336611),
  first attempt: after **2,250,000** sequential native
  Shape records had been parsed, one public BVV source segment
  request failed: `BLOCKED: original 1024-cell research source
  verification unavailable: fixed original ZIP segmented HTTPS
  source unavailable`. No complete-source read or 1,024-cell
  correlation result was recorded in Neon.
- [Independent original BVV source-only regression
  43483336967](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43483336967):
  the same class of source-segment HTTP failure occurred after
  **500,000** original Shape records. Both jobs remained
  **fail-closed** with no claim of full source or new model-admitted data.

These failures are consistent with transient provider HTTP/network
availability, **not** proof of source-file corruption or invalid
scientific geometry. The previously independently matching
**full compressed SHP member SHA-256
`22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615`**
and original native SHP SHA-256
`977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c`
are not altered.

**New narrowly bounded source-availability policy:** each
predeclared, original fixed public BVV HTTP 206 Range
(8 MiB maximum; 20 *accepted*, adjacent, nonoverlapping
original segments) permits at most **two total HTTPS attempts**,
with one **5-second pause** only if the initial request
fails due to a transient connection/reset/timeout, an
incomplete transport response, or provider HTTP status
**408, 500, 502, 503 or 504**. The program **never**
retries a **429** provider rate-limit response, a
**403/404**, redirect, wrong HTTP200, altered
`Content-Range`, object-size drift, ETag/Last-Modified mismatch,
unexpected MIME, re-encoding, missing original source bytes,
bad ZIP header, bad native TIFF, CRC32 or SHA-256.
It never retries/replays an **already accepted** segment.
A failed request contributes **zero** parsed, hashed or persisted
source bytes; only an individually accepted, complete exact
HTTP206 response can advance the contiguous stream. The
full original file's independently pinned SHA/CRC and record
counts still must pass before any research sample or cell
statistic is emitted.

This bounded retry is **not an unlimited network crawler**,
anonymous source-search, provider rate-limit workaround or a
change to the reviewed 2020-vs-current source admission.
New PR tests are fully offline and simulate HTTP503, URLError,
short replies, HTTP429, invalid source headers and the
two-attempt limit without calling the real provider. **No new
original-source success is claimed before a separately verified
trusted-main workflow result.**
