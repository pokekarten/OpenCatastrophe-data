<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-europe-building-attribute-discovery.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-europe-building-attribute-discovery.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery-only additional European building observations, national registers, energy certificates, heights, roof equipment, address IDs and cross-country links to enrich EUBUCCO; rights/science/admission never implied.

**Entries:** 16

## TUM GlobalBuildingAtlas ODbL building polygon subset

**Candidate ID:** `tum.globalbuildingatlas.odbl-polygons`  
**Provider:** Technical University of Munich / Zhu Lab  
**Categories:** `building_footprints`, `geometry`, `global`  
**Spatial scope:** Worldwide, quality and completeness geographically variable  
**Temporal scope:** GlobalBuildingAtlas 2025 release; upstream source vintage varies  
**Resolution / granularity:** Part GBA.ODbLPolygon only: building footprints from ODbL-licensed sources, separate from commercial-restricted 3D height products; building geometry stored as EPSG:3857 per publisher  
**Potential roles:** `eubucco_completeness_screen`, `candidate_building_footprint_match`, `cross_source_lineage_audit`  
**Access hint:** `odbl_subcollection_strict_rights_and_redistribution_review`  
**Authoritative source:** <https://huggingface.co/datasets/zhu-xlab/GBA.ODbLPolygon>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Important: the separate GBA.Polygon, GBA.LoD1 and GBA.Height datasets are CC BY-NC 4.0. Publisher warns some files appear tagged EPSG:4326 but should be interpreted as EPSG:3857. Check per-file CRS and OSM/Microsoft shared lineage; this polygon subset is not independently observed or an all-building census.

## TUM GlobalBuildingAtlas LoD1 and height model (noncommercial)

**Candidate ID:** `tum.globalbuildingatlas.lod1-nc`  
**Provider:** Technical University of Munich / Zhu Lab  
**Categories:** `building_3d`, `height`, `global`  
**Spatial scope:** Worldwide, spatially variable height quality and missing features  
**Temporal scope:** 2025 public science release  
**Resolution / granularity:** Level-of-detail-1 building volumes and GBA.Height data, derived by ML and footprint fusion  
**Potential roles:** `noncommercial_height_research_reference`, `3d_model_uncertainty_benchmark`  
**Access hint:** `cc_by_nc_4_0_restricted_commercial_use_block_until_rights_decision`  
**Authoritative source:** <https://github.com/zhu-xlab/GlobalBuildingAtlas>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Separate from ODbL polygons because GBA.LoD1/GBA.Height are CC BY-NC 4.0. Research evaluation alone does not authorize incorporation into operational commercial (re)insurance CAT models, nor redistribute derived 3D features. No provider web-viewer automation or feature streaming per explicit terms.

## 3D-GloBFP Europe building footprints with heights v1

**Candidate ID:** `zenodo.3d-globfp.europe-heights.v1`  
**Provider:** Che, Li, Liu and collaborators / Zenodo  
**Categories:** `building_height`, `building_geometry`, `europe`  
**Spatial scope:** European countries including non-EU Europe in country bundles  
**Temporal scope:** Version v1 released May 2024  
**Resolution / granularity:** Country-group RAR bundles of vector shapefiles with individual polygon height attributes (~20.8GB total)  
**Potential roles:** `height_candidate_crosswalk`, `eubucco_height_missingness_reduction`, `model_disagreement_challenge`  
**Access hint:** `zenodo_cc_by_4_0_original_files_model_lineage_review`  
**Authoritative source:** <https://zenodo.org/records/11391077>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher declares CC BY 4.0; release bundles are large and height estimates model-derived, not direct LiDAR field measurements. Select small bounded country/area after documenting RAR extraction, height units, CRS, matching, height uncertainty and possible overlapping model inputs.

## Estonia Ehitisregister (EHR) open building register, geometries and certificates

**Candidate ID:** `ee.ehr.public-building-register`  
**Provider:** Estonian e-Construction platform / Land and Spatial Development Board  
**Categories:** `building_attributes`, `building_ids`, `energy_certificates`, `estonia`  
**Spatial scope:** Estonia, nationwide public building register  
**Temporal scope:** Daily updated public extraction, historical records from 1994  
**Resolution / granularity:** Building objects and use categories, entrances, permits, occupancy, technical construction attributes, energy certificates and cadastral links  
**Potential roles:** `building_id_attribute_enrichment`, `construction_year_roof_material_research`, `registry_change_detection`  
**Access hint:** `public_openapi_report_exports_exact_field_reuse_and_privacy_review`  
**Authoritative source:** <https://swaggerui.ehr.ee/avaandmete_api>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Verified data descriptions via University of Tartu open-data overview. Distinguish buildings from apartment units and entrances, current/completed from planned/demolished. Check original source open-data license, coordinate CRS, exact IDs/geometry and personal/address fields before any import; use the official API instead of scraping site pages.

