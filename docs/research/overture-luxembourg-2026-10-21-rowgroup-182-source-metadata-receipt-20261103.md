<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Overture Luxembourg-city: original October 2026 row-group metadata receipt

**Execution date:** 2026-11-03 (UTC), exact research PR #1203.
**Evidence source:** [GitHub Actions run 41691813090, job 126112041798](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41691813090/job/126112041798),
completed **SUCCESS** including all **16 offline synthetic regression tests** and the
separate live bounded public STAC/S3 Parquet-footer probe.

## Fixed source identity and bounded observation

- Overture release: `2026-10-21.0`; theme `buildings`, type `building`.
- Original STAC item: `https://stac.overturemaps.org/2026-10-21.0/buildings/building/00226/00226.json`.
- Original S3 object key: `release/2026-10-21.0/theme=buildings/type=building/part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet`.
- Original file size from the bounded source checker: **609,459,333 bytes**;
  source metadata declares **5,054,907 rows** and **256 row groups**.
- The original Parquet **footer metadata**, not data pages, was range-read:
  **1,461,640 bytes**. Matching original STAC and the file's start/end metadata
  were required by the source checker; whole-file SHA-256 was **not verified**.
- Fixed Luxembourg-city research bbox (WGS84): `[6.129, 49.609, 6.131, 49.611]`.

## Verified *metadata-screen* outcome

| Row-group status | Groups | Source file rows in those groups |
| --- | ---: | ---: |
| Cannot exclude by bbox statistics (candidate) | **1** | **19,095** |
| Excluded by bbox statistics | **255** | **5,035,812** |
| Missing/invalid bbox stats (unknown) | **0** | **0** |
| **Total original file** | **256** | **5,054,907** |

Only the **zero-based Parquet row-group index 182** remains for a possible
future feature-level comparison with the exact test bbox.

**This does NOT mean 19,095 buildings are located in the city bbox**.
The file rows are grouped by column statistics and can cover a wider
geographic extent. This stage is a *necessary-only row-group filter*; no
individual feature, footprint, centroid, original geometry, building ID,
GERS registry match or exact insured asset was inspected. Nor is the file
equivalent to the entire Luxembourg building inventory, an independent
source-family count or the number of unique structures.

## Source-use, science and privacy controls

The original file's SHA-256, underlying contributor rights/ODbL obligations,
publisher authority for the exact retained original bytes, and complete
building/geometry authenticity remain **unreviewed**. Neither ETag nor an
HTTP 206 metadata response is a full-object source hash. No provider data
pages, model-ready coordinates, feature-level locations, private insurer
policy/TIV data, production Neon rows or CAT inputs were stored here.

**Admission:** `cat_model_input_approved=false`,
`insurance_model_input_approved=false`,
`source_file_full_sha256_verified=false`,
`no_original_building_data_pages_read=true`.

**Next gate:** independently authorize and SHA-pin the exact source object,
then use a separately bounded and rights-reviewed **feature-level**
geometry/identity validator for row group 182. Only after a verified asset
location and original event-hazard overlap could any building be considered
an exposure *candidate*; insured TIV and policy attachment need a separate
private consumer and independent validation.
