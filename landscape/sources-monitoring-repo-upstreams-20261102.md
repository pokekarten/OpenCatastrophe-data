<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-monitoring-repo-upstreams-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-monitoring-repo-upstreams-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery of authoritative upstream event, warning, humanitarian-response and meteorological sources used by World Monitor-like repositories; software aggregators are evidence pointers rather than source admission.

**Entries:** 12


## GLIDE global disaster identifier catalogue

**Candidate ID:** `adrc.glide.disaster-identifiers`  
**Provider:** Asian Disaster Reduction Centre / GLIDE partners  
**Categories:** `event_catalogue`, `multi_hazard`, `event_identity`  
**Spatial scope:** global  
**Temporal scope:** historical and ongoing records; registration and completeness vary  
**Resolution / granularity:** Global disaster numbers, country, disaster type, onset dates and linked reports  
**Potential roles:** `cross_provider_event_identity`, `historical_event_crosswalk`  
**Access hint:** `public_search_and_report_download_rights_review_required`  
**Authoritative source:** <https://glidenumber.net/glide/public/disclaimer.jsp>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Found through MapAction disaster-impact. GLIDE explicitly discourages secondary statistical analysis of its database; use identifiers to reconcile events, not as an independent loss or frequency estimate. Resolve variant dates, multi-country events, missing and duplicate IDs.


## IDMC Internal Displacement Updates (IDU)

**Candidate ID:** `idmc.idu.disaster-displacement`  
**Provider:** Internal Displacement Monitoring Centre  
**Categories:** `humanitarian_impact`, `displacement`, `event_catalogue`  
**Spatial scope:** global, event and country dependent  
**Temporal scope:** provisional latest 180 days; daily updates, historical GIDD separate  
**Resolution / granularity:** Event-linked displacement estimates and disaster type with selected geospatial downloads  
**Potential roles:** `post_event_population_impact`, `disaster_event_crosswalk`, `impact_validation_context`  
**Access hint:** `public_downloads_api_key_request_rights_and_provisional_data_review`  
**Authoritative source:** <https://www.internal-displacement.org/internal-displacement-updates/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Found through MapAction disaster-impact. IDU is a provisional count of internal movements, not unique people, building damage or insured losses. Preserve event window, source, estimate vintage and subsequent GIDD revisions; inspect API authentication and terms separately.


## UN CERF grants and project data API

**Candidate ID:** `unocha.cerf.gms-api`  
**Provider:** UN OCHA Central Emergency Response Fund  
**Categories:** `humanitarian_finance`, `disaster_response`, `impact_proxy`  
**Spatial scope:** global countries receiving CERF allocations  
**Temporal scope:** historical and current allocations and project records  
**Resolution / granularity:** Application, project, country, year, sector and allocation metadata  
**Potential roles:** `response_timing_context`, `event_crosswalk`, `humanitarian_impact_proxy`  
**Access hint:** `public_documented_api_exact_endpoints_rights_review_required`  
**Authoritative source:** <https://cerfgms-webapi.unocha.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** MapAction disaster-impact treats CERF as an event-related source. Financial allocations indicate humanitarian response, not gross catastrophe damage or insured claims; funding timing, emergency classification, code and overlaps with IFRC must be preserved.


## IFRC GO Disaster Response Emergency Fund appeals API

**Candidate ID:** `ifrc.go.dref-appeals-api`  
**Provider:** International Federation of Red Cross and Red Crescent Societies  
**Categories:** `humanitarian_impact`, `response_funding`, `event_catalogue`  
**Spatial scope:** global where Red Cross/Red Crescent appeals operate  
**Temporal scope:** operational and historical appeal/event records; completeness varies  
**Resolution / granularity:** Appeal code, event link, country, start/end, appeal type, amounts requested/funded and beneficiaries  
**Potential roles:** `post_event_response_context`, `cross_agency_event_crosswalk`, `humanitarian_impact_validation`  
**Access hint:** `documented_api_source_data_licence_not_confirmed`  
**Authoritative source:** <https://go-wiki.ifrc.org/en/go-api/data_dictionary_appeal>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** MapAction disaster-impact lists IFRC-DREF. GO appeal atype=0 denotes DREF; event associations may be absent and reported beneficiaries are not insured loss. GO upstream data rights may be unstated; review API conditions and field-level semantics before any persistent import.


## International Charter Space and Major Disasters activations

