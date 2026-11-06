<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FHWA 2025 NBI versus NTAD 2025 bridge identity and geometry challenger

**Research-only, 2026-11-06. Never insurer exposure/model admission.**

## Why an independent bridge-key and coordinate test?

The [FHWA NBI Socrata source](https://data.transportation.gov/Roadways-and-Bridges/National-Bridge-Inventory/pced-83j4) contains original historical coded latitude/longitude and year/structure IDs. The separate [USDOT/BTS NTAD 2025 point layer](https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_National_Bridge_Inventory/FeatureServer/0) declares source vintage June 20, 2025 and point geometries in EPSG:4326. **Different sources/snapshots are not identical just because both use NBI field names.** Layer EPSG does not verify accuracy or identity of any individual bridge.

The previous original-provider checks verified 100 selected source rows across three samples plus the independent NTAD metadata. This follow-up checks *individual bridge IDs* and *cross-source angular coordinate discrepancies* without calling either provider a geodetic survey.

## Bounded original-source acquisition and matched-pair policy

The independent source runner, research_runners/fhwa_ntad_2025_cross_source_audit_v0.py:

1. Selects exactly **25** original public Socrata rows using explicit 2025 and state 6 filters and deterministic structure-number ordering; retains original string IDs with leading zeros.
2. Constructs **one allowlisted ArcGIS query** from only these verified source identifiers, with original NTAD state codes 06 or 6; requests at most 100 features. No whole-country row scraping.
3. Joins strictly on normalised state and **exact original structure ID**. Distinguishes unmatched, duplicate, malformed and unrelated features; neither fuzzy matching nor silent invented correspondences are permitted.
4. Compares matched historical construction years and coded DDMMSSss/DDDMMSSss positions. Calculates **unsigned** angular magnitude differences against the NTAD point geometry, without inferring sign, datum, ownership or positional accuracy.
5. Returns approximate 0–25 m, >25–250 m, and >250 m discrepancy buckets plus max difference, source response SHA-256, and source coverage counts. These are **diagnostic** thresholds and not a surveyed positional tolerance.
6. Never uploads or prints original bridge IDs or coordinates and never stores original feature rows in Git/Neon. Source requests are HTTPS-only, redirect-denying and strictly byte-bounded.

The source workflow now runs **10 new synthetic adversarial offline tests** before attempting the exact original cross-source sample. Corrupt source keys, unsafe query identifiers, duplicate bridges, wrong states/vintages, truncated results, unparseable formats and spurious model admission must not pass silently.

**Source chronology caution:** NTAD reports a 2025-06-20 provider snapshot, while the separately queried Socrata 2025 records may have changed later. Even successful key matches do not establish historical survey identity or precise spatial accuracy. No SNBI field crosswalk has been validated here.

## Explicit research admission and next gate

The report always exposes model_input_admitted **false**, independent_official_survey_validation **false**, and insured_bridge_TIV_or_fragility_inferred **false**. If no bridge matches, that is a **negative cross-source match outcome**, not proof that the United States is missing bridges. Row-sha receipts bind exact responses but are not independently publisher-signed original file hashes.

Document actual source-run coverage and discrepancy counts only after the exact workflow passes. Independently verify the whole-repository CI on the final PR head, not just the first source revision. Before CAT/insurance calibration, separately establish exact year-specific provider vintages, coordinate/datum/bridge-ID truth, original source rights, physical hazard and validated bridge fragility/TIV.
