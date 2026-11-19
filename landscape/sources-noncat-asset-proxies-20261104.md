<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-noncat-asset-proxies-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-noncat-asset-proxies-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of unconventional public administrative, procurement, emissions and transport asset data that may calibrate synthetic insured exposure; no raw source bytes, portfolio assertions or commercial model permissions are granted.

**Entries:** 6

## NYC PLUTO tax-lot land use and building characteristics 26v2

**Candidate ID:** `nyc.dcp.pluto.26v2`  
**Provider:** New York City Department of City Planning (DCP)  
**Categories:** `cadastral_parcels`, `building_characteristics`, `land_use`, `valuation_proxy`  
**Spatial scope:** New York City five boroughs, United States; tax lots rather than all buildings or individual insured locations  
**Temporal scope:** DCP published version 26v2 on 2026-08-24; field vintages differ across contributing city agencies  
**Resolution / granularity:** Tax-lot CSV with official Borough-Block-Lot (BBL) identifiers, use, building area, unit counts, vintage, zoning and city-agency attributes; current Socrata table and separately versioned GIS releases  
**Potential roles:** `building_attribute_join_by_tax_lot`, `occupancy_and_floor_area_prior`, `assessed_value_proxy_challenge`, `administrative_exposure_version_control`  
**Access hint:** `public_socrata_csv_odata_metadata_only_review_exact_version_and_reuse`  
**Authoritative source:** <https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks/about_data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original DCP dataset identifies 26v2 and 2026-08-24 update. One row usually represents a tax lot, not a building: lots can have multiple structures and condominium units are aggregated at complex level. Tax assessment, if selected and documented at field level, is neither market value nor insured replacement cost/TIV. Pin field dictionary, release, BBL normalization, null/zero distinctions and DCP/DOF upstream lineage. No automatic parcel-to-policy or property-owner inference.

## NYC Local Law 84 annual building energy and water benchmarking disclosure

**Candidate ID:** `nyc.dob.ll84.energy-water.2022plus`  
**Provider:** New York City Department of Buildings (DOB)  
**Categories:** `building_energy`, `building_use`, `floor_area`, `exposure_enrichment`  
**Spatial scope:** New York City covered larger buildings and qualifying property classes; selection-biased relative to entire building stock  
**Temporal scope:** Data reported 2023 onwards for calendar years 2022 onwards; official dataset metadata updated 2026-04-21  
**Resolution / granularity:** Property-level annual energy and water benchmarking records; official property identifiers with possible multi-valued BBL or Building Identification Number (BIN) links  
**Potential roles:** `large_building_occupancy_and_area_proxy`, `energy_intensity_vulnerability_covariate`, `nyc_pluto_many_to_many_join_challenge`  
**Access hint:** `public_socrata_json_csv_odata_field_dictionary_rights_review_pending`  
**Authoritative source:** <https://data.cityofnewyork.us/Environment/NYC-Building-Energy-and-Water-Data-Disclosure-for-/5zyy-y8am/about_data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider states annual disclosure, not comprehensive citywide coverage. A reported property may contain multiple BBLs or BINs; the record is not necessarily one building. A high consumption number does not establish facility replacement value, occupancy at a specific date, business-interruption limits or insurer. Review field units, missingness and current reporting obligations before any derived use.

## EU Tenders Electronic Daily linked open public procurement notices

**Candidate ID:** `eu.publications-office.ted.open-data`  
**Provider:** Publications Office of the European Union  
**Categories:** `public_procurement`, `construction_cost_proxy`, `public_facilities`, `supply_chain`  
**Spatial scope:** European Union and other contracting jurisdictions represented in TED notices; not all spending or privately owned assets  
**Temporal scope:** Historical and current TED notices spanning legacy standard forms and eForms; each notice has its own publication and contract dates  
**Resolution / granularity:** Contract and award notices as RDF/SPARQL and XML/search APIs with buyers, suppliers, CPV, award amounts and reported place-of-performance fields where present  
**Potential roles:** `construction_and_repair_unit_cost_research`, `public_infrastructure_capex_context`, `critical_facility_industry_cpv_prior`  
**Access hint:** `public_sparql_linked_open_data_ted_search_api_per_notice_scope_review`  
**Authoritative source:** <https://data.ted.europa.eu/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original EU provider describes RDF linked open data, SPARQL, notice lookups and downloadable results. CPV and award values concern contracted works/supplies, NOT building replacement cost, policy limit or completed asset value. Notice-level changes, frameworks, lots and amendments can duplicate contract amounts; subthreshold tenders, site coordinates and actual expenditure are incomplete. Preserve eForms versus legacy structure and rights/attribution review.

