<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WorldCover 2021 v200 N48E009: original TIFF tile-array byte proof

**Scope:** one separately reviewed exact 10,368-byte metadata range, no
compressed pixel-block body, raster class, original full-file SHA-256,
COG conformance or insurer CAT model input admitted.

## Verified original provider response

[GitHub Actions run 41326835655](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41326835655),
source job `reviewed-tile-tables`, executed the 7 focused deterministic
negative/positive tests, validated the canonical source access projection,
then performed exactly one original 2021 v200 N48E009 WorldCover
public S3 request:

- UTC: `2026-11-01T16:32:23.599696+00:00`
- Frozen request: `GET`, `Range: bytes=13644-24011`
- HTTP **206**; `Content-Range: bytes 13644-24011/94851935`;
  `Content-Type: binary/octet-stream`; body **10,368 bytes**
- SHA-256 of **only these original 10,368 bytes**:
  `7de08710b64cad350b81da83a81fcfc0c74f5285e20e28b0a3e42d19151885ba`
- Frozen request hash:
  `19298f9120433f4bfcae097d58b41e8aec7912d19109487d6088607edc81d462`
- Source-access contract SHA-256:
  `e9fef192cdf560511a527b9e57df55a81cec6e06294f54cb9b7c21b1d78ef3a4`
- Source code SHA-256:
  `ec79aeed1209de9cd7957e059c38601200d21a18b52ff78ff003d8e54bb1c6c0`

## Parsed and quality-checked tile table values

The sample was split into two 5,184-byte original TIFF LONG32
arrays, 1,296 offset/count pairs; all 1,296 pairs have a nonzero
in-source byte range. **Zero** sparse/missing tile entries and **zero**
compressed interval overlaps were detected. All bytecounts were positive
and bounded, ranging **3,023 to 85,725 bytes**; aggregate reported
compressed block bytes: **59,172,345**. A valid TIFF table alone is not
evidence that all blocks are decodable.

For the single predeclared synthetic geo query at `(9.5°E,50.5°N)`,
the header-only mapping identified internal TIFF block row 5,
column 5, row-major block index **185**. Its actual source metadata
specifies a **56,442-byte** compressed segment at original file
bytes **43,278,196–43,334,637 inclusive**.

This is a metadata-only description for possible future sampling.
`selected_block_bytes_downloaded=false`,
`raster_pixels_downloaded=false`,
`raster_classes_verified=false`,
`source_bytes_persisted=false`,
`source_wide_sha256_verified=false`,
`model_input_approved=false`.

## Next separately reviewed step

Freeze an exact one-block GET **only after reviewing** the source
TIFF compression and predictor tags (the original first 4 KiB
header still defines those), as well as geospatial/temporal lineage
and the approved one-block byte limit. The only candidate exact
block Range is `bytes=43278196-43334637`, length 56,442,
against the same versioned ESA WorldCover N48E009 object.

An original compressed block must be strictly authenticated to
its metadata sample identity, safely decompressed with a maximum
uncompressed-byte bound, checked against TIFF sample coding
and allowed WorldCover 2021 class code set, and discarded
after emitting aggregate counts/quality evidence. The bytecount
table digest alone does not prove full-source immutability,
classification correctness, ground truth, insured exposure,
pixel-level uncertainty or CAT-model admission.
