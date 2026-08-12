<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03

**Provider:** Deutscher Wetterdienst (DWD)

**Product name:** 10-minute station observations of extreme wind for Germany

**Version or release:** v24.03

**Canonical source:** <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/>

**Retrieved at:** 2026-08-09T18:35:00Z

**Retrieval query or filters:** Metadata-only source review. Historical quality-controlled files are the intended first research subset; no station subset or source bytes have been acquired yet.

**Access class:** open

**Modelling layer:** hazard

**Intended use:** Public observational evidence for validation and later calibration research in a bounded Germany wind-hazard pilot. This source is not by itself a spatially complete catastrophe event set or production hazard model.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** CC-BY-4.0

**Licence name:** Creative Commons Attribution 4.0 International

**Terms reference:** <https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf>

**Terms reviewed at:** 2026-08-09T18:35:00Z

**Terms version or date:** CDC Terms of use: May 2024; dataset description version v24.03; reviewed 2026-08-09

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** Credit Deutscher Wetterdienst (DWD) as source, comply with CC BY 4.0 attribution, and follow DWD source-notice guidance; indicate modifications where applicable.

**Share alike or derivative requirements:** CC BY 4.0 permits adaptation without a share-alike requirement; attribution and indication of changes remain required.

**Notes:** The source-specific DWD dataset description states that CC BY 4.0 applies and points users to the CDC terms of use. The CDC Open Data directory exposes Terms_of_use.pdf with status May 2024, which states that CC BY 4.0 applies; current DWD Open Data FAQ and legal notices independently confirm reuse of freely accessible DWD geodata under CC BY 4.0 with source attribution. terms_content_sha256 remains null until the exact raw terms bytes can be acquired and hashed in an acceptance environment; no hash is inferred from rendered/search text. This review is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** Subject to CC BY 4.0 and DWD source-attribution requirements. This records the source-rights ceiling only; OpenCatastrophe has not approved or identified any raw artifact yet.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The admitted source metadata describes publicly available meteorological station observations. The DWD dataset description applies CC BY 4.0 to the product, including observations originating from DWD and legally/qualitatively equivalent partner networks.

## Spatial

**Crs:** EPSG:4326

**Extent:** Meteorological stations in Germany

## Temporal

**Extent:** 1989-07-03 onward according to dataset description v24.03; historical files are versioned and quality-controlled, while recent/now data are mutable and not fully quality-controlled.

## Variables and units

### Item 1

**Name:** FX_10

**Unit:** m/s

**Description:** Maximum wind speed observed during the preceding 10-minute interval.

### Item 2

**Name:** FNX_10

**Unit:** m/s

**Description:** Minimum wind speed observed during the preceding 10-minute interval.

### Item 3

**Name:** FMX_10

**Unit:** m/s

**Description:** Maximum derived from one-minute mean wind speeds based on three-second maxima within the preceding 10 minutes.

### Item 4

**Name:** DX_10

**Unit:** degree

**Description:** Wind direction associated with the maximum wind speed in the preceding 10-minute interval.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-09T18:35:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only engineering approval based on the authoritative DWD dataset description, CDC source-specific terms of use, and current DWD legal/Open Data pages. No DWD source ZIP has been committed, acquired into an OpenCatastrophe artifact identity, or approved for repository publication. Raw/derived publication remains blocked pending exact artifact identity and explicit narrower asset review.
