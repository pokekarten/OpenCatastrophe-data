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

## Actual original publisher ZIP result — successful 2026-11-01

Actual GitHub Actions exact original-source run:
[41322016521](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41322016521).
All **11 synthetic fail-closed HTTP/ZIP tests** passed, followed by the
real official source-byte range experiment on only the fixed city group.

| Verified against real official original grouped archive | Actual result |
| --- | ---: |
| Official source total ZIP bytes from exact JSON/HEAD | **1,700,086,212** |
| Fixed official resource ID | `9bc4df35-4c5a-4d79-8a05-a2faadd6dab1` |
| Original group name | `Lidar2024_C020_R013` |
| Official original ZIP tail fetched | **65,557 bytes**, HTTP206 |
| Original standard ZIP central directory fetched | **549 bytes**, HTTP206 |
| **Original ZIP member count** | **9** |
| Original members with `.laz` suffix | **9** |
| Original members explicitly suffixed `.copc.laz` | **0** |
| Original members explicitly suffixed `.las` | **0** |
| Fixed city study tile `77000_75500` member name found | **YES, one member** |
| Original sum of 9 member compressed payload sizes (ZIP metadata, no payload read) | **1,700,085,236 bytes** |
| Actual ZIP/LAZ data payload obtained | **0 bytes** |
| Actual LAS header, COPC VLR, classes 2/5/6 observed | **NO** |

Only **66,106 actual original ZIP bytes** were retrieved instead
of the whole **1.70GB** source archive; access to the central directory
is now verified through two exact original HTTP206 ranges. Original
member names/offsets were parsed transiently but **not exported** in
the source report. The same small original source check confirms that
the single required city tile is really an internal LAZ archive member.

**Important limitation:** the publisher describes classified COPC data,
but these member *filenames* end in `.laz`, **not** `.copc.laz`.
Neither ordinary/CO PC LAS format, presence of individual class-6 points,
coordinate accuracy, class histogram nor scientific classification
accuracy can be inferred from ZIP metadata. Do not convert the
suffix into a classification fact. The publisher SHA1 is still metadata,
not an independently rehashed archive digest. The real next stage is a
*single member* ZIP local-header range-read with compression-method and
size gates and **bounded decompression** (or raw member first bytes for a
STORED entry) to inspect only the LAS/COPC header and classification
schema. A member may be >100 MB, so never proceed to full member
retrieval without a separate capped budget and rights review.

The failed first provider attempt was due to querying uData's
display-oriented `size` rather than its numeric `filesize`
field. It was corrected to reuse the already validated #987
provider metadata contract; the final exact-source run succeeded.
