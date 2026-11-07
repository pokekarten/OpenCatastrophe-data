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

## Exact two-state original source results — 2026-11-06

[Latest original provider workflow #42269564860](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42269564860) completed **SUCCESS** on code commit 4322e1c874b048c9036bfee429cd20c0633eafb3. **14/14** synthetic adversarial tests passed before both independent bounded original 2025 ID/geometry queries.

| 2025 state code | Matched exact unique ID | NBI attribute/age agree | Geometry vs historic DMS up to 25 m | >25–250 m | >250 m | Maximum approximate difference |
|---|---:|---:|---:|---:|---:|---:|
| 6 (California) | 25/25 | 25/25 | 20 | 2 | 3 | 1,676.57 m |
| 36 (New York) | 25/25 | 25/25 | 24 | 1 | 0 | 62.85 m |
| **Total, nonrandom selected records** | **50/50** | **50/50** | **44** | **3** | **3** | **1,676.57 m** |

Both source regions have **25/25** original published NTAD LATDD/LONGDD values concordant with the published NTAD EPSG:4326 *point geometry*, with **zero** >25 m differences. In the same 50 cases, the original historical NBI coded coordinates are exactly equal between the FHWA Socrata and NTAD legacy NBI *attribute* tables. Yet **6/50** original point coordinates and decoded historic NBI angular magnitudes differ by >25 m. This is a bounded source representation discrepancy, NOT independently confirmed accuracy error, insured exposure, observed loss or regional anomaly rate.

| State | Original FHWA 25-row response | Original NTAD 25-feature response |
|---|---|---|
| 6 | 3,676 bytes; SHA256 `f20c98b58f3b34cb14d6370ce61d418ace0c90e734b392e763422b3f3b8a687f` | 7,305 bytes; SHA256 `3cf70827384a2176ac736f3b99388a034e3e1476439fbea4edc0b82834aa5553` |
| 36 | 3,676 bytes; SHA256 `895903b99f08b3c6c5878433cc53d01febd3af22a4245c0d5f588c31d87e9e73` | 7,288 bytes; SHA256 `6e3792dcc3f5c0088adbb3c460002126aa4b716bf2a19f134d3ee3a8a8d17b11` |

This exact source result unambiguously **retains 6 flagged locations for independent source/vintage/geodesy review** and prohibits automatically selecting either source's point value as truth. All raw individual bridge IDs and coordinates were held in ephemeral GitHub runner memory only. Response hashes are not publisher-signed. Even a 25 m discrepancy threshold has not been validated as a legitimate underwriting, flood/earthquake intensity join or claims model coordinate tolerance.

**Decision: Draft / no CAT exposure admission.** Next scientifically relevant checks are official historic NBI-to-current NTAD geometry processing documentation, an independently sourced bridge-position control, and explicit 2025 snapshot vintage reconciliation. Latest full repository CI must be independently assessed at the **last** PR commit rather than assuming a passing source workflow is sufficient.

## Axis-specific source discrepancy diagnosis (2026-11-06 follow-up)

Historical 2025 FHWA codes match the independently published NTAD legacy attribute strings for all 50 audited state-6/state-36 matched bridge IDs; both NTAD LATDD/LONGDD columns match the advertised point geometry in the prior exact-head source proof. A 6/50 diagnostic difference over 25 m between *historical encoded magnitudes* and *the NTAD decimal geometry* is therefore an **internal published data-representation mismatch**; it is not proof of a misplaced bridge, particular editing provenance, wrong insurer, faulty CRS or source-data corruption. Provider metadata describes layer EPSG:4326, but the legacy DMS string conversion's per-site survey truth has not been independently measured.

The new runner additionally classifies **approximate north- and east-component magnitude differences** separately at the diagnostic 25 m threshold, counting north-only, east-only and both-component outliers and max component distances across matched original source IDs. It outputs only aggregate figures and exact source SHA receipts; no per-bridge identifiers, original coordinates or raw original source rows. This helps test whether differences affect one or both coordinate components, but the dimensions remain unsigned/approximate and cannot be interpreted as exact measured vector displacement.

Two additional synthetic negative/positive regression tests check the conservative component-count contract and distinct one-axis/both-axis disagreement; no test permits source admission or automatic insertion into CAT exposures. The original bounded two-state live workflow and full repository CI must be rerun at the final new head. Additional provider documentation and independent position survey are still required before any bridge-level location choice.

## Live original axis-component challenge and diagonal reconciliation (2026-11-06)

[Source-only run #42292525732](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42292525732) **SUCCESS** on code commit af8add4c44ddd2a79a6209cfbe17858c8d592c6f with **16/16** adversarial/offline tests, followed by the original provider re-fetch for both explicit 2025 state samples. No original individual bridge ID/location was exported.

- **State 6 (California):** 25/25 exact identities; **3** bridges with both north and east components above the approximate 25 m threshold; **1** east-only above 25 m; **0** north-only. Maximum separate component magnitudes approximately **824.35 m north** and **1,459.91 m east**. The earlier vector-distance gate classified **5** positions above 25 m: the remaining fifth position is therefore a *diagonal combined-distance exceedance*, although neither individual component exceeds 25 m.
- **State 36 (New York):** 25/25 exact identities; **1** north-only component above 25 m, **0** east-only and **0** both-axis. Maximum approximate component magnitudes **62.51 m north** and **23.18 m east**; vector-distance gate previously found **1** combined exceedance.

This is a source-view comparison, **not** a scientific claim that the true bridge moved north/east or that published geometry is wrong. Components use unsigned legacy source angular magnitudes, not independently surveyed signed geodesy. The diagnostic is now extended to report an explicit **diagonal-only vector threshold** and to assert exact conservation: north-only + east-only + both-axis + diagonal-only = all >25 m vector outliers. Additional synthetic regression verifies a vector over 25 m with each component below 25 m. A full original live run and repository CI on that newest code must independently pass. The persistent rule remains `model_input_admitted=false` for every case.

## Exact original two-state diagonal/axis audit — 2026-11-06

[GitHub original source workflow run #42292781813](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42292781813) completed **SUCCESS** on exact source commit `5d57ccd8398b75a80671db4709b8e456ab479649`. The runner executed **17/17** isolated synthetic adversarial tests, then independently fetched both original 2025 source sets and produced only aggregate source-bound receipts.

| Source region | Exact join count | North-only >25 m | East-only >25 m | Both axes >25 m | Combined >25 m, neither axis >25 m | Total diagonal distance >25 m |
|---|---:|---:|---:|---:|---:|---:|
| California (state code 6) | 25/25 | 0 | 1 | 3 | 1 | 5 |
| New York (state code 36) | 25/25 | 1 | 0 | 0 | 0 | 1 |
| **Total (nonrandom and nonindependent public source views)** | **50/50** | **1** | **1** | **3** | **1** | **6** |

The new **diagonal-only** category closes the previous apparent 4-vs-5 California discrepancy: a two-dimensional vector can exceed a 25 m diagnostic distance even when its north/east components are each at or below 25 m. The new executable conservation contract verifies north-only + east-only + both-axis + diagonal-only = all vector-distance outliers, and the independent source re-fetch returned these exact values.

The original provider source SHA256s remained unchanged under the same bounded query and returned bytes:
- California FHWA: `f20c98b58f3b34cb14d6370ce61d418ace0c90e734b392e763422b3f3b8a687f`; NTAD: `3cf70827384a2176ac736f3b99388a034e3e1476439fbea4edc0b82834aa5553`.
- New York FHWA: `895903b99f08b3c6c5878433cc53d01febd3af22a4245c0d5f588c31d87e9e73`; NTAD: `6e3792dcc3f5c0088adbb3c460002126aa4b716bf2a19f134d3ee3a8a8d17b11`.

## 2026-11-07 follow-up: signed native decimal/point conflict gate

A source-only regression audit identified a false-green in the **internal NTAD LATDD/LONGDD versus NTAD FeatureServer point** diagnostic: the prior formula took absolute values on both signed native coordinates and could report zero discrepancy if an otherwise identical native point was reflected into the wrong hemisphere. The historical FHWA/NBI DDMMSSss and DDDMMSSss comparison remains deliberately **unsigned**: its sign cannot be reconstructed by this research fixture.

The independent NTAD decimal-versus-geometry calculation now retains latitude and longitude signs. A synthetic two-feature red case flips longitude sign for one point and latitude sign for a different point; it must report two native decimal/point discrepancies even though their unsigned historical-code distance remains zero. No row-level coordinates or identifiers enter Git or logs. Existing 50 original source observations and their past recorded results are **historical receipts**, not proof that this new check has rerun on original bytes. Recheck newest-HEAD source job and full CI independently. This improves error visibility only: no surveyed geodetic truth, 2025 source-vintage equivalence, or model/insured-exposure admission is established.

**Hard scientific boundary:** No independent geodetic survey, provider bridge-location editorial pipeline, accurate signed displacement or underlying source-version equality was established. The original per-bridge data remains ephemeral; neither raw identifiers nor coordinates were uploaded, printed or inserted into Neon. This is a conflict **diagnostic**, not a location promotion for CAT intensity footprints or an insured loss probability. Production admission stays **false**.

The latest documentation-only commit following this source receipt requires a fresh exact-head CI result; green source checks from its predecessor must not be attributed to the newer commit without verification.
