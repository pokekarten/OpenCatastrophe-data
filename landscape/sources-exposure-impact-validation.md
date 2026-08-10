<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-exposure-impact-validation.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-exposure-impact-validation.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of additional exposure, built-environment and impact-validation sources relevant to catastrophe risk.

**Entries:** 10

## Google Open Buildings 2.5D Temporal Dataset v1

**Candidate ID:** `google.open-buildings.temporal.v1`  
**Provider:** Google Research — Open Buildings  
**Categories:** `built_environment`, `building_presence`, `building_height`, `temporal_exposure`, `remote_sensing`  
**Spatial scope:** Africa, South Asia, South-East Asia, Latin America and the Caribbean  
**Temporal scope:** annual 2016-2023  
**Resolution / granularity:** annual rasters with approximately 4 m effective spatial resolution, distributed at 0.5 m pixel spacing  
**Potential roles:** `temporal_exposure_validation`, `building_stock_change_context`, `building_height_covariates`, `disaster_exposure_baseline`  
**Access hint:** `public_download_and_earth_engine`  
**Authoritative source:** <https://sites.research.google/gr/open-buildings/temporal/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Google documents dual CC BY 4.0 / ODbL 1.0 reuse and explicitly includes commercial social-good users; a future admission should select one licence path and exact annual assets. Presence, fractional counts and height are model-derived Sentinel-2 products, not cadastral observations.

## DLR World Settlement Footprint 2019

**Candidate ID:** `dlr.wsf.2019`  
**Provider:** German Aerospace Center (DLR) Earth Observation Center  
**Categories:** `settlement_extent`, `built_environment`, `exposure_context`, `remote_sensing`  
**Spatial scope:** global land between approximately 60°S and 78°N  
**Temporal scope:** 2019  
**Resolution / granularity:** 10 m binary settlement mask derived from multitemporal Sentinel-1 and Sentinel-2 imagery  
**Potential roles:** `settlement_extent_validation`, `exposure_context`, `urban_footprint_baseline`, `cross_source_building_coverage_comparison`  
**Access hint:** `public_download_stac_and_wms`  
**Authoritative source:** <https://geoservice.dlr.de/data-assets/twg5xsnquw84.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DLR labels the product CC BY 4.0 and provides DOI, download, STAC and WMS access. It is a remotely sensed binary settlement classification with omission/commission uncertainty, not a building inventory; exact tiles and attribution still require source-specific admission review.

## DLR World Settlement Footprint Evolution

**Candidate ID:** `dlr.wsf.evolution.1985-2015`  
**Provider:** German Aerospace Center (DLR) Earth Observation Center  
**Categories:** `settlement_extent`, `urbanisation`, `temporal_exposure`, `remote_sensing`, `historical_context`  
**Spatial scope:** global  
**Temporal scope:** yearly settlement-detection history 1985-2015  
**Resolution / granularity:** 30 m settlement-evolution raster plus yearly Input Data Consistency score  
**Potential roles:** `historical_exposure_proxy`, `urbanisation_change_context`, `temporal_validation`, `settlement_growth_covariate`  
**Access hint:** `public_download_stac_and_wms`  
**Authoritative source:** <https://web.geoservice.dlr.de/web/datasets/wsf_evo>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DLR labels the dataset CC BY 4.0. Landsat availability varies strongly over space and time; preserve the yearly Input Data Consistency score and treat encoded years as estimated settlement detection rather than authoritative construction dates or annual building counts.

## DLR World Settlement Footprint 3D

**Candidate ID:** `dlr.wsf.3d.v02`  
**Provider:** German Aerospace Center (DLR) Earth Observation Center  
**Categories:** `built_environment`, `building_height`, `building_area`, `building_volume`, `exposure_context`  
**Spatial scope:** global  
**Temporal scope:** released 2023; current service exposes V02 layers  
**Resolution / granularity:** approximately 90 m global gridded building height, area, volume and fraction layers  
**Potential roles:** `building_stock_intensity`, `exposure_covariates`, `height_and_volume_validation`, `cross_source_exposure_comparison`  
**Access hint:** `public_download_and_web_services`  
**Authoritative source:** <https://c.geoservice.dlr.de/web/datasets/wsf_3d>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DLR labels WSF 3D CC BY 4.0 and the current service exposes V02 layer identifiers. The fields are model-derived 90 m aggregates informed by remote sensing and ancillary data, not verified structure-level heights, areas or values.

## USACE National Structure Inventory Base 2026

**Candidate ID:** `usace.nsi.base.2026`  
**Provider:** U.S. Army Corps of Engineers Hydrologic Engineering Center  
**Categories:** `exposure`, `structures`, `occupancy`, `replacement_value`, `population`, `consequence_modelling`  
**Spatial scope:** United States  
**Temporal scope:** 2026 base release  
**Resolution / granularity:** point-based modeled structure inventory with standardized public attributes; state files and API subsets  
**Potential roles:** `exposure_benchmark`, `flood_consequence_research`, `occupancy_and_value_covariates`, `insurance_interoperability_research`  
**Access hint:** `public_download_and_api`  
**Authoritative source:** <https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2026/technical-documentation>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** USACE documents the 2026 Base as a public modeled national inventory and older NSI guidance states the public release removes fields derived from licensed data. A canonical current standard licence for redistribution/commercial reuse was not established in this landscape check, so rights stay fail-closed. Values and attributes are modeled estimates, not structure-by-structure truth.

## FEMA USA Structures