**Candidate ID:** `disasterscharter.activations.archive`  
**Provider:** International Charter Space and Major Disasters  
**Categories:** `satellite_response`, `event_catalogue`, `disaster_mapping`  
**Spatial scope:** global activations; selective coverage  
**Temporal scope:** public activation archive from 2000 onward  
**Resolution / granularity:** Activation ID/date, disaster type, country, links to imagery and event-specific derived mapping products  
**Potential roles:** `satellite_damage_map_discovery`, `event_identity_crosswalk`, `post_event_footprint_discovery`  
**Access hint:** `public_activation_metadata_event_products_have_separate_reuse_rights`  
**Authoritative source:** <https://disasterscharter.org/activations>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Found through MapAction disaster-impact. Activation is an observation/response selection signal, not an exhaustive event inventory. Map/imagery products have individual rights, footprints and confidence; do not conflate an activation with an observed damage polygon.


## Nepal BIPAD disaster, flood-gauge and incident APIs

**Candidate ID:** `np.ndrrma.bipad.api`  
**Provider:** Government of Nepal / NDRRMA BIPAD portal  
**Categories:** `flood`, `earthquake`, `incident_catalogue`, `hydrometeorology`, `impact`  
**Spatial scope:** Nepal  
**Temporal scope:** operational and historic portal holdings; endpoint-dependent  
**Resolution / granularity:** Events, alerts, river/rain stations, hazard layers and selected impact records by administrative geography  
**Potential roles:** `national_flood_event_monitoring`, `flood_gauge_crosscheck`, `post_event_impact_validation`  
**Access hint:** `public_api_documentation_endpoint_auth_rights_and_privacy_review_required`  
**Authoritative source:** <https://bipadportal.gov.np/api/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Discovered from Ancoda Atlas. Public API documentation lists event, flood-station, rain-stations, incident and geohazard GeoJSON endpoints; some schemas include household or individual data and must be excluded. Require per-endpoint auth, provider rights and sensitive-data review before use.


## Environment Agency real-time flood monitoring API

**Candidate ID:** `uk.environment-agency.flood-monitoring-api`  
**Provider:** Environment Agency (England)  
**Categories:** `flood`, `river_level`, `streamflow`, `warnings`, `observation`  
**Spatial scope:** England; specific forecast documents may have broader coverage  
**Temporal scope:** operational latest readings and current warnings; typical reading archive approx. four weeks with separate daily CSV archives  
**Resolution / granularity:** River stage/flow station observations, timestamps, flood warnings and warning-area geometries  
**Potential roles:** `flood_warning_trigger`, `hydrological_observation_validation`, `warning_area_crosswalk`  
**Access hint:** `open_government_licence_api_attribution_and_field_scope_review`  
**Authoritative source:** <https://environment.data.gov.uk/flood-monitoring/doc/reference>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Discovered from Emergency Centre. API documentation states public OGL open data and 15-minute service cycles but individual station upload cadence varies. Warning areas are not measured inundation and latest readings are not a complete archive. Capture unit, station datum, time and warning lifecycle.


## Met Office National Severe Weather Warnings Service API

**Candidate ID:** `uk.met-office.nswws-public-warnings`  
**Provider:** UK Met Office  
**Categories:** `severe_weather`, `alerts`, `windstorm`, `flood_context`  
**Spatial scope:** United Kingdom  
**Temporal scope:** operational issued/updated warnings; provider states no historical warnings archive  
**Resolution / granularity:** Atom feed of issued warnings, issue/change timestamps, MultiPolygon warning areas, impact likelihood and severity  
**Potential roles:** `uk_severe_weather_warning_trigger`, `warning_footprint_context`, `event_crosswalk`  
**Access hint:** `public_warning_api_terms_and_product_scope_review_required`  
**Authoritative source:** <https://datahub.metoffice.gov.uk/docs/g/category/warnings/overview>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Discovered from Emergency Centre. Met Office documents Atom as the live source of truth and no historical warning API. Need capture issued/updated/cancelled lifecycle while monitoring. Polygon means forecast warning area, never an observed physical wind/flood footprint.


## Open-Meteo multi-model forecast and archived single-runs APIs

