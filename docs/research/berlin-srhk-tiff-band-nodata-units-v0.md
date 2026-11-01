<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin 2025 Starkregen: strict water-depth TIFF band metadata contract (v0)

**Offline, synthetic-only parsing contract, 2026-11-01.**
No original WFS, ZIP or TIFF source bytes were downloaded by this PR.
The existing source receipts in
docs/research/berlin-starkregen-source-access-preflight-20261101.md
already establish exact source ZIP identity, both original internal TIFF
GeoKey EPSG:25833, one TIFF-named ZIP member per scenario and bounded
source-byte read. PR #1057 separately owns grid affine, pixel dimensions
and pilot-bounding-box support; do not duplicate that work.

## The separate hazard-science gap

A projected CRS, pixel scale and raster extent do **not** prove:
- The original numerical band stores **metres of water depth** rather
  than centimetres, a scaled/offset integer, a flow speed or encoded
  category. Projected-coordinate metre units are not automatically
  raster **band value** units.
- Which numeric cell values are genuinely **NoData**, outside raster
  coverage or zero dry depth. 0 must never be substituted for missing
  data merely because GDAL_NODATA tag is missing.
- Which pixels are genuinely present or physically valid. Header-only
  declarations do **not** verify decompressed pixel blocks, nodata mask
  semantics or source event/scenario timing.

## Implemented independent bounded parser

research_runners/berlin_srhk_tiff_band_semantics_v0.py accepts at most
**1 MiB** of already independently source-authenticated and decompressed
*classic TIFF header* bytes. It does not read provider URLs or TIFF
pixel/tiles. It handles first-IFD-only declarations:

| Source TIFF tag | Metadata extracted | Gate |
| --- | --- | --- |
| BitsPerSample (258) | explicit scalar bit depth | SHORT, count exactly 1 |
| Compression (259) | integer TIFF compression code | SHORT, count exactly 1 |
| SamplesPerPixel (277) | declared bands per pixel | SHORT, count exactly 1 |
| SampleFormat (339) | integer sample type code | SHORT, count exactly 1 |
| GDAL_NODATA (42113) | finite source numeric sentinel or NaN sentinel | NUL-terminated bounded ASCII, never inferred dry |
| GDAL_METADATA (42112) | source-declared UNITTYPE, SCALE and OFFSET for band 0, if present | bounded ASCII XML, no DTD/entities, duplicate fields or unknown arbitrary promotion |

An absent tag, a tag whose payload is beyond the source prefix, or
a units value that is not one of the **explicit reviewed labels**
is reported as **unknown** instead of inferred. Recognised labels are
only m/metre/meter, cm and mm variants; a source declaration is **not**
a physical calibration or validation of BKG's flood-product units.
The parser retains finite scale and offset as **claims** and never
applies those values to pixel data. Numeric infinity, malformed XML,
unsafe pointers, duplicate semantic tags, invalid sample types and
oversized metadata are blocked.

Every output explicitly states
nodata_mask_or_pixels_validated=false,
water_depth_units_or_scale_scientifically_validated=false and
building_hazard_or_cat_loss_admitted=false. No raw XML,
personal data or per-building location is exported.

## Tests and next source boundary

Synthetic tests prove missing/unknown versus zero, NaN NoData
sentinels, stated mm/cm/m, malformed scales, XML entity rejection,
duplicate TIFF/UNITTYPE entries, oversized or inaccessible TIFF
metadata and non-admission flags.

The isolated GitHub Actions workflow runs **only these synthetic
tests** with no source network call. Once the noncolliding affine
work in #1057 is merged, a separately reviewed extension can
reuse the already authenticated two original 65,536-byte ZIP-range
prefixes, derive the bounded TIFF prefix and invoke this parser.
This source execution should report the actual original GDAL
metadata **without claiming it proves depth units or valid cells**.
The next scientific step remains pixel-block validation plus rights,
NoData mask, meaningful scenario and water-depth physical scale.
