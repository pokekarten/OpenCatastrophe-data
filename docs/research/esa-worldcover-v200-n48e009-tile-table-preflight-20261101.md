<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ESA WorldCover 2021 v200 N48E009: source TIFF tile-directory preflight

**Date:** 2026-11-01. **Scope:** original provider's *existing*
4,096-byte TIFF header only; no tile directory or raster pixel acquisition.

## Exact observed original TIFF layout

In [fixed original-source audit run 41326367000](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41326367000)
the source-side bounded parser read the original
`https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N48E009_Map.tif`,
request `Range: bytes=0-4095` only, and passed 14 existing
and four new synthetic tests.

- UTC original source request: `2026-11-01T16:26:54.654103+00:00`.
- HTTP 206; original object length from Content-Range: **94,851,935 bytes**.
- Original 4,096-byte sample SHA-256 unchanged:
  `a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529`.
- First-IFD count 21, first-IFD offset 192; image 36,000 ×
  36,000, 1 sample per pixel, 1,024 × 1,024 internal TIFF blocks,
  compression tag 8.
- Computed block grid **36 × 36 = 1,296** blocks; TIFF tag
  `324` TileOffsets and tag `325` TileByteCounts are both
  type LONG32 with **1,296** original-value entries apiece.
- Original-file *directory byte ranges* decoded from the **first-IFD
  pointers only**:
  - TileOffsets: **13,644–18,827** (5,184 bytes).
  - TileByteCounts: **18,828–24,011** (5,184 bytes).
- The two directory ranges are adjacent, so a distinct future
  exact `Range: bytes=13644-24011` would cover **10,368 bytes**
  in total, without provider crawling or full-object acquisition.
- `table_original_bytes_downloaded=0`;
  `tile_offsets_validated=false`,
  `individual_block_bytecounts_validated=false`,
  `tile_pixels_downloaded=false`,
  `model_input_approved=false`.

The actual offset/bytecount array contents have **not** been fetched,
parsed or validated; the first-IFD *addresses* and expected sizes
are all that this source receipt proves. An offset found in a source
TIFF is never itself an authorization to retrieve arbitrary bytes.

## Next narrowly reviewed source access

A separate reviewed probe may request **only** the exact 10,368-byte
range `bytes=13644-24011` from the same pinned WorldCover 2021 v200
N48E009 object, provided the canonical access contract is
independently updated beforehand to allow that specific one-shot
metadata request.

Its validation must require HTTP 206, original-object identity,
Content-Range and Content-Length, no redirects and no body content
beyond 10,368 bytes. Verify both arrays have exactly 1,296 positive
aligned/in-bounds offset/count entries and evaluate overlaps and
bytecount size limits before authorizing **one independently frozen**
compressed pixel block in a later PR.

The 10,368-byte directory sample SHA-256 would **not** be the original
94.85 MB file checksum and neither a directory pointer nor a metadata
sample certifies a usable COG, imagery/pixel sample, land-cover class
or insurance model exposure. Source bytes must remain transient,
with only minimal verified metadata and hashes logged.