## TalTech expert-validated Estonian apartment archetype and materials data

**Candidate ID:** `ee.taltech.apartment-archetypes.2026`  
**Provider:** TalTech / Iliste &amp; Viskus  
**Categories:** `material_types`, `building_archetypes`, `building_samples`, `estonia`  
**Spatial scope:** Estonian Soviet-era mass apartment housing sample  
**Temporal scope:** Released September 2026, ~1,868 expert-labelled buildings  
**Resolution / granularity:** EHR-coded apartment buildings with year, roof, wall, storeys, staircase and floor-area properties; archetype material intensities and panel counts  
**Potential roles:** `construction_material_validation_holdout`, `european_prefab_typology_prior`, `damage_repair_component_model`  
**Access hint:** `public_research_release_license_and_field_privacy_review`  
**Authoritative source:** <https://data.taltech.ee/records/k7019-pm060>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Highly useful small expert-labelled reference. Not a nationwide random building sample; Soviet mass-housing focus creates strong selection bias. Keep EHR_code only when lawful and nonidentifying; verify actual source of each reported value. Material intensities derive from archival standard-design passports, not destructive material surveys of each building.

## GeoE3 cross-border Buildings 2D OGC API collections

**Candidate ID:** `eu.geoe3.buildings2d.ogc-api`  
**Provider:** GeoE3 European location-services consortium / National Land Survey Finland  
**Categories:** `buildings`, `interoperability`, `ogc_api`, `europe`  
**Spatial scope:** Multi-country API collections: Estonia, Finland, Netherlands, Norway, Spain, France, Slovenia  
**Temporal scope:** Service snapshots and member feeds are mutable  
**Resolution / granularity:** OGC API Features harmonised access to national building polygon/reference collections  
**Potential roles:** `cross_country_schema_probe`, `building_id_translation_contract`, `spatial_reference_consistency`  
**Access hint:** `public_metadata_ogc_api_and_provider_rights_individual_review`  
**Authoritative source:** <https://locationeurope.eu/geoe3/api/buildings/collections>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Gateway republishes national authorities' information and is NOT an independent building-survey source. Each collection requires its own service terms, access limits, country-specific content/version and original license; do not confuse harmonised schema with harmonised rights.

## France IGN LiDAR HD classified point-cloud tiles

**Candidate ID:** `fr.ign.lidar-hd.classified`  
**Provider:** Institut national de l'information géographique et forestière  
**Categories:** `lidar`, `building_height`, `roof_geometry`, `france`  
**Spatial scope:** Metropolitan France and listed overseas regions as acquisition progresses; map availability per tile  
**Temporal scope:** 2026 source update; survey dates vary across acquisition blocks  
**Resolution / granularity:** Classified LAZ 1.4 or COPC tiles with ground/building/vegetation classes, 1km² tiles often 0.5–2GB; &gt;=10 laser shots/m² typical under 3200m  
**Potential roles:** `independent_building_height_check`, `roof_shape_geometry_extraction`, `ground_floor_elevation_proxy`  
**Access hint:** `fr_open_licence_v2_tile_download_rights_and_coverage_review`  
**Authoritative source:** <https://www.data.gouv.fr/datasets/nuages-de-points-lidar-hd>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official French data portal states Licence Ouverte v2.0, but check exact tile and attribution. Cloud acquisition may precede latest footprint; huge tile volumes. Convert vertical reference before height comparison; do not mistake roof altitude for ground-relative building height. Coverage expected by 2026 is not guaranteed complete on 2026-11-01.

## Germany NRW Geobasis 3D laser measurement point clouds (3DM)

**Candidate ID:** `de.nrw.geobasis.3d-lidar`  
**Provider:** Bezirksregierung Köln / Geobasis NRW  
**Categories:** `lidar`, `terrain`, `building_height`, `germany`  
**Spatial scope:** North Rhine-Westphalia, Germany statewide  
**Temporal scope:** Continuous regional acquisition with heterogeneous campaigns; planned increased density end-2026 onward  
**Resolution / granularity:** LAS/LAZ airborne point clouds with return class, intensity, GPS timestamp and ground/surface distinction  
**Potential roles:** `building_height_lidar_holdout`, `roof_obstruction_validation`, `flood_ground_elevation_support`  
**Access hint:** `state_open_geobasis_tile_license_version_review`  
**Authoritative source:** <https://www.bezreg-koeln.nrw.de/geobasis-nrw/produkte-und-dienste/hoehenmodelle/3d-messdaten>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Capture exact acquisition tile, original CRS/horizontal and vertical reference, point density and measurement date. Not direct construction year or material. Do not assume planned 2027 enhanced point density exists in current historical tiles.

