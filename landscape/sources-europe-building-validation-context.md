<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-europe-building-validation-context.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-europe-building-validation-context.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of additional European building geometry, height, population-level, national identity, energy and reference-cost context sources for EUBUCCO cross-checks. All data rights and model admission remain separate.

**Entries:** 19

## Flanders official Buildings Register / Gebouwenregister

**Candidate ID:** `be.vlaanderen.gebouwenregister`  
**Provider:** Digitaal Vlaanderen  
**Categories:** `buildings`, `ids`, `lifecycle`, `geometry`, `belgium`  
**Spatial scope:** Flemish Region, Belgium  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Building and building-unit identities, lifecycle/status and object geometries; official OGC API Features  
**Potential roles:** `building_id_crosswalk`, `building_footprint_validation`  
**Access hint:** `public_ogc_api_registration_and_terms_review`  
**Authoritative source:** <https://geo.api.vlaanderen.be/Gebouwenregister/ogc/features/v1/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Stable building identifiers enable region-level matching to GRB and 3D GRB; retain building-versus-building-unit identity and version. Building register geometry is derived from GRB, so this pair is shared lineage, not two independent sources.

## Flanders 3D GRB building heights and LoD1 geometry

**Candidate ID:** `be.vlaanderen.3d-grb`  
**Provider:** Digitaal Vlaanderen  
**Categories:** `buildings`, `height`, `3d_geometry`, `belgium`  
**Spatial scope:** Flemish Region, Belgium  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** GRB building geometry extruded to LoD1 with heights derived from Flemish digital height model DHMVII  
**Potential roles:** `height_cross_validation`, `building_stock_validation`  
**Access hint:** `public_wms_and_catalogue_service_conditions_exact_asset_review`  
**Authoritative source:** <https://www.vlaanderen.be/datavindplaats/catalogus/3d-grb>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Good for quantitative building-height checks where matched to the Flemish register/GRB. The WMS is a view interface; downloadable bulk geometry and height fields must be validated separately. Derived heights are not independent field measurements.

## Brussels UrbIS parcels and buildings

**Candidate ID:** `be.brussels.urbis-buildings`  
**Provider:** Brussels regional authority / Paradigm  
**Categories:** `buildings`, `footprints`, `addresses`, `belgium`  
**Spatial scope:** Brussels-Capital Region, Belgium  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Two-dimensional building geometries, current addresses and cadastral parcel geometry; downloadable ZIP and WFS  
**Potential roles:** `footprint_cross_validation`, `building_address_linkage`  
**Access hint:** `public_download_wfs_mixed_component_licence_review`  
**Authoritative source:** <https://data.gov.be/en/datasets/2cf42541-1813-11ef-8a81-00090ffe0001>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Important rights nuance: cadastral parcel class originates from Belgian federal finance and is subject to its own licence. Separate actual building/adress class before mixing or redistribution. Verify spatial and temporal join and never assume address equals a building.

## Wallonia PICC large-scale topographic reference

**Candidate ID:** `be.wallonie.picc`  
**Provider:** Service public de Wallonie / Geoportail de la Wallonie  
**Categories:** `buildings`, `topography`, `geometry`, `belgium`  
**Spatial scope:** Walloon Region, Belgium  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Large-scale topographic object data with buildings and 3D coordinate context; availability and exact feature layers need verification  
**Potential roles:** `regional_building_coverage_validation`, `footprint_cross_validation`  
**Access hint:** `public_metadata_spatial_service_and_rights_review`  
**Authoritative source:** <https://geoportail.wallonie.be/catalogue/b795de68-726c-4bdf-a62a-a42686aa5b6f.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Candidate for Walloon footprint coverage independent of Flemish and Brussels regional data. Check downloadable polygon/3D representation, survey precision, attribution, contractual right to automated access and scope before claiming free reuse.

## Switzerland Federal Register of Buildings and Dwellings (GWR/RegBL) public extract

**Candidate ID:** `ch.bfs.gwr-regbl`  
**Provider:** Swiss Federal Statistical Office (BFS)  
**Categories:** `buildings`, `ids`, `construction_attributes`, `switzerland`  
**Spatial scope:** Switzerland, public level A records according to federal ordinance  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Public GWR CSV/DSV downloads and web services with EGID building IDs and selected administrative attributes  
**Potential roles:** `egid_attribute_enrichment`, `building_id_crosswalk`  
**Access hint:** `public_level_a_download_attribution_webservice_limits_review`  
**Authoritative source:** <https://www.rea.admin.ch/de/data/supply/public.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Strong EGID linkage with swissBUILDINGS3D 3.0 in EGID-enabled cantons. Public level A is allowed with source attribution; field visibility differs by access level. Provider says extracts are uncorrected raw records; public query interface prohibits robots and webservices have rate limits. Prefer authorised bulk extract, not scraping.

