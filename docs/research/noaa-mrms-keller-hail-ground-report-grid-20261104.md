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


## Executed real-byte/geolocation result — 2026-11-04

GitHub-hosted [NOAA direct proof run #41797985117](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41797985117) was **successful**, checking all three pinned objects including the actual 2021 hail-positive case. This run performs **direct HTTPS GET, SHA-256, gzip CRC32, GRIB2 center/discipline/category/parameter, Section 3 template-0 grid geometry and external report site indexing**; no source file bytes are written to the repo or exported to artifacts.

| Actual source verification | Observed/checked result |
| --- | --- |
| NCEI independent event report | `956694`, ~32.92°N, −97.29°, hail **63.5 mm** from ground report |
| Original NOAA object time | **2021-04-29T01:36:39Z**, 21 seconds before report |
| Compressed source bytes | **54,463** |
| SHA-256 from actual direct HTTPS matches earlier intermediary | `7d1fc719f0791e25ddd2919cb5dcea1302caa4150712feebc42b6c0cbe84fdf6` |
| GZIP independently verified by zlib | **CRC32 pass**, decoded GRIB **90,747 bytes** |
| GRIB2 product identifier | NOAA center **161**, discipline **209**, category **3**, parameter **28** (MESH) |
| Grid definition | Template 3.0 regular latitude/longitude, **7,000 × 3,500 = 24,500,000** cells |
| Original grid first/last latitude | **54.995° N** (first) to **20.005001° N** (last); north-to-south scan |
| Original grid first/last east-longitude | **230.005° E** (first) to **299.994998° E** (last), i.e. approximately −129.995° to −60.005° |
| Angular steps | **0.01° longitude**, **0.01° latitude** |
| GRIB2 scanning mode | **0**; i eastward and j southward |
| Nearest nominal cell for ground-report point | **column 3270, row 2207** (zero-based); *cell value NOT decoded* |
| Rigor / authority | Correct source identity, geometry and timestamp; **not** physical hail observation, quality skill, claim footprint, insured loss or source/model admission |

### Important parser correction from actual original source

The first execution of the new grid parser **blocked correctly** because the synthetic fixtures assumed only `(basic angle, subdivisions)=(0,0)`. The original source disclosed `(1,1000000)`, also exactly **10^-6 degree** per WMO GRIB2 Template 3.0 Note 1. The parser now validates the actual **ratio**, with fail-closed rejection of non-equivalent scales; unit tests cover both WMO zero/missing sentinels and the observed positive ratio. This is a standards-based correction, **not** removal of the grid checks. Invalid geometries still fail.

**Remaining:** all source raster intensity values, no-data/bitmap semantics, event-vs-radar timing bias, and independent ground observation uncertainty remain untested. The 63.5 mm figure comes **exclusively from the NCEI report** and must not be represented as a decoded MESH value. Independent ecCodes/wgrib2 point sampling of this fixed source is the next defensible science step.


## First actual radar-value decode: independent ecCodes four-cell challenge (2026-11-04)

[Source-action run #41799100987](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41799100987) was the first **successful real original-field value decode** for this case, using ecCodes Python **2.50.0**, in a separate opt-in research-only GitHub Actions job. It first fetched the **fixed and SHA-256/CRC32 verified original NOAA S3** `MRMS_MESH_00.50_20210429-013639.grib2.gz` (54,463 bytes compressed), opened its decompressed GRIB2 message in memory, and used **ecCodes independent geodesic nearest-four** to read just four cells surrounding the rounded `32.92°N / −97.29°` NCEI location. The test did not commit original binary bytes or full raster values.

| Relative grid corner | Source zero-based index | Grid center lat/lon (0..360 east) | ecCodes distance from rounded NCEI report | Actual decoded MESH value |
| --- | ---: | --- | ---: | ---: |
| North-west | 15,452,270 | 32.925°N / 262.704999°E | 0.7255 km | **5.8 mm** |
| North-east | 15,452,271 | 32.925°N / 262.714999°E | 0.7254 km | **14.6 mm** |
| South-west | 15,459,270 | 32.915°N / 262.704999°E | 0.7256 km | **4.4 mm** |
| South-east | 15,459,271 | 32.915°N / 262.714999°E | 0.7254 km | **16.8 mm** |

**All four values are valid decoded numeric source cells**; none was classified missing. The independent NCEI employee-reported tennis-ball hail was **2.50 inches = 63.5 mm** at `2021-04-29T01:37:00Z`, only **21 seconds** after the original MESH timestamp.

**Observed discrepancy, not resolved model bias:** Across four adjacent radar cells MESH is **4.4–16.8 mm** versus a **63.5 mm ground hail report**. The 63.5 mm is an independently reported observation and **not an ecCodes result**. The 2021 object is an *instantaneous* radar estimate, not a local event-lifetime maximum. The NCEI location is coarse and appears effectively at a **four-cell junction**; each grid center is approximately **0.725 km** from its rounded point. Radar storm structure, spatial offset, hail-time uncertainty, report rounding, calibration/vintage and data packing/quality rules are all potential differences. This comparison alone **cannot justify reducing insurer losses, calibrating vulnerability, inferring an annual frequency or certifying an accuracy score**.

The original NCEI report says **NWS Employee**, event ID 956694, `1.5NNW KELLER ALTA VISTA AR`, with local historical `04/28/2021 19:37 CST-6` label. Beware that NOAA uses an explicit fixed `CST-6` offset: converting the timestamp to UTC is **01:37Z**, whereas wall-clock daylight local labels seen on some secondary sites may show **20:37 CDT** for the same event. The corresponding NCEI `40.00M` property-damage field, if read, is **not a policy claim, independent insurer paid-loss dataset, or per-coordinate ground truth**. Source: https://www.ncei.noaa.gov/access/storm-events-database/event-details/956694.

**Next falsifiable science checks:** read exact `MESH_Max_30min` swath for the same episode and 2–3 adjacent two-minute instantaneous source records; verify the maximum within a bounded time window, true missing/zero semantics and radar version, and compare across multiple de-duplicated NCEI point reports. A 30-minute rolling swath is **not an additional physical event** and must not be added to instantaneous MESH as an independent occurrence. This remains **research-only** with no hazard, vulnerability, pricing, TIV, insurer loss or model-input admission.
