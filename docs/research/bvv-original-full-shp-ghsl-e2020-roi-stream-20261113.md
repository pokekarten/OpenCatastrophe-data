<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bavaria HU-BY full original SHP stream → frozen GHSL E2020 ROI (2026-11-13)

## Research objective and admission status

Implement the **first source-complete, bounded-memory, original-publisher
Hausumringe geometry inventory for the exact previously decoded
GHS-BUILT-S/V E2020 32×32 native grid window** in the Munich region.
Do **not** claim success, full archive CRC, original full-SHP SHA,
ROI totals, historical 2020 footprint truth or Neon observed-values
sample until the **new trusted-main source workflow succeeds** and its
real original-provider log is inspected.

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
`main` event may perform **one** anonymous fixed original source
GET, no retries, redirects, credentials, URL parameters, discovered
URLs, pagination or automatic model registration.

| Property | Exact reviewed original proof |
| --- | --- |
| Original official ZIP | `https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip` |
| Full original ZIP object bytes | **174,299,765** (only member read) |
| Exact HTTP Range (includes 45-byte ZIP local header) | **bytes=275903-166448183** |
| Exact response size | **166,172,281 bytes** |
| Original member | `hausumringe.shp`, DEFLATE, not all four ZIP files |
| Full compressed original SHP member bytes | **166,172,236** |
| Full decoded native SHP bytes | **501,212,696** |
| Original ZIP-directory member CRC32 | `55540a66` (must be recomputed over **all** decoded native bytes) |
| Source native records from separately verified original SHX/DBF | **2,703,736** |
| Verified original SHX smallest/largest Polygon content size | **112 / 10,284 bytes** |
| Original HTTP Range prefix SHA-256 (first 49,197 received bytes) | `8a3c95bbbca493b192f6923fa4b6060798f561775f647bd34ffd4fc3af316f80` |
| Native SHP header SHA-256 (first 100 decoded bytes) | `f312c12beea148041db5ebf9727ad2aca59e036bef4665aae47402008f02bb09` |

The Python standard-library streaming source parser strictly checks
original **HTTP 206**, complete Content-Range/full archive size,
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

The transient ROI collection is limited to 100,000 intersecting
features; a larger area blocks the job for an explicit resource review,
not silent truncation.

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
budget overruns must be recorded as **BLOCKED**. The new provider
workflow **has not run on original data at PR stage**.
