<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CAL FIRE DINS ↔ FRAP: original incident-field concordance, research v0

**Status:** candidate identity preflight only. No real point/polygon data, source bytes, insurance exposure, claims, API queries or proven event joins.

## What original sources actually say

- CAL FIRE DINS [POSTFIRE layer 0](https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/POSTFIRE_MASTER_DATA_SHARE/FeatureServer/0) exposes `INCIDENTNUM`, `CALFIREUNIT`, `INCIDENTSTARTDATE`, `HAZARDTYPE`, `INCIDENTNAME` and point geometry. Its service metadata gives a DINS incident example with a CAL FIRE prefix followed by numeric local incident code. Neither `INCIDENTNAME` nor a six-digit suffix alone is a unique cross-product identifier.
- CAL FIRE FRAP [historical fire perimeter layer 0](https://services.arcgis.com/V6ZHFr6zdgNZuVG0/ArcGIS/rest/services/California_Fire_Perimeters/FeatureServer/0) exposes `INC_NUM` (local number, up to eight characters), `UNIT_ID`, `ALARM_DATE`, `YEAR_`, `FIRE_NAME`, and `IRWINID` for edition `firep25_1`. Its [service root](https://services.arcgis.com/V6ZHFr6zdgNZuVG0/ArcGIS/rest/services/California_Fire_Perimeters/FeatureServer) describes gaps, updates and multiagency source selection. The FRAP original 2023 data dictionary documents `INC_NUM` as emergency-command-center numbering, not as a universal DINS event key.
- DINS is an inspected-structure database (damaged-only records before 2018); FRAP maps wildfire perimeters under varying mapping thresholds. They are distinct, incomplete observation frames.

## Conservative bounded code

`scripts/calfire_dins_frap_identity_preflight_v0.py` accepts a **single incident-summary** and at most 25 preselected FRAP metadata candidates. Supported DINS example-format `CA<UNIT> <six digit code>`, FRAP `INC_NUM`, `UNIT_ID`, `ALARM_DATE` and integer `YEAR_` are checked with explicit literal and calendar constraints. No provider-derived normalization or real data access is implemented. The supported format is intentionally narrow: other official numbering systems must be independently mapped and must not be forced through this gate.

- DINS hazard must be `Fire`; unit within DINS number must equal its independently declared CAL FIRE unit.
- FRAP local incident code must preserve all leading zeros and match the **exact** extracted six-character text, not the integer or incident-name spelling.
- FRAP `ALARM_DATE` and `YEAR_` must agree; the DINS start and FRAP discovery dates must be within three days in the same calendar year. Three days is a conservative candidate-screening parameter **not a scientifically proven maximum fire-date difference**. Legitimate cases outside that range remain unlinked and need manual investigation.
- Wrong units, differing event identifiers, date conflicts or unsupported DINS incident-number formats block or yield no candidate.
- Multiple otherwise matching perimeter headers produce `ambiguous_candidates_quarantined`, **not** one selected polygon. A unique candidate still produces `candidate_requires_original_identity_review`, **not** `matched`.
- `IRWINID` is visible on the FRAP side but lacks an equivalent DINS join field in the published schema. It is useful for subsequent *original evidence corroboration*, not an automatic DINS join.
- `origin=synthetic` permits no SHA claims; `origin=externally_prepared_incident_metadata` requires two lower-case SHA-256-shaped source snapshot references. The tool **does not verify** those hashes against original data, prove the provider mappings or authorize creation of original feature snapshots.
- Input is capped at 16 KiB; exact safe field names prohibit addresses, APNs, individual inspections, coordinates and geometry. No automatic point-in-polygon spatial overlay or insurer-loss calculation is possible here.

## What would prove a real linkage

Obtain one *authorized, version-frozen* non-sensitive incident summary from each original provider and independently confirm identifier lineage (e.g. provider incident-number cross-reference and date/agency fields). Pin provider URL, request/edition, response bytes SHA-256, retrieval UTC, known relevant timezone and revision. Resolve duplicate fire perimeters and cross-jurisdiction event naming. Only then, after access/privacy/science approval, compare a spatially valid DINS inspection frame with its contemporaneous FRAP polygon and a **separate** complete building inventory and fire intensity evidence. Final perimeter coverage is not observed local fire severity.

The source-linkage hypothesis is also registered in `scripts/source_linkage_audit_v0.py`, preserving `automatic_source_join_allowed=false`, `scientific_independence_proven=false` and `model_input_admitted=false`.
