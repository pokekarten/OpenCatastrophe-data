<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-industrial-epc-bridges-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-industrial-epc-bridges-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission discovery of complementary global industrial emitting assets, Spanish building attributes, US bridges and manufacturing supply-chain facility candidates for CAT exposure and synthetic insurer portfolio validation; no data bytes, insurer ownership inference or model admission.

**Entries:** 4

## Climate TRACE Emissions Inventory 5.12.0: asset and source location with optional ownership

**Candidate ID:** `climatetrace.emissions-inventory.v5.12`  
**Provider:** Climate TRACE Coalition  
**Categories:** `industrial_assets`, `facility_identity`, `energy`, `manufacturing`, `economic_activity`, `ownership_context`  
**Spatial scope:** Global; sector-dependent point/centroid or regional aggregation, not an exhaustive survey of insured or physical facilities  
**Temporal scope:** Release 5.12.0 announced 2026-10-29 with monthly emission estimates through 2026-08; provider continuously revises model and historical vintages  
**Resolution / granularity:** Emissions source_id, names, approximated lat/lon or geometry_ref, sector/subsector, annual/monthly emissions and optional company/owner fields; 2.7m sources and 744m underlying assets are not equivalent distinct verified facility locations  
**Potential roles:** `industrial_site_candidates`, `economic_activity_and_bi_priors`, `industrial_asset_geocode_crosscheck`, `corporate_asset_grouping_hypotheses`  
**Access hint:** `official_bulk_csv_download_and_beta_v7_api_access_documented_exact_package_terms_and_source_type_probe_pending`  
**Authoritative source:** <https://climatetrace.org/data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official release 2026-10-29, beta API reference at https://api.climatetrace.org/v7/docs/index.html and terms at https://climatetrace.org/terms. General CC BY 4.0 has exceptions for some external inputs: determine exact selected package/field licence before admitting or publishing bytes. Source centroid can represent an administrative area rather than an individual property. Do not equate emission quantity, source count, source owner or parent with insured TIV, facility occupancy, physical vulnerability, insured risk location, policyholder or claims. Freeze downloaded release, source ID, source_type, time window, geometry provenance, method and confidence; do not use bulk API without rate-limit control.

## Aragon Energy Performance Certificate Register: building attributes and cadastral crosswalk

**Candidate ID:** `es.aragon.energy-efficiency-certificates`  
**Provider:** Gobierno de Aragon, Direccion General de Energia y Minas  
**Categories:** `building_attributes`, `epc`, `floor_area`, `construction_year`, `cadastral_crosswalk`, `spain`  
**Spatial scope:** Spain: Autonomous Community of Aragon only (Zaragoza, Huesca, Teruel); energy-certificated stock rather than full building universe  
**Temporal scope:** Official CKAN dataset reviewed 2026-11-05; catalogue displays real-time update but individual files may have older source and metadata timestamps; pin exact resource and observation date  
**Resolution / granularity:** Certificate records with construction year, built/useful area, type, postal and cadastral reference, address and coordinates where supplied; publication offers province and combined CSV/JSON/XML/XLSX  
**Potential roles:** `buildings_age_and_floor_area_priors`, `epc_to_cadastre_building_matching`, `occupancy_and_vulnerability_archetype_validation`, `spanish_exposure_quality_pilot`  
**Access hint:** `official_ckan_cc_by_4_csv_json_resources_listed_exact_resource_vintage_personal_data_review_and_read_probe_pending`  
**Authoritative source:** <https://opendata.aragon.es/datos/catalogo/dataset/registro-de-certificacion-de-eficiencia-energetica-de-edificios-de-aragon>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official catalogue declares CC BY 4.0 and lists year, area, building type, coordinate and cadastral reference fields; no original resource file downloaded here. Certificates are not unique buildings, can be stale/replaced, may refer to a unit rather than a whole building, and include address-level information requiring privacy/provenance review. Use deduplication, valid-as-of, unit/building and cadastral-ID matching before calculating exposure archetypes. Never infer insurer assignment, replacement cost or CAT claims from EPC alone.

## US DOT FHWA National Bridge Inventory 2026 public Socrata dataset

**Candidate ID:** `us.fhwa.nbi.2026-11-socrata`  
**Provider:** US Federal Highway Administration, Department of Transportation  
**Categories:** `transport_infrastructure`, `bridges`, `construction_year`, `structural_condition`, `critical_infrastructure`, `us_exposure`  
**Spatial scope:** United States, Puerto Rico, Guam and US Virgin Islands according to official Socrata coverage; public road bridge inspection scope  
**Temporal scope:** Official Socrata dataset metadata updated 2026-11-02; underlying temporal applicability 2024-2025 in metadata, record YEAR must be used as true measurement vintage  
**Resolution / granularity:** One row per public-road bridge/year with 124 published columns in live data portal, structural and condition properties, location and bridge identifier; original source linked to FHWA NBI bulk files  
**Potential roles:** `bridge_infrastructure_exposure_index`, `flood_and_earthquake_bridge_risk_pilot`, `road_network_disruption_priors`, `bridge_attribute_and_vintage_validation`  
**Access hint:** `official_public_domain_cc0_socrata_api_dataset_documented_bounded_live_row_probe_pending`  
**Authoritative source:** <https://data.transportation.gov/Roadways-and-Bridges/National-Bridge-Inventory/pced-83j4>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official dataset page lists CC0/Public Domain US Government, 124 fields and 2026-11-02 metadata update. This does not mean every record was surveyed in 2026. Snapshot YEAR, state code and structure number; review bridge coordinates, projected geometry, duplicates, condition code units and historical changes. Public bridge inventory excludes private structures and has inspection/selection bias. Condition ratings are not hazard-conditioned fragility/vulnerability functions or insured values. API response was not independently fetched in this session.

## Open Supply Hub production-location registry and OS ID crosswalk

**Candidate ID:** `opensupplyhub.production-locations`  
**Provider:** Open Supply Hub  
**Categories:** `industrial_assets`, `manufacturing_facilities`, `supply_chain`, `facility_identity`, `corporate_entity_context`  
**Spatial scope:** Global production locations reported by contributors, uneven by geography, sector and contributor; not all factories or insured assets  
**Temporal scope:** Continuously maintained crowdsourced platform; exact profile export snapshot and provenance timestamps are required  
**Resolution / granularity:** Production-location profiles identified by Open Supply Hub OS ID with site-level location and reported supplier/contributor relations where available  
**Potential roles:** `manufacturing_facility_point_index`, `business_interruption_supplier_cluster_priors`, `facility_identity_deduplication`, `industrial_accumulation_scenarios`  
**Access hint:** `search_free_registration_download_up_to_5000_locations_annually_paid_api_and_custom_bulk_exports_permission_scope_review_pending`  
**Authoritative source:** <https://info.opensupplyhub.org/pricing>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official pricing as reviewed 2026-11-05: free registered downloads up to 5,000 locations/year; API starts at USD 225/month and custom bulk exports are separately priced. Public map browsing does not authorize scraping or unlimited programmatic reuse. Records may be contributor supplied, unverifiable, dated or location-approximate; confirm API licence, contributor provenance and allowed derivative/publication scope before any ingestion. Supplier or brand association does not establish insurance participation, insurable interest, TIV or loss experience.
