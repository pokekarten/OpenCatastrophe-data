<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Exact original USGS WESM GeoPackage: 64 KiB source-prefix receipt

## Provider and exact original request

The official [USGS 3DEP Spatial Metadata page](https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata) directly links the live [Work Unit Extent Spatial Metadata GeoPackage](https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.gpkg). USGS documents this publisher dataset as updated nearly daily; it is not a fixed versioned immutable URL. The source-original WESM CSV, separately version-hashed in merged PR #1739, is a **distinct object** and does not attest this 3.56 GiB spatial file.

A first source-bound PR #1740 probe [GitHub Actions run 43968011136, job 133652534037](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43968011136/job/133652534037) failed its initial 1 GiB safety ceiling **before reading original bytes**. A second [run 43968198021, job 133653353855](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43968198021/job/133653353855) logged the original HTTP206 Content-Range total **3827232768 bytes**, also blocking without reading original bytes. The access contract was then amended to approve the one exact source-advertised total, keeping **the original transfer limit at 65536 bytes**.

An actual **authentic original source prefix** was successfully retrieved in [GitHub Actions run 43968769537, job 133655199029](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43968769537/job/133655199029), on **2026-11-16T22:19:06.461974Z**:

| Evidence | Original provider result |
| --- | --- |
| Official exact original URI | `https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.gpkg` |
| Transport | Exact anonymous HTTPS GET, `Range: bytes=0-65535` |
| Original HTTP | **206**, `Content-Range: bytes 0-65535/3827232768` |
| Original response bytes read | **65,536** |
| SHA-256 of original 65,536 bytes only | `0344f898d4946a915ca0c3a5d0078fd72dc222179c54d8e9413a067c8ce5be88` |
| Advertised total original object size | **3,827,232,768 bytes (~3.56 GiB)** |
| Native first header | `SQLite format 3`, OGC GeoPackage application ID `0x47504b47` |
| Native SQLite page size | **4096 bytes** |
| Header declared pages | **934,383**, exactly **3,827,232,768** header-derived bytes |
| SQLite schema format / text encoding | **4** / **1** |
| OGC GeoPackage `user_version` | **10400** |
| SQLite creating library version number | **3045001** |
| Exact source-request SHA-256 | `f5614764b74f1bd5b5e55224ef7dc888f8f63f0c0dc3325dae82d71d4ee52d15` |
| Exact historical executed script SHA-256 | `139f20267ea5f2ac8cf4ecb423b65d45233401ff2761adb5cf85797d19d08ba6` |
| Exact historical executed source-contract SHA-256 | `d14463c379702fde4f55a45e7edc4903397d88d4fe887e0cb2952bd2b999d986` |

The original 65,536 provider bytes were processed **in memory only** and discarded. No work-unit polygon records, feature values, project identifiers or images were read from this original GeoPackage. Only structural header integers, original 64KiB hash, UTC and fingerprints were printed. No provider raw content was committed, stored in Neon or uploaded as a workflow artifact.

## Scientific source admission boundary

- **T0/T1/T3 partial source:** authentic fixed original WESM.gpkg HTTP 206 range and first GeoPackage/SQLite page header verified. This is an independent **original source-prefix** technical receipt.
- **T3 complete source:** **NOT verified**. No complete 3,827,232,768-byte original file hash or SQLite table integrity scan. A valid first page does not guarantee correct whole-file content, feature geometry, SRS or dataset status.
- **Original WESM CSV parity:** **NOT verified**; the original full CSV from 2026-11-16 has an independently frozen SHA-256, but the GeoPackage is mutable and may represent another publisher version.
- **Actual source geometry:** **NOT verified**. The number, validity and CRS of original WESM work-unit polygons are unknown. The separately observed 106 repeated CSV workunit-project pairs cannot be resolved as overlapping, split, repeated or differing polygons from this header.
- **Florida S1M terrain tile:** **NOT verified**. No source workunit polygon intersects or is linked to `S1M_n0450e1510_20260821.tif` by this job.
- **Scientific CAT use:** **BLOCKED**. No original S1M per-pixel lidar vintage/void-fill, no GEOID18 correction-chain proof, no ground truth and no insurer portfolio/model input approved.

**FINAL_CLASSIFICATION**: `TECHNICALLY_VERIFIED_ONLY` for exact **64KiB original USGS WESM GeoPackage header and transport metadata**; `BLOCKED_WITH_EVIDENCE` for complete provider GeoPackage, geographic join and insurance model use.

**Next causal action:** freeze the original 65536-byte prefix SHA-256 and exact total size in the source-only runner; reject original provider version drift. Because the actual original GeoPackage is **3.56 GiB**, do **not** automatically download it. Prefer a separately reviewed, bounded, source-authentic Florida geometry query or source-exact spatial subset. Independently validate source geometry SRS and WESM-to-Florida-S1M spatial joins before CAT use.