## Austria Gebäude- und Wohnungszählung building census time series

**Candidate ID:** `at.statistik-austria.building-census`  
**Provider:** Statistik Austria  
**Categories:** `statistics`, `building_stock`, `age_distribution`, `austria`  
**Spatial scope:** Austria, official building and dwelling population statistics  
**Temporal scope:** Historical time series from 2011 onwards, with 2026 catalogue update  
**Resolution / granularity:** Aggregate counts and housing characteristics, reference-period/cross-tabulation basis; not open individual footprints  
**Potential roles:** `regional_building_stock_validation`, `construction_age_prior`  
**Access hint:** `public_statistical_open_data_aggregation_and_rights_review`  
**Authoritative source:** <https://www.data.gv.at/datasets/e2b73830-54ed-3d36-9f7e-666e4f3c5e78?locale=de>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use to compare modelled count, residential mix and year distribution at matching administrative and observation periods. Do not back-project aggregate categories to exact buildings; this is not direct identity enrichment.

## Vienna Baukörpermodell LoD1.4 3D buildings

**Candidate ID:** `at.wien.baukoerper-lod14`  
**Provider:** City of Vienna MA 41 / Open Government Data Wien  
**Categories:** `buildings`, `3d_geometry`, `height`, `austria`  
**Spatial scope:** Vienna, Austria  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** 3D building bodies and simplified heights/geometries; geometry download release and restricted free test-sample routes require differentiation  
**Potential roles:** `height_cross_validation`, `urban_exposure_validation`  
**Access hint:** `public_city_ogd_dataset_but_full_model_vs_samples_review`  
**Authoritative source:** <https://www.data.gv.at/datasets/214a3e63-31aa-47de-a49c-5ea5a80330ed?locale=de>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Verify that selected resource is an actual open citywide triangulation file rather than free samples only. Use for urban height and footprint cross-checks; building roof forms are generalized and measured construction attributes need separate evidence.

## Netherlands Actueel Hoogtebestand Nederland (AHN) airborne LiDAR elevation products

**Candidate ID:** `nl.ahn.elevation`  
**Provider:** AHN / Rijkswaterstaat / PDOK  
**Categories:** `lidar`, `surface_model`, `terrain`, `height`, `netherlands`  
**Spatial scope:** Netherlands, tiled national coverage by AHN release  
**Temporal scope:** Multiple AHN campaigns; spatially heterogeneous acquisition and evolving releases  
**Resolution / granularity:** Classified LAZ point clouds, DTM/DSM GeoTIFF grids at 0.5 m and coarser resolution; mixed geographic and time vintages  
**Potential roles:** `height_model_source`, `terrain_elevation_source`  
**Access hint:** `open_data_tiled_laz_geotiff_download_explicit_version_licence_review`  
**Authoritative source:** <https://www.ahn.nl/dataroom>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Estimate heights as corrected roof surface minus local ground, with proper vertical datum and building footprint joins to BAG. Preserve AHN release and airborne acquisition date; bare DSM heights are not structural heights. 3DBAG/3D Basisvoorziening may already depend on AHN, so not independent height validation.

## Netherlands official 3D Basisvoorziening buildings and terrain

**Candidate ID:** `nl.kadaster.3d-basisvoorziening`  
**Provider:** Kadaster / PDOK  
**Categories:** `buildings`, `3d_geometry`, `terrain`, `netherlands`  
**Spatial scope:** Netherlands, nationwide annual 3D products subject to product coverage  
**Temporal scope:** Annual production; verify current release and date of incorporated BAG/height layers  
**Resolution / granularity:** 3D building and terrain geometry derived from BAG/BGT and height inputs with OGC service and downloads  
**Potential roles:** `3d_geometry_interoperability`, `height_cross_validation`  
**Access hint:** `public_ogc_api_and_download_terms_review`  
**Authoritative source:** <https://api.pdok.nl/kadaster/3d-basisvoorziening/ogc/v1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Important cross-check against 3DBAG but shared lineage: BAG buildings and airborne height inputs overlap; use release, upstream imagery and field-specific height provenance to avoid counting agreement as independent confirmation.

## Bavaria official 2D Hausumringe building footprint polygons

