<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-cross-domain-exposure-enrichment.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-cross-domain-exposure-enrichment.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of cross-domain Europe sources (building energy, surfaces, permits, industrial sites, economy, infrastructure, heritage, materials, lights) useful for catastrophe-model exposure and vulnerability validation, never an approved modeling-input list.

**Entries:** 18

## JRC Digital Building Stock Model DBSM R2025

**Candidate ID:** `ec.jrc.dbsm.r2025`  
**Provider:** European Commission Joint Research Centre  
**Categories:** `buildings`, `energy`, `roof_pv_potential`, `europe`  
**Spatial scope:** EU27 including outermost island regions (not full EUBUCCO Europe scope)  
**Temporal scope:** R2025 data release catalogued in 2026, building data vintages differ by source  
**Resolution / granularity:** Individual building polygons and height, compactness, construction epoch, building use, rooftop solar-PV potential  
**Potential roles:** `eubucco_polygon_crosswalk`, `building_attribute_imputation`, `roof_solar_asset_potential`  
**Access hint:** `public_jrc_data_odbl_v1_exact_file_and_derivative_review`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/a601a4a8-9289-4fc4-983a-25d54f957f3a>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DBSM R2025 publisher states ODbL v1.0. Footprints/attributes may derive from OSM, Microsoft, European Settlement Map and other common inputs with EUBUCCO and Overture; not independent ground truth. Roof PV POTENTIAL is not installed panel ownership or insured value. Keep polygon relationship, source lineage, time and model confidence.

## Copernicus HRL Imperviousness Density 2024

**Candidate ID:** `copernicus.clms.imperviousness-density.2024`  
**Provider:** Copernicus Land Monitoring Service / EEA  
**Categories:** `land_surface`, `urbanisation`, `surface_runoff`, `europe`  
**Spatial scope:** Pan-Europe, with product-specific regional exceptions  
**Temporal scope:** Reference year 2024; three-yearly product family  
**Resolution / granularity:** Sentinel-2 derived 10 m and 100 m raster percent sealed-surface fraction, EPSG:3035; companion confidence product  
**Potential roles:** `pluvial_flood_runoff_prior`, `urban_development_consistency`, `building_coverage_audit`  
**Access hint:** `public_clms_geotiff_download_data_policy_review`  
**Authoritative source:** <https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness/imperviousness-density-2024>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is proportion of impervious surface, not a list of buildings, water depth or sewer/drainage capacity. Product page currently notes validation pending. The separate Impervious Built-Up 2024 binary layer is already catalogued, do not count it as independent external truth.

## Copernicus HRL Tree Cover Density 2018-present 10m yearly

**Candidate ID:** `copernicus.clms.tree-cover-density.2018-present`  
**Provider:** Copernicus Land Monitoring Service / EEA  
**Categories:** `vegetation`, `wildfire_fuel_context`, `wind_exposure`, `europe`  
**Spatial scope:** Pan-Europe  
**Temporal scope:** Annual imagery-based layers from 2018, actual regional acquisition vintages differ  
**Resolution / granularity:** Sentinel-1/2-derived continuous tree canopy density fraction at 10m with confidence-layer products  
**Potential roles:** `wildfire_wui_proximity_prior`, `local_wind_exposure_context`, `forest_debris_impact_prior`  
**Access hint:** `public_clms_cdse_raster_and_rights_review`  
**Authoritative source:** <https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover/tree-cover-density-2018-present-raster-10-m-europe-yearly>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Canopy density is a proxy for vegetation, not combustible biomass, exact tree height, fire intensity or tree fall probability. Raster time must align with building footprint and hazard event dates. Tree/forest type layers can share sensor/model inputs.

## Copernicus HRL Forest Type 2018-present 10m

