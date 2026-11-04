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


## Follow-up research: time window around actual 2021 hail report

The **instantaneous at 01:36:39Z** first result (four local cells **4.4–16.8 mm** versus independently reported **63.5 mm** at **01:37:00Z**) warrants timing/aggregation challenge before any skill conclusion. The exact additional NOAA original S3 keys and **research-observed** hashes were found and are pinned in the source-byte preflight, awaiting independent **direct GitHub-hosted HTTPS/CRC32/ecCodes** validation:

| NOAA product | UTC | Offset from NCEI report | Original source compressed bytes | Preflight SHA-256 (intermediary-derived, *not yet direct-verified*) |
| --- | --- | --- | ---: | --- |
| `MESH_00.50` instantaneous | 2021-04-29 01:38:38 | **+98 seconds** | **54,575** | `f9dbacf40c9d68e222830aa3b50588231d8897e0a1745e16f348ef81c0f2fba3` |
| `MESH_Max_30min_00.50` max swath | 2021-04-29 01:38:00 | **+60 seconds** | **72,464** | `441cdeb5d6ba6406a4727b6a8c475be5f35920df398bcdfb7347e562999a25c2` |

The exact [instantaneous 01:38:38 NOAA original object](https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MESH_00.50/20210429/MRMS_MESH_00.50_20210429-013838.grib2.gz) was delivered in full via a read-only web intermediary (54,575-byte size matches original S3 listing). For the [30-minute 01:38:00 NOAA original object](https://noaa-mrms-pds.s3.amazonaws.com/CONUS/MESH_Max_30min_00.50/20210429/MRMS_MESH_Max_30min_00.50_20210429-013800.grib2.gz), a single intermediary response delivered only **59,198 of the listed 72,464 bytes**, and was explicitly rejected as **truncated**. Three independently bounded HTTP Range representations (0–29,999; 30,000–59,999; 60,000–72,463, inclusive) then yielded **72,464 total bytes**, a full gzip header and a published-filename-matching embedded gzip basename, with the research SHA shown above. **These are not yet authenticated original direct-download receipts**, and the full source gzip CRC/meteorological content has not been verified at this preflight stage.

The official NOAA/NSSL [operational MRMS GRIB2 table](https://www.nssl.noaa.gov/projects/mrms/operational/tables.php) identifies **MESH (discipline 209/category 3/parameter 28)** and **MESHMax30min (209/3/29)** in **mm**. NOAA's original [MESH Tracks guide](https://vlab.noaa.gov/web/wdtd/-/mesh-trac-3) defines the 30-minute track as a **maximum of MESH over that interval**, not a separate physical storm. An instantaneous radar estimate at t−21 s, an instantaneous estimate at t+98 s, and a rolling maximum at t+60 s are *different product semantics*, and cannot each be independently counted in annual CAT event frequency or insurer losses.

The scientific aim is to compare **same four report-neighbour cells, same independent event ID**, across these **three pinned source windows** using the existing direct-TLS / SHA / gzip CRC and ecCodes source field checks. No additional report points, whole-grid raster download, new source admission, or paid-loss data are authorized by the time-window study.


## Executed independent three-product Keller source test (2026-11-04)

**First successful real time-window comparison:** [GitHub Actions #41801684662](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41801684662) completed successfully on PR #1264's candidate head after fixed-source NOAA HTTPS/SHA256/CRC32 and WMO-grid checks, with independent **ecCodes Python 2.50.0** decoding **only the same four nearest Keller report cells**, not full gridded field export. The separate [direct-original-source run #41801684681](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41801684681) also succeeded for **all five** source files, including the two newly pinned 2021 files.

### Measured radar/source values at fixed report location

The NCEI Storm Events #956694 reported hail diameter **63.5 mm** at **2021-04-29T01:37:00 UTC**. Report location approximately 32.92°N, −97.29° and rounded such that four original GRIB cell centres lie around **0.725 km** away.

| Original NOAA source and reported time offset | NW | NE | SW | SE | Scientific reading |
| --- | ---: | ---: | ---: | ---: | --- |
| 2-minute MESH 01:36:39Z (**−21 seconds**) | 5.8 mm | 14.6 mm | 4.4 mm | 16.8 mm | 4 valid instantaneous estimates; local min/max 4.4–16.8 mm |
| 2-minute MESH 01:38:38Z (**+98 seconds**) | **missing (-1)** | 1.1 mm | **missing (-1)** | 2.0 mm | 2 valid instantaneous estimates; 2 source-defined **missing**, not zero hail |
| 30-minute rolling MESHMax30min 01:38:00Z (**+60 seconds**) | **71.7 mm** | **67.8 mm** | **77.8 mm** | **73.0 mm** | 4 valid **rolling 30-minute maxima**, local min/max **67.8–77.8 mm** |

The 30-minute **rolling source maxima exceed the 63.5-mm reported hail size in all four adjacent cells**, whereas the two **instantaneous** samples do not reproduce that reported maximum. This is **one targeted event challenge**, *not* population-level validation or an independently measured time series. Rolling/instantaneous products must not be treated as independent disaster events, and four adjacent cell maxima must not be counted as four hailstones/claims.

### Real source discovery exposed an additional scientifically material encoding

The initial direct source hashes and metadata passed, but the ecCodes source decoder rejected the **post-report instantaneous** file because two real neighbour cells decoded to **−1 mm**. The authoritative [NOAA/NSSL operational MRMS GRIB2 table](https://www.nssl.noaa.gov/projects/mrms/operational/tables.php) defines MESH (discipline 209 / category 3 / parameter 28) and MESHMax30min (parameter 29) in **mm**, with **Missing −1** and **No Coverage −3**. The table is current for MRMS v12.2, so historical 2021 algorithm/calibration equivalence is *not* asserted. Negative values `-1` and `-3` are now classified as distinct **source missing** and **source no coverage**, respectively, in the bounded ecCodes output, **never replaced with 0.0**. Arbitrary negative codes (including `-99`/`-999` associated with other radar parameters) remain scientifically **rejected**, and tests challenge those boundaries. Genuinely decoded valid `0.0` remains a valid numeric radar field value, without proving a verified absence of hail.

### Implications for OpenCatastrophe / NextGen

- Temporal product type is a **first-class semantic dimension**: instantaneous MESH versus rolling MESHMax30min, original UTC and report offset; a rolling source maximum may be much closer to the NCEI **reported local hail maximum** than a single instantaneous radar slice. That difference cannot be used to assert general algorithm skill from this one case.
- **Missing / no coverage / valid zero / positive decoded hail** must remain different cell statuses. Otherwise a consumer invents low-hail regions or suppresses real tails.
- A future source-consumer contract should include `event_id`, `peril=hail`, `product_time_aggregation`, `source_version`, `original_source_sha256`, `measurement_unit=mm`, `report_location_uncertainty`, `valid_cell_count` and `source_lineage`. These are *proposed fields*, not accepted production schema changes.
- Do **not** independently count the two-minute snapshots or rolling 30-minute maximum in event frequency, event loss tables, catastrophe years, OEP/AEP or insurer/ILS portfolios. Those are representations of **one evolving storm**, not independent catastrophe arrivals.
- Further science gate: multiple disjoint historical hailstorms/independent report sources, event-relative 30-min swath alignment, radar/gauge/version biases, vulnerability and exposure. **No insured/ground-up damage or model admission was derived**.

No raw NOAA GRIB2 bytes were committed to public Git or exported as Actions artifacts. The code logs four selected public-science site values and metadata only.
