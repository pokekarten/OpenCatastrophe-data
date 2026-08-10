<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-institutional-data-networks.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-institutional-data-networks.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of institutional data networks, catastrophe-risk benchmarks and interoperable observation services relevant to catastrophe risk.

**Entries:** 10

## DRMKC Risk Data Hub API and geospatial services

**Candidate ID:** `ec-jrc.drmkc.risk-data-hub-api`  
**Provider:** European Commission Joint Research Centre / Disaster Risk Management Knowledge Centre  
**Categories:** `multi_hazard`, `risk`, `exposure`, `vulnerability`, `disaster_loss`, `api`  
**Spatial scope:** Europe, with dataset-specific coverage and administrative units  
**Temporal scope:** historical disaster-loss records plus current and derived risk datasets; dataset-dependent  
**Resolution / granularity:** OGC API feature collections, GeoJSON/CSV responses and related geospatial service layers; dataset-dependent  
**Potential roles:** `european_risk_benchmark`, `loss_damage_validation`, `exposure_vulnerability_context`, `multi_hazard_risk_discovery`  
**Access hint:** `public_catalog_and_api_with_eu_login_token_and_layer_specific_lineage`  
**Authoritative source:** <https://drmkc.jrc.ec.europa.eu/risk-data-hub-api/docs/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The API portal currently documents Risk Data Hub API 3.1.0 and CC BY 4.0 service-level reuse, but individual layers can aggregate external sources; freeze the exact collection, API version, source lineage, units and any third-party rights before use.

## GFDRR Risk Data Library

**Candidate ID:** `worldbank.gfdrr.risk-data-library`  
**Provider:** World Bank Group / Global Facility for Disaster Reduction and Recovery  
**Categories:** `multi_hazard`, `risk_assessment`, `hazard`, `exposure`, `vulnerability`, `loss`, `data_catalog`  
**Spatial scope:** global collection with project- and country-specific coverage  
**Temporal scope:** ongoing collection of disaster and climate risk assessments; individual dataset vintages vary  
**Resolution / granularity:** heterogeneous raster, vector and tabular hazard, exposure, vulnerability and loss datasets  
**Potential roles:** `risk_dataset_discovery`, `regional_model_benchmark`, `exposure_vulnerability_source_discovery`, `loss_model_validation`  
**Access hint:** `public_catalog_with_dataset_specific_licenses`  
**Authoritative source:** <https://datacatalog.worldbank.org/collections>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The Risk Data Library is curated by GFDRR and includes public disaster-risk assessment datasets, but it is not one homogeneous asset; pin the exact World Bank dataset identifier, files, version, license and upstream input lineage before use.

## GEM Global Exposure Model

**Candidate ID:** `gem.global-exposure-model`  
**Provider:** Global Earthquake Model Foundation  
**Categories:** `earthquake`, `exposure`, `buildings`, `replacement_cost`, `population`, `risk_model_input`  
**Spatial scope:** global  
**Temporal scope:** current 2026 model generation with region- and source-specific underlying vintages  
**Resolution / granularity:** global mosaic of residential, commercial and industrial building stock; open release aggregated at administrative level 1 with higher-resolution variants under separate licenses  
**Potential roles:** `seismic_exposure_benchmark`, `building_stock_validation`, `replacement_cost_context`, `exposure_taxonomy_interoperability`  
**Access hint:** `open_noncommercial_sharealike_aggregate_with_higher_resolution_license_request`  
**Authoritative source:** <https://www.globalquakemodel.org/product/global-exposure-model>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GEM exposes an open CC BY-NC-SA 4.0 aggregate and separately licensed higher-resolution variants. The current product page references both v2026.1 presentation material and a v2026.0.0 cited dataset, so exact release identity and commercial-use rights must be resolved before admission.

## GEM Global Vulnerability Model

**Candidate ID:** `gem.global-vulnerability-model`  
**Provider:** Global Earthquake Model Foundation  
**Categories:** `earthquake`, `vulnerability`, `fragility`, `economic_loss`, `fatality`, `risk_model_input`  
**Spatial scope:** global country and regional model collection  
**Temporal scope:** current 2026 model generation  
**Resolution / granularity:** country- and region-specific vulnerability functions by building typology, including structural, non-structural, contents and fatality consequences  
**Potential roles:** `seismic_vulnerability_benchmark`, `damage_function_comparison`, `building_taxonomy_mapping`, `loss_model_validation`  
**Access hint:** `open_noncommercial_sharealike_download_with_commercial_license_request`  
**Authoritative source:** <https://www.globalquakemodel.org/product/global-vulnerability-model>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The open database is offered under CC BY-NC-SA 4.0 and commercial use requires a separate license. Preserve intensity measure, building taxonomy, loss component, country/region, function version and cited data release before comparing or using curves.

## WMO Information System 2.0

**Candidate ID:** `wmo.wis2`  
**Provider:** World Meteorological Organization and participating WIS2 centres  
**Categories:** `meteorological_observations`, `climate_observations`, `hydrology`, `real_time`, `data_exchange`, `discovery`  
**Spatial scope:** global WMO member and participating-centre network  
**Temporal scope:** operational since 2025-01-01 with continuously published data and metadata; archives are provider-dependent  
**Resolution / granularity:** federated dataset notifications and downloads through MQTT, HTTP(S), Global Brokers, Global Discovery Catalogues and Global Caches  
**Potential roles:** `global_observation_discovery`, `meteorological_validation`, `event_forcing`, `station_data_interoperability`  
**Access hint:** `core_data_unrestricted_recommended_data_provider_specific`  
**Authoritative source:** <https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/wmo-information-system-wis/wis2-overview>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** WIS2 is a federation rather than one dataset. Core data are downloadable without access restrictions from Global Caches while recommended data can require provider access controls; pin centre ID, topic, discovery record, data class, provider and retrieval time.