## EEA EU ETS Union Registry emissions and installation context through 2025

**Candidate ID:** `eea.eu-ets.union-registry.2025`  
**Provider:** European Environment Agency / European Commission Union Registry  
**Categories:** `industrial_activity`, `industrial_exposure`, `energy`, `facility_context`  
**Spatial scope:** EU ETS participating jurisdictions including EU Member States and relevant linked EEA jurisdictions; sector and installation participation bounded by ETS rules  
**Temporal scope:** September 2026 release covering 2005-2025 as published in EEA Datahub; regulatory scope changes over time  
**Resolution / granularity:** Public CSV/TXT/SQL downloads and aggregated viewer by country, activity and year; any installation-level identity/coordinates require separate verified field-level checks  
**Potential roles:** `industrial_activity_type_prior`, `large_emitter_site_reconciliation`, `industrial_concentration_and_time_context`  
**Access hint:** `public_eea_2026_09_csv_sql_download_original_registry_lineage_rights_review`  
**Authoritative source:** <https://www.eea.europa.eu/en/datahub/datahubitem-view/98f04097-26de-4fca-86c4-63834818c0c0>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EEA lists a September 2026 EU ETS dataset for 2005-2025. The viewer is aggregated by country/sector/year; do not assume a geocoded facility-level source, stable operator identities, plant capacity or covered insured value without inspecting the exact downloaded fields and Union Registry relationship. Emissions tonnes and allowance quantities are NOT property TIV, cargo inventory, fragility or policy count. Preserve ETS scope/year and industrial-facility lineage.

## US NGA World Port Index Publication 150 global port attributes

**Candidate ID:** `nga.world-port-index.pub150`  
**Provider:** United States National Geospatial-Intelligence Agency (NGA)  
**Categories:** `transport_infrastructure`, `ports`, `marine_cargo_context`, `critical_infrastructure`  
**Spatial scope:** Global ports represented in the World Port Index; coverage and data quality vary by port and update  
**Temporal scope:** NGA provides an operationally updated port directory; exact monthly CSV publication/version must be frozen for reproducible use  
**Resolution / granularity:** Port-level location, harbor classification, channel and anchorage depth, facilities and navigation metadata; provider download formats include CSV and geospatial representations  
**Potential roles:** `port_asset_location_prior`, `marine_cargo_accumulation_scenario`, `storm_surge_and_wind_port_overlay`  
**Access hint:** `public_nga_publication_csv_geopackage_monthly_version_and_reuse_review`  
**Authoritative source:** <https://msi.nga.mil/Publications/WPI>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The original WPI publisher offers downloadable port attribute data and periodic updates. Port locations and marine operating characteristics cannot determine terminal replacement value, berth inventory, vessel positions, exposure ownership, actual cargo values or insured location-level sums. Screen current US government and platform terms and verify individual field meanings/position accuracy before model use.

## OurAirports globally maintained airports and runway data dumps

**Candidate ID:** `ourairports.airports-runways.daily`  
**Provider:** OurAirports community project / David Megginson  
**Categories:** `aviation_infrastructure`, `airports`, `runways`, `transport_exposure`  
**Spatial scope:** Worldwide community-maintained airport, heliport and seaplane base inventory, varying completeness and verification  
**Temporal scope:** Nightly public CSV publication; exact snapshot date and original file hash need preserving  
**Resolution / granularity:** Airport point locations, identifiers, operating category and region; separate runways.csv with airport keys and physical runway attributes  
**Potential roles:** `airport_facility_hazard_overlay`, `runway_length_and_class_exposure_prior`, `aviation_business_interruption_context`  
**Access hint:** `nightly_public_domain_csv_official_project_files_snapshot_hash_required`  
**Authoritative source:** <https://ourairports.com/data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original project declares its own published datasets public domain without guarantees of accuracy or fitness; source-specific repository approval still required. Airport points are not airport building inventories, asset replacement values, aircraft fleets, risk retention, active schedules or business interruption coverage. Match runways by airport stable IDs; record community edits and nightly vintage and validate against national aviation authority sources for operational use.