**Candidate ID:** `de.bayern.hausumringe`  
**Provider:** Bayerische Vermessungsverwaltung / LDBV  
**Categories:** `buildings`, `footprints`, `cadastral`, `germany`  
**Spatial scope:** Bavaria, Germany  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Official cadastral-derived 2D building footprint polygons independent of 3D representation  
**Potential roles:** `footprint_cross_validation`, `geometric_coverage_benchmark`  
**Access hint:** `state_open_data_tiled_download_exact_licence_review`  
**Authoritative source:** <https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=hausumringe>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The best inexpensive geometry pilot for EUBUCCO. Compare geometry, area, building subdivision and vintage to Bavarian LoD2 without double counting the shared cadastral survey source. Capture attribution and no assumption of insured value.

## German federal Amtliche Hausumringe Deutschland (HU-DE)

**Candidate ID:** `de.bkg.hu-de`  
**Provider:** Bundesamt für Kartographie und Geodäsie (BKG) / AdV  
**Categories:** `buildings`, `footprints`, `cadastral`, `germany`  
**Spatial scope:** Germany; federal product derived from state cadastral house outlines  
**Temporal scope:** Quarterly product updates; exact region/vintage and contract differ  
**Resolution / granularity:** Survey-derived building footprint polygons, municipality and regional keys; product availability subject to license agreement  
**Potential roles:** `authoritative_footprint_validation`, `municipality_crosswalk`  
**Access hint:** `restricted_licence_agreement_eligible_users_only`  
**Authoritative source:** <https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/sonstige-geodaten/amtliche-hausumringe-deutschland-hu-de.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The BKG explicitly limits this national product to an eligible user circle and requires a licence agreement. Do not download or infer free national rights from the Bavaria open subset. Individual regional products may substitute for a free pilot.

## German Zensus 2022 open building and dwelling grid data

**Candidate ID:** `de.destatis.zensus2022-building-grid`  
**Provider:** Statistisches Bundesamt / Zensus 2022  
**Categories:** `statistics`, `buildings`, `construction_age`, `germany`  
**Spatial scope:** Germany, nationwide aggregate grid cells  
**Temporal scope:** Reference date Zensus 2022 with file updates and revisions thereafter  
**Resolution / granularity:** 100 m, 1 km and 10 km CSV grid records of residential building counts and construction-decade, type and dwelling attributes, subject to statistical secrecy  
**Potential roles:** `spatial_aggregate_calibration`, `construction_age_prior`  
**Access hint:** `public_gis_csv_zip_open_data_attribution_disclosure_controls`  
**Authoritative source:** <https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use for regional calibration of EUBUCCO's age/typology distributions. Grid cell is not a building or location ID and suppressed/undisclosed small counts are not zero. Never reconstruct individual confidential structures from the census.

## Great Britain OS Open UPRN addressable location identifiers

**Candidate ID:** `uk.os.open-uprn`  
**Provider:** Ordnance Survey  
**Categories:** `property_ids`, `geocoding`, `addresses`, `uk`  
**Spatial scope:** Great Britain; addressable locations including nonbuilding objects  
**Temporal scope:** Publisher updates about every six weeks  
**Resolution / granularity:** UPRN point identifiers/locations in British National Grid and latitude/longitude, supplied as CSV or GeoPackage  
**Potential roles:** `property_identifier_crosswalk`, `uk_epc_geocoding`  
**Access hint:** `public_open_download_licence_exact_release_review`  
**Authoritative source:** <https://www.ordnancesurvey.co.uk/products/os-open-uprn>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** About 40 million addressable locations; an UPRN is not a building polygon, and multiple UPRNs can map to one building or to nonbuilding assets. Use only a verified UPRN/geometry crosswalk before joining EPC or other property attributes.

## Great Britain OS OpenMap Local vector buildings

**Candidate ID:** `uk.os.openmap-local`  
**Provider:** Ordnance Survey  
**Categories:** `buildings`, `geometry`, `uk`  
**Spatial scope:** Great Britain nationwide  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Street-level vector topographic mapping including selected generalized building polygons in GeoPackage/Shapefile/GML distribution  
**Potential roles:** `footprint_cross_validation`, `uk_geospatial_baseline`  
**Access hint:** `open_geodata_download_license_and_buildings_feature_schema_review`  
**Authoritative source:** <https://osdatahub.os.uk/downloads/open/OpenMapLocal>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use generalized open buildings as geometry coverage benchmark only, not cadastral parcel identity. Distinguish this free product from paid OS National Geographic Database detailed building features and avoid implying full roof or construction attributes.

## EU Building Stock Observatory

