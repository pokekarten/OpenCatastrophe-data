<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ESA WorldCover 2021 v200 N48E009 — original 4 KiB TIFF-header sample

**Date:** 2026-11-01. **Scope:** one exact reviewed HTTP Range request
against one 2021 v200 Map tile; no bulk download or original-byte persistence.

## Exact provider byte receipt

The [source-specific Actions run 41318851400](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41318851400)
executed `python -m scripts.probe_esa_worldcover_tiff_header_v0 --live`
after eight synthetic security/response tests and canonical source-contract
projection validation both passed.

- Provider: ESA WorldCover 2021 v200 public S3, exact `N48E009` Map tile.
- URL identity: `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N48E009_Map.tif`.
- UTC retrieval: `2026-11-01T14:59:09.837711+00:00`.
- Request: fixed HTTPS GET, `Range: bytes=0-4095`, identity encoding; no redirects.
- Response: **HTTP 206**, `Content-Range: bytes 0-4095/94851935`,
  transport media type `binary/octet-stream`, exactly **4,096 bytes**.
- **SHA-256 of the sampled 4,096 bytes only:** `a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529`.
- Frozen request SHA-256: `9c78290a293c275f70235c83f90a2725193f19fb7d21f0056ab666e108eb0797`.
- Reviewed access-contract SHA-256: `a3401c6a194608a5eb8972afddd8d53b874007c5a2357491d3373358fd57a1c0`.
- Execution code SHA-256: `3c4a0f9c4ba6208e7566fea9a7502af0329573b3d1a0a02cb1be6d5ee70f11f3`.
- Original TIFF prefix: **classic TIFF, little-endian**, first IFD offset
  **192 bytes**, **21** IFD entries completely within the 4 KiB sample.
- `external_bytes_persisted=false`, `raster_values_inspected=false`,
  `full_original_sha256_verified=false`, `crs_verified=false`,
  `cog_layout_verified=false`, `model_input_approved=false`.

The original file is 94,851,935 bytes according to this response. **The
4,096-byte sample digest is NOT a full original TIFF SHA-256.** TIFF magic
and an in-range IFD cannot by themselves validate Cloud-Optimized GeoTIFF
layout, EPSG:4326 georeferencing, pixels, 10 m resolution, the 11 WorldCover
class meanings, or building/insurance asset identity. No source bytes are
committed, logged or stored in Neon.

## Provider rights, reproducibility and narrow next step

Official source: [ESA WorldCover data access](https://esa-worldcover.org/en/data-access);
ESA WorldCover 2021 v200 is distributed under CC BY 4.0 with attribution.
The exact operation and its rights scope are defined in
`access/esa.worldcover.2021.v200.json`. This audit does not widen the
existing permissions for any other tile or bucket directory.

Next, independently review a tightly bounded, preselected **geospatial
raster window** using the same fixed source and explicit original-byte
receipt. Confirm full GeoTIFF metadata/CRS and coding with a suitable
geospatial library in a temporary, isolated CAT runner before promoting
any derived land-cover context to an exposure enrichment pipeline.
Retain the 2021 observation/v200 algorithm identity and do not infer
building counts or insured sums from land-cover class alone. Do not
relabel this single header proof as full CAT model readiness.
