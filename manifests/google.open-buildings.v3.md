<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/google.open-buildings.v3.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `google.open-buildings.v3.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** google.open-buildings.v3

**Provider:** Google Research

**Product name:** Open Buildings

**Version or release:** v3

**Canonical source:** <https://sites.research.google/gr/open-buildings/>

**Retrieved at:** 2026-08-10T01:10:00Z

**Retrieval query or filters:** Metadata-only review of Open Buildings v3. No S2 tile, polygon, point, score-threshold or other dataset bytes were acquired. Future raw work must select and hash exact v3 assets independently.

**Access class:** open

**Modelling layer:** exposure

**Intended use:** Independent public building-footprint exposure-geometry source for coverage, omission, confidence-threshold and cross-source validation research. ML detections are not cadastral records, verified occupancy/construction attributes, insured locations, replacement values, vulnerability functions or claims.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** CC-BY-4.0

**Licence name:** Creative Commons Attribution 4.0 International

**Terms reference:** <https://sites.research.google/gr/open-buildings/>

**Terms reviewed at:** 2026-08-10T01:10:00Z

**Terms version or date:** Open Buildings v3 dual-licence statement reviewed 2026-08-10; CC-BY-4.0 selected for this admission

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** Use Open Buildings v3 under the selected CC BY 4.0 path and provide appropriate attribution, a link to the licence and indication of changes.

**Share alike or derivative requirements:** The selected CC BY 4.0 path has no share-alike requirement. Google also offers ODbL-1.0 as an alternative, but this admission does not select that path.

**Notes:** The underlying satellite imagery is not part of the released dataset and is not covered by this admission. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** Source rights can support sharing under the selected CC BY 4.0 path. This manifest records repository review status approved_metadata_only. At the manifest review time, no exact v3 S2 tile or companion artifact had been selected, acquired, hashed or approved for Git publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The reviewed product is a public ML-derived building-geometry dataset and does not include building type, street address, customer, policy, claims or person-level records.

## Spatial

**Crs:** `null`

**Extent:** Approximately 58 million km2 across Africa, South Asia, South-East Asia, Latin America and the Caribbean; exact selected S2 tile coverage must be pinned for raw use

## Temporal

**Extent:** v3 inference performed May 2023 from source imagery with location-dependent freshness; no single observation date applies to every building

## Variables and units

### Item 1

**Name:** building footprint geometry

**Unit:** `null`

**Description:** ML-derived WKT POLYGON or MULTIPOLYGON geometry for polygon records.

### Item 2

**Name:** area_in_meters

**Unit:** m2

**Description:** Area in square metres of the detected building polygon.

### Item 3

**Name:** confidence

**Unit:** dimensionless

**Description:** Model confidence score documented in v3 in the range 0.65 to 1.0; filtering thresholds are separate transformation choices.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-10T01:10:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only approval for version 3. Raw/derived publication remains blocked until exact v3 tile/companion byte identities, filtering choices and scientific limitations are independently pinned and reviewed.
