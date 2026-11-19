<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-peer-project-upstream-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-peer-project-upstream-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission peer-project upstream source discovery from original GitHub README/config files and publisher pages. These candidate sources do not confer asset rights, insurance input approval, scientific validity, or permission to redistribute bytes.

**Entries:** 8

## Natural Resources Canada National Human Settlement Layers Physical Exposure

**Candidate ID:** `can.nrcan.nhsl.physical-exposure.2016-2020`  
**Provider:** Natural Resources Canada Geological Survey of Canada  
**Categories:** `exposure`, `buildings`, `replacement_value`, `census`  
**Spatial scope:** Canada national and provincial releases  
**Temporal scope:** Inputs predominantly 2016 to 2020; monetary baseline 2019 CAD  
**Resolution / granularity:** Aggregated building and population exposure, occupancy and construction typology, structure/nonstructure/contents replacement values; downloadable GeoPackage and web map layers  
**Potential roles:** `building_stock_calibration`, `replacement_cost_prior`, `occupancy_and_construction_taxonomy`  
**Access hint:** `public_dataset_download_government_licence_canada_product_revision_check`  
**Authoritative source:** <https://opendrr.github.io/national-human-settlement/en/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** OpenDRR/national-human-settlement physical-exposure README attributes inventory to Statistics Canada 2016 dissemination-block housing census, georeferenced business listings and regional industry replacement-cost estimates. The official NRCan portal identifies Open Government Licence - Canada. Model approximates 9.7 million buildings over 390000 grouped locations, not per-building survey records or insured TIV. Freeze dataset vintage, data dictionary, region, cost year, occupancy rules and original terms before use. Primary technical method DOI 10.4095/330012.

## Natural Resources Canada National Human Settlement Layers Social Fabric

**Candidate ID:** `can.nrcan.nhsl.social-fabric`  
**Provider:** Natural Resources Canada Geological Survey of Canada  
**Categories:** `social_vulnerability`, `demography`, `resilience`, `exposure`  
**Spatial scope:** Canada national and provincial layers  
**Temporal scope:** Published NHSL product; original census and survey vintages differ by indicator  
**Resolution / granularity:** Social vulnerability indices and community capacity thresholds; GeoPackage, ArcGIS REST and published dictionaries  
**Potential roles:** `community_vulnerability_context`, `resilience_scenario_prior`, `geographic_aggregation_validation`  
**Access hint:** `public_dataset_download_government_licence_canada_indicator_method_review`  
**Authoritative source:** <https://opendrr.github.io/national-human-settlement/en/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from NHSL physical building values, and NOT a physical vulnerability/damage curve. Official portal describes Social Fabric and Capacity Threshold layers and Open Government Licence - Canada. Verify indicator weights, underlying census denominators, publication date, area geometry, demographic privacy and allowable use before scientific calibration.

## World Input-Output Database 2016 Release WIOT and socioeconomic accounts

**Candidate ID:** `rug.wiod2016.world-input-output-tables`  
**Provider:** University of Groningen Groningen Growth and Development Centre  
**Categories:** `economy`, `supply_chain`, `business_interruption`, `input_output`  
**Spatial scope:** 43 economies plus a modeled rest-of-world sector; not global granular firms  
**Temporal scope:** Historical annual tables 2000-2014; 2016 release  
**Resolution / granularity:** World Input-Output Tables 56 sectors, international trade flows, socio-economic accounts and satellite tables; millions of USD for current-price WIOTs  
**Potential roles:** `sector_network_prior`, `indirect_business_interruption`, `economic_exposure_consistency`  
**Access hint:** `public_download_cc_by_4_publisher_statement_exact_asset_check`  
**Authoritative source:** <https://www.rug.nl/ggdc/valuechain/wiod/wiod-2016-release>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NCCS global-impacts-modelling README explicitly fixes WIOD16 MRIOT year 2011 and indirect Leontief/Ghosh pathways. Groningen publisher describes 43 economies, 56 ISIC rev 4 sectors, 2000-2014, rest-of-world approximation and CC BY 4.0. Table-year, prices, sectors, exchange rates, national-versus-global denominators and licensing of selected archive require reproducible preflight. Not insurer-specific supply chains.

## COMPASS Paprotny global gridded population GDP and net fixed assets 1850-2100

**Candidate ID:** `compass.paprotny.global-exposure.2025.17572467`  
**Provider:** HORIZON COMPASS / Potsdam Institute for Climate Impact Research  
**Categories:** `exposure`, `economic_assets`, `population`, `scenario`  
**Spatial scope:** Global gridded country/scenario products  
**Temporal scope:** Annual historical 1850-2020 and projections through 2100 under five SSP trajectories; precise intervals differ by released files  
**Resolution / granularity:** 30 arc-second and 30 arc-minute global exposure products, with Python reconstruction code and source inputs; 2025 Zenodo record 17572467  
**Potential roles:** `economic_value_surface`, `future_synthetic_exposure`, `historical_exposure_benchmark`  
**Access hint:** `public_zenodo_metadata_and_selected_archives_15gb_rights_unreviewed`  
**Authoritative source:** <https://zenodo.org/records/17572467>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original Zenodo release explicitly lists dependency on JRC GHSL 1975-2030, Utrecht HYDE 3.2 population 1850-1980, WorldPop and FuturePop projections; individual sources are NOT independent empirical validation of this derivative. Dataset page does not establish a usable rights decision for all external inputs here. The project GitHub README inconsistently equates 30 arc-sec to 1.85 km; use Zenodo stated approx 0.93 km at equator and verify geospatial metadata. Never infer insured value from net fixed assets.

