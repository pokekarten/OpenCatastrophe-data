<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT LiDAR2019: original ZIP central-directory byte-range audit (three selected sites)

**2026-11-05 — research only.** No point cloud, private address, insurance exposure or building identity is approved.

## Why this is a separate original-source step

Merged [PR #1305](https://github.com/pokekarten/OpenCatastrophe-data/pull/1305) independently verified the official ACT LiDAR 2019 450,512-byte CRS84 GeoJSON index, 1,287 source tile polygons, original publisher SHA-1 6fa8f0bd8afdf87bd175c9dab2d7b479b1b18874 and independently computed original SHA-256 2ad881f794e3699b83a0b312c84c2b0e467f21a7ec92bbf10a0c9a21aa4d1e6a. The same fixed, predeclared 100 × 100 m city and Berdorf windows select exactly **one Luxembourg-city and two Berdorf original ZIP tiles**.

Merged [PR #1315](https://github.com/pokekarten/OpenCatastrophe-data/pull/1315) successfully issued only HEAD and four-byte Range requests against those three real provider ZIPs:

| Site | Published archive source HTTP Content-Length bytes | HEAD / four-byte range |
| --- | ---: | --- |
| Luxembourg city | 449,275,061 | HTTP 200 / 206, ZIP PK0304 prefix |
| Berdorf first index polygon | 410,361,626 | HTTP 200 / 206, ZIP PK0304 prefix |
| Berdorf second index polygon | 374,704,804 | HTTP 200 / 206, ZIP PK0304 prefix |

These are HTTP metadata observations, not original full ZIP-byte SHA256 checks or verified classification of actual LAS points. The original official data resource is the [ACT LiDAR2019 catalogue](https://data.public.lu/en/datasets/lidar-2019-releve-3d-du-territoire-luxembourgeois/).

## Implemented strict source audit, without the 1.23 GB transfer

Runner: research_runners/lu_act2019_zip_central_directory_range_v0.py

The new runner first rechecks the identical official original index hash, CRS and exact fixed geographic windows before constructing any network request to a ZIP archive. It accepts only same-host HTTPS original tile paths, no redirects, no userinfo/query/fragment and exactly three unique source URLs.

For each selected source archive it performs at most:
- one HEAD request with the official reported original size;
- one byte-range GET for the last up-to-65,557 bytes, the complete maximum-width standard ZIP end-of-central-directory (EOCD) search interval;
- **if needed**, one additional byte-range GET for a bounded, at-most-1 MiB central-directory interval. For a small directory already within the tail, there is no second GET.

Every data response must be HTTP 206, with exact requested start/end and advertised whole-object total in Content-Range. Unknown HTTP Content-Encoding and non-matching response byte counts fail closed; HTTP 200 full-body responses to Range are rejected, without reading the body.

The end-of-directory and central directory are interpreted using the public standard ZIP structure, with explicit limits on member count, metadata size, single-disk standard ZIP, filename length, encryption and path safety. ZIP64/multidisk structures are **not blindly accepted** and require a separate bounded implementation or source review.

The only released member-derived attributes are **aggregate file-type counts**, compression method codes, archive-level declared member compressed/uncompressed byte totals, source-reported archive length, range traffic budget and a **SHA-256 of just the read ZIP central directory**. No original member name, tile URL, per-tile geographic point, ZIP asset, LAZ header, classified return or insurance object leaves the ephemeral runner. A central-directory hash is emphatically **not the full original ZIP SHA-256**.

Maximum byte-range data budget per tile is **65,557 + 1,048,576 = 1,114,133 bytes**; three combined at most 3,342,399 byte-range bytes (plus the verified 450,512-byte original index). All existing reference geometries, raw LiDAR tiles and individual assets stay out of Git and out of Neon.

Focused offline synthetic test suite: tests/test_lu_act2019_zip_central_directory_range_v0.py
Dedicated original-source workflow: .github/workflows/luxembourg-act2019-zip-directory-range.yml

## Evidence gate (hold pending actual original-source job)

Do not claim that the three provider archives contain LAZ rather than LAS, any count or precise point-cloud member size, or that any actually selected archive is a valid full ZIP until the exact-head hosted original-data run has succeeded and its aggregate output is inspected. A ZIP directory containing a reported LAZ filename **would still not prove that member payload is a valid LAZ**, that raw 2019 building-class-6 returns are present or that the LiDAR is independent of municipality VDL LoD2.2 data.

Original 2019 observation and 2026 GeoBase building-vintage differences, source reuse rights, vertical/horizontal datum, original data licences, independent evidence and insurer valuation are all separately blocked. No CAT exposure model admission.

**Actual metadata counts and source directory hashes: unverified until GitHub Actions original-source job.**