**Candidate ID:** `eu.ec.building-stock-observatory`  
**Provider:** European Commission / Directorate-General for Energy  
**Categories:** `building_stock`, `energy`, `statistics`, `europe`  
**Spatial scope:** European Union and participating country-level building statistics  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Country/sector building-stock indicators, energy performance and construction/renovation characteristics at aggregate level  
**Potential roles:** `national_stock_calibration`, `energy_class_context`  
**Access hint:** `public_statistical_dashboard_exact_indicators_download_rights_review`  
**Authoritative source:** <https://energy.ec.europa.eu/topics/energy-efficiency/energy-performance-buildings/eu-building-stock-observatory_en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Candidate aggregate calibration for building type, age and energy class; it is not individual building geodata. Check source survey definitions, geographic vintage, update frequency and whether reproducible machine export exists.

## European TABULA / EPISCOPE residential building typologies

**Candidate ID:** `eu.tabula.episcope`  
**Provider:** TABULA / EPISCOPE European project consortium  
**Categories:** `building_typology`, `construction`, `residential`, `europe`  
**Spatial scope:** Selected European countries with different national residential typology coverage  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Reference building archetypes by age, size, envelopes and refurbishment assumptions; often national example structures  
**Potential roles:** `archetype_prior`, `vulnerability_taxonomy_research`  
**Access hint:** `public_webtool_reference_data_download_and_licence_review`  
**Authoritative source:** <https://webtool.building-typology.eu/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use archetype mapping only as a probabilistic vulnerability/material prior when year and typology evidence are missing. Example structures are not measured characteristics of EUBUCCO buildings, and no building-level IDs are supplied.

## Luxembourg BD-L-BATI3D official 2D footprints and LoD2.2 buildings

**Candidate ID:** `lu.act.bd-l-bati3d-2023`  
**Provider:** Administration du cadastre et de la topographie (ACT)  
**Categories:** `buildings`, `footprints`, `3d_geometry`, `luxembourg`  
**Spatial scope:** Luxembourg, nationwide according to 2023 aerial coverage, roof footprint threshold &gt;20 square metres  
**Temporal scope:** 2023 aerial observations; v2 resources and catalogue updated in March 2026  
**Resolution / granularity:** Official 2D building footprints available in GeoPackage and 3D building roof/wall/ground models in tiled CityGML/geodatabase  
**Potential roles:** `authoritative_footprint_validation`, `3d_roof_geometry_benchmark`  
**Access hint:** `cc0_dataset_catalog_2d_gpkg_small_pilot_exact_asset_sha_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2023/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Very strong bounded free pilot: publisher labels CC0 and offers 2D GeoPackage ZIP about 60 MB (2026-03-17 resource), versus much larger 3D data. Not all micro-structures (&lt;20 m²) covered; photo/model vintage and geom subdivision differ from EUBUCCO. Verify current file, ID, CRS and provenance before import.

## Luxembourg official BD-L-GeoBase geographic reference

**Candidate ID:** `lu.act.bd-l-geobase`  
**Provider:** Administration du cadastre et de la topographie (ACT)  
**Categories:** `topography`, `buildings`, `geometry`, `luxembourg`  
**Spatial scope:** Luxembourg, nationwide official vector baseline  
**Temporal scope:** Maintained source; exact data snapshot and observation vintage must be frozen  
**Resolution / granularity:** Official geodata vector baseline with multiple themes including buildings/topographic context to be verified per released layer  
**Potential roles:** `reference_geometry_validation`, `geospatial_context`  
**Access hint:** `public_catalogue_theme_specific_license_schema_review`  
**Authoritative source:** <https://data.public.lu/en/datasets/bd-l-geobase/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinguish this reference geobase from BD-L-BATI3D and the legacy BD-L-TC predecessor; assess exact building/footprint layer before any building-level join, avoid counting derived same-source geometry as independent evidence.

## Germany ETHOS.BUILDA residential building archetype dataset

**Candidate ID:** `de.fzj.ethos-builda`  
**Provider:** Forschungszentrum Jülich  
**Categories:** `buildings`, `construction_age`, `typology`, `germany`  
**Spatial scope:** Germany nationwide modeled residential building stock  
**Temporal scope:** Version 2.0.0 released October 2024; check publication/revision and exact files  
**Resolution / granularity:** Building-level derived construction year, size/refurbishment class and TABULA archetypes, with machine learning enrichment  
**Potential roles:** `missing_attribute_imputation_benchmark`, `residential_archetype_mapping`  
**Access hint:** `public_zenodo_release_odbl_terms_and_original_source_rights_review`  
**Authoritative source:** <https://zenodo.org/records/13771740>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** High-value experimental imputation comparator for EUBUCCO German residential buildings. Machine-learning derived values and upstream datasets may overlap EUBUCCO/OSM, so validate independence and matching identifiers before calibration. Do not equate archetype with surveyed material or actual insured exposure.
