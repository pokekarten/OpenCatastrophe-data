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

## First original exact-ID/geometric source proof (2026-11-06)

[Original research run #42268810111](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42268810111) **SUCCESS** on commit 5d19c58021226eaa40738e774eb2c78ca2f08016: 10/10 synthetic tests passed and the runner then fetched **25 original 2025 state-6 Socrata bridge rows** and their **25 independently matched NTAD feature records**. All 25 exact source IDs, legacy NBI coded latitude/longitude strings and published construction years agree. Yet the independent published GIS feature points diverge from the decoded original NBI angular magnitudes: **20 within 25 m**, **2 between 25 m and 250 m**, **3 above 250 m**, maximum approximately **1,676.57 m**. This is **not** an observed spatial surveying error or a definitive source-quality ranking; it is a research disagreement involving different source snapshot views and an unsigned coordinate-magnitude distance approximation.

Exact original response SHA-256 values: Socrata 25-row sample **f20c98b58f3b34cb14d6370ce61d418ace0c90e734b392e763422b3f3b8a687f**; NTAD original selected 25-feature JSON **393d8e1f99ec890797acc71d0426733f722b0d47c74e8402a1e44ab0b2e67bb1**. Source bytes remain ephemeral, raw per-bridge identifiers/coordinates not exported.

**Scientific blocker flagged:** Before using a point for hazard intersection, separately compare the NTAD provider's own LATDD/LONGDD decimal attributes to (1) the legacy DMS attributes and (2) the published FeatureServer geometry. The runner now requests these two additional official attribute fields and publishes only aggregate mismatch categories, never raw coordinates. This can distinguish internal provider geometry discrepancy from independent tabular-format discrepancy but **still cannot establish surveyed accuracy, true CRS, licensing or CAT model admission**. New synthetic negative regressions cover disagreeing/missing decimal fields. The new-head live source execution and full CI must be checked independently before recording real provider results.

## 2026-11-06 original NTAD decimal-coordinate triangulation

[Exact source job #42269210588](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42269210588) **SUCCESS** with **12/12** synthetic tests. All 25 same-state exact 2025 bridge identities, historical NBI coordinate codes and construction years agree. **25/25 NTAD LATDD/LONGDD decimal attributes agree exactly with NTAD point geometry** under the displayed magnitude discrepancy metric, while **5/25 NTAD decimal fields differ by more than 25 m** from the *historical NBI attribute codes*, with maximum difference approximately **1,676.57 m**. No surveyed cause was established. Original selected ArcGIS response SHA-256 **3cf70827384a2176ac736f3b99388a034e3e1476439fbea4edc0b82834aa5553**, Socrata original sample SHA-256 **f20c98b58f3b34cb14d6370ce61d418ace0c90e734b392e763422b3f3b8a687f**. Raw row-level geometries remain ephemeral. **Automatic CAT spatial admission remains blocked** even for those 20 positions meeting the diagnostic 25 m bucket, pending independent source/vintage/survey/rights validation.

### Replicate across a separately sourced 2025 state without sweeping

To test whether the observed source-view disagreement is specific to a single ordered state's first 25 bridge records, the original runner now accepts **only explicitly audited state codes 6 and 36**. The live workflow repeats the exact 25-source-row and bounded NTAD ID/geometry query for code **36**, in addition to code **6**. Strict positive and negative synthetic tests cover the second 2025 state and reject arbitrary other state selectors, avoiding uncontrolled whole-country harvesting. The two samples are nonrandom and are not regional/national frequency estimates.

The source/CI result for this *new combined state-6/state-36 HEAD* is pending until independently observed. Both raw provider responses must be source-hashed and reviewed; a successful older state-6 job cannot be used as proof for the new state-36 execution.
