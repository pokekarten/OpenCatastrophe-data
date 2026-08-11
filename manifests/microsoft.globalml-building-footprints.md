<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/microsoft.globalml-building-footprints.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `microsoft.globalml-building-footprints.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** microsoft.globalml-building-footprints

**Provider:** Microsoft

**Product name:** Global ML Building Footprints

**Version or release:** `null`

**Canonical source:** <https://github.com/microsoft/GlobalMLBuildingFootprints>

**Retrieved at:** 2026-08-10T00:55:00Z

**Retrieval query or filters:** Metadata-only review of the rolling public distribution. No dataset-links.csv snapshot, country/quadkey partition, coverage layer, or source bytes were acquired. Future raw work must pin an exact distribution-index snapshot and selected asset bytes independently.

**Access class:** open

**Modelling layer:** exposure

**Intended use:** Global/regional building-footprint exposure-geometry candidate for transparent spatial overlay, coverage, height-availability and source-comparison research. The ML-derived footprints and optional attributes are not authoritative cadastral/property records, insured values, occupancy, construction classes, vulnerability functions, policy data or claims.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** CDLA-Permissive-2.0

**Licence name:** Community Data License Agreement – Permissive, Version 2.0

**Terms reference:** <https://cdla.dev/permissive-2-0/>

**Terms reviewed at:** 2026-08-10T00:55:00Z

**Terms version or date:** CDLA-Permissive-2.0; Microsoft repository licence statement reviewed 2026-08-10

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** When sharing data under CDLA-Permissive-2.0, make the text of the agreement available with the shared data. Preserve any separately applicable notices for selected assets; do not imply Microsoft endorsement.

**Share alike or derivative requirements:** CDLA-Permissive-2.0 allows use, modification and sharing and does not impose a share-alike condition; its data-sharing conditions still apply.

**Notes:** Microsoft states that the Global ML Building Footprints data are licensed under CDLA-Permissive-2.0 and freely available for download and use. This review covers the released building dataset, not underlying third-party imagery. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** Source rights can support sharing under CDLA-Permissive-2.0 when its conditions are met, including making the agreement text available with shared data. OpenCatastrophe currently approves metadata only; no exact distribution snapshot or raw/derived asset has been selected, acquired, hashed or approved for Git publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The reviewed product is a publicly released dataset of ML-derived building geometries and optional model-derived attributes, not a customer, policy, claims or person-level dataset.

## Spatial

**Crs:** EPSG:4326

**Extent:** Global distribution with source- and update-dependent coverage gaps; exact coverage must be established for each selected snapshot/partition

## Temporal

**Extent:** Rolling distribution derived from source imagery with geography-dependent vintages; no single observation date applies to all footprints

## Variables and units

### Item 1

**Name:** building footprint geometry

**Unit:** `null`

**Description:** ML-derived building polygon geometry; model output rather than cadastral or legal property geometry.

### Item 2

**Name:** height

**Unit:** m

**Description:** Optional neural-network estimate of height above ground averaged within the building polygon; Microsoft documents -1 for structures without a height estimate.

### Item 3

**Name:** confidence

**Unit:** dimensionless

**Description:** Optional footprint-detection confidence between 0 and 1; not a height-confidence or general exposure-confidence measure. Microsoft documents -1 as a placeholder for older structures without this score.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-10T00:55:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only engineering approval based on Microsoft's public dataset documentation and CDLA-Permissive-2.0. Raw/derived publication remains blocked until the rolling distribution is frozen to exact selected assets, byte hashes, schema semantics and sharing conditions.
