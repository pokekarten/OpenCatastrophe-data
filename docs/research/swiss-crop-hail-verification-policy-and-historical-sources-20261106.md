<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Swiss crop hail: publication benchmark, sample coverage and historical land-use

**Scope: research-only / no model admission. Reviewed: 2026-11-06.**

Peer-reviewed method: Portmann et al., NHESS 24, 2541–2558 (2024), sections 2.2, 2.4 and 2.5:
https://doi.org/10.5194/nhess-24-2541-2024 .

## Two distinct source support questions

1. **Coordinate-key presence**: The existing original-source spatial audit checks whether a damage-grid coordinate matches a coordinate appearing in the 2021 crop exposure HDF5. A real GitHub run checked all 24 crop/resolution pairs and reported 19 pairs with all positions matched. In five pairs, 1,003 damage-grid positions lack a matching exposure coordinate, of which 461 are associated with 550 positive event-grid impact entries. These are not individual insurance claims, insured loss amounts, or distinct events.
2. **Nonzero crop exposure**: The paper defines exposed raster cells from actual crop-field count (normally at least one field; more for density sensitivity). A matching coordinate **does not prove a positive field count**. Our current 1,003/550 mismatch evidence is therefore a diagnostic of position support, **not** a complete count of positive observed damage on zero-crop-exposure grid cells. This second, scientifically essential mask has not yet been independently verified on original values.

The paper explicitly describes damage observed without matching exposure. This is a **documented limitation of the study**, not newly discovered source corruption. The paper used 2021 crop geography for 2017–2021 hail events, and reported relatively small differences between observed mismatches in older and 2021 events. Historical crop changes are thus only a **hypothesis**, not a proven source of discrepancy. Roughly one-quarter of the claims in the study lacked field-level coordinates and were redistributed at farmland/vineyard locations in the original research. Never claim all raster observations have exact observed per-claim field locations.

## Separate reference and diagnostic forecast scores

In section 2.5 the paper's 2×2 contingency scores are computed only on **nonzero exposed cells**, yielding hits, false alarms, misses and correct negatives; HSS, POD, FAR, frequency bias and CSI measure skill. New research_runners/swiss_crop_hail_verification_support_v0.py implements:

- **Paper-conditional benchmark:** score only true crop-exposure cells. Zero-exposure damage observations are excluded exactly as specified in the publication.
- **Additional diagnostic:** preserve all positive out-of-exposure observations as *additional misses* under an exposure-gated binary forecast, but do not invent extra negatives on arbitrary non-exposed geography. This diagnostic has a different sample population; it is **not the published HSS** and not a fully comparable whole-area forecast verification.

Both are synthetic-ready with explicit undefined-denominator and mask-mismatch guards. Actual published HSS values have **not** been reproduced from radar intensities yet. Another function reads only the versioned aggregate source TOML (no downloaded data) to calculate the *fraction of recorded positive event-grid observations outside the geometry-key footprint*, clearly labeled as position coverage, not crop exposure coverage or model skill.

Based on the fixed, previously verified original source report:

| Crop / grid resolution | Positive event-grid entries | Positive entries on positions absent from exposure geometry | Fraction outside geometry |
|---|---:|---:|---:|
| Maize, 2 km | 1,713 | 247 | 14.42% |
| Rapeseed, 2 km | 1,113 | 133 | 11.95% |
| Wheat, 2 km | 1,428 | 170 | 11.90% |

Across **all 24 crop×resolution comparisons**, which overlap both geographically and by historical event, 550 of 28,674 recorded positive entries have no matching 2021 source-coordinate key (approximately 1.92%). This is not an estimate of unique claims or insured losses.

Offline source-only proof:

    python -m unittest -v tests.test_swiss_crop_hail_verification_support_v0
    python -m research_runners.swiss_crop_hail_verification_support_v0

These fail closed if the original 24-pair source receipts have changed or imply production admission.

## Next exact source-validation steps

1. Inspect bounded HDF5 exposure *column-name* labels first. A change to the existing ephemeral original-HDF5 structure workflow will report field names (not private coordinates, crop quantities or numeric impact values) so the true field-count column can be identified instead of guessed.
2. Identify crop field count and/or crop area, check units, CRS, nodata, grid indexing, and then run a true nonzero-exposure support comparison for each historical event. Report paper-like excluded positives and a separate sensitivity result.
3. Independently reproduce the original published binary hail footprint formula and its contingency scores. Pay attention to threshold choice and 1/2/4/8 km aggregation, reported event count, and sample-selection dependence. A different crop-density threshold is not automatically a better insurance model.
4. Only after verified crop exposure values, licensed sources, independent annual event frequencies, damage severity and financial policy/treaty terms may a separate insured-loss EP model be evaluated.

