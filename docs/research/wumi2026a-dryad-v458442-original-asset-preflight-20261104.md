<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WUMI2026a Dryad v458442: original asset metadata preflight (2026-11-04)

**Executable bounded audit, no approved source-asset ingestion.** This narrows the actionable 2026 WUMI source from an enormous research archive to one exact, separately identifiable publisher file. It does not pretend a metadata hash validates the original ZIP.

## Verified from publisher's original metadata API

- Dataset DOI [10.5061/dryad.63xsj3vd4](https://datadryad.org/dataset/doi:10.5061/dryad.63xsj3vd4); Dryad [versions API](https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.63xsj3vd4/versions) distinguishes original WUMI2024a **version ID 413220** and WUMI2026a **version ID 458442**.
- Exact [v458442 original file inventory](https://datadryad.org/api/v2/versions/458442/files) has **seven files** including `WUMI2026a_final_wildfire_lists.zip`, **4,683,571 bytes**, publisher-claimed SHA-256 `8d8a59588935b832bf8e382a0c94b8a6705e6a8fa2bed161bacf1d9fe78726d0`, original file ID **4917545**.
- Original advertised [file download route](https://datadryad.org/api/v2/files/4917545/download); **no successful download or on-disk hash validation occurred during this review**. A read-only direct download attempt returned an HTTP **401 Unauthorized** on 2026-11-04. The standard isolated Linux network also failed DNS lookup. Access is **blocked pending authorized retrieval**; there is no basis to claim exact original ZIP bytes, ZIP integrity, internal list headers or event totals.
- The published metadata inventory also lists `fire_lists.zip` (26,481,076 bytes), `fire_maps.zip` (822,779,079 bytes) and `original_data.zip` (100,715,033,562 bytes). **Do not download the 100 GB original archive** for this task.

The v458442 file-list JSON is itself a live provider **metadata reply**, and its SHA-256 must be computed over **exact locally saved raw JSON response bytes**; the official file checksums above are publisher metadata claims until tested against an authorized original download. Neither metadata nor a file checksum proves a licence, authoritative fire event or insurer-model suitability.

## Offline read-only command

The checker consumes a privately captured original Dryad version-specific seven-file API response. It validates all seven names, original typed byte lengths, SHA-256 digest format, version consistency, file download link identity, and the selected 4.68 MB asset's exact publisher size/digest/file ID.

```sh
python -m research_runners.wumi2026a_dryad_original_asset_receipt_v0 \
  --metadata-json /private/dryad-v458442-files-original-response.json \
  --metadata-sha256 THE_SHA256_OF_EXACT_PRIVATE_JSON_BYTES \
  --dryad-version 458442
python -m unittest tests.test_wumi2026a_dryad_original_asset_receipt_v0 -v
```

Outputs only publisher metadata identities and non-admission flags. The script never fetches URLs, unpacks ZIPs, reads individual fires, writes model hazard, uses credentials, stores private observations or uploads data.

## Optional byte-identical ZIP and safe-members gate (prepared; not yet run on original)

The CLI also accepts `--original-zip /private/WUMI2026a_final_wildfire_lists.zip` **after an authorized download**. The ZIP checker first enforces **exact original publisher size and SHA-256**, then inspects entries *in memory* without extraction, rejecting traversal/absolute paths, case-fold duplicates, symlinks, encryption, unsupported compression and oversized expanded members. It validates ZIP CRC values and emits only member counts, not their names or content. **These tests use synthetic ZIPs only**; no real ZIP has yet been successfully fetched. Even a successful original ZIP checksum/CRC check does not settle parent/subfire semantics, scientific validity, actual fire coverage or data reuse rights.

## Next original-byte gate (currently blocked)

On an authorized machine with provider access, download **only** `/api/v2/files/4917545/download`, store the ZIP outside the public repository, check the downloaded byte count **4,683,571** and SHA-256 **8d8a59588935b832bf8e382a0c94b8a6705e6a8fa2bed161bacf1d9fe78726d0**, then inspect ZIP member list and syntax *without* extracting unsafe member paths. Inspect source `README.md` for its parent-only vs with-subfires wildfire event-list semantics and the six-state 2026a extension; retain label provenance. Evaluate rights for scientific, redistributed and commercial model uses **separately**. Do not ingest into NextGen/Neon as approved source until those checks pass. The original dataset may have differing publisher licence/access settings for metadata and actual files.

This work follows the [canonical alternative-source register](../../landscape/sources-wildfire-alternative-footprints-20261104.json) and [source investigation](us-wildfire-alternate-source-intake-20261104.md), which already record WUMI2026a, FEDS, FIREDpy, iWED and GlobFire.
