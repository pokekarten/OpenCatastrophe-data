<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original ACT LiDAR 2019: bounded ZIP central-directory preflight of three official tiles

**2026-11-04. Research and access only — no original point clouds, independent building ground truth or insurance exposure admission.**

## Why ZIP central directories

Merged [PR #1305](https://github.com/pokekarten/OpenCatastrophe-data/pull/1305) pinned the complete official original ACT LiDAR 2019 tile index (450,512 bytes, 1,287 CRS84 tile polygons, SHA256 \`2ad881f794e3699b83a0b312c84c2b0e467f21a7ec92bbf10a0c9a21aa4d1e6a\`). In two predeclared equal-area 100 × 100m windows, exactly **one** original index polygon intersects Luxembourg-city and **two** intersect Berdorf.

Merged [PR #1315](https://github.com/pokekarten/OpenCatastrophe-data/pull/1315) performed actual source HTTP HEAD and four-byte Range checks of all three selected ZIPs. In original index order, city original HEAD Content-Length was **449,275,061** bytes and Berdorf original lengths **410,361,626** and **374,704,804** bytes. All three returned 200 to HEAD, 206 to Range bytes 0–3, matching sizes and ZIP local signature PK0304. These lengths **do not** prove complete archive bytes, source hashes or observed point classes.

The [PKWARE ZIP APPNOTE format](https://github.com/cysp/libzip/blob/master/docs/appnote.txt) places a classic End of Central Directory (EOCD) near the end of a ZIP file, preceded by central-directory records describing archive members. [HTTP Range and Content-Range](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests) permit validating a bounded section of a server resource by HTTP 206; HTTP 200 on a Range request is **not** range delivery.

## Implementation and fail-closed envelope

- Research source: \`research_runners/lu_act2019_three_zip_directory_range_v0.py\`.
- Synthetic tests: \`tests/test_lu_act2019_three_zip_directory_range_v0.py\`.
- Original-data CI: \`.github/workflows/luxembourg-act2019-three-zip-central-directory.yml\`.

The tool retains all full-original-index SHA/source-window checks and chooses **exactly three** immutable source ZIP endpoints from the original GeoJSON rather than user-provided URLs. It enforces the **previously observed HTTP-reported** ZIP total lengths per site and a strict publisher-origin and no-redirect policy. For each file it makes an existing HEAD/four-byte prefix check; then retrieves only the final **at most 65,557 bytes** to locate a classic ZIP EOCD (22 bytes + maximum 65,535-byte ZIP comment) and a separate central-directory Range request only if necessary. Central-directory read bound is **262,144 bytes** and entry count bound is **256**. Any server HTTP 200, wrong Content-Range, changed origin/encoding, truncated response, unsupported ZIP64/split-disk offsets or an over-budget central directory is blocked. Only known source-valid stages and no raw URL/source strings appear in errors.

A successfully parsed **classic ZIP central directory** may reveal only **aggregated** member types (.laz/.las/.xml/.txt/.json/.prj/other), member counts, compression-method codes, encryption flags and metadata-reported compressed/uncompressed byte totals. It never emits original archive member filenames, filesystem paths or compressed member bytes. Archive member data, classified point returns, raw building geometries or real exposure coordinates are never fetched.

**Important:** This is a read-only central-directory survey, not full ZIP integrity (no original full source SHA256 or extracted CRC), not a LAS/LAZ header inspection, not proof that the provider's 2019 ALS LiDAR observations are independent from VDL Bati3DVDL, and not a scientifically/legally admissible CAT exposure.

## Original results

**Do not populate member counts or archive formats until actual source GitHub CI passes.** If the actual official ZIPs use ZIP64, a spanned archive, unexpected source syntax or larger metadata than the budget, the job will fail closed and the result must be documented as a source format discovery rather than by loosening constraints to force green.

Scientific downstream gates remain: original tile full SHA256, actual LAS/LAZ header and CRS/datum/classification verification, 2019 vs 2026 sensor/pipeline ancestry, blinded holdout and rights review. Model/insured-asset/TIV/claims admission remains false.
