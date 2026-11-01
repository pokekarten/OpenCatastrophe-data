<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg LiDAR2024: actual city candidate resource link & HEAD metadata

**Research-only / no original LAZ download.** This follows the real ACT
LiDAR2024 index read and verified 250 × 250m fixed-city candidate lookup
(10,905 national tile-index polygons; **2** candidates in the city pilot),
already in merged PRs #931 and #934.

## Why not immediately fetch the two LiDAR candidates?

Official ACT LiDAR2024 uses **500m point-cloud tiles packed into ZIP
groups of up to nine**, each potentially hundreds of MB or more.
Two indexed tile rows do **not** imply two independent ZIP group files,
nor that the original `DownloadLink` refers directly to a bounded LAZ.
The public dataset has >30 points/m² and classified ground (2), buildings
(6) and trees (3/4/5). Dates: February–April 2024 survey, not the 2023
summer aerial colourisation. Official source:

- https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/
- https://act.public.lu/fr/cartographie/lidar.html

## Implemented actual source-step

`research_runners/luxembourg_lidar2024_tile_group_link_preflight_v0.py`
reuses the exact source-index SHA-1 / SHA-256 validation from PR #931
and exact bounded 250 m source RTree selection from #934, then
**only internally** reviews the two candidate rows'
`Fichier`, `Dossier` and `DownloadLink` fields.

A safe original `DownloadLink` must be HTTPS with no userinfo,
query, fragment or nonstandard port, and match one of two fixed
provider resource patterns:

- `data.public.lu/{en,fr,de}/datasets/r/{UUID}` public catalogue resource;
- `download.data.public.lu/resources/bd-l-lidar2024-.../{timestamp}/lidar2024-cNNN-rNNN.zip`
  public, explicitly scoped original group ZIP.

Only for these reviewed patterns, the optional network step performs
**one HEAD request per distinct group URL**, without following redirects
and without reading any HTTP response body or ZIP/LAZ bytes.

Outputs are only: source-index prior SHA, number of spatial candidate rows,
count of unique group URLs, provider URL-type frequencies, blank metadata
field counts, HTTP status and HTTP Content-Length if supplied. No raw
original tile URL, UUID, file/folder/tile name, individual tile location,
original building geometry/ID or source-file byte is printed or stored.

A HEAD response, its redirect destination or its declared content length
is **not** original dataset validity or download authorization. If a
group is larger than 100 MiB, uncertain or lacks a validated size, the
current script never downloads it. The original GPKG index itself is
retrieved once to an ephemeral runner, already pinned to publisher
SHA-1 `3269aecb189271e7c3f86127c0e96f4e213557c9`
and prior observed SHA-256
`3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8`.

## Workflow

`.github/workflows/luxembourg-lidar2024-tile-head-preflight.yml`
is triggered on PR paths or manual dispatch. Uses source-exact HTTPS
index retrieval, pinned PyProj 3.7.2, eight isolated synthetic tests,
read-only GitHub permissions and HEAD-only tightly scoped official
resource metadata requests, with a short timeout and no redirect
following. No original provider tile/point-cloud data are downloaded,
committed, uploaded to artifacts or loaded into Neon.

```bash
python -m pip install pyproj==3.7.2
python -m unittest tests.test_luxembourg_lidar2024_tile_group_link_preflight_v0 -v
python -m research_runners.luxembourg_lidar2024_tile_group_link_preflight_v0 \
  --original-gpkg /private/pinned-lidar2024-ta.gpkg --probe-head
```

## Required before CAT exposure height calibration

1. Confirm exact original tile polygon intersection (RTree bbox only so far),
   metadata source identity and licensed URL/ZIP group size; never
   automatically follow an untrusted URL from source index data.
2. Acquire at most one **explicitly bounded**, licence-appropriate
   point-cloud subset/stream or already approved COG window, not an
   unlimited national ZIP; record original SHA and actual classifications.
3. Compare measured 2024 roof-class and ground-class elevation with
   pre-reviewed building footprints in a private bounded sample; distinguish
   trees, scan gaps, roof overhangs, ground elevation, vertical datum and
   acquisition epoch.
4. Only after manual scientific adjudication and independent control points
   consider calibrated physical heights and vulnerability classes.
   No insured replacement value, construction year or independent
   building identity has yet been established.

**Safety boundary:** No automatic CAT model input, no insurer exposures,
and no PostgreSQL/Neon database writes in this PR.

## Verified real-source result: large grouped archive, no point data fetched

On **2026-11-01**, the actual, exact-sha-pinned source index and official
public URL HEAD-only workflow passed, including **11 synthetic tests**:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41312731059 .

| Actual fixed-source observation | Verified |
| --- | ---: |
| Original national LiDAR index | 10,905 records, SHA-256 `3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8` |
| 250m × 250m city RTree candidate tile rows | **2** |
| Distinct allowlisted provider public resource links | **1** |
| First HEAD, public resource endpoint | **302** |
| Strictly validated redirect target | Official `download.data.public.lu` tile ZIP group |
| Second HEAD, direct resource | **200** |
| Direct ZIP resource **declared Content-Length** | **1,700,086,212 bytes** (about 1.70 GB or 1.58 GiB) |
| Full ZIP or LAZ bytes read | **0** |
| Actual point heights measured | **0** |

**Important distinction:** the initial first-hop response advertised
`Content-Length: 457`, which was the **302 redirect response**, not a
457-byte LiDAR archive. The corrected second **HEAD-only** request to the
strictly allowlisted publisher ZIP endpoint reports the **1.7 GB** archive
size. Both source rows point to the *same* original group resource; avoid
counting them as two downloadable ZIPs.

**Operational decision: NO 1.7 GB automatic download for a 250m research
window.** The measured HTTP response headers are strong metadata evidence
of transfer cost, but they do **not** constitute a downloaded archive
checksum or verification of compressed point-cloud content.

The next causal investigation is whether a **bounded spatial Cloud
Optimized GeoTIFF HTTP Range window** from the same official 2024 MNS/DSM
and MNT/DTM assets, or an ACT public profile-LiDAR service, can provide a
small, independently reproducible height sample. Validate server byte-range
behaviour, both raster CRSs, vertical reference, no-data masking, file
licences and source acquisition date; never infer physical buildings from
unfiltered DSM minus DTM without roofs/vegetation exclusion.