**Candidate ID:** `copernicus.clms.forest-type.2018-present`  
**Provider:** Copernicus Land Monitoring Service / EEA  
**Categories:** `forest`, `vegetation_type`, `wildfire`, `europe`  
**Spatial scope:** Pan-Europe  
**Temporal scope:** 2018 onward three-yearly  
**Resolution / granularity:** 10m raster broadleaved/coniferous/non-forest classes derived from tree cover and leaf type data  
**Potential roles:** `wildfire_fuel_class_prior`, `windfall_tree_type_context`, `vegetation_vulnerability_sensitivity`  
**Access hint:** `public_clms_raster_original_asset_rights_review`  
**Authoritative source:** <https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover/forest-type-2018-present-raster-10-m-europe-3-yearly>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Tree species classification alone cannot determine fire susceptibility, vegetation loss or actual fuel load; correlate with climate/humidity and avoid independent-evidence claims against other CLMS tree products.

## France SDES Sitadel urbanism building, extension and demolition permits

**Candidate ID:** `fr.sdes.sitadel-building-permits.2026`  
**Provider:** Service des données et études statistiques / French Ministry of Ecological Transition  
**Categories:** `construction_permits`, `demolition`, `new_exposure`, `france`  
**Spatial scope:** France with coverage by published administrative areas and exact product  
**Temporal scope:** 2013-present permits, published monthly; Sitadel3 replaces Sitadel2 for new output from March 2026  
**Resolution / granularity:** Reported granted building permits, prior declarations, residential/nonresidential creation, extensions and demolition permissions  
**Potential roles:** `building_stock_temporal_change_prior`, `potential_new_exposure_screen`, `demolition_review`  
**Access hint:** `public_monthly_download_sitadel3_schema_versions_rights_review`  
**Authoritative source:** <https://www.statistiques.developpement-durable.gouv.fr/donnees-des-permis-de-construire-et-autres-autorisations-durbanisme>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Permitted works are not proof of completion, occupation, built geometry or demolition. Exact geolocation/address availability and privacy fields must be checked per product before RNB/BDNB linkage; at minimum use published commune aggregates. Sitadel2 to Sitadel3 methodology/revision creates time-series break.

## Destatis GENESIS building permits construction and material statistics 31111

**Candidate ID:** `de.destatis.genesis.building-permits.31111`  
**Provider:** Statistisches Bundesamt (Destatis)  
**Categories:** `building_permits`, `construction_cost`, `building_materials`, `germany`  
**Spatial scope:** Germany with table-specific Bundesland/region coverage  
**Temporal scope:** Historical years to present, periodically updated  
**Resolution / granularity:** Official construction permit and planned construction costs, floors, building use and predominant construction-material tables by administrative statistical scope  
**Potential roles:** `construction_age_growth_prior`, `new_building_material_class_prior`, `construction_cost_benchmark`  
**Access hint:** `public_genesis_table_api_licence_and_unit_review`  
**Authoritative source:** <https://genesis.destatis.de/datenbank/online/statistic/31111/details>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Aggregated permits, not verified building-level footprints or completed structures. Construction-cost table values are planned costs under survey definitions, not replacement values or insured sums. Preserve classification, administrative boundary and period.

## EEA Industrial Emissions Portal Europe industrial facilities

**Candidate ID:** `eea.industrial-emissions.facilities.2026`  
**Provider:** European Environment Agency / Member State facility reporting  
**Categories:** `industrial_exposure`, `facilities`, `economic_activity`, `europe`  
**Spatial scope:** EEA and EU industrial reporting countries  
**Temporal scope:** Regular country reports; E-PRTR / IED v16.0 Feb 2026 documented  
**Resolution / granularity:** Geocoded industrial complexes with activity type, plant identifiers, waste/emissions and energy context; more than 60k sites in public portal  
**Potential roles:** `industrial_property_location_prior`, `commercial_business_interruption_context`, `industrial_concentration_validation`  
**Access hint:** `public_eea_industrial_release_and_facility_terms_review`  
**Authoritative source:** <https://industry.eea.europa.eu/industrial-emissions/dataset>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Emissions registry is not complete insured industrial inventory. Only regulated/threshold-reporting sites appear; coordinate may represent site centroid not each building, no verified insured sums or own/legal entity crosswalk. Preserve plant status, facility IDs, country and original rights.

