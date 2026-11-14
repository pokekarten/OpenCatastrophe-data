<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-building-codes-levee-claims-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-building-codes-levee-claims-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission discovery of four differentiated sources for jurisdictional building-code adoption, modeled code-related annual losses avoided, global flood-defence inventory context and observed insured catastrophe event benchmarks. This registry records public source-page evidence only; it does not admit external bytes, authorize commercial use or imply model fitness.

**Entries:** 4

## Preserved FEMA Building Code Adoption Tracker (BCAT) spatial extract v2

**Candidate ID:** `us.pedp.fema-bcat-archive.20260630.v2`  
**Provider:** Public Environmental Data Partners / Environmental Data and Governance Initiative; original programme FEMA  
**Categories:** `building_codes`, `vulnerability_context`, `jurisdictional_geography`, `united_states`, `resilience`  
**Spatial scope:** United States; tracked state, local, tribal and territorial jurisdictions, subject to FEMA tracking coverage and source geometry constraints  
**Temporal scope:** Uploader says source collected 2025-12-03; archived Zenodo v2 dated 2026-06-30; adoption effective dates and current status require field-level verification  
**Resolution / granularity:** Versioned Zenodo archive with BCAT_gepoackage.zip (1.2 GB), FEMA BCAT.gdb.zip (329.3 MB) and a metadata PDF; jurisdictional building-code adoption records, not building-by-building attributes  
**Potential roles:** `jurisdictional_code_adoption_prior`, `wind_and_seismic_vulnerability_sensitivity`, `building_age_code_crosswalk_challenge`, `regional_resilience_context`  
**Access hint:** `public_zenodo_archived_geopackage_gdb_cc0_metadata_claim_upstream_fema_rights_and_1_5gb_byte_identity_review`  
**Authoritative source:** <https://zenodo.org/records/21084129>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Zenodo names Public Environmental Data Partners as collector, publishes CC0 1.0 metadata and lists file MD5 values; this is a third-party preserved extract of FEMA's BCAT programme, NOT proof that FEMA authored or licensed the archive under CC0. Before acquisition or reuse verify upstream FEMA terms, archive provenance, record-level vintage, jurisdiction coverage and valid date, and compute SHA-256 on exact selected file. Adoption at jurisdiction scale does not prove code compliance, year-built, retrofitting, insured replacement value or event-level vulnerability. No dataset bytes downloaded or approved for modelling.

## FEMA Building Codes Save AALs from the adoption of I-Codes (FEMA-0173)

**Candidate ID:** `us.fema.building-codes-save.aala.2024`  
**Provider:** U.S. Federal Emergency Management Agency (FEMA), Resilience / Risk Management Directorate  
**Categories:** `vulnerability`, `building_codes`, `annualized_losses_avoided`, `hazard_mitigation`, `united_states`, `model_benchmark`  
**Spatial scope:** United States; FEMA catalogue describes local, state, regional and national aggregate outputs  
**Temporal scope:** Nationwide Building Codes Save analysis reports modeled building-code risk reduction for post-2000 construction; data.gov entry FEMA-0173 updated 2024-07, not an annual year-by-year observed claims time series  
**Resolution / granularity:** Official FEMA XLSX `fema_building-codes-save-study-results.xlsx` linked by US catalog.data.gov record FEMA-0173; specific workbook sheets, keys, versions, currency base and hazard breakdown unverified without original file examination  
**Potential roles:** `building_code_aal_reduction_sanity_check`, `hazus_damage_function_comparison`, `flood_wind_earthquake_code_sensitivity`, `model_dependence_and_validation_leakage_check`  
**Access hint:** `official_fema_public_xlsx_government_works_catalogue_exact_workbook_license_and_sha256_pending`  
**Authoritative source:** <https://catalog.data.gov/dataset/aals-from-the-adoption-of-i-codes>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official government catalogue identifies publication FEMA-0173, public access, FEMA publisher, links a government-works licence guidance page and supplies an XLSX resource at https://www.fema.gov/sites/default/files/documents/fema_building-codes-save-study-results.xlsx. These are MODELLED average annual losses avoided (AALA), not historical insured claims, claims frequency, independently observed loss reductions, a carrier TIV book or a vulnerability curve. They depend on Hazus and underlying modeled exposure and hazard assumptions; do not use as both training target and independent validation of a related Hazus-derived model. AALA is a scenario difference in AAL, not AAL or AEP/OEP itself. Verify source workbook table grain, dollar year, historical building stock and peril coverage, potential underlying third-party rights and selected file SHA-256 before model-use/licensing decisions. No XLSX or original source bytes acquired.

