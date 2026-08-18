<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/wsv.pegelonline.elbe-dresden-discharge.2020-2023.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `wsv.pegelonline.elbe-dresden-discharge.2020-2023.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** wsv.pegelonline.elbe-dresden-discharge.2020-2023

**Provider:** Wasserstraßen- und Schifffahrtsverwaltung des Bundes (WSV) / PEGELONLINE

**Product name:** PEGELONLINE long-term raw discharge observations, Dresden / Elbe

**Version or release:** `null`

**Canonical source:** <https://pegelonline.wsv.de/gast/stammdaten?pegelnr=501060>

**Retrieved at:** 2026-08-10T01:34:00Z

**Retrieval query or filters:** Metadata-only review for station DRESDEN, station number 501060, immutable station UUID 70272185-b2b3-4178-96b8-43bea330dcae, discharge/Q raw observations, predeclared holdout window 2020-01-01 through 2023-12-31. The target long-term download format is JSON with explicit ISO-8601 timezone offsets. No PEGELONLINE observation bytes were acquired or committed.

**Access class:** open

**Modelling layer:** hazard

**Intended use:** Observed river-discharge benchmark for a predeclared 2020-2023 temporal holdout comparison against the already admitted GloFAS v4.0 historical modelled river-discharge product at the Elbe/Dresden gauge. This source is an unvalidated raw observation stream and is not flood extent, inundation depth, damage, vulnerability or insured loss.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** `null`

**Licence name:** Datenlizenz Deutschland – Zero – Version 2.0 (DL-DE-Zero-2.0)

**Terms reference:** <https://www.pegelonline.wsv.de/webservice/downloads>

**Terms reviewed at:** 2026-08-10T01:34:00Z

**Terms version or date:** PEGELONLINE webservice/download licence statement and DL-DE-Zero-2.0 text reviewed 2026-08-10

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** DL-DE-Zero-2.0 imposes no attribution condition. OpenCatastrophe should nevertheless preserve WSV/PEGELONLINE provider identity, station UUID and scientific provenance in any derived evidence.

**Share alike or derivative requirements:** DL-DE-Zero-2.0 permits unrestricted commercial and non-commercial copying, modification, combination and transmission; no share-alike condition applies.

**Notes:** The PEGELONLINE webservice pages explicitly state that the provided unvalidated raw data are freely available under DL-DE-Zero-2.0. The official GovData licence text permits commercial and non-commercial use without restrictions or conditions. General website copyright language is not used to narrow the source-specific webservice data licence.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** The reviewed PEGELONLINE webservice data are reusable under DL-DE-Zero-2.0. This manifest records repository review status approved_metadata_only. At the manifest review time, no exact generated long-term download file had been acquired, hashed or approved for Git publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The reviewed source is a public federal-waterway hydrological station time series. Access logging/account data are service-operation concerns and are not part of the scientific dataset.

## Spatial

**Crs:** Station metadata exposes WGS84 coordinates through the PEGELONLINE REST API; legacy station-page coordinates also document the national reference system. Exact WGS84 values must be frozen from station UUID metadata at acquisition.

**Extent:** Single station DRESDEN on the ELBE, station 501060, UUID 70272185-b2b3-4178-96b8-43bea330dcae, river kilometre 55.63; authoritative supporting hydrology metadata report a 53,096 km2 drainage area.

## Temporal

**Extent:** Predeclared validation slice 2020-01-01 through 2023-12-31. PEGELONLINE exposes long-term Dresden raw discharge beginning 2000-01-01. The long-term JSON download format uses ISO-8601 timestamps with complete local legal-time UTC offsets; parse those explicit offsets to UTC before comparison. The separate free daily-file service documents year-round Central European standard time and must not be used as the timestamp rule for this long-term JSON workflow.

## Variables and units

### Item 1

**Name:** Q / Abfluss Rohdaten

**Unit:** m3/s

**Description:** Unvalidated raw discharge time series associated with the Dresden gauge. Discharge is an observation-derived hydrological quantity and source quality/measurement-rating semantics must be preserved.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-10T01:34:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only approval is bounded to the exact station/variable/2020-2023 holdout role defined in the paired source review. Raw publication remains blocked until the generated long-term JSON source file, request inputs, byte size/SHA-256, explicit timestamp-offset semantics and quality/completeness are frozen and independently reviewed.