**Candidate ID:** `openmeteo.model-forecast-single-runs`  
**Provider:** Open-Meteo GmbH (redistributor of national weather model output)  
**Categories:** `weather_forecast`, `storm`, `precipitation`, `ensemble`, `model_archive`  
**Spatial scope:** global with regional native model subsets  
**Temporal scope:** live forecasts; original-run archives depend on model and release, with IFS from 2024 and many models from April 2026  
**Resolution / granularity:** Point forecasts, selected model run/init/lead hour, model-specific spatial resolution and interpolated time series  
**Potential roles:** `cat_event_nowcast`, `multi_model_forecast_challenge`, `forecast_uncertainty_context`  
**Access hint:** `api_noncommercial_free_tier_commercial_plan_and_upstream_model_rights_review`  
**Authoritative source:** <https://open-meteo.com/en/docs/single-runs-api>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Discovered from Crisis Compass and Ancoda Atlas. The Open-Meteo APIs aggregate DWD ICON, ECMWF IFS, Météo-France ARPEGE, CMA GRAPES and other model outputs. Avoid double counting their upstream model sources as independent observations; record provider, exact model/run, interpolation, forecast lead time and commercial access terms.


## BMKG Indonesia open earthquake event feed

**Candidate ID:** `id.bmkg.earthquake-open-data`  
**Provider:** Badan Meteorologi Klimatologi dan Geofisika (BMKG)  
**Categories:** `earthquake`, `tsunami_context`, `event_catalogue`, `near_real_time`  
**Spatial scope:** Indonesia and surrounding earthquake region  
**Temporal scope:** recent earthquake snapshots updated on occurrence; separate reviewed historical repository  
**Resolution / granularity:** Recent and felt event JSON/XML with magnitude, depth, time, coordinates and ShakeMap image reference  
**Potential roles:** `southeast_asia_earthquake_event_crosswalk`, `quake_time_location_validation`  
**Access hint:** `public_json_xml_limit_60_per_minute_attribution_required_full_history_separate`  
**Authoritative source:** <https://data.bmkg.go.id/gempabumi/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Discovered in GlobeWatch. BMKG documents recent earthquake event products, seven current files and mandatory attribution, with 60 requests/minute/IP. Its public feed is a recent rolling snapshot, not complete historic seismicity. For history use the separately documented BMKG repository with authentication/rights review; preserve agency IDs and preliminary-to-reviewed revisions.


## Japan Meteorological Agency earthquake and volcano high-frequency XML feed

**Candidate ID:** `jp.jma.quake-volcano-high-frequency-xml`  
**Provider:** Japan Meteorological Agency (JMA)  
**Categories:** `earthquake`, `volcano`, `event_catalogue`, `near_real_time`  
**Spatial scope:** Japan and neighboring earthquake/volcano advisory domains  
**Temporal scope:** operational minute-updated feed carrying the most recent bulletins  
**Resolution / granularity:** Official XML bulletin references for recent earthquake and volcanic information  
**Potential roles:** `japan_event_crosswalk`, `operational_quake_warning_context`, `bulletin_revision_tracking`  
**Access hint:** `public_japan_government_standard_terms_temporal_retention_and_licence_review`  
**Authoritative source:** <https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Discovered from GlobeWatch; Japanese e-Gov data portal registers JMA eqvol.xml and Japanese Government Standard Terms of Use. Fast operational feed retains recent bulletins only, not a complete historical catalogue. Preserve native event/issue IDs, bulletin type, revisions and official original XML semantics.


## NASA Global Imagery Browse Services (GIBS) temporal satellite visualizations

**Candidate ID:** `nasa.gibs.wmts-temporal-imagery`  
**Provider:** NASA Earthdata / GIBS  
**Categories:** `satellite_imagery`, `earth_observation`, `event_context`  
**Spatial scope:** global, selected product coverage and map projection  
**Temporal scope:** time-varying NASA satellite visualization products; product-dependent archive  
**Resolution / granularity:** WMS, WMTS, TMS and XYZ map tiles with product-specific resolutions and timestamps  
**Potential roles:** `post_event_visual_review`, `satellite_overlay_context`, `original_raster_discovery`  
**Access hint:** `public_wms_wmts_visualization_service_exact_product_rights_and_data_review`  
**Authoritative source:** <https://nasa-gibs.github.io/gibs-api-docs/access-basics/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Discovered in Terra Watch. GIBS serves imagery visualizations; a colored map tile or corrected reflectance is not directly a damage mask, flood depth or numeric hazard. For quantitative CAT use identify and obtain original instrument/product values, version, cloud quality, time, projection, resampling and rights separately.