## Global Levee Database Inventory (GLDI) supporting gridded inventory

**Candidate ID:** `global.gldi.levee-database-inventory.2025`  
**Provider:** Global Levee Database Inventory research authors, International Journal of Disaster Risk Reduction  
**Categories:** `flood`, `flood_defence`, `levees`, `infrastructure`, `global`, `flood_model_validation`  
**Spatial scope:** Worldwide inventory of available national-scale levee records; spatial coverage and completeness vary substantially with underlying source country and inventory  
**Temporal scope:** Published November 2025; different source record dates and defence construction/upgrade vintages must remain separate  
**Resolution / granularity:** Article advertises immediately available supplementary 0.25-degree ASCII grid and source spreadsheet; individual detailed source data available on request. Inventory aggregates 638 distinct sources in 26 languages.  
**Potential roles:** `flood_defence_data_gap_screen`, `protected_area_sensitivity_prior`, `national_levee_dataset_discovery`, `flood_hazard_overstatement_challenge`  
**Access hint:** `public_article_supplementary_coarse_grid_individual_levee_records_request_author_original_licences_unverified`  
**Authoritative source:** <https://www.sciencedirect.com/science/article/pii/S2212420925006478>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The paper's open-access article licence must not be assumed to cover each underlying national levee record. The advertised 0.25-degree grid is coarse inventory context, not bank geometry, certified flood-protection standard, crest elevation, failure probability or return-period conditional protection. Exact supplementary file/version and rights must be checked before reading or redistribution; detailed data explicitly require author contact. Do not lower location flood risk solely because the inventory indicates a nearby levee. No external data ingested.

## Insurance Council of Australia catastrophe claims data hub

**Candidate ID:** `au.ica.catastrophe-data-hub.2026`  
**Provider:** Insurance Council of Australia (ICA)  
**Categories:** `insured_losses`, `observed_events`, `insurance`, `australia`, `validation`, `insurance_claims`  
**Spatial scope:** Australia; ICA-declared catastrophes and significant events, with variable impacted regions and peril coverage  
**Temporal scope:** Historical catastrophe event register extends to 1967; live data hub updates claims figures, so pin exact as-of date and underlying release when extracting; 2025-2026 resilience report is a distinct annual product  
**Resolution / granularity:** Event and declaration level: claim counts, incurred and outstanding insured costs, closed-rate, names/event codes and impacted regions; no policyholder records, spatial location TIV or insurer-level risk inventory  
**Potential roles:** `event_insured_loss_research_benchmark`, `peril_claims_development_context`, `reported_event_code_crosswalk`, `loss_development_bias_challenge`  
**Access hint:** `public_web_view_only_explicit_noncommercial_ica_disclaimer_commercial_exploitation_prohibited_no_model_ingestion`  
**Authoritative source:** <https://insurancecouncil.com.au/industry-members/data-hub/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The ICA Data Hub disclaimer explicitly prohibits commercial exploitation and reserves all copyright. Noncommercial excerpts require ICA attribution. Preserve these restrictions: publication or insurer-model calibration in commercial operations is NOT allowed by public viewing, and no source bytes/claims figures are admitted. Event losses are reported by members as claims evolve; incurred and outstanding are not ultimate gross or net loss, the declared-event selection is not complete all-peril loss experience, and figures are not independent of the underlying ICA member reporting. A separate written licence and scientific scope review would be needed for a commercial production consumer.
