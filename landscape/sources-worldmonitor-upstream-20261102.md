<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-worldmonitor-upstream-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-worldmonitor-upstream-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery of World Monitor upstream sources potentially useful to OpenCatastrophe catastrophe event monitoring, secondary impacts, critical infrastructure and exposure context; not a claim of source admission or source dataset rights.

**Entries:** 18

## NASA EONET Natural Events API v3

**Candidate ID:** `nasa.eonet.events-api-v3`  
**Provider:** NASA Earth Observatory Natural Event Tracker  
**Categories:** `multi_hazard`, `event_catalogue`, `near_real_time`  
**Spatial scope:** global  
**Temporal scope:** near-real-time and historic event metadata, variable by event  
**Resolution / granularity:** Event IDs, dates, categories, source links, point and polygon geometries  
**Potential roles:** `event_detection`, `event_crosswalk`, `satellite_layer_discovery`  
**Access hint:** `public_documented_api`  
**Authoritative source:** <https://eonet.gsfc.nasa.gov/docs/v3>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EONET is curated event metadata, not a complete hazard footprint, surveyed damage or loss. Freeze original event ID, all geometry timestamps and underlying sources; a World Monitor dashboard may drop polygon detail. Discovery evidence: World Monitor source-attribution manifest host eonet.gsfc.nasa.gov, code scripts/seed-natural-events.mjs; independently verify direct provider terms and exact product before use.

## Canadian Wildland Fire Information System operational products

**Candidate ID:** `ca.nrcan.cwfis-operational`  
**Provider:** Natural Resources Canada CWFIS  
**Categories:** `wildfire`, `fire_weather`, `event_observation`  
**Spatial scope:** Canada  
**Temporal scope:** current and historical coverage, product dependent  
**Resolution / granularity:** Fire locations, danger/weather indexes, burned area and linked spatial services  
**Potential roles:** `wildfire_hazard_context`, `fire_event_crosswalk`, `burned_area_validation`  
**Access hint:** `public_mapping_datamart_product_terms_review`  
**Authoritative source:** <https://natural-resources.canada.ca/forests-forestry/wildland-fires/wildland-fire-monitoring-reporting-tools>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Current fire locations are not necessarily perimeters; satellite and agency reports may disagree. Product, layer, timestamp and regional authority must be frozen separately. Discovery evidence: World Monitor source-attribution manifest host geoserver.cwfif.nrcan.gc.ca, code scripts/wildfire/cwfis-wfs.mjs; independently verify direct provider terms and exact product before use.

## Earthquakes Canada catalogue and significant events

**Candidate ID:** `ca.nrcan.earthquakes-canada`  
**Provider:** Natural Resources Canada  
**Categories:** `earthquake`, `event_catalogue`, `seismology`  
**Spatial scope:** Canada and adjacent areas  
**Temporal scope:** recent and historical earthquakes, operational revisions  
**Resolution / granularity:** Epicentres, magnitude, depth, event type and event identifiers  
**Potential roles:** `earthquake_event_crosswalk`, `regional_seismic_validation`  
**Access hint:** `public_catalogue_documented_feed_terms_review`  
**Authoritative source:** <https://www.earthquakescanada.nrcan.gc.ca/recent/index-en.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** World Monitor uses an NRCan Atom adapter. Quarry blasts and mine-induced events may appear alongside tectonic events; preserve event type and catalogue version. Discovery evidence: World Monitor source-attribution manifest host www.earthquakescanada.nrcan.gc.ca, code scripts/seismology/nrcan-atom.mjs; independently verify direct provider terms and exact product before use.

## NOAA NHC operational tropical cyclone GIS products

**Candidate ID:** `noaa.nhc.current-tropical-cyclone-gis`  
**Provider:** NOAA National Hurricane Center  
**Categories:** `tropical_cyclone`, `storm_track`, `forecast`, `geospatial`  
**Spatial scope:** Atlantic and eastern North Pacific as product coverage permits  
**Temporal scope:** operational advisories with frequent revisions  
**Resolution / granularity:** Forecast tracks, uncertainty cones, advisories and wind fields depending on layer  
**Potential roles:** `cyclone_event_tracking`, `forecast_hazard_context`, `track_crosswalk`  
**Access hint:** `public_operational_gis_endpoints_terms_review`  
**Authoritative source:** <https://www.nhc.noaa.gov/gis/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Forecast cones are not wind footprints or loss probabilities. Store storm ID, advisory number, issuance time, basin and layer; do not substitute forecasts for best track. Discovery evidence: World Monitor source-attribution manifest host mapservices.weather.noaa.gov, code scripts/seed-natural-events.mjs; independently verify direct provider terms and exact product before use.

