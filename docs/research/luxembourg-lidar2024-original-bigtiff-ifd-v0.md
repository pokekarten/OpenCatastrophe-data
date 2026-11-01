<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg LiDAR2024: bounded original COG BigTIFF IFD metadata

**Research only.** Official Luxembourg ACT LiDAR2024 MNT (ground) and
MNS (surface) original cloud-optimized BigTIFF sources passed exact
4,096-byte HTTP 206 reads in merged PR #945. Publisher response sizes:
**40,131,787,860** and **42,849,815,758** bytes. The prior SHA-256
`c2bceb795e786013f8d235e3aa3fe5707e75faf6a6be39b2a3d7da67113161c8`
pins **only the first 4KiB fragment** of both originals, not entire files.

## Causal improvement

`research_runners/luxembourg_lidar2024_bigtiff_ifd_v0.py` reads
original BigTIFF IFD metadata using Python's standard library and two
**exact official HTTPS source URLs only**, inherited from #945.

- Each source request is **one exactly aligned 4KiB HTTP Range GET**;
  only HTTP **206** with exact Content-Range and declared original
  10–120GiB source size is accepted. HTTP 200 and redirects are
  rejected before reading any response body.
- Strict limit: **16 distinct 4KiB requests = 65,536 bytes total per
  source**, and no metadata pointer beyond the first **1 MiB**.
  Inconsistent source length, wrong first-page SHA256, malicious BigTIFF
  pointer, unexpected tag type or duplicate tag fails closed.
- Parse original BigTIFF header and first IFD for image width/height,
  internal tile width/height, tile array cardinality, compression code,
  bit depth, GeoTIFF pixel scale and declared projected EPSG **2169**.
- Print only small aggregate source metadata. No original TIFF pages,
  tile pixel values, coordinates, building IDs, source archive,
  insurance exposure or CAT model input is exported/persisted.
- **12 fully synthetic unit tests**; narrow original-source workflow
  `.github/workflows/luxembourg-lidar2024-bigtiff-ifd.yml`
  checks MNT and MNS separately on disposable GitHub runners.

```bash
python -m unittest tests.test_luxembourg_lidar2024_bigtiff_ifd_v0 -v
python -m research_runners.luxembourg_lidar2024_bigtiff_ifd_v0 --asset MNT
python -m research_runners.luxembourg_lidar2024_bigtiff_ifd_v0 --asset MNS
```

The first IFD may describe a reduced resolution overview rather than
full national base raster. This probe must not infer alignment or
source pixel coverage if the original IFD does not support the
tiled/GeoKey assumptions. A passing metadata gate is **not** an
actual DSM–DTM height calculation.

## What remains

Need independently resolve actual full-resolution IFD selection,
geotransform alignment, vertical reference, no-data, tree canopy
versus roofs and bounded tile response sizes before acquiring any
real source heights. Later manually adjudicate ACT roof features with
terrain/building classes; the derived property height is not insured
replacement value or construction year.

Official catalogue:
https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/

Original URL and 4KiB source receipts:
`docs/research/luxembourg-lidar2024-mnt-mns-cog-http-range-v0.md`.

## Actual original provider BigTIFF metadata receipt, 2026-11-01

The original-source job successfully read both provider COG first IFDs,
using **one 4,096-byte** HTTP Range per source; the previous first-page
fragment digest matched for both original assets.

**Initial real provider run:**
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41314087848

| First IFD metadata | MNT original | MNS original |
| --- | ---: | ---: |
| Width (pixels) | **114,617** | **114,617** |
| Height (pixels) | **163,687** | **163,687** |
| Declared pixel size | **0.5 × 0.5** | **0.5 × 0.5** |
| Internal TIFF tile | **128 × 128** | **128 × 128** |
| Internal tile array entries | **1,145,984** | **1,145,984** |
| Bits per sample | **64** | **64** |
| Compression code | **5 (TIFF LZW)** | **5 (TIFF LZW)** |
| Projected GeoKey code | **2169** | **2169** |
| HTTP provider-reported source bytes | **40,131,787,860** | **42,849,815,758** |
| Actual downloaded | **4,096 bytes** | **4,096 bytes** |

These are real source metadata, not estimated pixel measurements.
The first-IFD tag sequence is valid and its internal tile count is
consistent with dimensions and tile size; the subsequent grid-digest
verification uses the full declared scale, tiepoint and dimensions to
check whether source georeferencing is exactly congruent. Matching
scale/dimensions alone is insufficient to prove matching pixel origins.

**No original pixel values or building heights were read.** The pixel
scale is horizontal CRS units, not a vertical accuracy or an insured
building height. A full-raster SHA-256 and ground-controlled axis order
remain unavailable.

## Verified declared MNT/MNS raster grid equivalence

The amended original provider workflow
[41314251647](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41314251647)
succeeded for **both** fixed original source URLs, including **12 synthetic
regressions**. In addition to the first IFD attributes above:

- `sample_format_code = 3` for both MNT and MNS (**IEEE floating point**);
  combined with 64 bits/sample, source pixels are represented as IEEE
  64-bit floating point, although no actual pixel was read.
- SHA-256 of the canonical **declared raster grid** (dimensions,
  PixelScale, ModelTiepoint and projected EPSG) is identical for both:
  `a95a2dfc078d31fbe6c7531cef19e39fb5e57d6656e7beb4f0045a0b77cec5ca`.
- Each original source required **one strict 4,096-byte range request**,
  with matching prior first-page fragment checksum, correct HTTP
  206 Content-Range and unchanged declared full-file total size.
- The source-level CRS **EPSG:2169**, **128×128 TIFF blocks**, horizontal
  **0.5m pixel scale**, **1,145,984** internal block index entries and
  **TIFF LZW compression code 5** are shared by both.

**Conclusion:** MNT/MNS first-IFD source grid metadata are *congruent*
(important for a future pixel-aligned DSM–DTM method). This is stronger
than equal image dimensions alone, but still does **not** independently
certify axis order, geodetic control, vertical units/datum, no-data
masking, classified roofs or ground truth. Reading a real bounded
compressed raster block requires a separately audited byte-offset,
byte-count and decompression gate with a strict transfer cap.
