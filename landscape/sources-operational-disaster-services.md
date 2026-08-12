<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-operational-disaster-services.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-operational-disaster-services.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-12`  
**Purpose:** Non-admission discovery registry of operational disaster alert, rapid-mapping, event-response and loss-and-damage tracking services relevant to catastrophe risk.

**Entries:** 5

## Global Disaster Alert and Coordination System (GDACS) API

**Candidate ID:** `ec-jrc.gdacs.api`  
**Provider:** European Commission Joint Research Centre / United Nations partner network  
**Categories:** `multi_hazard`, `event_catalogue`, `alerting`, `api`, `geospatial`  
**Spatial scope:** global  
**Temporal scope:** operational near-real-time event monitoring plus historical event resources; event-type dependent  
**Resolution / granularity:** event and episode records plus GeoJSON/CAP resources, hazard geometries, cyclone areas of interest and earthquake ShakeMap-linked products  
**Potential roles:** `global_event_detection`, `event_identity_crosswalk`, `alert_context`, `hazard_geometry_discovery`  
**Access hint:** `public_openapi_and_public_event_resources`  
**Authoritative source:** <https://www.gdacs.org/gdacsapi/swagger/index.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GDACS documents an OAS 3.0 Web API with event-list, polygon, cyclone-AOI, ShakeMap and related endpoints, and public event resource directories expose GeoJSON/CAP artifacts. Treat automated alert/model outputs as event-discovery and context evidence rather than unquestioned ground truth; freeze event type, event/episode identifiers, retrieval time and resource identity.

## DLR Center for Satellite Based Crisis Information (ZKI) Activations

**Candidate ID:** `dlr.zki.activations`  
**Provider:** German Aerospace Center (DLR) / Center for Satellite Based Crisis Information  
**Categories:** `rapid_mapping`, `satellite_observations`, `emergency_response`, `event_catalogue`, `geospatial`  
**Spatial scope:** global and Germany-focused activations depending on tasking and event  
**Temporal scope:** historical activation archive plus current crisis-mapping exercises and operational products  
**Resolution / granularity:** activation records with event metadata and downloadable mapping products; activation catalogue exposes GeoJSON and GeoRSS feeds  
**Potential roles:** `rapid_mapping_discovery`, `independent_damage_mapping`, `event_response_validation`, `activation_crosswalk`  
**Access hint:** `public_activation_catalog_with_geojson_georss_and_product_specific_access`  
**Authoritative source:** <https://activations.zki.dlr.de/en/activations/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ZKI exposes GeoJSON and GeoRSS activation feeds and publishes event-specific map products in formats that can include GeoPDF, KMZ and image products. Availability, downstream imagery rights and product formats vary by activation, so each concrete product still requires asset-level provenance and rights review.

## NASA Disasters Mapping Portal

**Candidate ID:** `nasa.disasters.mapping-portal`  
**Provider:** NASA Earth Science / Disasters Program  
**Categories:** `rapid_mapping`, `near_real_time`, `remote_sensing`, `gis_services`, `multi_hazard`  
**Spatial scope:** global, event- and product-dependent  
**Temporal scope:** near-real-time products plus disaster-specific event products  
**Resolution / granularity:** heterogeneous GIS layers and products exposed through Esri REST and open-source-compatible WMS endpoints  
**Potential roles:** `rapid_mapping_discovery`, `event_observation`, `cross_source_validation`, `gis_service_ingestion`  
**Access hint:** `public_rest_and_wms_no_login`  
**Authoritative source:** <https://disasters.nasa.gov/what-we-do/disasters/practitioner-resources>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NASA documents the Disasters Mapping Portal as freely accessible without login and exposes products through REST and WMS. The portal is a distribution layer over heterogeneous upstream products, so preserve layer/service identifiers, source mission or model, event, timestamps, processing level and upstream rights rather than treating the portal as one homogeneous dataset.

## NASA/JPL ARIA Event Response Products

**Candidate ID:** `nasa-jpl.aria.event-response`  
**Provider:** NASA Jet Propulsion Laboratory / Advanced Rapid Imaging and Analysis (ARIA)  
**Categories:** `rapid_mapping`, `sar`, `earthquake`, `flood`, `damage_proxy`, `event_response`  
**Spatial scope:** event-specific coverage where suitable SAR/GNSS observations are available  
**Temporal scope:** historical and current urgent-response products; event dependent  
**Resolution / granularity:** event-response Damage Proxy Maps, Flood Proxy Maps, InSAR and GPS results with sensor- and event-specific resolution  
**Potential roles:** `damage_proxy_validation`, `flood_extent_validation`, `earthquake_response_observation`, `independent_rapid_mapping`  
**Access hint:** `public_event_response_share_no_login_with_separate_standard_product_login`  
**Authoritative source:** <https://aria.jpl.nasa.gov/products/index.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ARIA states that event-response products are available through ARIA Share without login, while standard product search uses NASA Earthdata authentication. Damage and flood proxy maps are derived remote-sensing products, not direct structure-level loss observations; freeze event, input sensor/acquisition pair, product version, processing method and mask/quality semantics.

## UNDRR DELTA Resilience

**Candidate ID:** `undrr.delta-resilience`  
**Provider:** United Nations Office for Disaster Risk Reduction and partner organizations  
**Categories:** `disaster_loss`, `damage`, `hazard_events`, `impact_tracking`, `interoperability`, `api`  
**Spatial scope:** country-owned national and subnational deployments with global methodological framework  
**Temporal scope:** operational rollout from 2025 onward, building on DesInventar historical loss-and-damage practice  
**Resolution / granularity:** hazardous-event and disaster-impact records with sectoral, human, economic and non-economic loss-and-damage dimensions and UUID-based linkage  
**Potential roles:** `loss_damage_interoperability`, `official_impact_linkage`, `event_impact_crosswalk`, `loss_model_validation`  
**Access hint:** `open_source_toolkit_with_open_api_capability_and_country_specific_data_governance`  
**Authoritative source:** <https://www.undrr.org/building-risk-knowledge/disaster-losses-and-damages-tracking-system-delta-resilience>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** UNDRR describes DELTA as a standards-based system that supports open APIs and links hazardous events to observed impacts using UUIDs and WMO-CHE-aligned methods. The software architecture and methodological framework do not imply that every country deployment or national dataset is openly redistributable; data governance and rights must remain instance- and dataset-specific.