## US National Weather Service CAP alerts

**Candidate ID:** `us.nws.active-weather-alerts-cap`  
**Provider:** NOAA National Weather Service  
**Categories:** `severe_weather`, `alerting`, `cap`, `geospatial`  
**Spatial scope:** United States and NWS coverage regions  
**Temporal scope:** operational active alerts; historical retention restricted  
**Resolution / granularity:** CAP v1.2 alerts in XML and JSON-LD with event areas and validity windows  
**Potential roles:** `regional_warning_trigger`, `alert_area_validation`  
**Access hint:** `public_alert_api_rate_limits`  
**Authoritative source:** <https://www.weather.gov/documentation/services-web-alerts>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Operational alerts describe warned areas and uncertainty, not measured extreme-wind, hail or flood footprints; respect NWS rate limit and expiration. Discovery evidence: World Monitor source-attribution manifest host api.weather.gov, code scripts/_weather-alert-select.mjs; independently verify direct provider terms and exact product before use.

## Hong Kong Observatory public tropical cyclone and marine warnings

**Candidate ID:** `hk.hko.tropical-cyclone-public-bulletins`  
**Provider:** Hong Kong Observatory  
**Categories:** `tropical_cyclone`, `storm_surge`, `weather_alert`  
**Spatial scope:** Hong Kong and western North Pacific warning context  
**Temporal scope:** operational warning bulletins  
**Resolution / granularity:** Regional storm tracks, warning signals and coastal conditions, field availability varies  
**Potential roles:** `western_pacific_event_monitoring`, `coastal_warning_context`  
**Access hint:** `public_web_and_open_data_product_terms_review`  
**Authoritative source:** <https://www.hko.gov.hk/en/wxinfo/currwx/tc.htm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Treat HKO warnings as official local alert context, not standardized loss footprints; pin issue time, basin, warning area and authoritative product. Discovery evidence: World Monitor source-attribution manifest host data.weather.gov.hk, code scripts/natural/western-pacific-cyclones.mjs; independently verify direct provider terms and exact product before use.

## India Meteorological Department coastal and sea-area bulletins

**Candidate ID:** `in.imd.coastal-marine-bulletins`  
**Provider:** India Meteorological Department  
**Categories:** `tropical_cyclone`, `storm_surge`, `coastal_weather`, `alerting`  
**Spatial scope:** Indian coastal waters and adjacent sea areas  
**Temporal scope:** operational area and port bulletins  
**Resolution / granularity:** Warnings for wind, sea state, visibility, port signals and surge by coastal area  
**Potential roles:** `north_indian_ocean_warning_context`, `coastal_event_trigger`  
**Access hint:** `public_bulletin_reading_noncommercial_terms_review`  
**Authoritative source:** <https://mausam.imd.gov.in/Forecast/coastal_bulletin_new.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The upstream World Monitor documentation notes non-commercial RTI constraints for IMD; access and commercial rights require independent review. Pin bulletin area, valid interval and issuing office. Discovery evidence: World Monitor source-attribution manifest host mausam.imd.gov.in, code scripts/lib/imd-cyclone-marine.mjs; independently verify direct provider terms and exact product before use.

## Environment and Climate Change Canada public weather alerts

**Candidate ID:** `ca.eccc.operational-weather-alerts`  
**Provider:** Environment and Climate Change Canada  
**Categories:** `severe_weather`, `cap`, `alerting`  
**Spatial scope:** Canada  
**Temporal scope:** near-real-time warnings with issue and expiry windows  
**Resolution / granularity:** Regional public watches, warnings and advisories  
**Potential roles:** `severe_weather_alert_trigger`, `national_weather_crosscheck`  
**Access hint:** `public_alert_feeds_terms_review`  
**Authoritative source:** <https://www.weather.gc.ca/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** An alert polygon or warning region is not an observed hazard footprint. Freeze product ID, issue time, language and validity window; assess reuse terms. Discovery evidence: World Monitor source-attribution manifest host api.weather.gc.ca, code scripts/_weather-alert-select.mjs; independently verify direct provider terms and exact product before use.

## WMO Severe Weather Information Centre 3.0

