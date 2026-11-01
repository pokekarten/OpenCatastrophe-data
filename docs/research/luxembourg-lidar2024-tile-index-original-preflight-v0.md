<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT LiDAR2024: exact tile-index GeoPackage source receipt

**Research-only original-source validation; not an approved CAT model input or independent measured building height.** Date: 2026-11-01.

## Authoritative asset, not a 2 TB download

The Administration du cadastre et de la topographie (ACT) BD-L-Lidar2024 release contains classified LAZ/COPC point clouds, a 50 cm DTM / MNT and DSM / MNS, and a **compact official GeoPackage tile assembly/index**. The original technical documentation says around **10,905** 500 × 500 m point-cloud tiles arranged into groups of up to nine, but this is NOT assumed to be equal to the tile-index table row count; the source schema decides that. LiDAR has >30 emitted points per square metre. Classification includes ground, buildings, vegetation and water. Survey acquisition and derivative release dates must be distinguished.

- Publisher dataset: https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/
- Exact index resource: https://data.public.lu/en/datasets/r/04cfeb86-c9df-4ee6-a45a-8671af98a114
- Exact direct official index: https://download.data.public.lu/resources/lidar-2024-releve-3d-du-territoire-luxembourgeois/20250117-095958/lidar2024-ta.gpkg
- Publisher listed **3.4 MB** and SHA-1 **`3269aecb189271e7c3f86127c0e96f4e213557c9`**, resource updated **2025-01-17**, provider labelled **CC0**. Declared geometry CRS **LUREF LTM / EPSG:2169**.
- Provider documentation: https://data.public.lu/en/datasets/r/d629dfb3-3c02-4b93-953e-0455ed74b3d7 . Full national point clouds are **over two terabytes**, so indiscriminate ingestion is inappropriate.

## Implemented

`research_runners/luxembourg_lidar2024_tile_index_receipt_v0.py` accepts only one locally acquired, publisher-SHA1-pinned GPKG. It checks file size, SQLite header/application ID, required metadata tables, EPSG2169 feature-layer CRS, polygon layer type, row count bounds and *column names only*, reports whether an RTree is present, and computes an exact original-file SHA256. It does not extract a single tile URL or feature geometry and does not fetch any LAZ or COG rasters.

```bash
python -m unittest tests.test_luxembourg_lidar2024_tile_index_receipt_v0 -v
python -m research_runners.luxembourg_lidar2024_tile_index_receipt_v0 \
  --original-gpkg /private/official/lidar2024-ta.gpkg
```

A dedicated GitHub Actions source runner downloads only that **specific** 3.4 MB file into a temporary environment, runs ten synthetic safety/rights tests and the original-file metadata check, then deletes the source. It never emits source URL values, individual tile IDs, point-cloud bytes, building locations or any per-feature records. If the official SHA1 is different or the format/drift differs, the run must **fail** rather than substitute a data vintage. The observed SHA256 provides a stronger reproducibility receipt but a publisher SHA1 is not a signed authenticity proof.

## How this makes catastrophe exposure work better

1. Cross-check the actual original index fields and tile grouping/URL names. Catalogue claims such as `10,905 tiles` must be checked against actual table semantics, not assumed from count.
2. Select just one authorised index **tile** covering our previously measured 250 m Luxembourg-city ACT/EUBUCCO roof overlap window, after EPSG2169 native coordinate controls and tile field semantics are reviewed.
3. Fetch only the licensed required LAZ group or bounded COG window externally to Git and lightweight insurance Neon. Freeze independent source hashes. Verify LAZ classifications, point density, geometry axis interpretation, vertical heights/datum, data coverage and camera/temporal alignment.
4. Derive building height distributions from ground-class points and roof-class points or bounded DSM−DTM, excluding trees (separate vegetation class), with aggregate uncertainty bands; compare observed LiDAR heights with EUBUCCO's `height_source` **estimated** versus **gov** groups and ACT2023v2 roof-level `zmin`. **`zmin` is not a building's total height**.
5. Create a manual sample grouped by residential/commercial, roof complexity and urban density. Report height bias, MAE, missingness and coverage with held-out source lineage. Avoid reusing same ACT aerial/photogrammetric source as independent height validation without checking acquisition methods.
6. Only after original source-specific rights and scientific admission may these height features calibrate insured exposure/value or structural vulnerability. No individual insurer value, person, address, loss or CAT input has been established.

## Related actual original building evidence

- ACT2013 LoD1: national original `lod1-par-pays.zip` SHA256 `d60f0efd2d66f0a446cd2216be1b40e97ac4f15edfc5e3c8a3aaff390c326fa1` (merged #925).
- EUBUCCO v0.2 LU00: original `LU00.parquet` SHA256 `d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c` (merged #919).
- ACT2023v2: original roof GPKG SHA256 `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf` (merged #912).
- ACT GeoBase October 2026: original Buildings GPKG SHA256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676` (merged #926).

This stage **does not** prove tile download capability, independently observed building height, EUBUCCO geometry identity, construction year, insurer-specific TIV or measured hazard/loss.

## Actual original-file receipt (2026-11-01)

The narrow official-data GitHub Actions run [41310189592](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41310189592) succeeded with **all 10 synthetic safety tests** and the true publisher-hosted original GeoPackage. Exact observed evidence:

| Original property | Verified |
| --- | ---: |
| Original GeoPackage bytes | **3,518,464** |
| Original publisher SHA-1 | `3269aecb189271e7c3f86127c0e96f4e213557c9` (**match**) |
| Newly computed original SHA-256 | `3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8` |
| GeoPackage feature layer | **`TableauAssemblage`** |
| Exact index feature rows | **10,905** |
| Source geometry/CRS | **POLYGON / EPSG:2169** |
| Original field names | `fid`, `geom`, `Fichier`, `Dossier`, `DownloadLink` |
| Spatial RTree index | **present** |

This is a strong practical result: the exact original index contains **a real spatial index and a provider URL field**, making a narrowly bounded one-tile original LiDAR download feasible in a separately controlled follow-on experiment. The 10,905 rows are index records, not measured buildings or independent building height values. Provider entry URLs and individual tile geometry have not yet been read in this stage. The source file was never uploaded to Git, Neon or artifacts.
