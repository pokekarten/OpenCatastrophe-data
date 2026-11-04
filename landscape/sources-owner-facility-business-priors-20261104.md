<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-owner-facility-business-priors-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-owner-facility-business-priors-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of non-CAT industrial facility identity, corporate asset ownership and firm operations data that may constrain synthetic physical exposure and business-interruption priors; no observed insured portfolio or model admission.

**Entries:** 5

## Global Energy Monitor Global Energy Ownership Tracker

**Candidate ID:** `gem.global-energy-ownership-tracker`  
**Provider:** Global Energy Monitor  
**Categories:** `industrial_assets`, `energy`, `ownership_graph`, `entity_resolution`, `critical_infrastructure`  
**Spatial scope:** Global; asset-type coverage limited to its named coal, power, oil and gas, mining, steel, cement, bioenergy and pipeline trackers  
**Temporal scope:** Evolving release family; official page observed 2026-11-04, exact download release and ownership as-of dates still to be pinned  
**Resolution / granularity:** Tracked asset IDs and direct-to-ultimate parent ownership chains, declared ownership fractions, entity references and asset context  
**Potential roles:** `asset_to_corporate_group_graph`, `industrial_accumulation_prior`, `cross_border_group_asset_reconciliation`, `business_interruption_network_context`  
**Access hint:** `official_download_page_research_only_exact_release_rights_review_pending`  
**Authoritative source:** <https://globalenergymonitor.org/projects/global-energy-ownership-tracker>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from already registered GEM Global Gas Infrastructure Tracker and WRI power plant snapshots: this product explicitly links multiple physical asset types to chains of direct and ultimate owning entities. Ownership stakes and entity labels are not insured interests, policies, insured sums or claims. Do not infer an LEI match or assume coverage of every facility. Freeze source tracker, asset/entity IDs, as-of vintage, ownership share, confidence, inclusion threshold and effective ownership conventions before use.

## US EPA ECHO Exporter 2.0 and Facility Registry Service linkage files

**Candidate ID:** `us.epa.echo-exporter-frs.v2`  
**Provider:** US Environmental Protection Agency  
**Categories:** `industrial_facilities`, `facility_identity`, `industry_classification`, `us_exposure`, `environmental`  
**Spatial scope:** United States; EPA-regulated facilities only, not the universe of US businesses  
**Temporal scope:** Exporter 2.0; official weekly refresh, exact ZIP release and observation dates not yet frozen  
**Resolution / granularity:** Over 1.5 million regulated facility summary records in published ECHO Exporter; available latitude/longitude, industry/permit fields, Facility Registry Service (FRS) ID and cross-program linkage files  
**Potential roles:** `industrial_facility_geocoding`, `frs_id_entity_crosswalk`, `industrial_exposure_land_use_validation`, `commercial_building_occupancy_prior`  
**Access hint:** `official_bulk_zip_and_fr_records_readable_public_page_rights_science_review_pending`  
**Authoritative source:** <https://echo.epa.gov/tools/data-downloads>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EPA states the Exporter can be joined to other ECHO collections through FRS identifiers. Facility records can include duplicated program identities, missing/imprecise coordinates, inactive/historical sites and regulated activities rather than insured buildings. Regulatory presence or emissions do not establish replacement values, ownership of risk, policy coverage or catastrophe losses. Preserve FRS registry ID, program code, dates and coordinate-quality flags; only acquire fixed original files after source rights review.

## World Bank Enterprise Surveys formal-sector published indicators and research microdata