**Candidate ID:** `wmo.swic3.global-cap-warnings`  
**Provider:** World Meteorological Organization  
**Categories:** `severe_weather`, `tropical_cyclone`, `cap`, `multi_hazard`  
**Spatial scope:** multi-country worldwide member coverage, incomplete by member  
**Temporal scope:** operational member warnings  
**Resolution / granularity:** CAP member advisories and tropical cyclone tracks with source agency identity  
**Potential roles:** `global_warning_discovery`, `country_alert_crosswalk`  
**Access hint:** `public_warning_portal_underlying_member_terms_review`  
**Authoritative source:** <https://severeweather.wmo.int/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** SWIC aggregates member warnings, with incomplete CAP availability; original national meteorological services are the authoritative issuers. Avoid interpreting absence as no warning. Discovery evidence: World Monitor source-attribution manifest host severeweather.wmo.int, code scripts/_weather-alert-select.mjs; independently verify direct provider terms and exact product before use.

## ReliefWeb disasters and situation reports API

**Candidate ID:** `unocha.reliefweb.disasters-api`  
**Provider:** UN OCHA ReliefWeb  
**Categories:** `disaster_impact`, `event_catalogue`, `humanitarian`, `api`  
**Spatial scope:** global  
**Temporal scope:** near-real-time reports and historical archive  
**Resolution / granularity:** Disaster records, country associations, reports, original sources and update times  
**Potential roles:** `impact_context`, `event_identity_crosswalk`, `humanitarian_validation`  
**Access hint:** `approved_appname_required_provider_content_rights_review`  
**Authoritative source:** <https://apidoc.reliefweb.int/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official API requires approved appname. Report text and embedded content have independent publisher rights. Not insured losses or independent validation if sourced from the same agencies. Discovery evidence: World Monitor source-attribution manifest host api.reliefweb.int, code scripts/seed-climate-disasters.mjs; independently verify direct provider terms and exact product before use.

## IOM Displacement Tracking Matrix aggregated displacement API

**Candidate ID:** `iom.dtm.displacement-api`  
**Provider:** International Organization for Migration  
**Categories:** `population`, `displacement`, `humanitarian_impact`  
**Spatial scope:** country and subnational coverage where active  
**Temporal scope:** survey and assessment rounds, varies by operation  
**Resolution / granularity:** Aggregated internally displaced population counts by administrative level  
**Potential roles:** `post_event_displacement_validation`, `population_context`  
**Access hint:** `public_aggregated_api_terms_and_scope_review`  
**Authoritative source:** <https://dtm.iom.int/es/node/38776>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DTM aggregates at country/admin levels with sampling and coverage differences. Never equate displacement with insured loss or identify individual households. Discovery evidence: World Monitor source-attribution manifest host dtmapi.iom.int, code scripts/seed-dtm-displacement.mjs; independently verify direct provider terms and exact product before use.

## UNHCR Refugee Data Portal datasets and API

**Candidate ID:** `unhcr.refugee-data-portal`  
**Provider:** United Nations High Commissioner for Refugees  
**Categories:** `population`, `displacement`, `social_vulnerability`  
**Spatial scope:** global and country-specific series  
**Temporal scope:** periodic releases, country and indicator dependent  
**Resolution / granularity:** Aggregated refugee and displacement indicators and metadata  
**Potential roles:** `population_exposure_context`, `cross_border_movement_context`  
**Access hint:** `public_portal_api_dataset_specific_rights_review`  
**Authoritative source:** <https://refugeedata.unhcr.org/en/documentation/start-here/about/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not a catastrophe event feed or household exposure inventory. Preserve definitions and publication timing; avoid double counting IOM and UNHCR populations. Discovery evidence: World Monitor source-attribution manifest host data.unhcr.org, code scripts/seed-cross-border-arrivals.mjs; independently verify direct provider terms and exact product before use.

## IMF PortWatch port activity and maritime trade monitoring

**Candidate ID:** `imf.portwatch-maritime-activity`  
**Provider:** International Monetary Fund PortWatch  
**Categories:** `maritime`, `critical_infrastructure`, `supply_chain`  
**Spatial scope:** global maritime ports and shipping routes, product dependent  
**Temporal scope:** frequently updated maritime activity estimates  
**Resolution / granularity:** Port calls, chokepoint activity and trade disruption indicators  
**Potential roles:** `business_interruption_context`, `port_exposure_enrichment`, `trade_disruption_validation`  
**Access hint:** `public_portal_download_api_terms_review`  
**Authoritative source:** <https://portwatch.imf.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Shipping data are operational proxies, not cargo value at risk or insured business interruption. Preserve port identifiers, coverage, aggregation and methodological changes. Discovery evidence: World Monitor source-attribution manifest host portwatch.imf.org, code scripts/build-chokepoint-transit-snapshot.mjs; independently verify direct provider terms and exact product before use.

## Global Energy Monitor Global Gas Infrastructure Tracker