## Switzerland swissSURFACE3D national LiDAR classified point cloud

**Candidate ID:** `ch.swisstopo.swisssurface3d-lidar`  
**Provider:** Swiss Federal Office of Topography swisstopo  
**Categories:** `lidar`, `building_height`, `surface_models`, `switzerland`  
**Spatial scope:** Switzerland and Liechtenstein, nationally available since 2024  
**Temporal scope:** Mixed acquisition years; new COPC/LAZ types since 2024  
**Resolution / granularity:** Georeferenced classified XYZ points for buildings, bare earth and vegetation, generally 1 km² tiles  
**Potential roles:** `building_height_ground_truth_candidate`, `terrain_elevation_link`, `3d_building_roof_validation`  
**Access hint:** `official_open_geodata_tile_terms_crs_and_attribution_review`  
**Authoritative source:** <https://www.swisstopo.admin.ch/de/hoehenmodell-swisssurface3d>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct raw observation layer versus already catalogued swissBUILDINGS3D 3.0 derived model; may share raw LiDAR processing and is not independent of the derived model. Swiss vertical datum and EGID building linkage need review.

## Slovenia official real estate cadastre building layer INSPIRE WFS

**Candidate ID:** `si.gurs.realestate-cadastre-buildings`  
**Provider:** Surveying and Mapping Authority of the Republic of Slovenia (GURS)  
**Categories:** `cadastral_buildings`, `official_ids`, `slovenia`  
**Spatial scope:** Slovenia nationwide  
**Temporal scope:** Maintained real estate cadastre, metadata from 2022 and updates thereafter  
**Resolution / granularity:** Building polygons and cadastral parcels in national D96/TM (EPSG:3794) via WFS/WMS and cadastral records  
**Potential roles:** `official_building_footprint_benchmark`, `national_building_identifier_crosswalk`  
**Access hint:** `public_inspire_wfs_service_terms_and_original_rights_review`  
**Authoritative source:** <https://eprostor.gov.si/imps/srv/api/records/9a8fd241-9162-407c-94e7-c98e05766881/formatters/xsl-view?portalLink=&view=inspire>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** INSPIRE building polygons are not automatically freely bulk redistributable; examine specific WFS schema/terms and cadastral identification separately. Map provider feature identifiers to durable local IDs with type/geometry and snapshot preservation.

## Madrid Autonomous Community Energy Efficiency Certificate Register (CEEE)

**Candidate ID:** `es.madrid.energy-certificates`  
**Provider:** Comunidad de Madrid Open Data  
**Categories:** `epc`, `building_technical`, `spain`  
**Spatial scope:** Madrid autonomous region, certified residential and other buildings  
**Temporal scope:** Year-scoped public CSV downloads, monthly current-year updates incl 2026  
**Resolution / granularity:** Certificates with heating/cooling, energy rating, date and selected building construction/system characteristics  
**Potential roles:** `construction_class_enrichment`, `certificate_era_calibration`, `roof_wall_thermal_feature_prior`  
**Access hint:** `regional_csv_open_data_licence_address_fields_privacy_review`  
**Authoritative source:** <https://datos.comunidad.madrid/dataset/registro_certificados_eficiencia_energetica>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Certificate scope may be a dwelling or building, many vintages per real property, missing exact cadastral IDs; do not treat as exhaustive housing stock or a direct structural material survey. Avoid over-linking raw addresses to individuals; check original source licence and matched spatial precision.

## Lombardy regional CENED+2.0 Energy Performance Certificates

**Candidate ID:** `it.lombardia.cened-plus2`  
**Provider:** Lombardia / ARIA CENED  
**Categories:** `epc`, `building_attributes`, `italy`  
**Spatial scope:** Lombardy, Italy; certified premises  
**Temporal scope:** Rolling certification data; published version varies by dataset  
**Resolution / granularity:** Public datasets with building location context, energy rating, geometric characteristics, systems and renewable-energy use  
**Potential roles:** `building_geometry_energy_crosswalk`, `construction_use_enrichment`, `heating_equipment_context`  
**Access hint:** `public_socrata_csv_original_licence_qa_and_privacy_review`  
**Authoritative source:** <https://www.cened.it/opendata-cened-2.0>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** APE certificate is a property/dwelling observation, not necessarily whole-building identity. Multiple certificates across time create duplicated buildings. Preserve valid year, status, cadastral/address match and source entity granularity; do not infer structural vulnerability from energy performance alone.

