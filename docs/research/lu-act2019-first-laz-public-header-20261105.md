<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT Luxembourg LiDAR2019: first LAZ member public LASF header, no point data

**2026-11-05 — immutable original-source research preflight; NOT exposure, hazard, vulnerability or insurer/insured asset admission.**

## Starting evidence already on main

The existing original source runners fully hashed ACT 2019 GeoJSON tile index, 450512 bytes, 1287 native CRS84 tile polygons and SHA256 2ad881f794e3699b83a0b312c84c2b0e467f21a7ec92bbf10a0c9a21aa4d1e6a. Two predeclared 100m squares selected one Luxembourg-city and two Berdorf ZIP source archives.

[Existing original central-directory evidence](https://github.com/pokekarten/OpenCatastrophe-data/blob/main/docs/research/lu-act2019-three-zip-central-directory-range-20261104.md): each original ZIP has exactly 9 LAZ-suffixed member directory entries with ZIP compression method 8 (DEFLATE), no encryption flag; all three original central-directory metadata SHA256 fingerprints are already pinned in research_runners/lu_act2019_three_zip_directory_range_v0.py. Those ZIP directory entries do **not** prove actual valid LAZ payloads or classified LiDAR observations.

## New strictly bounded original member challenge

Research runner: research_runners/lu_act2019_first_laz_public_header_v0.py

1. Check the exact full official original index SHA256 and predeclared geometry windows, selecting only the previously fixed three archives. No arbitrary source URLs.
2. Reuse the canonical GitHub-verified ZIP HEAD, 4-byte PK signature, end-of-directory and central-directory SHA256/size source pin checks.
3. Re-read the immutable original central bytes, select the first original LAZ-suffixed member in each archive, and validate ZIP method 8, offsets, source local header and original member filename equality without logging original names/identifiers.
4. Request only the 30-byte ZIP local header and bounded local name/extra bytes via exact HTTP 206 Content-Range. Never follow unapproved redirects or accept a full HTTP 200 payload as a byte-range response.
5. Fetch at most **16384 bytes of ZIP DEFLATE-compressed member prefix**. Use Python zlib with raw DEFLATE wbits=-15 and hard **111-byte maximum uncompressed LAS header output**. This is always below the minimum LAS public header size of 227 bytes. Decode no point record, spatial coordinates, raw producer text or LAS VLR payload.
6. Require actual LASF signature and coherent public LAS 1.2/1.3/1.4 version, header-size, point-data offset, VLR count, point-format code and point-record length. Do not invent or reinterpret invalid source fields.
7. Aggregate only reviewable structural header numbers, explicit non-admission flags and a declared first-member original ZIP order per site. No full ZIP/LAZ acquisition, no individual member name/URL, no classified point data, no insurance or database write.

Offline synthetic tests: tests/test_lu_act2019_first_laz_public_header_v0.py

Original-source GitHub Actions workflow: .github/workflows/luxembourg-act2019-first-laz-public-header.yml

## Actual source-result gate

No real 2019 LAS version, point format or first-member signature is claimed until this exact-head original-source GitHub Actions workflow passes and its source output is checked.

A successful result would show **only** that the first original LAZ-suffixed member of each source ZIP starts with a coherent public LAS header after one layer of ZIP Deflate decompression. It would NOT prove full member ZIP CRC/SHA256, valid remaining LASzip compressed content, point density, point class 6 buildings, 2019/2026 building existence, geodetic CRS/datum or independent VDL original aerial source.

The 2019 original ZIP bytes in full, any point and class records, underlying flight/sensor genealogy, city municipality LoD2.2 licence, insured exposure identity and CAT model input remain **unverified/not admitted**.
