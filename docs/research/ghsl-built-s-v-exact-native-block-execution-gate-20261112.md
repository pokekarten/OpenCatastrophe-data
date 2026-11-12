<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GHSL BUILT-S / BUILT-V R2023A — original native E2020 block proof gate

**2026-11-12 design and executable implementation. The first new
original-provider block run is NOT claimed until its main-branch Actions
logs are inspected.** This is a read-only research-only original-value
sample candidate, not source/model admission.

## Original source and exact bounded retrieval contract

Source: European Commission JRC
[GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php)
(square metres built surface per gridded source cell) and
[GHS-BUILT-V R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buV2023.php)
(cubic metres modelled built volume per source cell). These are two
different derived products, not two independent observations of the same
quantity. Their original JRC
[surface licence notice](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/copyright.txt)
and [volume licence notice](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_V_GLOBE_R2023A/copyright.txt)
require CC BY 4.0 attribution and modification disclosure. No raw
original raster bytes or source location values are redistributed.

The [original 32 KiB source receipts](ghsl-built-s-v-original-native-32k-header-20261112.md)
are already pinned with SHA-256, true little-endian UINT32/Deflate
TIFF coding, EPSG:4326, 512×512 native block geometry, 2020 epoch
and 30-arcsecond angular pixel pitch. Two fixed, directly reviewed
S3 objects are accessed anonymously, with **exactly two sequential
HTTP Range GETs per product**, no retries, redirects, pagination or
bulk sweep:

| | BUILT-S surface | BUILT-V volume |
| --- | ---: | ---: |
| Reviewed original total TIFF bytes | 173,085,842 | 187,376,914 |
| Exact required header Range | `0–32767` (32,768 B) | `0–32767` (32,768 B) |
| Original 32 KiB SHA-256 | `002c21c644073b889df87135a95c902eecf8859b572458a021341ae5c90b35ea` | `7e61b8056273ea0f2fa84913c3458da6d5c38f52f41881af20a42b0d966e76bd` |
| Native block index | 809 | 809 |
| Native compressed block Range | `73699060–74222432` (523,373 B) | `80549811–81120367` (570,557 B) |
| Maximum decoded block bytes | 1,048,576 | 1,048,576 |
| Max original bytes permitted per request | 600,000 | 600,000 |

Each request must have HTTP **206**, the exact Content-Range
`bytes start-end/full-object-size`, exact Content-Length and a
reviewed TIFF/octet-stream MIME; any changed host, path, byte count,
compression, original header hash or full object length blocks the run.

## Independent scientific sample method

`scripts/probe_ghsl_built_native_original_block_v0.py` first invokes
the SHA-pinned original TIFF/CRS/table verifier. Only on success does
it request the preselected original compressed block, decode it
in memory via Python's bounded TIFF Deflate algorithm to exactly
`512*512*4` unsigned 32-bit bytes and inspect the **same fixed
32×32 native raster cell window** in the central Germany source-block
region. No other tiles, source dates, locations or caller-selected
areas are allowed. The output is limited to source-byte SHA-256s,
the decoded-block SHA-256, the fixed-window uint32 SHA-256 and
aggregate counts/sums/min/max values.

**No individual pixel array is output, saved in Neon, logged in
Actions or added to the public repository.** Any value equal to
`2^32−1` is reported separately as a *candidate* NoData sentinel:
the code intentionally sets
`uint32_max_nodata_semantics_approved=false`. Native raster
units are interpreted only according to the publisher's
product-specific definitions, not as individual buildings,
ground surface square metres, TIV, hazard depth or flood/wind damage.

The main-only source workflow is
`.github/workflows/ghsl-built-native-original-block.yml`.
On untrusted pull requests it performs **synthetic/offline
tests only**; on the reviewed main branch, a source-specific
push or explicit manually dispatched run tests each fixed original
product once in a transient GitHub runner. No credentials or signed
URLs are required. No original artifacts are uploaded.

## Interpretations and next gate

The exact full source TIFF file SHA-256 is not obtained; the original
source block SHA-256 will be measured during the first successful
live run, not guessed. The pixel values are **not** yet independently
checked against ground truth, and one historical 2020 epoch is not
a current building survey. Source spatial reference degrees,
uncertainty, source scale and NoData meanings must be reviewed
before use in a scientific CAT exposure model.

After **actual verified main-run success**, stage the aggregates into
the *separate* insurance research Neon source-sample table as
`sample_kind=observed_values`, with the literal original compressed
block digest from the completed run. Verify the canonical JSONB
sample hash and change only the strictly reviewed
`actual_sample_state` to `collected_rights_cleared`.
All model-admission and source-file/raw-byte persistence flags remain
false. If either original read is unavailable or mismatched, document
**BLOCKED** and do not stage fabricated or synthetic values as original.