## Germany Marktstammdatenregister public rooftop solar unit inventory

**Candidate ID:** `de.bnetza.mastr.public-solar`  
**Provider:** Bundesnetzagentur / Marktstammdatenregister  
**Categories:** `rooftop_pv`, `equipment`, `building_assets`, `germany`  
**Spatial scope:** Germany nationwide with privacy-restricted site precision  
**Temporal scope:** Daily public XML full extract and dated snapshots; new export structure October 2025  
**Resolution / granularity:** Public registered solar units by commissioning time, capacity and site fields subject to data protection  
**Potential roles:** `rooftop_equipment_exposure_prior`, `pv_hail_wind_vulnerability_scope`, `technology_growth_validation`  
**Access hint:** `public_xml_bulk_dlde_by_2_and_localisation_privacy_restriction_review`  
**Authoritative source:** <https://www.marktstammdatenregister.de/MaStR/Datendownload>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official register withholds street/house number and geocoordinates of solar installations &lt;=30kWp and other natural-person details. It MUST NOT be reverse-geocoded to individual homes via external datasets. Match only lawful published precise sites or aggregate by geography; do not treat PV capacity as insured replacement amount. Full XML extract ~3GB zipped as of 2026-11-01.

## France Base Adresse Nationale (BAN) official geocoded address dataset

**Candidate ID:** `fr.ban.national-addresses`  
**Provider:** French national reference addresses / IGN and local authorities  
**Categories:** `addresses`, `geocoding`, `building_links`, `france`  
**Spatial scope:** France national, department-sliced releases  
**Temporal scope:** Daily per-department published files; latest directory updated October 2026  
**Resolution / granularity:** Addresses with stable BAN identifiers and geocoded representative points in CSV, national reference service  
**Potential roles:** `rnb_bdtopo_address_crosswalk`, `geocoding_confidence_assessment`, `certificate_building_linkage`  
**Access hint:** `public_open_license_exact_download_original_data_rights_review`  
**Authoritative source:** <https://adresse.data.gouv.fr/outils/telechargements>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** An address point is NOT a building centroid, and a building can contain many addresses; do not create false one-to-one building IDs or retain owner/occupant details. Legacy api-adresse.data.gouv.fr endpoint deprecated, use modern Geoplateforme or official downloadable files, version and coordinate CRS.

## Hotmaps EU heat demand and gross floor area density raster references

**Candidate ID:** `eu.hotmaps.heat-demand-100m`  
**Provider:** Hotmaps EU research consortium  
**Categories:** `floor_area`, `heat_demand`, `building_stock_aggregates`, `europe`  
**Spatial scope:** EU28 and selected neighbouring countries incl Switzerland Norway Iceland  
**Temporal scope:** 2015 heat/floor reference, legacy 2017–2019 modeling papers  
**Resolution / granularity:** 100m x 100m heat-density/finished floor-area and housing-category raster datasets, plus downloadable model data repositories  
**Potential roles:** `residential_floor_area_aggregate_validation`, `building_storeys_urban_prior`, `heated_occupancy_class_prior`  
**Access hint:** `public_open_research_raster_version_and_licence_review`  
**Authoritative source:** <https://wiki.hotmaps.eu/en/Hotmaps-open-data-repositories>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Heat demand and floor area are modelled from stock data, not individual building records. 2015 data are temporally stale; avoid exact building assignment. Use only aggregated catchment/grid validation, accounting for source duplication with Eurostat national building statistics.

## Ordnance Survey NGD roof geometry/attributes (restricted product)

**Candidate ID:** `uk.os-ngd.roofs.2025`  
**Provider:** Ordnance Survey Great Britain  
**Categories:** `roof_shapes`, `building_3d`, `uk`  
**Spatial scope:** Great Britain; provider reports coverage of more than 40 million roofs  
**Temporal scope:** New roof theme launched March 2025  
**Resolution / granularity:** Detailed roof mapping products in OS National Geographic Database intended for commercial/geospatial workflows  
**Potential roles:** `roof_form_wind_hail_model_reference`, `commercial_dataset_cost_benchmark`  
**Access hint:** `proprietary_os_ngd_licensed_access_not_open_source`  
**Authoritative source:** <https://www.ordnancesurvey.co.uk/news/new-roof-data-for-over-40-million-buildings>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Keep discovery only: OS NGD roof attributes should not be confused with free OS OpenMap Local and OS Open UPRN. Before any use, purchase/contract/rights and data licensing review; do not claim free download or derive user-facing roof models from proprietary source.
