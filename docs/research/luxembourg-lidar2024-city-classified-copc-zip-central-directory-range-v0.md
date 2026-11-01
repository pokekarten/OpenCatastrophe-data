<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg: original ACT LiDAR2024 city-group ZIP central directory without a 1.70GB download

**Research-only. Original source point cloud and building height not read, no CAT admission.**

## Frozen source

Official ACT classified LiDAR2024 group resource ID
`9bc4df35-4c5a-4d79-8a05-a2faadd6dab1` corresponds to the original
tile-index group `Lidar2024_C020_R013` covering the 100m Luxembourg city
study (known public original tile name `77000_75500`, via #975).

Actual official uData resource JSON and HEAD successful in merged #987:
- Official [resource](https://data.public.lu/en/datasets/r/9bc4df35-4c5a-4d79-8a05-a2faadd6dab1).
- Publisher-reported SHA1 `f8650c5eee38d941921199a0c6e1f64b985c9b34`,
  **not verified against full original ZIP bytes**.
- Original file `lidar2024-c020-r013.zip`, numeric HTTP HEAD byte size
  **1,700,086,212**; official HTTPS `download.data.public.lu/resources/`
  source path. Neither original ZIP contents nor individual COPC files
  were previously read.

## Purpose and strict byte budget

The 2024 source MNS+MNT raster building-height proxy includes vegetation,
and the next useful quality gate requires building-class points (class 6)
versus tall vegetation (class 5) versus ground (class 2). The
city-pointcloud group ZIP alone is **1.70GB**; a full transfer is
not justified to locate the one predeclared 500m tile.

`research_runners/luxembourg_lidar2024_city_copc_zip_directory_range_v0.py`
performs exactly:

1. An original fixed official public-resource JSON GET (<=256KiB),
   requiring exact resource UUID, publisher SHA1 metadata from the merged
   source receipt, **same whole original advertised size**.
2. A HTTPS HEAD on the direct official group ZIP, exact 1,700,086,212 bytes.
   No arbitrary URL, user input, query or redirected origin.
3. A single ZIP end-of-central-directory HTTP **206** fixed range of
   **65,557 bytes** at the end of that original ZIP; validates
   `Content-Range` and ZIP EOCD signature, disk count, comment length,
   member count, central-directory length and offset. Rejects HTTP200
   BEFORE reading any giant body bytes.
4. If ordinary (non-ZIP64) central directory <=256KiB, exactly one
   additional HTTP **206** range fetch of *only* that directory.
   Bounded syntactic ZIP central-directory parsing checks at most
   100 members, paths/traversal, encryption, sizes and compression
   headers, and reports only total declared `.laz`, `.copc.laz`,
   `.las` counts and **boolean/count** of the already-public fixed
   city tile filename reference. No original internal member filename
   or file bytes are printed.
5. If publisher uses ZIP64, encrypted members, non-206 transfer,
   inconsistent metadata or huge directory, the probe **fails closed**.
   It does NOT automatically extend byte budgets, use an alternative
   source, or download the 1.70GB original archive.

Estimated maximum original ZIP transfer is <0.33MB (plus bounded
resource JSON). This does NOT validate the archive's full SHA1/256,
CRC of any original LAZ member, LAS point classification, vertical
datum, accuracy, license approval or building height.

Dedicated workflow has eleven synthetic ZIP/HTTP tests and one live
publisher original-source range run. Unambiguous original provider
results must be appended here after actual execution, never guessed.

## Scientific downstream gate

After a successful bounded directory read, verify whether the
`77000_75500` member is COPC LAZ or ordinary LAZ, check remote ZIP
member range addressing and a separate **bounded decompression budget**;
then read only needed classified points in temporary authorised storage.
LiDAR producer class 6 roof and class 5 tree labels are **not
scientifically independent** of 2024 MNS: an external manual holdout
is needed before claiming an accurately measured building height or
accepting it into insurer exposures. No original pixels, points,
insured TIV or CAT model-input rows are admitted by this audit.
