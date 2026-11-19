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

## Original source-read integration — pending reviewed main workflow

With #1057 affine work and #1062 standalone band parser merged, the
original `research_runners/berlin_srhk_zip_first_tiff_header_v0.py`
now invokes the new NoData/units parser on **the same already
source-authenticated and bounded in-memory TIFF prefix**.
It does not change the original 65,536-byte per-source network budget,
the pinned first-512 SHA-256, original ZIP size/Last-Modified,
HTTP 206 requirement, Deflate cap or non-admission policy.

The dedicated existing workflow
`.github/workflows/berlin-srhk-tiff-header.yml` invokes
both original scenarios only after review and merge of the workflow
revision to main. PR checks are synthetic only.
**No original band NoData, unit, scale or offset result is
claimed until the actual post-merge provider run is inspected.**

## Tests and next source boundary

Synthetic tests prove missing/unknown versus zero, NaN NoData
sentinels, stated mm/cm/m, malformed scales, XML entity rejection,
duplicate TIFF/UNITTYPE entries, oversized or inaccessible TIFF
metadata and non-admission flags.

The isolated GitHub Actions workflow runs **only these synthetic
tests** with no source network call. The source-bound extension now reuses those original ZIP source
byte-range contracts and is pending real-provider main workflow proof.
Source declarations must still be independently reviewed against
physical units, NoData masks and pixel blocks before model admission.
The next scientific step remains pixel-block validation plus rights,
NoData mask, meaningful scenario and water-depth physical scale.


## Actual original Berlin source-band result — independently verified

The reviewed original-source workflow
[GitHub Actions 41335440273](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41335440273)
ran the merged #1063 data path (main merge commit
\`383ab39fb6f7612660476b7b5992b9df76c012c3\`).
It reused **exactly 65,536 original HTTP206 ZIP-prefix bytes per
source**, with fixed source identity, previously observed first-512
SHA-256 and the original Last-Modified unchanged. The actual
execution code SHA-256 was
\`4f162912e975ca16818dc7389ea39bf010b858c742ccb482e0624946897dc5cb\`.

| Independently read original TIFF declaration | Extreme | Extraordinary |
| --- | --- | --- |
| First-IFD band fields available | Yes | Yes |
| SampleFormat code | **3 = IEEE floating-point** | **3 = IEEE floating-point** |
| BitsPerSample | **32** | **32** |
| SamplesPerPixel | **1** | **1** |
| TIFF compression method | **5 = LZW** | **5 = LZW** |
| GDAL_NODATA tag 42113 | **present** | **present** |
| **Source-declared NoData numeric sentinel** | **−9999.0** | **−9999.0** |
| GDAL_METADATA tag 42112 | absent | absent |
| Explicit GDAL UNITTYPE declared | **no** | **no** |
| Explicit GDAL SCALE/OFFSET declared | **no/no** | **no/no** |
| Prior TIFF internal projected EPSG GeoKey | 25833 | 25833 |
| 1-m TIFF affine header & pilot bbox fully covered | yes/yes | yes/yes |
| Exact source ZIP-prefix-only SHA-256 | \`9b86b039e4c0915b76f4ea64bc13c201f43483a2585dcdd8f6650d6e1a70579f\` | \`ba22dae2169f3ffab268f9411099e98c5fc3a15cfd8094d6b486b6e9a0c32149\` |
| Source UTC read | 2026-11-01 18:13:03 UTC | 2026-11-01 18:13:03 UTC |
| Original raster pixel/NoData-mask sample read | **No** | **No** |
| Physical water-depth unit independently verified | **No** | **No** |

This is direct **original IFD metadata evidence**, not a claim
that any water-depth pixels, masking convention or physical unit
is validated. A pixel value of −9999 must never be interpreted
as a negative water depth; it is the source-declared NoData
sentinel. However, observed NoData **cells**, valid 0-depth
pixels, physical water-depth unit, unit scaling, coverage
within the 200×200 m building pilot and insurer losses remain
unverified. Absence of explicit UNITTYPE or SCALE does **not**
prove a default unit of metres or scale factor of 1.

### Next source access engineering constraint

There are **two compression layers**, independently observed:
the original ZIP member uses **Deflate (ZIP method 8)** and the
contained TIFF raster reports **LZW (TIFF compression 5)**.
The ZIP has only one TIFF member, with original large source objects
619,211,977 B and 563,115,763 B. Ordinary byte-range access to
the outer ZIP does **not** directly permit arbitrary GeoTIFF tile
access inside its Deflate stream: random access generally requires
prior sequential decompression or a separately built, verified
Deflate seek index. The inner TIFF's LZW tiles cannot be sampled
by assuming their compressed offsets equal original ZIP HTTP
offsets.

Before real building × flood support:
1. Review a rights-compatible, controlled one-time streaming
   original-source ingest into **isolated CAT temporary storage**,
   with fixed full ZIP SHA-256, bounded expanded bytes, zip-bomb
   controls and per-member CRC, or find an authoritative
   **independently verified raster subset service** with equivalent
   depth-mask and scenario semantics.
2. Open a **small original TIFF pixel window** in a controlled
   raster runtime after verified decompression, confirming actual
   32-bit samples, −9999 NoData masks, depth physical units,
   and any extra mask/scale behavior.
3. Only then overlay georeferenced valid cells with the
   original-derived BLD4 building polygons, including provider
   rights, temporal mismatch and vulnerability/insurance
   restrictions. No insurer exposure/TIV or CAT loss is
   admitted by the present header-only proof.