## NASA Black Marble VIIRS VNP46A2 Version 2 daily nighttime lights

**Candidate ID:** `nasa.black-marble.vnp46a2.v2`  
**Provider:** NASA Earthdata / LAADS DAAC  
**Categories:** `night_lights`, `economic_activity_proxy`, `satellite`, `global`  
**Spatial scope:** Global, including Europe  
**Temporal scope:** 2012-01-19 onward daily Version 2 collection  
**Resolution / granularity:** 15 arc-second roughly 500m daily corrected nocturnal radiance including quality, cloud, lunar and snow flags in HDF5  
**Potential roles:** `economic_activity_proxy`, `power_outage_change_validation`, `spatial_exposure_density_challenge`  
**Access hint:** `earthdata_registered_download_attribution_and_distribution_review`  
**Authoritative source:** <https://www.earthdata.nasa.gov/data/catalog/laads-vnp46a2-2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Nightlight radiance is NOT building value, insurer exposure, household wealth, exact workforce or outage ground truth. Respect QA clouds, snow, season, stray light, lunar correction, gap filling and baseline differences. Lights emitted beyond buildings and rural dark sites require careful modelling.

## Prebuilt European high-voltage electricity network for PyPSA-Eur Version 0.6

**Candidate ID:** `eu.pypsa-eur.grid-osm.v0.6`  
**Provider:** Xiong, Fioriti, Neumann, Riepin, Brown / TU Berlin collaborators  
**Categories:** `power_grid`, `infrastructure`, `graph`, `europe`  
**Spatial scope:** Multiple European countries according to v0.6 release  
**Temporal scope:** Open version 0.6 published November 2024, underlying OSM observation snapshot  
**Resolution / granularity:** Topologically connected 220–750 kV AC and DC power network, substations, buses and modeled lines with OSM identifiers  
**Potential roles:** `power_grid_cascading_failure_scenario`, `critical_infrastructure_network_prior`, `commercial_bi_dependency_research`  
**Access hint:** `public_zenodo_odbl_licence_and_file_schema_review`  
**Authoritative source:** <https://zenodo.org/records/14144752>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not an up-to-date verified operator topology or local low-voltage distribution grid; OSM edits and heuristic corrections mean missing/disconnected links. Buses may merge substations within 500m. Use synthetic outage simulations only after checking network rights, electrical parameters and uncertainty.

## European Landslide Susceptibility Map ELSUS v2

**Candidate ID:** `ec.jrc.esdac.elsus.v2`  
**Provider:** European Commission JRC / ESDAC and scientific collaborators  
**Categories:** `landslide`, `soil`, `terrain`, `europe`  
**Spatial scope:** EU except Malta plus several surrounding European countries  
**Temporal scope:** 2018 scientific version, calibration from heterogeneous historic landslide inventories  
**Resolution / granularity:** Continental-scale generic landslide susceptibility zonation derived from terrain, geology, land cover and past landslide locations  
**Potential roles:** `landslide_peril_screening`, `geotechnical_building_exposure_prior`, `cross_hazard_spatial_correlation_research`  
**Access hint:** `registration_required_esdac_dataset_rights_review`  
**Authoritative source:** <https://esdac.jrc.ec.europa.eu/content/european-landslide-susceptibility-map-elsus-v2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Susceptibility is neither annual event occurrence probability, hazard intensity or deterministic individual-building structural failure. Caution about spatial and temporal scale, database bias and model training overlap.

## National Heritage List for England listed buildings spatial data

