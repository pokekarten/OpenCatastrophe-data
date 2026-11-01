<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg LiDAR2024: bounded original COG BigTIFF IFD metadata

**Research only.** Official Luxembourg ACT LiDAR2024 MNT (ground) and
MNS (surface) original cloud-optimized BigTIFF sources passed exact
4,096-byte HTTP 206 reads in merged PR #945. Publisher response sizes:
**40,131,787,860** and **42,849,815,758** bytes. The prior SHA-256
`c2bceb795e786013f8d235e3aa3fe5707e75faf6a6be39b2a3d7da67113161c8`
pins **only the first 4KiB fragment** of both originals, not entire files.

## Causal improvement

`research_runners/luxembourg_lidar2024_bigtiff_ifd_v0.py` reads
original BigTIFF IFD metadata using Python's standard library and two
**exact official HTTPS source URLs only**, inherited from #945.

- Each source request is **one exactly aligned 4KiB HTTP Range GET**;
  only HTTP **206** with exact Content-Range and declared original
  10–120GiB source size is accepted. HTTP 200 and redirects are
  rejected before reading any response body.
- Strict limit: **16 distinct 4KiB requests = 65,536 bytes total per
  source**, and no metadata pointer beyond the first **1 MiB**.
  Inconsistent source length, wrong first-page SHA256, malicious BigTIFF
  pointer, unexpected tag type or duplicate tag fails closed.
- Parse original BigTIFF header and first IFD for image width/height,
  internal tile width/height, tile array cardinality, compression code,
  bit depth, GeoTIFF pixel scale and declared projected EPSG **2169**.
- Print only small aggregate source metadata. No original TIFF pages,
  tile pixel values, coordinates, building IDs, source archive,
  insurance exposure or CAT model input is exported/persisted.
- **11 fully synthetic unit tests**; narrow original-source workflow
  `.github/workflows/luxembourg-lidar2024-bigtiff-ifd.yml`
  checks MNT and MNS separately on disposable GitHub runners.

```bash
python -m unittest tests.test_luxembourg_lidar2024_bigtiff_ifd_v0 -v
python -m research_runners.luxembourg_lidar2024_bigtiff_ifd_v0 --asset MNT
python -m research_runners.luxembourg_lidar2024_bigtiff_ifd_v0 --asset MNS
```

The first IFD may describe a reduced resolution overview rather than
full national base raster. This probe must not infer alignment or
source pixel coverage if the original IFD does not support the
tiled/GeoKey assumptions. A passing metadata gate is **not** an
actual DSM–DTM height calculation.

## What remains

Need independently resolve actual full-resolution IFD selection,
geotransform alignment, vertical reference, no-data, tree canopy
versus roofs and bounded tile response sizes before acquiring any
real source heights. Later manually adjudicate ACT roof features with
terrain/building classes; the derived property height is not insured
replacement value or construction year.

Official catalogue:
https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/

Original URL and 4KiB source receipts:
`docs/research/luxembourg-lidar2024-mnt-mns-cog-http-range-v0.md`.
