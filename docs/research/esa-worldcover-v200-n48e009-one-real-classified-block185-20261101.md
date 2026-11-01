<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ESA WorldCover 2021 v200: original classified TIFF block 185 receipt

**Date:** 2026-11-01. **Scientific status:** original-byte research
sample only. Not full source coverage, independent ground truth,
insured asset or CAT model input admission.

## Exact original provider acquisition

The [one-block live GitHub Actions source run
41327465666](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41327465666)
completed all seven synthetic negative/positive security and TIFF
decode tests before the live original-source probe.

The source is the ESA WorldCover 2021 v200 **Map** layer, exact N48E009 tile,
via the reviewed anonymous official public S3 endpoint. Three exact
frozen HTTP Range GETs (each checked for HTTP 206, Content-Range,
length, MIME and original 94,851,935-byte source size) were requested
from the same object:

1. Original first 4,096 bytes `0–4095`, hash
   `a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529`
2. Original 10,368 TIFF offset/bytecount table bytes `13644–24011`, hash
   `7de08710b64cad350b81da83a81fcfc0c74f5285e20e28b0a3e42d19151885ba`
3. **Only one compressed original TIFF block**, index 185, internal
   (row 5, col 5), range `43278196–43334637`, length **56,442 bytes**;
   original compressed block SHA-256
   `526eb0819a9101a4e23df17dd70a040444190bb034528237fee29b415f9dd29a`.

The first two samples match their previously frozen original SHA-256
receipts and the exact block range matches the rechecked original
tile table. No caller-selected URL, extra range, other tile or
whole-object GET was permitted.

UTC retrieval: `2026-11-01T16:40:01.597244+00:00`.

## Native scientific validation and observed class results

Original TIFF coding in the sample is:

- `BitsPerSample=8`, unsigned integer, planar configuration 1,
  `SamplesPerPixel=1`.
- `Compression=8` (TIFF Deflate), `Predictor=1` (no horizontal
  differencing). The decoder also exercises predictor-2 handling
  with **synthetic tests** but the original here did not require it.
- Original compressed bytes decoded to **exactly 1,048,576** one-byte
  pixels, a single **1024×1024** internal raster block.
- Source decompressed pixel SHA-256:
  `5a7cd7ce34de5d054e0f134cd5823b6bac77314fd3a2431ee547fe40cc0b3b7e`.

All source pixel values belong to the ESA WorldCover 2021 v200
**Map** legend (0=nodata, 10 tree cover, 20 shrubland,
30 grassland, 40 cropland, 50 built-up, 60 bare/sparse vegetation,
70 snow/ice, 80 water, 90 herbaceous wetland, 95 mangroves,
100 moss/lichen). Exact original block histogram:

| Land-cover code | Class | Observed pixels |
| ---: | --- | ---: |
| 10 | Tree cover | 433,361 |
| 30 | Grassland | 400,059 |
| 40 | Cropland | 185,821 |
| 50 | Built-up | 29,214 |
| 60 | Bare / sparse vegetation | 52 |
| 80 | Permanent water bodies | 69 |
| **Total** | | **1,048,576** |

No other class including nodata was observed in this one block.
The predeclared **synthetic test coordinate** `(9.5°E, 50.5°N)`
maps into this internal TIFF block (local row 880, col 880).
The actual class at that one test-grid cell is **10, tree cover**.
This coordinate was used to choose a deterministic research sample,
not to represent an insured property or building.

Source and land-cover definitions:
[ESA WorldCover project](https://esa-worldcover.org/en/data-access);
[WorldCover 2021 v200 Product User Manual](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf).
Original product data are CC BY 4.0; observe attribution.

## Explicit remaining barriers

The source pixel block was never saved to Git, the conversation,
an artifact or a database. Only code, provenance hashes, source-byte
lengths and aggregate class counts were recorded.

- `source_bytes_persisted=false`,
  `raster_pixels_persisted=false`.
- `full_original_file_sha256_verified=false`;
  `full_cog_conformance_verified=false`.
- `real_building_exposure_matched=false`,
  `model_input_approved=false`.

A single class-50 built-up pixel is **not a particular physical
building, roof, valuation, sum insured, damage or peril-specific
vulnerability**. Its original observation/reference year is 2021,
not 2026. Pixel classification has product-level and locally
variable uncertainty, so a valid code is not ground-truth proof.

A later building enrichment stage must bind an independently
sourced, rights-verified building footprint with CRS and timestamp
and use full polygon/raster intersections with uncertainty flags.
Do not infer buildings, insured TIV, construction type or occupancy
from WorldCover pixels alone. Source data stay separate from
the Pokémon databases.