**Candidate ID:** `uk.historicengland.nhle-listed.2026`  
**Provider:** Historic England  
**Categories:** `heritage`, `building_materials_proxy`, `special_values`, `uk`  
**Spatial scope:** England only  
**Temporal scope:** Maintained listings including October 30, 2026 GIS release  
**Resolution / granularity:** Listed building designations as points/polygons plus status and heritage context downloadable through official Open Data Hub  
**Potential roles:** `heritage_building_enrichment`, `nonstandard_replacement_cost_flag`, `historical_construction_context`  
**Access hint:** `public_open_government_licence_exact_file_and_attribution_review`  
**Authoritative source:** <https://historicengland.org.uk/listing/the-list/data-downloads/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Heritage designation polygon may enclose multiple structures or a site, and a point may not match EUBUCCO building centroid. Listing does not establish actual masonry structure, actual material or replacement price. Heritage-specific conservation rebuild costs require separate evidence.

## France Mérimée historic protected building registry

**Candidate ID:** `fr.culture.monuments-historiques`  
**Provider:** Ministère de la Culture / Monuments historiques  
**Categories:** `heritage`, `historic_buildings`, `roof_materials`, `france`  
**Spatial scope:** France national and overseas scope per source records  
**Temporal scope:** Historic listings from 1840 onward, official revision dates per record  
**Resolution / granularity:** Historic monument protection records with building descriptions, roof types, era, some wall materials, administrative locations and cadastre references  
**Potential roles:** `historic_building_age_enrichment`, `construction_material_evidence`, `high_value_exposure_flag`  
**Access hint:** `public_french_open_dataset_attribute_licence_review`  
**Authoritative source:** <https://www.data.gouv.fr/datasets/immeubles-proteges-au-titre-des-monuments-historiques-2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** For protected stock only, not complete structures. Records can represent sites not single buildings; not all fields reliable/complete. Join RNB/BDTOPO geometrically with human review where ID missing. Roof/material descriptions sometimes observed in documentation but cannot be generalized to neighbours.

## Eurostat residential house price and sales indices

**Candidate ID:** `eu.eurostat.house-price-index`  
**Provider:** Eurostat / European Commission  
**Categories:** `house_prices`, `economics`, `value_context`, `europe`  
**Spatial scope:** EU and reporting European statistical countries  
**Temporal scope:** Annual and quarterly national house transaction price series with revisions  
**Resolution / granularity:** HPI national transaction price indices (base 2015) and number/value of house sales indicator series  
**Potential roles:** `housing_market_inflation_context`, `regional_value_sanity_check`  
**Access hint:** `public_eurostat_sdmx_data_source_rights_review`  
**Authoritative source:** <https://ec.europa.eu/eurostat/web/housing-price-statistics/information-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Transaction market prices include land/location scarcity and are not replacement construction costs, sums insured or building value. No automatic allocation to a specific building. Distinguish from previously proposed Eurostat construction-cost indices.

## Eurostat regional structural business statistics (NUTS 2021)

**Candidate ID:** `eu.eurostat.sbs.nuts2021`  
**Provider:** Eurostat / European Commission  
**Categories:** `business_statistics`, `commercial_exposure`, `employment`, `europe`  
**Spatial scope:** EU regions NUTS2; table-specific country coverage  
**Temporal scope:** Multiannual regional NACE structural business tables; updates and NUTS classification changes  
**Resolution / granularity:** Enterprise numbers, turnover, personnel costs and industry breakdowns by NUTS2 and NACE Rev.2  
**Potential roles:** `commercial_portfolio_sector_prior`, `business_interruption_value_context`, `regional_industry_calibration`  
**Access hint:** `public_eurostat_sdmx_statistical_data_rights_review`  
**Authoritative source:** <https://ec.europa.eu/eurostat/databrowser/view/sbs_r_nuts2021/default/table>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Reported turnover/revenue does not imply insured BI sum, location of every establishment or physical property assets. Enterprise HQ, local units and branches differ. Honor missing/suppressed cells, NACE industry and NUTS vintage.

## Eurostat business demography by regional NUTS3 industry/size