## WMO Hydrological Observing System

**Candidate ID:** `wmo.whos`  
**Provider:** World Meteorological Organization and participating hydrological data providers  
**Categories:** `hydrology`, `river_discharge`, `water_level`, `hydrometeorology`, `observations`, `data_federation`  
**Spatial scope:** global federation with national, regional and basin-specific provider coverage  
**Temporal scope:** real-time and historical hydrological data depending on the original provider  
**Resolution / granularity:** provider station time series and metadata exposed through interoperable WHOS views, portals and web-service endpoints  
**Potential roles:** `discharge_validation`, `water_level_validation`, `hydrological_station_discovery`, `flood_drought_observation_context`  
**Access hint:** `federated_public_and_provider_specific_access`  
**Authoritative source:** <https://wmo.int/activities/wmo-hydrological-observing-system-whos>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** WHOS brokers heterogeneous hydrological providers and does not erase original source semantics. Preserve provider, station identifier, variable, unit, service endpoint, observation status and provider-specific access or reuse conditions.

## EUMETNET OPERA Radar Database

**Candidate ID:** `eumetnet.opera.radar-database`  
**Provider:** EUMETNET OPERA  
**Categories:** `weather_radar`, `station_metadata`, `network_inventory`, `precipitation_context`  
**Spatial scope:** European weather-radar network  
**Temporal scope:** current operational inventory with archived radar-database views; last observed update 2026-06-17  
**Resolution / granularity:** radar-site inventory with attributes such as band, Doppler capability, polarization, operational status and country; downloadable as CSV, XLSX and JSON  
**Potential roles:** `radar_network_discovery`, `observation_coverage_context`, `radar_source_inventory`  
**Access hint:** `public_network_metadata_download`  
**Authoritative source:** <https://eumetnet.eu/wp-content/themes/aeron-child/observations-programme/current-activities/opera/database/OPERA_Database/index.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This database is radar-network metadata, not radar reflectivity or precipitation observations. Use it to discover and freeze network/site metadata; actual radar products require separate source, product-version and rights review.

## European Severe Weather Database

**Candidate ID:** `essl.eswd`  
**Provider:** European Severe Storms Laboratory and partner networks  
**Categories:** `severe_convective_storm`, `hail`, `tornado`, `wind`, `event_catalogue`, `validation`  
**Spatial scope:** Europe with partner-dependent reporting coverage  
**Temporal scope:** historical and continuously collected severe-weather reports  
**Resolution / granularity:** event and point reports with event-type metadata, source information and ESWD quality-control levels  
**Potential roles:** `convective_event_validation`, `hail_tornado_wind_catalogue`, `impact_event_benchmark`  
**Access hint:** `public_subset_noncommercial_with_broader_access_by_agreement`  
**Authoritative source:** <https://www.essl.org/cms/european-severe-weather-database/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ESSL states that commercial use of public ESWD data is not allowed and broader access is agreement-based. Preserve report type, QC level, source provenance and duplication semantics; ESSL recommends QC1 as a lower bound for statistical studies.

## EMSC SeismicPortal FDSN Event service

**Candidate ID:** `emsc.seismicportal.fdsn-event`  
**Provider:** European-Mediterranean Seismological Centre  
**Categories:** `earthquake`, `event_catalogue`, `near_real_time`, `seismology`, `validation`, `api`  
**Spatial scope:** EMSC event catalogue with strong Euro-Mediterranean operational focus and contributed seismic solutions  
**Temporal scope:** historical and near-real-time catalogue with event updates  
**Resolution / granularity:** FDSN Event API returning event parameters and optionally all origins and arrivals in QuakeML, JSON or text  
**Potential roles:** `earthquake_event_validation`, `near_real_time_event_discovery`, `cross_agency_origin_comparison`  
**Access hint:** `public_fdsn_api_cc_by_4_0`  
**Authoritative source:** <https://www.seismicportal.eu/fdsn-wsevent.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The service is CC BY 4.0 and supports contributor/origin detail. Operational event solutions can change, so freeze event IDs, query, retrieval time, catalogue and contributing origins rather than treating a live response as immutable.

## PERILS Industry Exposure Database 2025

**Candidate ID:** `perils.industry-exposure-database.2025`  
**Provider:** PERILS AG  
**Categories:** `insured_exposure`, `market_sums_insured`, `natural_catastrophe`, `insurance`, `cresta`  
**Spatial scope:** 21 PERILS-covered countries across Europe, Asia-Pacific and Canada in the 2025 release  
**Temporal scope:** exposure in force at 2025-01-01  
**Resolution / granularity:** market sums insured by CRESTA zone, line of business and coverage type  
**Potential roles:** `insured_exposure_benchmark`, `market_share_scaling`, `insurance_exposure_validation`, `cresta_aggregation_reference`  
**Access hint:** `industry_benchmark_with_provider_access_terms`  
**Authoritative source:** <https://www.perils.org/news/perils-releases-industry-exposure-database-2025-ied-2025-severe-convective-storm-added>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** PERILS documents market sums insured by CRESTA zone, line of business and coverage type and added severe convective storm exposure in 2025. Treat this as a high-value benchmark lead, not open data; exact access, redistribution and commercial terms require provider-specific review.
