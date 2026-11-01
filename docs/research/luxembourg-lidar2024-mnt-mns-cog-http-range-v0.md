<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT LiDAR2024: bounded national MNT/MNS COG HTTP-range capability

**Research only.** ACT publishes the national LiDAR2024 50 cm Digital
Terrain Model (MNT/DTM) and Digital Surface Model (MNS/DSM) as
cloud-optimized GeoTIFF files, approximately **37.4GB and 39.9GB**.
They may allow efficient small EPSG2169 windows without downloading a
1.70GB LiDAR source group's ZIP. This must be demonstrated, not assumed.

Official original catalogue: https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/

Exact officially listed original direct COG URLs:
- MNT https://download.data.public.lu/resources/bd-l-lidar2024-releve-3d-du-territoire-luxembourgeois/20241223-093912/MNT_Lidar2024.tif
- MNS https://download.data.public.lu/resources/bd-l-lidar2024-releve-3d-du-territoire-luxembourgeois/20241223-093912/MNS_Lidar2024.tif

## Small exact-source live capability gate

The stdlib-only script
research_runners/luxembourg_lidar2024_cog_range_capability_v0.py
contacts **only one of the two hardcoded exact official HTTPS assets**.
The HTTP request is `GET` with
`Range: bytes=0-4095` and `Accept-Encoding: identity`.
It accepts only **HTTP 206 Partial Content**, matching
`Content-Range: bytes 0-4095/<source-total>` and an actual TIFF/BigTIFF
magic header. If the server returns HTTP 200 (ignores the Range) it
rejects the response **without reading any body bytes**. Unexpected
redirects are rejected for independent provenance review. Total bytes
must be within a reasonable 10–120 GiB range. No bytes are persisted;
output is only file kind, declared original total size, first 4096-byte
fragment SHA256 and fail-closed flags. The digest is **NOT** a SHA256 of
the full official 37–40GB source.

```bash
python -m unittest tests.test_luxembourg_lidar2024_cog_range_capability_v0 -v
python -m research_runners.luxembourg_lidar2024_cog_range_capability_v0 --asset MNT
python -m research_runners.luxembourg_lidar2024_cog_range_capability_v0 --asset MNS
```

The dedicated GitHub Action runs nine synthetic HTTP boundary/safety
tests, then attempts one 4KiB origin fragment for each exact official
dataset. Any original source network redirect/timeout/ignored Range is
a **blocked provider capability**, not permission to download a 37–40GB
file. This step does not perform GDAL raster reads or certify internal
tiled GeoTIFF layout.

## Why this is the next useful height test

Previously merged Luxembourg pilots pinned:
- official LiDAR2024 index original: 10,905 tile geometries,
  SHA256 `3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8`;
- 250×250m central Luxembourg city ACT/EUBUCCO study, original
  LiDAR RTree 2 tile candidates and **2 true tile polygon intersections**
  under PR #941's exact source read;
- these two tiles use a **single approximately 1.70GB provider ZIP group**,
  as measured by the parallel original-link HEAD research.

If HTTP byte ranges are genuinely supported on both COGs, a
**separate** tested GDAL/rasterio reader can use bounded EPSG2169
window reads, verify per-raster CRS, resolution, nodata, vertical datum
and tile coverage, then derive a *proxy* 2024 DSM–DTM roof/ground height
distribution for manually selected ACT buildings. DSM includes trees
and other elevated surfaces; subtracting DSM–DTM blindly is **not**
an observed building height. EUBUCCO's estimated height provenance
must be distinguished from actual measured values. Neither the
coordinate axis, underlying independent source, property identity,
licences for downstream CAT use nor insurer replacement values are
approved by this byte-range capability gate.

**No full original GeoTIFF SHA, LAZ bytes, buildings, insured exposure,
hazard or model-input admission in this stage.**

## Actual original server result (2026-11-01)

The fixed-source GitHub Actions run [41313098014](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41313098014) succeeded. All **nine synthetic network-safety tests** passed, and the official provider responded to both strict requests with **206 Partial Content**, correct range `bytes 0-4095`, valid **BigTIFF** headers and exactly 4096 bytes of payload per source. These are *remote original fragment receipts*, not whole-file hashes or height validation.

| Official 2024 raster | Observed HTTP total size | Actual downloaded in this probe |
| --- | ---: | ---: |
| Digital Terrain Model **MNT** | **40,131,787,860 bytes** | **4,096 bytes** |
| Digital Surface Model **MNS** | **42,849,815,758 bytes** | **4,096 bytes** |

Both actual fragments reported SHA-256
`c2bceb795e786013f8d235e3aa3fe5707e75faf6a6be39b2a3d7da67113161c8`
(**fragment digest only**; common BigTIFF file header is not evidence the source rasters are the same). The server byte-range capability is therefore **verified** on these exact official paths, without downloading either full source. Next gate: a minimal fixed-area, range-only GDAL raster metadata/window probe with strict byte/window bounds, source CRS, nodata and coverage. Do not claim heights or roof membership before that succeeds.
