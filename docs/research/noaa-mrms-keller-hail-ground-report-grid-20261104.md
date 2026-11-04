<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MRMS MESH at a real 2021 hail report: Keller / Tarrant County (2026-11-04 preflight)

**Purpose:** Move beyond proof that historical NOAA MRMS GRIB2 bytes are accessible to a **positive hail-observation case** that can support a future actual physical-field validation. This document does **not** demonstrate meteorological skill, observed hail footprint, property-level exposure, insured damage, source admission or CAT-model fitness.

## Independent real-world event reference

- [NOAA/NSSL Warn-on-Forecast case study](https://www.nssl.noaa.gov/projects/wof/casestudies/hail-oktx-apr2021/): April 28, 2021 southern Plains supercells struck San Antonio, Fort Worth and Norman with damaging large hail.
- [NCEI Storm Events report `956694`](https://www.ncei.noaa.gov/access/storm-events-database/event-details/956694) gives Keller Alta Vista, Tarrant County, Texas, reported `Hail` magnitude **2.50 inches = 63.5 mm**, approximate location **32.92°N, −97.29°**, and **2021-04-28 19:37 in fixed CST-6 labeling** (equivalent **2021-04-29T01:37:00Z**). Do not parse this label as US Central daylight offset a second time. The local point may be rounded, reported time approximate, and measured hail diameter differs from a radar-estimated maximum.
- NCEI describes reports as county/zone event components in larger episodes. Related NWS, preliminary SPC, and later NCEI reports can reflect the **same physical hailstorm**, not independent loss events. NCEI reported monetary damage is **not** insurer claims, policy TIV, vulnerability calibration, or a precise footprint.

## Exact NOAA original-source object candidates

Original public provider S3 bucket: [NOAA MRMS AWS registry](https://registry.opendata.aws/noaa-mrms-pds/).

The original S3 ListObjectsV2 with prefix `CONUS/MESH_00.50/20210429/MRMS_MESH_00.50_20210429-013` returned **five dated object keys** corresponding to UTC times 01:30:40, 01:32:40, 01:34:41, **01:36:39**, 01:38:38. The selected instantaneous MESH file is only **21 seconds** before the reported NCEI time (not guaranteed to sample the same falling stone):

| Source detail | Fixed value / provenance limit |
| --- | --- |
| Selected object | `CONUS/MESH_00.50/20210429/MRMS_MESH_00.50_20210429-013639.grib2.gz` |
| [NOAA source HTTPS URL](https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MESH_00.50/20210429/MRMS_MESH_00.50_20210429-013639.grib2.gz) | Fixed full provider key, no dynamic API query or supplied host |
| Listed and intermediary-delivered length | **54,463 bytes**, both identical |
| **Research-computed** compressed SHA-256 | `7d1fc719f0791e25ddd2919cb5dcea1302caa4150712feebc42b6c0cbe84fdf6` |
| Intermediary-delivered gzip header | Valid magic and embedded original `.grib2` basename |
| GZIP trailer ISIZE declared | **90,747** uncompressed bytes (**not independently decompressed in the intermediary probe**) |
| Initial trust boundary | Source bytes delivered via web intermediary; separately verified original direct HTTPS + gzip CRC / GRIB sections **pending workflow** at candidate-PR start |

A second public S3 ListObjectsV2 query confirmed the *different* `CONUS/MESH_Max_30min_00.50/` series for the same UTC event: exact **01:36:00** object `MRMS_MESH_Max_30min_00.50_20210429-013600.grib2.gz` is 72,599 bytes on provider index. It is a **rolling 30-minute maximum**, not another independent storm or ground observation. Its source bytes remain uninspected in this bounded case.

## Bounded technical check

- The existing [offline original-file preflight](../../research_runners/noaa_mrms_mesh_original_preflight_v0.py) is extended to this single exact positive-hail MESH key, with fixed basename, recorded size/SHA-256 and source parameter 209/3/28. No raw NOAA bytes in Git.
- Additional GRIB2 section 3, template 3.0 parser derives **Ni/Nj**, first/last latitude/longitude, i/j angular step and scanning direction, enforcing Ni×Nj equals declared total and endpoint consistency; WMO GRIB2 coordinate fields use **sign magnitude**, not ordinary two's-complement integers. Grid geolocation is **not a field-value/raster intensity decode**.
- At the independent NCEI point only, compute a **nearest nominal source grid row/column** under the source scanning mode; a coordinate-to-cell match **does not mean** the nearest cell's value equals an observed hailstone size or a storm footprint. Real raster values, point support and QC must be assessed separately with a suitable GRIB decoder.
- [Direct HTTPS proof](../../research_runners/noaa_mrms_mesh_direct_https_proof_v0.py) and opt-in/path-scoped GitHub Actions workflow add the fixed third sample after ensuring the original provider bytes match the intermediary digest; none of these routines writes source bytes, claims, raster values, or financial positions to Git.

## Scientific invalidation gates remaining

1. Validate live direct provider SHA and gzip CRC/GRIB section field identity for the 2021 object. Never silently rewrite pinned checksums to match changed provider content.
2. Independently verify the **actual** GRIB2 grid/template, scan, coordinate reference and nearest report coordinate with a trusted ecCodes/wgrib2/GDAL decoder.
3. Decode a **bounded source raster cell neighborhood** centered on Keller, checking missing/background codes, true radar MESH physical diameter in mm, and overlap with 2-minute/30-minute products; preserve provider version, execution environment and exact sample.
4. Compare to independent ground hail observations with temporal, spatial, height/beam, feature-label and report selection uncertainty. One matched point cannot infer annual hail frequency, insured roof damage or vulnerability.
5. No dataset/source admission or downstream insurer loss use until dedicated rights, provenance and science review.

The repository continues to publish only original-provider **references, source receipts, bounded validators and research findings**, not third-party raw data.