**Candidate ID:** `fema.usa-structures`  
**Provider:** U.S. Federal Emergency Management Agency / Oak Ridge National Laboratory / U.S. Geological Survey  
**Categories:** `built_environment`, `building_footprints`, `occupancy`, `exposure`, `emergency_management`  
**Spatial scope:** United States and territories  
**Temporal scope:** rolling national inventory; federal catalogue metadata last modified 2025-04-01  
**Resolution / granularity:** building-footprint inventory of structures greater than 450 square feet with occupancy attribution  
**Potential roles:** `us_building_exposure_baseline`, `structure_footprint_validation`, `occupancy_crosswalk`, `hazard_exposure_overlay`  
**Access hint:** `public_federal_geospatial_dataset`  
**Authoritative source:** <https://catalog.data.gov/dataset/usa-structures-4749e>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The federal catalogue identifies public access and U.S. government-works licensing guidance. A future admission must still freeze an exact FEMA/ArcGIS release or service snapshot and verify field-level provenance. Occupancy classifications combine automated inference and source fusion and are not cadastral or assessor truth.

## OpenFEMA NFIP Redacted Claims v3

**Candidate ID:** `fema.openfema.nfip-redacted-claims.v3`  
**Provider:** U.S. Federal Emergency Management Agency / National Flood Insurance Program  
**Categories:** `flood`, `insurance_claims`, `historical_losses`, `impact_validation`, `vulnerability`  
**Spatial scope:** United States National Flood Insurance Program  
**Temporal scope:** 1970-present; service metadata declares monthly refresh  
**Resolution / granularity:** redacted flood-insurance claim transactions; current v3 service contains more than 2.7 million records  
**Potential roles:** `insured_flood_loss_validation`, `claims_frequency_and_severity_research`, `flood_vulnerability_calibration`, `hydrology_claims_linkage`  
**Access hint:** `public_api_and_download`  
**Authoritative source:** <https://www.fema.gov/openfema-data-page/nfip-redacted-claims-v3>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** High-value empirical insurance-impact evidence, but current OpenFEMA v3 metadata marks access public while leaving the licence field unset; redistribution and commercial-use rights therefore remain fail-closed pending source-specific review. Preserve redaction, transaction semantics, monetary vintage and programme-policy changes rather than treating rows as homogeneous loss observations.

## OpenFEMA NFIP Redacted Policies v3

**Candidate ID:** `fema.openfema.nfip-redacted-policies.v3`  
**Provider:** U.S. Federal Emergency Management Agency / National Flood Insurance Program  
**Categories:** `flood`, `insurance_policies`, `insured_exposure`, `portfolio_context`, `validation`  
**Spatial scope:** United States National Flood Insurance Program  
**Temporal scope:** 2009-present; service metadata declares monthly refresh  
**Resolution / granularity:** redacted policy transactions; current v3 service contains more than 74 million records  
**Potential roles:** `insured_exposure_baseline`, `claims_denominator`, `take_up_and_portfolio_research`, `flood_insurance_validation`  
**Access hint:** `public_api_and_download`  
**Authoritative source:** <https://www.fema.gov/openfema-data-page/nfip-redacted-policies-v3>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A natural exposure denominator and companion to NFIP claims, but current OpenFEMA v3 metadata marks access public while leaving the licence field unset; rights remain fail-closed pending source-specific review. Policy transaction rows must be reconstructed carefully and must not be treated directly as a clean contemporaneous in-force portfolio.

## OpenFEMA Individual Assistance Multiple Loss Flood Properties v1

**Candidate ID:** `fema.openfema.ia-multiple-loss-flood-properties.v1`  
**Provider:** U.S. Federal Emergency Management Agency  
**Categories:** `flood`, `historical_impacts`, `repetitive_loss`, `residential_exposure`, `validation`  
**Spatial scope:** United States disaster-assistance records  
**Temporal scope:** 2002-present; declarations older than 30 days; service metadata declares daily refresh  
**Resolution / granularity:** applicant/property impact records with privacy-coarsened coordinates, disaster identifiers and flood-impact attributes  
**Potential roles:** `repetitive_flood_impact_validation`, `event_linkage`, `residential_vulnerability_research`, `flood_risk_benchmarking`  
**Access hint:** `public_api_and_download`  
**Authoritative source:** <https://www.fema.gov/openfema-data-page/Individual-Assistance-Multiple-Loss-Flood-Properties-v1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** OpenFEMA metadata marks access as public but leaves its licence field unset and points users to OpenFEMA Terms and Conditions/citation requirements; exact redistribution and commercial-use terms therefore remain fail-closed until admission review. Coordinates are deliberately rounded to one decimal for privacy and can cross county/state boundaries, so aggregate with the supplied geography fields.

## OpenFEMA Disaster Declarations Summaries v2

**Candidate ID:** `fema.openfema.disaster-declarations-summaries.v2`  
**Provider:** U.S. Federal Emergency Management Agency  
**Categories:** `disaster_events`, `event_catalogue`, `administrative_context`, `impact_linkage`  
**Spatial scope:** United States federal disaster declarations  
**Temporal scope:** 1953-present; service metadata declares approximately 20-minute refresh cadence  
**Resolution / granularity:** declaration and declared-area records with disaster numbers, incident types, dates and programme flags  
**Potential roles:** `event_identity_crosswalk`, `fema_dataset_linkage`, `historical_event_context`, `impact_validation_join`  
**Access hint:** `public_api_and_download`  
**Authoritative source:** <https://www.fema.gov/openfema-data-page/Disaster-Declarations-Summaries-v2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Useful as the event-identity spine for other OpenFEMA impact datasets. Current OpenFEMA metadata marks access as public but leaves its licence field unset, so source-specific reuse rights remain fail-closed pending terms review; county detail is unavailable before 1964 and historical records include known incompleteness and human-entry error.
