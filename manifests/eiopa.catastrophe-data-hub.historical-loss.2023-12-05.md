<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/eiopa.catastrophe-data-hub.historical-loss.2023-12-05.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `eiopa.catastrophe-data-hub.historical-loss.2023-12-05.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Dataset id:** eiopa.catastrophe-data-hub.historical-loss.2023-12-05

**Provider:** European Insurance and Occupational Pensions Authority (EIOPA)

**Product name:** Historical loss data - catastrophe data hub.xlsx

**Version or release:** 2023-12-05 public resource

**Canonical source:** <https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en>

**Retrieved at:** 2026-08-10T01:10:00Z

**Retrieval query or filters:** Metadata-only review of the EIOPA Catastrophe Data Hub historical-loss workbook listed on 2023-12-05. No XLSX bytes were acquired. Raw/derived redistribution remains unreviewed pending inspection of the exact workbook and any file-specific or third-party notices.

**Access class:** open

**Modelling layer:** observed_loss

**Intended use:** Public aggregated incurred-claims benchmark for selected European catastrophe events. Useful for observed insurance-loss semantics and cautious validation, but not a complete market loss history, ground-up economic loss dataset, insurer-specific claims history, or transferable vulnerability curve.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** `null`

**Licence name:** EIOPA website copyright/reuse notice

**Terms reference:** <https://www.eiopa.europa.eu/legal-notice_en>

**Terms reviewed at:** 2026-08-10T01:10:00Z

**Terms version or date:** EIOPA legal notice reviewed 2026-08-10; public resource dated 2023-12-05

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** Acknowledge EIOPA as the source as required by the EIOPA legal notice. Follow its conditions for transformed/republished material and EIOPA material incorporated into sold documents.

**Share alike or derivative requirements:** No share-alike requirement is recorded in the general EIOPA website notice. Third-party material is excluded and must be reviewed separately.

**Notes:** Because the workbook is based on insurer-reported claims and has not been inspected for file-specific notices, only metadata-level reuse is cleared by this review. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** metadata_only

**Conditions:** Only repository-authored metadata about the public EIOPA resource is cleared here. Raw or derived workbook redistribution remains blocked until exact-file and third-party rights are explicitly reviewed.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** This admission describes only EIOPA's aggregated public release. The technical description states that each displayed loss point represents at least three company-submitted values to preserve anonymity; undertaking-level submissions remain outside scope.

## Spatial

**Crs:** `null`

**Extent:** European regions affected by the selected published events; exact geographic identifiers and suppression/aggregation rules require workbook review

## Temporal

**Extent:** Selected events: Central European flood 2013, Portugal wildfire 2017, and European windstorm Ciara/Sabine 2020; public resource dated 2023-12-05

## Variables and units

### Item 1

**Name:** incurred claims for buildings

**Unit:** `null`

**Description:** Aggregated incurred claims for building coverage; exact monetary unit and workbook field semantics require workbook review.

### Item 2

**Name:** other incurred claims

**Unit:** `null`

**Description:** Aggregated incurred claims outside building coverage; EIOPA notes examples such as contents or business interruption. Exact monetary unit requires workbook review.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-10T01:10:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only approval. Raw/derived XLSX publication remains blocked pending exact-file rights, byte identity, workbook schema and unit review.
