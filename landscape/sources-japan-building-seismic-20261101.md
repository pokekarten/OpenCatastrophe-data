<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-japan-building-seismic-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-japan-building-seismic-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of Japan building geometry, semantic 3D city attributes and seismic hazard context for future catastrophe exposure and hazard research; no source rights or scientific model admission.

**Entries:** 3

## Japan MLIT PLATEAU municipal 3D city models (CityGML)

**Candidate ID:** `jp.mlit.plateau.citygml.3d-city-models`  
**Provider:** Japan Ministry of Land, Infrastructure, Transport and Tourism (MLIT) / municipal publishers  
**Categories:** `buildings`, `building_geometry_3d`, `building_attributes`, `japan`, `exposure_context`  
**Spatial scope:** Japan; municipality-dependent coverage, not a complete national building census  
**Temporal scope:** Municipal CityGML vintages and revisions differ; exact municipality, edition and source acquisition date required  
**Resolution / granularity:** CityGML building objects with varying LoD and optional measured height, floors, use and construction-year attributes; availability varies by city and object  
**Potential roles:** `building_footprint_attribute_crosswalk`, `building_height_vulnerability_prior`, `urban_building_exposure_validation`  
**Access hint:** `official_citygml_catalogue_metadata_first_city_specific_licence_and_api_terms_review`  
**Authoritative source:** <https://www.mlit.go.jp/plateau/en/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** MLIT publishes open CityGML models and describes multiple permissive licence families, but exact city/edition, municipal attribution and service-specific API terms require separate review. PLATEAU's experimental CityGML API has no guaranteed stable schema or service level. LoD1 heights may be abstracted; polygon, measured height, usage and construction year are not complete, independent or insured asset records.

## Japan GSI Fundamental Geospatial Data basic items: building outlines

**Candidate ID:** `jp.gsi.fgd.building-outline.gml`  
**Provider:** Geospatial Information Authority of Japan (GSI)  
**Categories:** `buildings`, `building_footprints`, `authoritative_mapping`, `japan`, `geometry_validation`  
**Spatial scope:** Japan; coverage and revision dates depend on mesh and production area  
**Temporal scope:** Continuously revised Fundamental Geospatial Data basic items; exact mesh file and creation date must be frozen  
**Resolution / granularity:** JPGIS/GML basic mapping items including building exterior lines, without inferred roof type or insured valuation  
**Potential roles:** `plateau_building_outline_comparison`, `building_geometry_source_crosscheck`, `geospatial_registration_audit`  
**Access hint:** `free_user_registration_required_survey_act_and_reuse_permissions_check_no_anonymous_bulk_probe`  
**Authoritative source:** <https://service.gsi.go.jp/kiban/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GSI requires free user registration for download and warns that Survey Act reproduction/use applications may be required. Do not automate credentialed access, mirror source bytes or assert open redistribution. Native exterior-line features are not identical to PLATEAU building objects: align vintage, map-sheet coverage, CRS and topology before any many-to-many matching.

## Japan NIED J-SHIS probabilistic seismic hazard and site amplification

**Candidate ID:** `jp.nied.jshis.pshm.site-amplification`  
**Provider:** National Research Institute for Earth Science and Disaster Resilience (NIED) / J-SHIS  
**Categories:** `earthquake`, `seismic_hazard`, `site_amplification`, `japan`, `hazard_context`  
**Spatial scope:** Japan national hazard-map and subsurface grids with release-specific regional coverage  
**Temporal scope:** J-SHIS map products are released by version/scenario; preserve version, reference epoch, probability window and model assumptions  
**Resolution / granularity:** Probabilistic shaking exceedance maps and curves (CSV/Shapefile/KML) and site amplification factors; grid and parameters differ by product  
**Potential roles:** `seismic_hazard_grid_crosswalk`, `building_site_condition_prior`, `hazard_model_consistency_challenge`  
**Access hint:** `jshis_public_download_portal_raw_redistribution_prohibited_derived_sale_permission_contact_no_automation`  
**Authoritative source:** <https://www.j-shis.bosai.go.jp/en/downloads>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NIED J-SHIS Terms Article 5 explicitly prohibits copying/distributing/transferring original seismic hazard maps even in a converted format; processed outputs may be distributed subject to restrictions, and commercial sale of results requires provider contact and possibly approval. Article 4 requires attribution and specific site-amplification citations. Source access stays restricted_by_terms/do_not_automate; never treat free download as licence for a public hazard raster mirror or commercial CAT model. A probability of exceedance over a specified period is not an observed event, damage, or insured loss. Exact map edition, hazard measure/horizon, mesh, data lineage and model rights still require review.