**Candidate ID:** `eu.eurostat.business-demography.nuts3`  
**Provider:** Eurostat / European Commission  
**Categories:** `business_demography`, `company_counts`, `employment`, `europe`  
**Spatial scope:** EU and participating NUTS3 regions where released  
**Temporal scope:** Time series and NUTS versions vary; validate exact download code  
**Resolution / granularity:** Counts of enterprises with employees and age/size by NUTS3 and NACE industry (table-specific)  
**Potential roles:** `synthetic_commercial_policy_counts`, `industry_sector_validation`, `growth_turnover_context`  
**Access hint:** `public_eurostat_table_sdmx_with_suppression_check`  
**Authoritative source:** <https://ec.europa.eu/eurostat/databrowser/view/bd_size_r/default/table>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Business count is not directly a geolocated insured site. Cannot infer the location of a firm or asset from NUTS3 aggregate; avoid double counting with NUTS2 SBS and country company registries.

## EU27 harmonised building material and life-cycle inventory by archetype

**Candidate ID:** `eu.kuleuven.building-material-archetypes.2025`  
**Provider:** Ramon, Pristerà and collaborators / KU Leuven RDR  
**Categories:** `building_materials`, `archetypes`, `construction`, `europe`  
**Spatial scope:** EU27 country-level archetypes  
**Temporal scope:** 2025 research dataset, vintage by archetype and source  
**Resolution / granularity:** Life-cycle inventory of material/energy quantities by building archetype and element (wall, roof etc), annual flows and environmental impacts  
**Potential roles:** `material_composition_prior`, `roof_wall_component_value_model`, `embodied_asset_context`  
**Access hint:** `research_repository_file_licence_and_method_review`  
**Authoritative source:** <https://doi.org/10.48804/vxjuew>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Component-level archetype material volume may support vulnerability and repair-cost priors, not direct evidence of actual materials or values for any building. Do not confuse life-cycle environmental impact accounting with construction/replacement price. Check exact open file licence before reuse.

## JRC PVGIS 6 geospatial solar radiation and PV performance

**Candidate ID:** `ec.jrc.pvgis6.geospatial`  
**Provider:** European Commission Joint Research Centre / ECMWF  
**Categories:** `solar`, `roof`, `weather`, `europe`  
**Spatial scope:** Global land including Europe  
**Temporal scope:** PVGIS 6 product, 2026 update with periodic data revisions  
**Resolution / granularity:** Geospatial GeoTIFF radiation/PV output datasets and API for location-specific solar resource and theoretical PV performance  
**Potential roles:** `rooftop_pv_hazard_sensitivity`, `solar_equipment_potential_context`  
**Access hint:** `public_pvgis6_licence_requires_attribution_api_limits_review`  
**Authoritative source:** <https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/general-information/geospatial-data-download_en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Potential generation/radiation does not show installed rooftop arrays or their replacement value. Validate actual PV presence elsewhere; hazard vulnerability differs by installed panel design and mounting. Avoid reusing DBSM PV potential as independent evidence if based on PVGIS.

## ECB Household Finance and Consumption Survey HFCS public aggregate tables 2021 wave

**Candidate ID:** `ecb.hfcs.household-wealth.2021`  
**Provider:** European Central Bank / Household Finance and Consumption Network  
**Categories:** `household_wealth`, `housing_values`, `contents`, `europe`  
**Spatial scope:** Euro area and participating European countries  
**Temporal scope:** 2021 survey wave; public statistical tables revised June 2026  
**Resolution / granularity:** Aggregate sample-distribution tables on housing wealth, financial and tangible assets and household structure  
**Potential roles:** `household_asset_value_distribution_prior`, `contents_value_sensitivity`, `synthetic_portfolio_disparity_check`  
**Access hint:** `public_aggregate_tables_only_no_microdata_licence_review`  
**Authoritative source:** <https://www.ecb.europa.eu/stats/ecb_surveys/hfcs/html/index.en.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Survey-reported home values include location/land, often self-assessed. Aggregate wealth is not insured home/contents sum insured. Microdata access/privacy restrictions apply; build only anonymised aggregate priors, never individual address/property or identifiable household links.
