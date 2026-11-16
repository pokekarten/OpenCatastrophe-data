<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USGS WESM: full original CSV SHA-256 and source-quality counts

## One authentic complete original source receipt

The official U.S. Geological Survey [3DEP Spatial Metadata](https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata) provides WESM CSV data for 3DEP lidar work units. The source file is frequently regenerated and is *not* the S1M terrain GeoTIFF itself. The original [USGS WESM.csv](https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv) was read exactly once, transiently in public GitHub Actions [workflow run 43963850431, original job 133638077985](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43963850431/job/133638077985).

- Original retrieval UTC: **2026-11-16T21:49:08.229071+00:00**.
- Original source HTTPS GET **200**, no URL change/redirect and no alternate original objects.
- **Entire original source CSV bytes: 2,267,051**; **whole-original SHA-256: `a5f56b54f26767311156116b4721d477bf5d7b6069056117127898852d2d1b83`**.
- The first original 32,768 bytes independently matched the previously observed public original source SHA-256 `19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d` (GitHub run 43961768133 and later replay 43962483437).
- Original CSV field count **28**, original ordered header field SHA-256 `c2893167ec1839f74db9c67704f9f3fbd3c4ed9d6d65359bf1914ce19abb2746`.
- Source rows **3,308**. In the seamless status column: `Meets = 2,157`, `Does not meet = 966`, `Meets with variance = 129`, `Pending publication = 56`, `Under review = 0`, `unknown_or_blank = 0`. These are source **row** counts, not a population of unique projects/polygons and not raster-cell percentages.
- No missing workunit/project ID rows in this data read. **106 appearances of a workunit_id seen previously**; do not infer duplicated spatial coverage, contradictory source quality, two projects or an error without independent workunit-project-polygon lineage. Workunit-ID uniqueness is not a source admission gate here.
- Executed exact runner SHA-256 `2879389e6031d76efd4c1c26ea9081e9365aa5c0a62e65e3e219d57422f9d6d6`, exact access contract SHA-256 `d399827e415adead3443f33ee2b7503cbf3dc572e0f5a5a6286b1c5d14826c45`. These identify the **historical executed code and contract**, not future edited versions.
- Original CSV body is not logged/persisted/committed. Source row values and IDs are not exported; only SHA-256, source byte count, source-status aggregates, UTC and script/contract fingerprints are recorded. No Neon write, GeoPackage download or insurer exposure imported.

## Scientific interpretation and validation boundary

This is an actual **original full-file CSV SHA-256** receipt, not an approximation based on the first 32KiB or a provider-documented file size. The current source snapshot can be reproducibly compared to a later one if both full-file SHA-256 values are preserved.

**Do not infer compliance from row percentages:** status fields differ for lidar point clouds, source DEMs, one-metre DEMs and seamless DEMs. Even a row labelled `Meets` means the USGS WESM **work unit** reports that specific product status; it says nothing yet about the work unit's geographic intersection or contributing pixels within the frozen `S1M_n0450e1510_20260821.tif` Florida tile. A 3DEP workunit can be represented by multiple rows/metadata identities; source-version and geometry checks are independent of workunit ID frequency.

- **T0** source/terms verified: official USGS WESM public-domain provider publication; internal Git publication scope remains metadata-only.
- **T1/T3 original complete CSV**: **VERIFIED** for this exact 2026-11-16 source snapshot, SHA and row-level *aggregate labels*.
- **Original spatial WESM GeoPackage**: **NOT VERIFIED**, no source polygon geometries.
- **S1M per-cell source lidar vintage, void-fill, vertical GEOID18 transformation, independent accuracy**: **NOT VERIFIED**.
- **T4 CAT use, building elevations and actuarial insurer losses**: **NOT APPROVED**. No model input admitted or Neon-source-sample row approved.

**CLASSIFICATION:** `TECHNICALLY_VERIFIED_ONLY` for complete **USGS WESM CSV source snapshot**, `BLOCKED_WITH_EVIDENCE` for spatial source lineage and CAT model use.

**Next causal action:** review exact USGS WESM GeoPackage original access/size/rights; acquire independently and compute its full original SHA, select only geometry matching the exact Florida S1M tile, then use the accepted WESM status classifier to qualify actual joined source work units. Check original lidar survey dates, overlapping source footprints and independent lidar ground-checkpoint accuracy; never model `Meets` as equivalent to loss or flood validity.
