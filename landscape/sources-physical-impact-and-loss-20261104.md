<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-physical-impact-and-loss-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-physical-impact-and-loss-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of source-original physical climate risk hazard indicators, a multi-peril impact-function discovery portal and a licensed historical US disaster-loss database. These are distinct capabilities, not independently verified CAT loss inputs.

**Entries:** 3

## OS-Climate Physrisk public hazard-indicator collection

**Candidate ID:** `osclimate.physrisk.hazard-indicator-public-bucket`  
**Provider:** OS-Climate / Open Source Climate / AWS Open Data  
**Categories:** `hazard`, `multi_hazard`, `climate_risk`, `indicator_catalogue`, `cloud_open_data`  
**Spatial scope:** Multi-region/global depending on each individual hazard array, scenario and original data source  
**Temporal scope:** Historical baselines and climate projection periods vary by individual indicator; collection is updated and not a single fixed release  
**Resolution / granularity:** 3-dimensional hazard indicator arrays indexed by hazard-specific return period or threshold and spatial grid, with inventory paths, CRS, units and scenario metadata; public S3 bucket without AWS credentials  
**Potential roles:** `hazard_indicator_inventory_bridge`, `return_period_intensity_benchmark`, `asset_level_hazard_sampling_preflight`  
**Access hint:** `public_anonymous_s3_collection_mixed_upstream_rights_individual_product_review_required`  
**Authoritative source:** <https://registry.opendata.aws/os-climate-physrisk/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** AWS registry identifies s3://os-climate-physical-risk (us-east-1), accessible with aws s3 ls --no-sign-request. Canonical inventory at https://github.com/os-climate/hazard/blob/main/src/inventories/hazard/inventory.json maps individual hazard resources to model/provider lineages and index semantics. https://github.com/os-climate/physrisk is the separate Apache-2.0 computational engine, NOT a new independent hazard observation. The inventory includes WRI Aqueduct Floods products already represented in OpenCatastrophe; preserve upstream identity and avoid counting transformed indicators as independent validation. A listing or unrestricted AWS notice is not an exact-asset SHA, original-vintage proof, automatic commercial sublicense of upstream assets, or scientific/model admission. Crucially, the original OS-Climate hazard inventory labels Jupiter-derived layers as Commercial and expressly disallows use related to emergency management, public safety, physical safety or property endangerment; anonymous S3 readability and the broad AWS registry notice do not override such provider-specific terms. Jupiter data must not be imported or used in CAT modelling absent direct written clearance.

## OpenVulnerability multi-hazard physical impact model discovery library

**Candidate ID:** `ucl.openvulnerability.impact-model-portal.2026`  
**Provider:** Roberto Gentile / University College London and collaborators  
**Categories:** `vulnerability`, `fragility`, `consequence`, `multi_hazard`, `model_catalogue`, `built_environment`, `critical_infrastructure`  
**Spatial scope:** Model-specific local, regional and international applicability; no one global loss calibration  
**Temporal scope:** Continuously updated model library, reported approximately six-month refresh cadence; catalogue observation 2026-11-04  
**Resolution / granularity:** Model-level hazard, GED4ALL asset taxonomy, intensity variable, fragility/vulnerability/consequence category, source provenance and downloadable individual Excel model files  
**Potential roles:** `multi_peril_vulnerability_discovery`, `intensity_damage_function_crosswalk`, `curve_provenance_and_applicability_review`  
**Access hint:** `public_search_free_individual_excel_download_institutional_bulk_or_api_partnership_required`  
**Authoritative source:** <https://openvulnerability.robertogentile.org/faq>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official FAQ distinguishes fragility state probabilities, vulnerability expected loss ratios and consequence repair-cost/downtime outputs; they are not interchangeable. Includes source collections already registered separately in OpenCatastrophe (e.g. ESRM20, GEM, JRC and HAZUS): these must be cross-linked, not recounted as independent originals. Browse and single-model downloads are free according to provider FAQ; organisational bulk/API access needs partnership. The portal is a discovery/harmonisation layer, not a blanket licence for each underlying model; verify exact model source, units, damage metric, site/structure fit and original rights before any conversion, redistribution or CAT engine use. Provider site terms: https://openvulnerability.robertogentile.org/terms.

## SHELDUS spatial hazard events and losses database for the United States

**Candidate ID:** `asu.sheldus.us-county-hazard-losses.2026`  
**Provider:** Center for Emergency Management and Homeland Security / Arizona State University  
**Categories:** `observed_impact`, `historical_disasters`, `economic_loss`, `validation`, `multi_hazard`, `united_states`, `licenced_data`  
**Spatial scope:** United States by state and county, with source-dependent hazard/event coverage  
**Temporal scope:** Historical event records and aggregated series; version and extraction period to be pinned at authorised retrieval  
**Resolution / granularity:** CSV historical hazard losses by county/date/hazard and named event; source provides separately priced raw records and spatial/temporal/hazard aggregate downloads  
**Potential roles:** `regional_disaster_loss_challenge`, `county_peril_loss_sanity_check`, `event_and_impact_lineage_reconciliation`  
**Access hint:** `licensed_account_and_paid_query_raw_or_aggregated_csv_no_bulk_redistribution_authority`  
**Authoritative source:** <https://cemhs.asu.edu/sheldus/products>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher requires registered account and query/purchase, with commercial raw-record pricing and subscriptions for aggregated downloads; exact end-user licence governs use. South Carolina data have a stated free-access exception, which does NOT imply all-state redistribution. Potential overlap/derivation from NOAA Storm Events means this is not automatically an independent holdout. Raw event losses and aggregate economic damage do not imply insured losses or company-level TIV; review definitions, inflation, hazard labels, joins, source vintage and allowed derivative scope. Do not automate acquisition or ingest into public or private production stores without explicit rights and original-byte provenance.