## WorldPop FuturePop SSP population projections v0.2

**Candidate ID:** `worldpop.futurepop.ssp.1km.v0.2`  
**Provider:** WorldPop University of Southampton  
**Categories:** `population`, `scenario`, `demography`, `exposure`  
**Spatial scope:** Global land grid with country-specific masks  
**Temporal scope:** 2025 to 2100, five SSP pathways, five-year intervals  
**Resolution / granularity:** Global 30 arc-second approximately 1 km gridded projected population rasters; exact product DOI 10.5258/SOTON/WP00849  
**Potential roles:** `future_population_prior`, `scenario_exposure_allocation`, `demographic_denominator`  
**Access hint:** `public_download_cc_by_4_per_original_product_check_lineage`  
**Authoritative source:** <https://hub.worldpop.org/geodata/summary?id=110984>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Listed by COMPASS global exposure model as original dependency. Original WorldPop publisher labels v0.2 release and CC BY 4.0; provider warns some other WorldPop products derived from OSM or Microsoft may be ODbL, so do not generalise licences across families. Country and scenario totals are not independent building or insurance observations.

## HYDE 3.2 historical gridded population baseline

**Candidate ID:** `uu.hyde3.2.historical-population`  
**Provider:** Utrecht University HYDE research dataset  
**Categories:** `population`, `historical_exposure`, `land_use`  
**Spatial scope:** Global historical gridded product  
**Temporal scope:** Historical model with a specific subset 1850-1980 used by COMPASS; full publisher coverage differs  
**Resolution / granularity:** Gridded historical population count popc baseline decennial subset, not observed asset valuation  
**Potential roles:** `historical_population_prior`, `historical_exposure_reconstruction`  
**Access hint:** `public_historical_archive_exact_revision_and_rights_unverified`  
**Authoritative source:** <https://geo.public.data.uu.nl/vault-hyde/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** COMPASS Zenodo 17572467 cites the original Utrecht HYDE 3.2 archive, baseline popc selected decennial timesteps from 1850 to 1980. Must fix exact archive snapshot, layer version, units, masks, and reuse terms; derivative uncertainty and interpolation mean these are modeled population grids, not contemporaneous census observations at each grid cell.

## SpaceNet 7 Multi-Temporal Urban Development satellite building labels

**Candidate ID:** `spacenet.spacenet7.multitemporal-urban-development`  
**Provider:** SpaceNet / SpaceNet Challenge  
**Categories:** `buildings`, `remote_sensing`, `validation`, `change_detection`  
**Spatial scope:** Selected global urban areas, not representative worldwide  
**Temporal scope:** Multi-date optical observations; dataset and train/test scene vintages differ  
**Resolution / granularity:** High-resolution multispectral imagery and building footprint tracking labels for benchmark AOIs  
**Potential roles:** `building_extraction_holdout`, `building_vintage_validation`, `segmentation_quality_assessment`  
**Access hint:** `public_challenge_dataset_individual_asset_licences_and_ground_truth_rights_review`  
**Authoritative source:** <https://spacenet.ai/sn7-challenge/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GFDRR urban_validation original README names SpaceNet 7 as AOI-specific reference footprints. License, image source restrictions, training/test independence, annotation quality, scene acquisition times and spatial sampling bias must be checked at the exact release. Do not use benchmark labels as countrywide building stock or insured loss.

## ETH NCCS Global Impacts climate and economic sector input collection

**Candidate ID:** `eth.nccs.global-impacts-data-collection.2025`  
**Provider:** ETH Zurich / Swiss National Centre for Climate Services  
**Categories:** `exposure`, `multi_hazard`, `economy`, `impact_model`  
**Spatial scope:** Multiple countries and economic sectors; product- and scenario-dependent  
**Temporal scope:** Historical and climate scenarios, as distributed in the project collection  
**Resolution / granularity:** Project-associated archive for direct hazards/exposure inputs and impact outputs, linked to CLIMADA v6.1 and WIOD 2016 2011 MRIOT  
**Potential roles:** `sector_exposure_methods`, `indirect_business_interruption_benchmark`, `model_input_lineage`  
**Access hint:** `research_collection_public_metadata_asset_level_licence_and_version_review`  
**Authoritative source:** <https://hdl.handle.net/20.500.11850/785985>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NCCS GitHub README identifies ETH research collection as required pipeline data input. Code sectors include forestry, manufacturing, mining, utilities; hazards tropical cyclone, river flood, Europe windstorm, relative crop yield. Its WIOD16/2011 matrices, World Bank GDP and mineral rents, and CLIMADA hazards/impact functions require distinct original-provider lineage; the bundled outputs are not independent loss truth. Archive contents and per-file rights not downloaded or audited.
