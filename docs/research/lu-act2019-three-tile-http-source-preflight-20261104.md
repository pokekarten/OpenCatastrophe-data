<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT LiDAR 2019: three selected original tile ZIP HTTP source metadata

**2026-11-04, original-source research only; not a building/insurance data admission.**

## Research scope

Merged PR #1305 verified the ACT full original 450,512-byte LiDAR 2019 index, 1,287 CRS84 tile footprints, source-published SHA1 \`6fa8f0bd8afdf87bd175c9dab2d7b479b1b18874\` and computed SHA256 \`2ad881f794e3699b83a0b312c84c2b0e467f21a7ec92bbf10a0c9a21aa4d1e6a\`. Against two previously fixed 100 × 100m public research windows, exactly **one** index tile intersects Luxembourg-city and **two** index tiles intersect Berdorf.

The official [ACT LiDAR 2019 dataset](https://data.public.lu/en/datasets/lidar-2019-releve-3d-du-territoire-luxembourgeois/) lists 1,297 main provider files, including many individual ZIP resources hundreds of megabytes long (e.g., catalogue examples 348.7 and 431.9 MB), and a CC0 licence label. The **tile index does not contain per-tile source ZIP SHA256 bytes**. A successful 450kB index check therefore cannot establish that individual 300+ MB point-cloud files remain accessible, have the expected format, or correspond to the original 2019 observations. Neither the archive bytes nor classified LAS/LAZ points have yet been fully examined for these sites.

## Implemented constrained original-source access challenge

Runner: research_runners/lu_act2019_three_tile_http_preflight_v0.py

1. Before network IO, accept only the exact fully verified ACT index **with pinned full source SHA1, SHA256, size, 1287 source features**, and the exact two published EPSG3035 100m windows, using the existing upstream validator.
2. Select exactly **three** unique provider ZIP URLs via **positive-area intersection** of index tile polygons with the frozen city/Berdorf research windows. Revalidate exact HTTPS publisher origin, approved path, .zip filename, no user-info, query, fragment or unreviewed percent-encoding.
3. For each approved URL, make one HEAD request, limit to **15 seconds**, enforce a positive reported full Content-Length under **1.5GB**.
4. Only if a bounded HEAD size is present, send one Range request for bytes **0–3**. Accept HTTP 206 and matching \`Content-Range: bytes 0-3/N\` as positive range-support metadata, and read **only four bytes** to test the ordinary ZIP local-header signature. Reject redirects; an HTTP 200 response to Range is **not** considered byte-range support.
5. Publish only an ordered per-site set of HTTP statuses, publisher-reported source ZIP Content-Length and a few boolean format/range flags, with **no tile URL, original filename, per-tile coordinates, exact geometry, original ZIP, raw point cloud or person-level data in GitHub logs/artifacts**.
6. HTTP failure or missing Content-Length is represented as **unverified**, never converted to a positive access claim. A 4-byte ZIP signature, HEAD content length or HTTP 206 response is **NOT a full archive SHA256, LAZ-content, classification, height, site coverage or rights proof**.
7. No GitHub Actions artifacts and no Neon/database writes. Offline tests use mocked HTTP responses and invented synthetic URLs, with no network.

Official original index:
https://download.data.public.lu/resources/lidar-2019-releve-3d-du-territoire-luxembourgeois/20200225-183349/lidar-urls.geojson

Workflow: .github/workflows/luxembourg-act2019-three-tile-http-preflight.yml

**Actual three-tile remote metadata results:** only assert after successful original-source workflow on the reviewed branch. Do not infer results from unrelated published example ZIPs.

## Scientific follow-up dependent on this preflight

If all three source ZIPs appear accessible and support reliable byte-range delivery, choose a **separately rights-reviewed, fully byte-verified single original tile first** in an isolated ephemeral environment. Only then inspect ZIP central directory, actual LAS/LAZ member types, EPSG2169 axis/datum, LiDAR classification \`6\` building points and source QA. A small 100m crop derived from LAZ does not prove underlying VDL Bati3DVDL-independent ground truth: first compare original capture periods, upstream flight/sensor lineage, roof-vs-ground footprints, and the historical 2019/2026 time mismatch. No insurer building identity, TIV, risk attribution, vulnerability or CAT model input is admitted in this stage.

**Pinned-admission gates:** actual 2019 ZIP bytes are not present in Git, each original tile ZIP full SHA256 remains unverified, and scientific/rights/independent control/model-input flags remain false.


## Measured official original-source HTTP results (2026-11-04)

**GitHub Actions real-provider run:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41903085731, **success**, 13/13 fictional no-network regression tests passed. Pinned original 450512-byte GeoJSON SHA256 stayed \`2ad881f794e3699b83a0b312c84c2b0e467f21a7ec92bbf10a0c9a21aa4d1e6a\`. After original GeoJSON validation, exactly three source ZIP URLs were selected by the same two fixed EPSG3035 research windows. The log contains **zero original individual tile URLs or coordinates**.

| Predeclared public study site / candidate order | Server-reported full source ZIP Content-Length (bytes) | HEAD status | 4-byte Range status | Exact range-to-HEAD total | ZIP local header bytes |
| --- | ---: | ---: | ---: | --- | --- |
| Luxembourg-city, one index tile | **449275061** | 200 | 206 | matches | PK0304 |
| Berdorf, first index tile | **410361626** | 200 | 206 | matches | PK0304 |
| Berdorf, second index tile | **374704804** | 200 | 206 | matches | PK0304 |

The sum of HTTP **server-advertised** source lengths is 1234341491 bytes (approximately 1.23 decimal GB), *not an independently hashed or acquired 1.23GB data receipt*. The first four bytes of all three resources match the common ZIP local-file-header signature, and each valid HTTP 206 Content-Range advertises the same total length as its HEAD response. A successful source-header preflight makes the next targeted source acquisition possible; it **does not** validate whole-file ZIP CRC, source SHA256, LAS/LAZ file signatures, 2019 point classification, point cloud spatial coverage, epoch, or building identity.

The code is strictly limited to HEAD and a four-byte Range GET per official source ZIP; no full raw point-cloud ZIP has been downloaded, no data have been written to a database and nothing has been admitted to an insurance exposure/hazard/vulnerability model. **Actual original source metadata checks have passed; ZIP content and rights gates remain pending.**