## Historical agricultural land-use sources: evidence and rights

The Federal Office for Agriculture publishes MGDM 153.1 crop use/land-utilisation geometry with canton data via geodienste.ch:
https://www.blw.admin.ch/de/landwirtschaftliche-kulturflaechen
https://www.geodienste.ch/services/lwb_nutzungsflaechen

National current annual data existence does **not** establish free complete original historical versions for every year 2017–2020.

Canton Bern's official older LANDKULT/NUTZFL metadata specifically lists archived **2018, 2019, 2020 and 2021** annual snapshots, but states that archived geodata are supplied through a **paid order**. Original provider PDF:
https://geofiles.be.ch/geoportal/pub/metaarchiv/LANDKULT/LANDKULT_NUTZFL_2024_01_de.pdf

These are a **candidate historical source only**: neither original archived bytes, licensing, price, historical polygon coverage nor portability across Swiss cantons have been checked. Historical data must not be copied into public GitHub or an insurer database without source-specific rights checks.

**Strict boundary:** No annual hail catalogue rate, insured sum, individual claim amount, quantitative severity model, GUL/IL/RI, or gross/net OEP/AEP curve has been validated or admitted by this work.

## New original-byte verification: released HDF5 actual n_fields source mask

Passing original-source workflow: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42245432836 . Its execution downloaded both originally published ZIPs into temporary runner storage, checked publisher MD5, opened all 24 original HDF5 crop/damage pairs, read each exposure's actual n_fields field and distinguished three categories for every positive observed event-grid matrix entry: n_fields >= 1, existing source coordinate with n_fields == 0, and coordinate absent from the source exposure table.

- 28,674 positive event-grid matrix entries across all overlapping crop/resolution comparisons: **28,124 on n_fields >= 1 source support**, **0 on present coordinates with n_fields == 0**, **550 at positions entirely absent from the released 2021 exposure table**.
- In these exact published HDF5 files the exposure table already contains **no positions with n_fields == 0**. Thus a rounded-coordinate key is equivalent to n_fields >= 1 **for this released source version and default threshold 1 only**. Do not generalise to historical or alternative crop data, or higher n_fields thresholds.
- Rechecked out-of-support positive entries: maize 2 km 247, rapeseed 2 km 133, wheat 2 km 170; other crop/resolution published positive entries are within released 2021 support. These are sparse event-by-raster observations, not identifiable insurance claims.
- **Scientific interpretation:** The primary paper's field-level / municipality-imputed data and evaluation populations need not be identical to the published processed gridded HDF5 files. Its reported 1 km no-exposure claim fractions cannot be reconstructed by treating the current released gridded file as raw insurer claims. This difference is not evidence of published-paper error or time-change causality.

The deterministic aggregate per-crop original-source evidence is preserved in research/observations/swiss_crop_hail_original_n_fields_support_v0.toml. No values or original files are stored in Git or Neon; rights, original HSS reproduction, annual frequencies, financial loss severities and production admission remain unresolved.

## Published model-code review (read-only, version tag 1.0)

Original source: https://github.com/raphael-portmann/202403_crop_hail_damage_footprint/tree/1.0 and exact publisher release https://zenodo.org/records/12784190 . The code has **not been imported or executed** on original data by OpenCatastrophe.

The versioned utility.py function for converting raw crop damage grids to CLIMADA Impact selects rows where the supplied NetCDF field n_fields_exp is strictly positive. Separately, its exposure_from_gpd function drops exposure rows where crop-area value is zero. This **demonstrates an explicit source-filtering stage in published code** and is compatible with the finding that the released HDF5 exposure tables contain no n_fields == 0 rows. It does **not prove** the exact released HDF5 creation notebook applied that same code path for every crop and resolution, nor does it reconstruct underlying claims without the unreleased preprocessing inputs.

The README also states that certain plots require additional NetCDF files or randomized municipality-claim placement datasets that are **available upon request**, not automatically included among the published four Zenodo releases. Therefore, the original field-level claims-based mismatch and some paper figures are not reproducible from the eight checked released files alone.

**Annual-frequency warning:** The published Impact conversion helper assigns its event frequency array the value one and computes some event-mean quantities using a span of selected original dates. Those are artefacts of a historical study and **not a defensible independently calibrated yearly stochastic CAT occurrence model**. OpenCatastrophe must not convert this metadata into annual AEP/OEP without a complete independently validated annual hail event set and losses. See the publication itself for the study objective, binary damage footprint skill, and its stated source limitations.
