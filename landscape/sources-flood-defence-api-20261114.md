<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-flood-defence-api-20261114.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-flood-defence-api-20261114.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-14`  
**Purpose:** Non-admission discovery and source-specific bounded access preflight for public England Environment Agency and USACE flood-defence inventories, with no CAT-model approval or external data redistribution.

**Entries:** 3

## Environment Agency AIMS spatial flood defences (standardised attributes)

**Candidate ID:** `uk.ea.aims.spatial-flood-defences.2026`  
**Provider:** UK Environment Agency  
**Categories:** `flood`, `flood_defence`, `infrastructure`, `england`, `geo_api`  
**Spatial scope:** England; Environment Agency-owned, managed or inspected flood-defence features; not all flood barriers or protected areas  
**Temporal scope:** Continuously updated service; data.gov.uk catalogue updated 2026-09-18; per-asset effective/inspection dates require separate validation  
**Resolution / granularity:** ArcGIS REST FeatureServer layer 0; polyline assets with standard of protection, level, condition and maintenance metadata; British National Grid EPSG:27700; one-feature no-geometry canary  
**Potential roles:** `flood_defence_geometry_prior`, `flood_protection_sensitivity`, `levee_hazard_overlay_validation`  
**Access hint:** `public_ogl3_provider_arcgis_feature_layer_0_single_record_no_geometry_verified_via_intermediary`  
**Authoritative source:** <https://www.data.gov.uk/dataset/cc76738e-fc17-49f9-a216-977c61858dda/aims-spatial-flood-defences-inc-standardised-attributes>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official catalogue declares Open Government Licence for this product; full legal, attribution and source snapshot review remains open. Original provider service https://environment.data.gov.uk/arcgis/rest/services/EA/SpatialFloodDefencesIncStandardisedAttributes/FeatureServer/0 exposes query JSON. On 2026-11-14 an intermediary fetched precisely one no-geometry OBJECTID value (HTTP content shaped as FeatureServer JSON, EPSG:27700) using a bounded GET; this is not a trusted direct runner receipt or original archive SHA. Asset presence and nominal protection standard do not establish actual defended footprint, defence reliability, breach/overtopping probability, modelled flood depth reduction or insurer exposure. No original response bytes committed or model admitted.

## Environment Agency linked asset-management records and maintenance activities API

**Candidate ID:** `uk.ea.aims.asset-management-api.2026`  
**Provider:** UK Environment Agency  
**Categories:** `flood`, `flood_defence`, `maintenance`, `infrastructure`, `england`, `linked_data_api`  
**Spatial scope:** England; Environment Agency asset inventory, with maintenance records for a subset of assets  
**Temporal scope:** Continuously maintained operational register; historical/future maintenance events vary by asset  
**Resolution / granularity:** Documented Linked Data REST API with asset and maintenance activity/task/plan JSON endpoints, selectable _limit; relationships require asset-level keys and version-aware joins  
**Potential roles:** `defence_asset_condition_context`, `maintenance_date_sensitivity`, `flood_defence_join_challenge`  
**Access hint:** `official_documented_ogl3_asset_management_api_no_live_original_value_probe_for_this_identity`  
**Authoritative source:** <https://environment.data.gov.uk/asset-management/doc/reference>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official developer documentation describes GET endpoints, query limit and a response meta.license identifying UK OGL 3.0. This is not identical to the AIMS spatial feature layer and its join keys, ownership, availability and source-rights scope require separate verification. Documentation was inspected, but no trusted original value read or asset-to-feature link was proven. A maintenance activity record is not a verified breach history, insurance loss or structural performance estimate. Do not ingest complete asset data or infer protection quality.

## USACE National Levee Database public floodwall GIS layer

**Candidate ID:** `us.usace.nld.public-floodwalls.2026`  
**Provider:** U.S. Army Corps of Engineers, National Levee Database  
**Categories:** `flood`, `flood_defence`, `levees`, `floodwalls`, `infrastructure`, `united_states`, `geo_api`  
**Spatial scope:** United States including available territories; coverage and submitted-record completeness vary  
**Temporal scope:** Continuously maintained database with irregular source updates; check per-record last-updated date  
**Resolution / granularity:** Public ArcGIS NLD/Public FeatureServer layer 12 (Floodwalls), polyline geometry, NAD83 EPSG:4269; height/depth/width and system fields; one-feature no-geometry canary  
**Potential roles:** `levee_floodwall_inventory_crosscheck`, `flood_defence_geometry_prior`, `hazard_protection_uncertainty`  
**Access hint:** `public_usace_nld_arcgis_feature_layer_12_single_record_no_geometry_verified_via_intermediary`  
**Authoritative source:** <https://nld.sec.usace.army.mil/data-services/services/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** USACE explicitly states that public NLD data may be downloaded/shared/used, but public GIS records and non-public detailed NLD records differ; independently review each API service's conditions and source provenance before publication or commercial modelling. Original https://geospatial.sec.usace.army.mil/dls/rest/services/NLD/Public/FeatureServer/12 responds with public floodwalls schema (OBJECTID, FLOODWALL_ID, WALL_HEIGHT_FEET, SYSTEM_ID). On 2026-11-14 intermediary one-record no-geometry JSON was returned, EPSG:4269. No trusted original runner receipt or source-file hash. Do not assume height is certified protection, complete national coverage, hydraulic connectivity, or actual failure probability. No geometry, TIV or raw payload admitted.
