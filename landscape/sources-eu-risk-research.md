<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-eu-risk-research.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-eu-risk-research.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-12`  
**Purpose:** Non-admission discovery registry of EU, Copernicus and EU-funded catastrophe-risk datasets, research infrastructures and machine-readable services with explicit OpenCatastrophe integration value.

**Entries:** 13

## JRC Risk Data Hub Disaster Losses collection

**Candidate ID:** `ec-jrc.rdh.disaster-losses`  
**Provider:** European Commission Joint Research Centre / Disaster Risk Management Knowledge Centre  
**Categories:** `disaster_loss`, `historical_impacts`, `multi_hazard`, `europe`, `api`, `validation`  
**Spatial scope:** Pan-European loss and damage records with event and administrative-unit fields, including NUTS-linked geography where available  
**Temporal scope:** Historical disaster events assembled from incorporated open sources; the live API collection is mutable and source coverage is dataset-dependent  
**Resolution / granularity:** Event × hazard × asset × metric × administrative-division records exposed through Risk Data Hub API 3.1.0; GeoJSON is default and CSV/JSON/JSON-LD are documented formats  
**Potential roles:** `historical_loss_benchmark`, `event_loss_crosswalk`, `loss_damage_validation`, `vulnerability_model_challenge`, `rdls_interoperability_research`  
**Access hint:** `eu_login_short_lived_token_ogc_api_geojson_csv_and_geospatial_services`  
**Authoritative source:** <https://drmkc.jrc.ec.europa.eu/risk-data-hub-api/docs/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Highest-value concrete lane inside the already-registered generic Risk Data Hub family. The documented `losses/losses/items` route supports bounded filtering, paging and machine formats after EU Login plus a short-lived token. Preserve event codes, hazard taxonomy, administrative version, asset/metric/unit, source list and both nominal/adjusted value semantics. RDH describes these as harmonised/derived loss records rather than raw insurance claims; source-specific lineage and third-party rights must be frozen before any model input or publication. For OpenCatastrophe this can provide a European empirical loss benchmark and event-to-loss crosswalk.

## JRC AI-Enhanced Disaster and Health Threats Storylines

**Candidate ID:** `ec-jrc.ai-disaster-health-storylines`  
**Provider:** European Commission Joint Research Centre  
**Categories:** `disaster_events`, `health_threats`, `storylines`, `knowledge_graph`, `generative_ai`, `impact_context`  
**Spatial scope:** Multi-country event corpus linked to disaster and health-threat records; exact geographic coverage changes with the maintained corpus  
**Temporal scope:** Continuously maintained event/storyline corpus; JRC catalogue declares daily update frequency  
**Resolution / granularity:** CSV event records augmented with news-derived narratives and causal knowledge-graph information created with EMM retrieval, RAG and JRC language-model tooling  
**Potential roles:** `event_context_enrichment`, `impact_chain_extraction_benchmark`, `knowledge_graph_research`, `causal_storyline_challenge`, `event_entity_resolution`  
**Access hint:** `public_jrc_catalog_csv_download_daily_mutable_dataset`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/747cf15b-87b4-4b92-a1be-10465c972929>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Machine use can start from the JRC catalogue CSV resource and should pin retrieval time, resource identity and content hash because the dataset is updated daily. The product is AI-generated enrichment built from event records plus retrieved news, not independent ground truth; hallucination, source-selection, temporal leakage and knowledge-graph extraction error must be evaluated. Upstream EM-DAT/news and generated-output rights need their own review. For OpenCatastrophe it is especially useful for testing event storylines, impact-chain extraction, entity linking and AI-agent retrieval without making the generated narrative authoritative.

## CEMS Global River Flood Hazard Maps

**Candidate ID:** `ec-jrc.cems.global-river-flood-hazard-maps.2026`  
**Provider:** European Commission Joint Research Centre / Copernicus Emergency Management Service  
**Categories:** `flood`, `riverine_flood`, `hazard`, `inundation_depth`, `return_period`, `global`  
**Spatial scope:** Global river network excluding Greenland, Antarctica and small islands with river basins below 500 km2  
**Temporal scope:** Probabilistic return-period hazard surfaces rather than an event time series; current JRC catalogue citation is the 2026 dataset identity  
**Resolution / granularity:** Downloadable TIFF water-depth grids in metres for seven return periods from 1-in-10 to 1-in-500 years, generated with LISFLOOD flows and LISFLOOD-FP inundation modelling  
**Potential roles:** `river_flood_hazard_baseline`, `exposure_overlay`, `return_period_benchmark`, `flood_model_challenge`, `global_risk_screening`  
**Access hint:** `public_jrc_downloadable_tiff_release`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/jrc-floods-floodmapgl_rp50y-tif>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is a static modelled hazard layer, distinct from GloFAS discharge histories and GFM observed flood extent. Machine integration can use exact TIFF assets after pinning the DOI/release, return period, CRS, grid and byte hashes. JRC explicitly states that the product is not an official flood hazard map. For OpenCatastrophe it can provide globally consistent flood-depth/return-period hazard surfaces for exposure overlays and independent comparison against event observations, while national maps should remain preferred where authoritative local detail is required.

## CEMS River Flood Hazard Maps for Europe and the Mediterranean

**Candidate ID:** `ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026`  
**Provider:** European Commission Joint Research Centre / Copernicus Emergency Management Service  
**Categories:** `flood`, `riverine_flood`, `hazard`, `inundation_depth`, `return_period`, `europe`  
**Spatial scope:** Most geographical Europe plus river basins entering the Mediterranean and Black Seas across the Caucasus, Middle East and North Africa  
**Temporal scope:** Probabilistic return-period hazard surfaces rather than an event time series; current JRC catalogue citation is the 2026 dataset identity  
**Resolution / granularity:** High-resolution gridded water-depth product for nine return periods from 1-in-10 to 1-in-500 years; river basins above 150 km2; LISFLOOD and LISFLOOD-FP model chain  
**Potential roles:** `european_flood_hazard_baseline`, `regional_exposure_overlay`, `return_period_benchmark`, `flood_damage_workflow_input_candidate`, `national_map_comparison`  
**Access hint:** `public_jrc_downloadable_gridded_release`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/1d128b6c-a4ee-4858-9e34-6210707f3c81>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This Europe/Mediterranean sibling is materially different from the global product: it covers smaller basins and offers nine return periods, making it the better first candidate for a European flood-risk lane. Machine use should freeze exact assets, return period, grid/CRS, depth units and release identity before any damage calculation. It remains a modelled trans-national hazard product and JRC warns it is not an official national flood map. OpenCatastrophe can use it for consistent cross-border benchmarking and regional exposure overlays, then challenge it against national hazard maps, GFM event footprints and gauge/discharge observations.

## GHSL GHS-AGE R2025A

**Candidate ID:** `ec-jrc.ghsl.ghs-age.r2025a`  
**Provider:** European Commission Joint Research Centre / Global Human Settlement Layer  
**Categories:** `exposure`, `built_environment`, `building_age`, `vulnerability_covariate`, `global`, `raster`  
**Spatial scope:** Global built-up areas  
**Temporal scope:** Dominant built-stock age derived from 1975-2020 built-up history  
**Resolution / granularity:** World Mollweide raster at 100 m and 1 km; each cell represents the epoch when 50% of its 2020 built-up surface was first reached, with 5-year and 10-year interval products  
**Potential roles:** `building_age_vulnerability_proxy`, `historical_exposure_context`, `fragility_segmentation_covariate`, `exposure_validation`, `resilience_research`  
**Access hint:** `public_ghsl_download_wizard_and_direct_raster_downloads`  
**Authoritative source:** <https://human-settlement.emergency.copernicus.eu/datasets.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GHS-AGE R2025A adds a vulnerability-relevant dimension not present in the repository's generic GHSL R2023A entry. Machine processing is straightforward raster ingestion after pinning release, resolution, interval, CRS and tile/global-file identity. The value is a derived dominant-age proxy, not a cadastral construction year for individual buildings. For OpenCatastrophe it can support age-stratified vulnerability research, historical exposure reconstruction and cross-checks against building-level sources without pretending to provide insured values or structure-level truth.

## GHSL GHS-OBAT R2024A

**Candidate ID:** `ec-jrc.ghsl.ghs-obat.r2024a`  
**Provider:** European Commission Joint Research Centre / Global Human Settlement Layer  
**Categories:** `exposure`, `buildings`, `building_attributes`, `building_age`, `building_height`, `building_function`, `global`  
**Spatial scope:** Global building-footprint attribute tables split by country and GADM 4.1 administrative areas  
**Temporal scope:** Reference epoch 2020, linked to Overture Buildings release 2024-07-22.0 and GHSL R2023/R2024 derived attributes  
**Resolution / granularity:** Footprint-level rows with identifiers, centroid/location, height, compactness, function, construction-year class, area and perimeter in CSV and GeoPackage; supplementary grid aggregates are also published  
**Potential roles:** `building_attribute_enrichment`, `exposure_taxonomy_mapping`, `vulnerability_covariates`, `overture_entity_linkage`, `building_stock_validation`  
**Access hint:** `public_jrc_csv_geopackage_and_aggregate_downloads_with_representation_specific_rights`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/f41a22f1-5741-4c41-86eb-6384654f6927>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Potentially one of the strongest open exposure-enrichment candidates because it links building-level attributes to a named Overture release. Machine use can ingest country/admin CSV or GeoPackage partitions and join by published identifiers. Rights are representation-sensitive: the catalogue exposes different use conditions for some downloadable resources, including ODbL-labelled database assets, so no provider-wide licence shortcut is valid. Attributes are model-derived and inherit completeness/quality limits from footprints and GHSL inputs. OpenCatastrophe can use this for reproducible building taxonomy and vulnerability covariates if exact partitions, upstream release lineage and downstream database-right obligations are reviewed.

## CLIMAAX Climate Risk Assessment Toolbox and risk workflows

**Candidate ID:** `eu.climaax.cra-toolbox`  
**Provider:** CLIMAAX consortium / Horizon Europe grant 101093864  
**Categories:** `climate_risk`, `multi_hazard`, `risk_workflows`, `python`, `jupyter`, `methodology`, `europe`  
**Spatial scope:** European regional climate-risk assessments with workflows designed to combine pan-European/global reference data and local inputs  
**Temporal scope:** Active Horizon Europe project 2023-2027; workflow and handbook releases are versioned independently  
**Resolution / granularity:** Hazard-organised GitHub repositories containing workflow descriptions plus hazard- and risk-assessment Jupyter notebooks, Python environments and optional containerised execution  
**Potential roles:** `risk_workflow_reference`, `reproducible_method_benchmark`, `adapter_design_reference`, `climate_hazard_pipeline_prototype`, `regional_cra_interoperability`  
**Access hint:** `public_github_jupyter_workflows_with_conda_docker_and_upstream_source_specific_data_access`  
**Authoritative source:** <https://www.climaax.eu/handbook/toolbox/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CLIMAAX is primarily a reusable modelling/workflow source rather than one homogeneous dataset. Hazard repositories can be cloned, their conda environments executed, and the notebooks run locally; CLIMAAX also documents a maintained Docker environment and restricted project JupyterHub. Individual workflows may fetch Copernicus/ECMWF or other upstream data and therefore inherit source-specific credentials and data rights even when workflow code/documentation is open. For OpenCatastrophe the main value is as an independent reference implementation for hazard→exposure→vulnerability pipelines, reproducibility patterns and region-specific CRA adapters.

## MYRIAD-EU Hazard Event Sets and MYRIAD-HESA

**Candidate ID:** `myriad-eu.hazard-event-sets`  
**Provider:** MYRIAD-EU consortium / Horizon 2020 grant 101003276  
**Categories:** `multi_hazard`, `compound_events`, `event_sets`, `historical_events`, `python`, `methodology`  
**Spatial scope:** Global multi-hazard event-set compilation  
**Temporal scope:** Historical event sets spanning 2004-2017  
**Resolution / granularity:** MYRIAD-HES CSV archive with one hazard per row, event IDs, start/end times, intensity/unit and WKT geometry across eleven hazards; companion MYRIAD-HESA v1 Python algorithm compiles event sets from single-hazard inputs  
**Potential roles:** `multi_hazard_event_benchmark`, `compound_event_linkage_reference`, `cross_peril_event_clustering`, `temporal_spatial_association_validation`, `systemic_risk_research`  
**Access hint:** `public_zenodo_bulk_archive_and_versioned_python_algorithm`  
**Authoritative source:** <https://zenodo.org/records/8269680>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The published HES archive is about 6.4 GB and the companion HESA v1 software is separately archived and linked to GitHub. Rather than committing the corpus, OpenCatastrophe should first reproduce the event-linking algorithm on tiny synthetic fixtures, then review the exact HES archive and all material upstream source licences before any sample or model use. Event-set membership is algorithmic association, not proof of causal interaction. The source is valuable for benchmarking our own multi-hazard clustering, time-lag semantics and compound-event identity model.

## EFEHR European Databases of Seismogenic Faults

**Candidate ID:** `epos.efehr.edsf`  
**Provider:** EFEHR / EPOS ERIC  
**Categories:** `earthquake`, `seismogenic_faults`, `tectonics`, `hazard_input`, `europe`, `gis`  
**Spatial scope:** European crustal faults and subduction systems compiled from regional and national published sources  
**Temporal scope:** Current harmonised fault compilation; source vintages vary by contributing regional or national dataset  
**Resolution / granularity:** Geologic fault objects harmonised across borders and exposed through Seismofaults.EU interactive interfaces, webservices and direct GIS downloads  
**Potential roles:** `seismic_source_geometry_reference`, `fault_hazard_input_candidate`, `cross_border_fault_harmonisation`, `eshm_source_model_challenge`, `tectonic_context`  
**Access hint:** `public_efehr_webservices_and_direct_gis_download`  
**Authoritative source:** <https://www.epos-eu.org/tcs/seismology/services/edsf-european-databases-seismogenic-faults-efehr>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EDSF complements the repository's existing ESHM20/ESRM20 work by exposing source-fault information rather than hazard/risk output maps. A future machine contract should pin the specific Seismofaults service or GIS release, feature schema, fault category, geometry/CRS and contributing-source lineage. Harmonisation does not make completeness spatially uniform, and an absent fault is not evidence of zero seismic hazard. OpenCatastrophe can use EDSF to test source-model geometry, regional fault crosswalks and explainability of European seismic hazard models.

## EMODnet Geology Geological Events and Probabilities

**Candidate ID:** `emodnet.geology.geological-events`  
**Provider:** European Marine Observation and Data Network / EMODnet Geology  
**Categories:** `marine_hazards`, `earthquake`, `submarine_landslide`, `volcano`, `tsunami`, `tectonics`, `europe`, `ogc`  
**Spatial scope:** European seas and adjoining geological domains represented by EMODnet Geology partners  
**Temporal scope:** Heterogeneous event and geological-feature vintages by source layer; current service is maintained operationally  
**Resolution / granularity:** Harmonised GIS layers for geological events and probabilities, including earthquakes, submarine landslides, volcanoes, tsunamis, Quaternary tectonics and fluid emissions; documented OGC WMS and WFS services plus downloads  
**Potential roles:** `marine_geohazard_context`, `tsunami_source_context`, `submarine_landslide_reference`, `cross_hazard_event_discovery`, `coastal_risk_input_discovery`  
**Access hint:** `public_ogc_wms_wfs_and_emodnet_downloads`  
**Authoritative source:** <https://emodnet.ec.europa.eu/en/emodnet-web-service-documentation>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EMODnet documents dedicated Geology Events and Probabilities WMS and WFS capability endpoints, giving us a genuine machine route rather than a map-only portal. This entry is distinct from the existing EMODnet Bathymetry DTM 2024 source. Before use, pin exact feature layers, service version, geometry scale, source partner, event/feature semantics and licence per layer. For OpenCatastrophe this can connect bathymetry with European marine earthquakes, submarine landslides, volcanoes and tsunami-related source context for coastal and cascading-hazard studies.

## Destination Earth Data Lake Harmonised Data Access

**Candidate ID:** `destination-earth.data-lake`  
**Provider:** European Commission Destination Earth / DestinE Data Lake  
**Categories:** `digital_twin`, `climate`, `weather_extremes`, `earth_observation`, `data_platform`, `stac`, `api`  
**Spatial scope:** Collection-dependent European and global Earth-system coverage across Destination Earth Digital Twins and federated providers  
**Temporal scope:** Operational and scenario/simulation data with collection-specific time ranges; some Digital Twin Extremes collections use rolling availability windows  
**Resolution / granularity:** Harmonised Data Access REST API with service discovery and STAC v2 collection metadata, item search and retrieval across multi-petabyte EO, in-situ, statistical and Digital Twin holdings  
**Potential roles:** `digital_twin_scenario_forcing`, `extreme_event_simulation_benchmark`, `climate_adaptation_scenarios`, `stac_interoperability`, `high_resolution_model_challenge`  
**Access hint:** `public_metadata_then_destine_account_for_items_downloads_with_additional_digital_twin_permissions`  
**Authoritative source:** <https://hda.data.destination-earth.eu/docs>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The HDA API is infrastructure, not one stable dataset. `/services` and collection metadata can be explored anonymously; item search/download requires a DestinE account and some Digital Twin outputs require additional permission. Machine integration should first discover and pin a concrete collection ID, queryables, model/experiment/version, initialization or scenario time, variable, spatial subset and retrieval receipt. Rolling collections must never be treated as immutable. For OpenCatastrophe the value is access to high-resolution Digital Twin extremes and climate-adaptation simulations plus a strong STAC/API interoperability target.

## Eurostat GISCO Census Population Grid 2021

**Candidate ID:** `eurostat.gisco.census-population-grid.2021`  
**Provider:** European Commission Eurostat / GISCO  
**Categories:** `population`, `exposure`, `demographics`, `census`, `europe`, `grid`  
**Spatial scope:** EU-wide harmonised 1 km2 census grid with cross-border comparable population attributes  
**Temporal scope:** 2021 census reference; current download version on the GISCO page dated 2026-05-30  
**Resolution / granularity:** 1 km2 ETRS89-LAEA EPSG:3035 polygon/raster products in CSV, GeoPackage and raster formats, covering 13 census variables including total population, age, sex, employment and migration/place-of-birth dimensions  
**Potential roles:** `population_exposure_baseline`, `demographic_vulnerability_covariates`, `cross_border_exposure_validation`, `event_population_overlay`, `regional_aggregation_reference`  
**Access hint:** `public_versioned_zip_csv_geopackage_raster_download_with_product_specific_rules`  
**Authoritative source:** <https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is more suitable than treating 'GISCO' as one generic source. The current page exposes dated 2021-census download versions and harmonised 1 km2 files, so a machine workflow can pin the 2026-05-30 ZIP and exact representation. Eurostat states EU copyright/CC BY 4.0 for the Census Grid 2021, while older GEOSTAT products have materially different restrictions; rights therefore must remain product- and version-specific. For OpenCatastrophe this is a strong European population denominator and demographic-vulnerability layer for hazard overlays and validation.

## PARATUS Dynamic Systemic Multi-Hazard Risk Platform

**Candidate ID:** `eu.paratus.dynamic-systemic-risk`  
**Provider:** PARATUS consortium / Horizon Europe grant 101073954  
**Categories:** `multi_hazard`, `systemic_risk`, `impact_chains`, `dynamic_risk`, `decision_support`, `europe`  
**Spatial scope:** Methodology and platform developed through European and international case studies including Istanbul, Romania/Bucharest, Alpine/Brenner and Caribbean settings  
**Temporal scope:** Horizon Europe project 2022-2026 with evolving platform, deliverables and scenario tools  
**Resolution / granularity:** Cloud/web-based modelling and information service for multi-hazard impact chains, systemic vulnerability, risk-reduction and response scenarios; component datasets and model resolutions vary by case study  
**Potential roles:** `systemic_risk_method_reference`, `impact_chain_ontology_research`, `cascading_hazard_scenario_design`, `decision_support_interoperability`, `multi_sector_vulnerability_research`  
**Access hint:** `public_project_outputs_and_web_platform_machine_api_not_yet_verified`  
**Authoritative source:** <https://cordis.europa.eu/project/id/101073954>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** PARATUS is presently most valuable as a methodology/toolchain reference rather than a frozen source dataset. CORDIS describes an open-source dynamic-risk platform, while project deliverables document a web-based multi-hazard impact-chain service and tools such as FastFlood; a stable public machine API for the integrated platform was not established in this review, so automation must not be invented. OpenCatastrophe should mine its impact-chain/systemic-vulnerability concepts and compare scenario semantics, then separately review any concrete code, API or dataset release before integration.
