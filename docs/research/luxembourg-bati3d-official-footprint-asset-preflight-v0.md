<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg official footprint asset: exact 2D product preflight

**Research only — not a successful download, source admission or model input.**  
**Provider page verified:** 2026-11-01.

## Original authoritative product

- Publisher: **Administration du cadastre et de la topographie (ACT), Luxembourg**.
- Catalogue: <https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2023/>.
- Product: **BD-L-BATI3D 2023, ACT2023v2, Empreintes 2D des bâtiments en GeoPackage**.
- Exact provider resource ID: `d62942ec-0dc8-40e2-9fa4-27841e6e1ac1`.
- Stable resource page: <https://data.public.lu/en/datasets/r/d62942ec-0dc8-40e2-9fa4-27841e6e1ac1>.
- Official direct distribution URL: <https://download.data.public.lu/resources/base-de-donnees-nationale-des-batiments-3d-2023/20260317-160936/act2023v2-buildings3d-footprints.gpkg.zip>.
- Listed update time: **2026-03-17**.
- Listed format: `gpkg.zip` (GeoPackage archive), listed size **60.3 MB**.
- Provider catalogue licence label: **Creative Commons Zero (CC0)**. Capture exact terms and required source citation in asset receipt before any downstream distribution or commercial integration.
- Provider-reported metadata `md5`: `3e91220a3aaa436b3a98f82612bd8f30-13`. This **is not a conventional 32-hex MD5 checksum** (appears multipart-like); DO NOT treat it as verified MD5. Compute a local SHA-256 of the exact retrieved ZIP and any extracted source GeoPackage.
- Product title `2023` is **not automatically the acquisition/observation date**: dataset catalogue records a later temporal coverage and updated 2026 resources. Pin precise observation epoch, producer processing release and actual feature-date semantics independently.

## Machine-readable data evidence gate

The direct official URL was identified, but download from the current analysis execution environment **failed**. Therefore the following remain UNVERIFIED:

- Exact archive byte SHA-256 and decompression integrity; ZIP member names and compression limits; GeoPackage layer/table names and actual field list.
- True number of individual building footprints or compound/multi-part features; geometry types and original CRS.
- Original building IDs, area semantics and split/merge correspondence with EUBUCCO Luxembourg.
- Whether the complete file is suitable to distribute under exact resource rights, not merely the catalogue-level label.
- Percent coverage of residential/nonresidential stock, historic/annex footprints and acquisition date.
- Licence and original source lineage of the **EUBUCCO Luxembourg subset**. The official dataset's CC0 label does NOT confer rights to EUBUCCO or their combined derivative.

## First bounded experiment (NOT executed here)

1. Review exact resource licence and terms; download only via provider's supported **download** endpoint, never website/API scraping. Freeze ZIP SHA-256, provider resource ID, UTC retrieval time, raw size, original file names, full schema and origin CRS.
2. Inspect the GeoPackage outside Git and the small metadata Neon database. Reject unexpected layers, invalid or mixed geometry, missing CRS and unexpected file expansion before processing.
3. Limit to a reproducible **small geographic window** and at most 1,500 unique footprints per input; select the EUBUCCO Luxembourg subset from its exact licensed official release and reconcile its observation period.
4. Use `scripts/building_footprint_overlap_v0.py` after converting both bounded regions to two small local 2D GeoJSON FeatureCollections with explicit building IDs and declared original CRS. Distinguish high-IoU matches, ambiguous 1:n and n:1, weak matches and missing polygons.
5. Audit a manually labelled sample to calibrate tentative thresholds, distinguish source segmentation differences from genuinely missing buildings, and compute accuracy (precision/recall), before any trust in a proposed crosswalk.
6. Only then consider assigning values or connecting original building data to hazard/vulnerability. No person, insurer policy or building ownership data is required.

## Stewardship

Source discovery catalogue candidate: `lu.act.bd-l-bati3d-2023` (formerly PR #901, now main). It stays `not_admitted`, `not_reviewed` for rights and science. The research SQL view `research.building_source_shortlist_v0` in the separate Neon insurance DB is metadata-only and can be queried for canonical GitHub blob and commit identity. No raw provider asset is in Git or Neon.
