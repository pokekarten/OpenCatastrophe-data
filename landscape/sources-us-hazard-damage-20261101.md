<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-us-hazard-damage-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-us-hazard-damage-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of US observed severe-storm footprints, wildfire building damage and fuel vegetation data for distinct OpenCatastrophe hazard and validation use cases; model use, rights and retrieval are not approved.

**Entries:** 3

## NOAA NCEI Event Footprint Catalog (EFC) 2026

**Candidate ID:** `noaa.ncei.event-footprint-catalog.2026`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `tornado`, `hail`, `severe_convective_weather`, `event_footprints`, `validation`  
**Spatial scope:** All 50 US states and selected US territories, with sensor- and hazard-specific availability  
**Temporal scope:** Tornado footprints January 2010 onward; hail footprints October 2020 onward; launched 2026 and refreshed about daily  
**Resolution / granularity:** Event-specific GeoJSON and CSV footprint polygons, metadata and narratives; approximately 1 km source gridding for hail, assessment-derived paths for tornadoes  
**Potential roles:** `tornado_hail_event_footprint_challenge`, `historical_event_to_exposure_overlay`, `noaa_event_lineage_crosswalk`  
**Access hint:** `public_event_and_bulk_geojson_csv_download_exact_asset_and_terms_review`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/event-footprint-catalog>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Product lineage is NOT independent of NOAA Storm Events Database, NWS Damage Assessment Toolkit (DAT) and MRMS hail estimates, which may also contribute to previously registered NOAA/SPC data. DAT/Storm Events damage-path geometry and MRMS hail-polygon geometry are distinct source measurements and assumptions, not certified parcel-level damage. NOAA does not archive old catalog updates; freeze exact retrieval UTC, hazard, event/date, source version, bytes and SHA-256 before a reproducibility claim. No published API authorization is assumed.

## CAL FIRE Damage Inspection (DINS) Data

**Candidate ID:** `us.calfire.dins.structure-damage`  
**Provider:** California Department of Forestry and Fire Protection (CAL FIRE)  
**Categories:** `wildfire`, `observed_building_damage`, `building_attributes`, `validation`, `california`  
**Spatial scope:** California State Responsibility Area (SRA), inspected structures inside or within 300 feet of mapped wildfire perimeters  
**Temporal scope:** Incident-based mutable public database; provider portal updated 2026-10-21  
**Resolution / granularity:** Structure-level inspection and damage-state attributes; portal offers ArcGIS GeoServices REST, CSV, GeoJSON, GeoPackage and other geographic downloads  
**Potential roles:** `empirical_wildfire_building_damage_challenge`, `damage_state_taxonomy_research`, `wildfire_event_building_spatial_linkage`  
**Access hint:** `public_portal_and_arcgis_geoservices_rest_cc_attribution_claim_exact_dataset_and_privacy_review`  
**Authoritative source:** <https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider documents affected/minor/major/destroyed/inaccessible/no-damage categories and reports survey/access limitations. Inspected structures are NOT a complete control sample of unburned buildings; absence from DINS must never imply no loss. Field-observed addresses and parcel/APN spatial joins can be uncertain; do not import or publish address-/parcel-level personal or policy data without a separate privacy decision. Portal states Creative Commons Attribution and no public-use restrictions, but exact resource reuse, citation, snapshot date and model semantics still require review.

## LANDFIRE 2025 vegetation and fire fuel products

**Candidate ID:** `us.landfire.fuel-vegetation.2025`  
**Provider:** LANDFIRE / USGS and US Forest Service  
**Categories:** `wildfire`, `fuel_models`, `vegetation`, `remote_sensing`, `hazard_covariates`  
**Spatial scope:** United States; product/region coverage varies for CONUS, Alaska, Hawaii and insular areas  
**Temporal scope:** LANDFIRE 2025 update with phased releases during 2026; CONUS full-extent update announced 2026-10-27  
**Resolution / granularity:** Product-specific fire-behavior fuel rasters, canopy cover and height, fuel disturbance, seasonal fuels and vegetation classifications; region/resolution vary  
**Potential roles:** `wildfire_fuel_layer_research`, `wildfire_spread_input_candidate`, `vegetation_exposure_context`  
**Access hint:** `public_full_extent_download_lfps_rest_image_wcs_wms_exact_release_and_product_review`  
**Authoritative source:** <https://landfire.gov/data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Source is a versioned FAMILY of modelled vegetation/fuel products, not a single observed wildfire, loss dataset or homogeneous global coverage. Select an exact named layer (e.g. FBFM40 or canopy height), US region, release, resolution, classification, observation vintage and byte identity before any research sample. Do not conflate fire fuel hazard potential with empirical burned area or building losses; model dependencies and reuse terms must be independently reviewed.
