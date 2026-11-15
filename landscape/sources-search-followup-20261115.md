<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-search-followup-20261115.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-search-followup-20261115.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-15`  
**Purpose:** Non-admission source discovery for independently verifiable tropical cyclone intensity fields, Central and Eastern European named-insurer statistics, and US crop insurance loss calibration. Every provider and product keeps separate data rights, exact asset identity, and future CAT scientific admission gates.

**Entries:** 3

## ISIMIP3b MIT synthetic tropical cyclone wind and rain fields (20251001)

**Candidate ID:** `isimip.isimip3b.mit-tc-wind-rain-fields.20251001`  
**Provider:** ISIMIP Repository / Potsdam Institute for Climate Impact Research  
**Categories:** `tropical_cyclone`, `windstorm`, `precipitation`, `hazard`, `climate_scenarios`, `model_output`, `global`  
**Spatial scope:** Global gridded tropical cyclone field products; scenario and GCM coverage varies  
**Temporal scope:** Published 2025-10-01, version 1.0 / file family version 20251001; historical and SSP scenarios, synthetic 2015-2100 time span  
**Resolution / granularity:** 88 provider DOI-linked dataset groups, H08 and ER11 parametric wind schemes, windlifetimemax and maxrain NetCDF files split by GCM, scenario and year; example exact 2025 H08 MPI-ESM1-2-HR ssp585 windlifetimemax file ID 1d48a26c-8483-4973-a8ba-8a49624abc55, publisher SHA-512 recorded on file page  
**Potential roles:** `tc_wind_hazard_field_candidate`, `tc_rain_hazard_field_candidate`, `scenario_conditioned_intensity_research`, `tc_model_method_crosscheck`  
**Access hint:** `public_publisher_cc0_field_file_metadata_documented_exact_file_access_and_upstream_track_rights_review_pending`  
**Authoritative source:** <https://data.isimip.org/10.48364/ISIMIP.779038>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The exact published field file page labels its particular NetCDF field CC0 and provides a SHA-512, but no original bytes or trusted response hash were acquired here. The upstream MIT synthetic track product is separately non-commercial without a licence; do not conflate its terms or assets with CC0 field products or infer permission to redistribute tracks. Freeze DOI, specific file UUID, field model, GCM, SSP, year, native units/CRS/time dimensions, checksum and upstream lineage before any download or model-input admission. Spatial intensities are not stochastic losses or an approved insurer portfolio.

## Polisa Central and Eastern Europe insurer-by-line market compilation (README 2026-11-09)

**Candidate ID:** `polisa.cee18-insurer-market-compilation.20261109`  
**Provider:** Polisa independent public insurance market compilation  
**Categories:** `insurance`, `insurer_entity`, `market_share`, `premium`, `claims`, `solvency`, `line_of_business`, `europe`  
**Spatial scope:** 18 Central and Eastern European insurance markets; national legal-entity and local group reporting  
**Temporal scope:** Historical annual company and line figures since 2021; README identifies 2026-11-09.d5ad62, website and export status subject to update  
**Resolution / granularity:** Insurer/year market-level premium, market share, line of business, claims, own funds, SCR, ratios and source URLs; site documentation and README are not proof of an actual complete verified CSV export  
**Potential roles:** `named_insurer_lob_benchmark`, `regional_market_share_prior`, `synthetic_insurer_premium_constraints`, `upstream_regulator_source_linkage`  
**Access hint:** `official_readme_claims_csv_files_site_export_status_conflicts_source_specific_legal_terms_required`  
**Authoritative source:** <https://polisapro.com/data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** README.txt names a versioned polisa-all-markets.csv and per-market exports, while the data landing page retrieved in this review still says files are being prepared. No CSV bytes, row count or source checksum was independently verified. Polisa licences its own calculations CC BY 4.0 but explicitly preserves original supervisory/reporting licences: among others Serbia NBS commercial reuse requires consent; some Hungary, Slovenia and Bosnia and Herzegovina inputs are noncommercial/restricted; Estonia-derived figures can be CC BY-SA. Require country, legal entity/group level, data vintage, row-level source URL, original source rights and double-count checks before CAT calibration. Do not promote site publication into commercial reuse, model input or individual insured exposure.

## USDA Risk Management Agency crop insurance Cause of Loss Summary of Business

**Candidate ID:** `usda.rma.crop-cause-of-loss-summary.2026`  
**Provider:** United States Department of Agriculture, Risk Management Agency (RMA)  
**Categories:** `insurance`, `agricultural_exposure`, `observed_indemnity`, `claims`, `hail`, `flood`, `windstorm`, `crop`  
**Spatial scope:** United States, state and county level crop insurance reporting; reporting coverage and program mix vary  
**Temporal scope:** Historical annual releases 1989-2026 listed by the provider; 2026 and recent years are subject to revision  
**Resolution / granularity:** Official yearly ZIP bundles of pipe-delimited agricultural cause-of-loss Summary of Business data, record layout and month-of-loss fields; potentially insurer counts, premium, indemnities, insured production and crop codes at various levels  
**Potential roles:** `agriculture_cat_loss_validation`, `county_crop_peril_loss_prior`, `crop_portfolio_synthetic_calibration`, `historical_peril_impact_benchmark`  
**Access hint:** `official_yearly_zip_and_record_layout_documented_exact_zip_bytes_and_terms_not_reviewed`  
**Authoritative source:** <https://www.rma.usda.gov/tools-reports/summary-of-business/cause-loss>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider currently lists annual 1989-2026 ZIPs and separate record layouts. No exact versioned ZIP, year-specific layout, source-body SHA-256 or automation licence receipt is present in this review. Verify RMA crop-year versus year/month-of-loss, cause codes and coverage category, policy and claim denominator, reporting revisions and geographic aggregation before joining event footprints. Aggregated indemnity is insured agricultural programme loss, not individual claims, all-insurer commercial property loss, full exposure or directly modelled ELT.