**Candidate ID:** `globalenergymonitor.ggit-infrastructure`  
**Provider:** Global Energy Monitor  
**Categories:** `critical_infrastructure`, `gas_pipelines`, `lng`, `exposure`  
**Spatial scope:** global  
**Temporal scope:** periodically released asset inventory  
**Resolution / granularity:** Pipelines, LNG terminals, project phases, capacity and approximate or mapped locations  
**Potential roles:** `critical_infrastructure_exposure`, `natcat_business_interruption_context`  
**Access hint:** `public_download_requires_exact_release_and_attribution_review`  
**Authoritative source:** <https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Pipeline routes may be approximate and proposed projects are not operating exposure. Preserve release, status, source geometry precision, and exact CC attribution conditions. Discovery evidence: World Monitor source-attribution manifest host globalenergymonitor.org, code scripts/import-gem-pipelines.mjs; independently verify direct provider terms and exact product before use.

## ENTSO-E Transparency Platform electricity system data

**Candidate ID:** `entsoe.transparency-electricity`  
**Provider:** European Network of Transmission System Operators for Electricity  
**Categories:** `electricity`, `infrastructure`, `business_interruption`  
**Spatial scope:** European electricity-market coverage  
**Temporal scope:** operational and historic system time series  
**Resolution / granularity:** Generation, load, transmission flows and outages where available  
**Potential roles:** `electricity_interruption_context`, `power_system_stress_validation`  
**Access hint:** `registration_api_token_and_terms_review`  
**Authoritative source:** <https://transparency.entsoe.eu/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Grid time series are not property vulnerability or claim data. Freeze bidding zones, temporal resolution, revisions and licensing terms. Discovery evidence: World Monitor source-attribution manifest host web-api.tp.entsoe.eu, code scripts/seed-electricity-prices.mjs; independently verify direct provider terms and exact product before use.

## OpenAQ global air-quality measurement API

**Candidate ID:** `openaq.global-air-quality-api`  
**Provider:** OpenAQ  
**Categories:** `air_quality`, `wildfire_smoke`, `health_context`  
**Spatial scope:** global network coverage with large spatial gaps  
**Temporal scope:** measurement observations and updates, station dependent  
**Resolution / granularity:** Station observations of particulate matter and other air pollutants  
**Potential roles:** `wildfire_smoke_observation`, `secondary_impact_validation`  
**Access hint:** `public_api_key_and_terms_review`  
**Authoritative source:** <https://docs.openaq.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Smoke particles are not fire perimeter or loss. Station and sensor biases and contributor-specific rights require separate verification. Discovery evidence: World Monitor source-attribution manifest host api.openaq.org, code scripts/seed-health-air-quality.mjs; independently verify direct provider terms and exact product before use.

## NSIDC Sea Ice Index G02135

**Candidate ID:** `nsidc.sea-ice-index-g02135`  
**Provider:** National Snow and Ice Data Center  
**Categories:** `sea_ice`, `climate`, `marine_navigation`  
**Spatial scope:** Arctic and Antarctic  
**Temporal scope:** daily and monthly historic series from 1978  
**Resolution / granularity:** Extent and concentration reference products, time series and GIS files  
**Potential roles:** `marine_climate_context`, `polar_navigation_risk_context`  
**Access hint:** `public_data_archive_product_version_terms_review`  
**Authoritative source:** <https://nsidc.org/data/seaice_index/data-and-image-archive>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not a storm-loss input. Use as polar marine hazard conditioning with product version, quality flags and observation gaps. Discovery evidence: World Monitor source-attribution manifest host noaadata.apps.nsidc.org, code scripts/seed-climate-ocean-ice.mjs; independently verify direct provider terms and exact product before use.

## World Bank World Development Indicators API v2

**Candidate ID:** `worldbank.wdi-indicators-v2`  
**Provider:** World Bank  
**Categories:** `population`, `economics`, `exposure_context`  
**Spatial scope:** global national indicators  
**Temporal scope:** annual and other periodic indicators by series  
**Resolution / granularity:** National population and economic indicators with methodology and vintage  
**Potential roles:** `portfolio_macro_scaling`, `country_exposure_context`  
**Access hint:** `public_indicators_api_dataset_license_review`  
**Authoritative source:** <https://datahelpdesk.worldbank.org/knowledgebase/articles/889392>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Country averages are not geolocated building exposure or insured values. Freeze indicator IDs, unit, country, release and missing-value semantics. Discovery evidence: World Monitor source-attribution manifest host api.worldbank.org, code scripts/_demographics-capability-source.mjs; independently verify direct provider terms and exact product before use.