**Candidate ID:** `worldbank.enterprise-surveys.formal-indicators`  
**Provider:** World Bank Group  
**Categories:** `firm_surveys`, `economic_activity`, `business_interruption`, `industry`, `cross_country`  
**Spatial scope:** More than 150 economies; economy/subnational aggregates and separately accessible sampled firm microdata  
**Temporal scope:** Surveys have country-specific vintages and revisions; record each exact economy/year/survey edition  
**Resolution / granularity:** Survey-derived indicators on business operations, infrastructure interruptions, sales, employment and firm characteristics; public aggregate series and separate microdata access  
**Potential roles:** `sector_business_interruption_severity_prior`, `noncat_business_loss_baseline`, `economic_vulnerability_validation`, `synthetic_industry_size_calibration`  
**Access hint:** `public_aggregate_indicators_microdata_login_and_separate_rights_review`  
**Authoritative source:** <https://www.enterprisesurveys.org/en/data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Separate published aggregates from confidential/anonymized and differently licensed country microdata. Sampling weights and standard errors matter. Electricity outage loss as a share of sales is a non-CAT disruption indicator, not a cyclone/flood occurrence probability, facility coordinate, insured claim, physical damage function or business interruption policy; never directly calibrate a CAT BI vulnerability curve without independent event-conditioned evidence.

## US EIA Form 860 annual plant, generator, utility and generator ownership data (2025)

**Candidate ID:** `us.eia.eia860.annual.2025`  
**Provider:** US Energy Information Administration  
**Categories:** `power_generation`, `industrial_assets`, `eia_plant_id`, `ownership`, `us_exposure`  
**Spatial scope:** United States electric power plants above 1 MW combined nameplate threshold; EIA survey scope and exceptions apply  
**Temporal scope:** EIA Form 860 reporting year 2025, exact official ZIP and workbook release/update date to be frozen  
**Resolution / granularity:** Plant, utility and individual generator workbook tables, with a separate ownership table for jointly or third-party-owned generators; contains official plant and generator identifiers  
**Potential roles:** `eia_plant_id_identity_bridge`, `epa_frs_eia860_plant_crosswalk`, `power_asset_capacity_prior`, `generator_owner_entity_research`  
**Access hint:** `official_annual_zip_xlsx_public_download_original_hash_and_rights_review_pending`  
**Authoritative source:** <https://www.eia.gov/electricity/data/eia860/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from existing EIA-860M *preliminary monthly* candidate; annual 2025 reports plant/generator and operator/owner records and the EIA plant ID is a potential intermediate key to EPA FRS program EIA-860 ID (documented by USEPA FRS samples). The 2025 ownership schedule does not record each wholly operator-owned generator as a separate owner row. A plant may have multiple generators and owner shares. No FRS-GEM corporate/asset identity, installed replacement value, insured exposure, insurer membership or treaty can be concluded from EIA IDs alone. Pin exact original EIA sheet headers, release, source rights and vintage.

## Global Energy Monitor Global Integrated Power Tracker September 2026

**Candidate ID:** `gem.global-integrated-power-tracker.2026-09`  
**Provider:** Global Energy Monitor  
**Categories:** `power_generation`, `building_exposure_context`, `industrial_assets`, `facility_locations`, `owner_graph`  
**Spatial scope:** Global power facility and unit/phase coverage with underlying tracker-specific minimum sizes and differing site-accuracy levels  
**Temporal scope:** September 2026 release built from multiple constituent technology tracker releases of different dates  
**Resolution / granularity:** GEM unit/phase ID and GEM location ID; technology, capacity, status, location-accuracy and stated owner/parent evidence at unit, plant or phase grain depending on technology  
**Potential roles:** `gem_site_id_model`, `epa_eia_gem_crosswalk_research`, `power_facility_exposure_prior`, `source_vintage_and_location_accuracy_gate`  
**Access hint:** `original_gem_release_download_page_workbook_exact_schema_terms_review_pending`  
**Authoritative source:** <https://globalenergymonitor.org/projects/global-integrated-power-tracker>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Different product from existing GEM Global Energy Ownership Tracker (corporate hierarchy), and also from the registered GEM Global Gas Infrastructure Tracker. The GIPT methodology identifies unit or phase records separately from project-location IDs, and some coordinates are approximate. The verified methodology does not establish an automatic universal EPA FRS or EIA-860 plant-ID field on all GEM rows. Any EIA-to-GEM bridge requires distinct original source IDs and facility-vs-unit cardinality validation before linking owners, let alone inferring insured value.
