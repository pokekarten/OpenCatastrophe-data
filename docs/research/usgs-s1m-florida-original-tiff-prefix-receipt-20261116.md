<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USGS S1M Florida exact original TIFF: bounded 64 KiB prefix receipt

## Evidence and exact source boundary

- **Source:** `usgs.3dep.seamless-1m.s1m`; `USGS 3DEP Seamless 1-Meter (S1M)`, distinct from legacy project-based 1-m DEM.
- **Original exact provider URL:** `https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/S1M/n04e15/n0450e1510/S1M_n0450e1510_20260821.tif`.
- **Catalogue source ID:** `6a9785801ba49b050c166274`, title `S1M n0450e1510 20260821`; metadata-only TNMAccess sample #6 held in authorised Neon research.
- **Original source transport:** precisely one anonymous HTTPS GET with `Range: bytes=0-65535`; HTTP **206** and `Content-Range: bytes 0-65535/447032917`. No redirect, no retry, no alternative asset or URI, no 200-range fallback, no persistent provider bytes.
- **Provider retrieval UTC:** `2026-11-16T20:18:29.460229+00:00`.
- **Original 65,536-byte body SHA-256:** `56d8d147056fcd28ad916799cd6b917c57d9d08b3e07dfe06931f2a4d5edb2f2`.
- **Advertised *whole TIFF* byte length, NOT a whole-file hash:** `447032917`.
- **Trusted public GitHub Actions original-source job:** [run 43948359780, job 133583989829](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43948359780/job/133583989829) for PR #1728, original source code commit `be2c439b0b74439e57b89d48686e0ca51d85477a`.
- **Source request SHA-256:** `d9935d8d63062925100ab0fb6525e1e84a500e0f92a0465a5033edf0373a5f59`. **Original executed script SHA-256:** `73c7f39abb7d904f72d16836061bd9badb5db1c63cfa58b33c306417c22b27d0`. **Original executed source access-contract SHA-256:** `8dfe9d077a77bdfe010e5403775a684ea4d965b8afbc914c770f477e66f20ce1`. These execution hashes are historical; they must not be overwritten when code/contracts evolve.

## What the real bytes actually established

The 64 KiB sample is a genuine fixed provider-original source prefix, with **classic TIFF**, **little-endian**, first IFD at byte offset **192**, all **19** first IFD entries in the original prefix, native first-IFD width **10,000** and height **10,000**. The GeoKeyDirectory, ModelPixelScale, and GDAL NoData *tag identifiers* were present.

**Scientific limits:** tag *presence* did NOT establish actual EPSG:6350, EPSG:5703/NAVD88/GEOID18, units or the native NoData numeric value. No pixel-value blocks were downloaded or decoded. Full original TIFF SHA-256, independent horizontal/vertical CRS validation, companion source-project spatial metadata GeoPackage, void-fill provenance and actual elevation quality are still unverified. A valid TIFF prefix is not a CAT-model input.

## Independent second source-original replay: actual scientific TIFF tag values

The original **same** 65,536-byte TIFF prefix was retrieved and hash-checked again in trusted public [GitHub run 43949836747 / job 133589184974](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43949836747/job/133589184974), executed **2026-11-16T20:27:08.673211Z**. The original provider range remained `bytes 0-65535/447032917` and original prefix SHA-256 remained `56d8d147056fcd28ad916799cd6b917c57d9d08b3e07dfe06931f2a4d5edb2f2`; the second run script SHA-256 was `cc931c1b8be9f3eb5c82df6019adb67c35ae0d67e07d5726a171e22ee32f69dc` and contract SHA-256 `80538c1c3a69733a07740e2673ee7dd9aa6a346c40530a5e65aeb48cb524145f`.

The revised bounded parser required the pinned source-prefix SHA and advertised file size **before examining values**, then decoded the original source GeoKeyDirectory, GDAL_NODATA and ModelPixelScale tags. Its reproducible result was:

| Scientific check from original TIFF prefix | Result |
| --- | --- |
| Original first IFD, `10000 × 10000` | Verified |
| GeoKeyDirectory member count | **5** |
| Original projected coordinate-system key (EPSG) | **6350 verified** |
| Original vertical coordinate-system key (EPSG) | **5703 verified** |
| Original GDAL NoData ASCII value | **`-999999` verified** |
| Original horizontal model pixel scales | **1 metre × 1 metre verified** |
| Original source **GEOID18 transformation chain** | **NOT verified** |
| Original full TIFF / pixel-value decoder and per-cell lineage | **NOT verified** |
| Full TIFF original SHA-256, independent relief accuracy, insurer/CAT input | **NOT verified / NOT approved** |

This is a stronger original *metadata-value* proof than presence-only first-IFD tags; it does not certify the complete underlying raster or the 3DEP lidar acquisition lineage. The source-native numeric CRS/NoData/scale checks are scientific T3 **partial** only. They must not be mistaken for a full source-asset admission or an independent hydrological validation.

## Access and admission decision

USGS official National Map downloadable datasets are public domain with requested USGS acknowledgement. The distinct exact-original-header access contract `access/usgs.3dep.s1m.florida-native-tiff-prefix.json` permits only **one limited 64KiB GET per explicit, reviewed workflow run** and explicitly reserves raw redistribution, large asset retrieval, any automatic full-file fetch, GeoPackage and insurance-model use for further review. No original source bytes were committed, uploaded to Neon, or otherwise persisted by this job.

- **T0**: official product, licence, frozen exact public source URI and S1M-vs-legacy semantics.
- **T1/T3 partial**: verified authentic original 64KiB range, byte count/hash, first-IFD structure.
- **T2**: no credentials required.
- **T3 complete**: **NOT verified** (no full file SHA, actual raster/data quality, geoid/lineage).
- **T4 / model admission**: **NOT approved**.
- **FINAL_CLASSIFICATION:** `TECHNICALLY_VERIFIED_ONLY` for **one original TIFF prefix**; `BLOCKED_WITH_EVIDENCE` for full original source and CAT use.
- **Next causal action:** Reuse the now independently fixed prefix SHA and advertised file size to fail-close subsequent original-only GeoKeyDirectory + GDAL NoData *value* inspection. Then obtain separately approved complete TIFF/GeoPackage hashes and assess geoid/void-fill and independent terrain holdout before any risk-model use.

This is original provider-byte evidence, not merely a copied documentation claim or an approved source model.
