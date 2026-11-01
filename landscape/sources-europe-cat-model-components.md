<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-europe-cat-model-components.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-europe-cat-model-components.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission public source discovery of missing European catastrophe model hazard, hydrology, protection standards, vulnerability, historic economic and insurance-loss components; not a data input allow-list.

**Entries:** 14

## Copernicus Enhanced European Windstorm tracks and footprints

**Candidate ID:** `copernicus.c3s.european-windstorm-reanalysis`  
**Provider:** ECMWF / C3S  
**Categories:** `windstorm`, `hazard`, `tracks`, `europe`  
**Spatial scope:** Europe  
**Temporal scope:** 1940-present; monthly additions  
**Resolution / granularity:** Event tracks and 72h peak 10-m gust footprints at ERA5 resolution and downscaled products  
**Potential roles:** `historical_storm_event_catalogue`, `multi_country_correlation`  
**Access hint:** `cds_registered_download_and_exact_product_terms_review`  
**Authoritative source:** <https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis?tab=overview>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Unlike existing CLIMK-WINDS, EWS is an all-season updated reanalysis family. Pin event ID, algorithm (TRACK/TempestExtremes), gust temporal statistic, resolution and release. Reanalysis-derived tracks must not be mistaken for independent measured winds or full annual stochastic catalogs.

## Copernicus EU-Hydro River Network Database

**Candidate ID:** `eu.copernicus.eu-hydro-river.v1.3`  
**Provider:** Copernicus Land Monitoring Service  
**Categories:** `flood`, `hydrology`, `rivers`, `europe`  
**Spatial scope:** European catchments  
**Temporal scope:** Reference imagery 2006-2012; V1.3 Nov 2020  
**Resolution / granularity:** Drainage lines, lakes, river networks and catchment topology, vector EPSG:3035  
**Potential roles:** `hydrologic_network_reference`, `flood_geometry_validation`  
**Access hint:** `public_download_by_basin_and_original_rights_review`  
**Authoritative source:** <https://land.copernicus.eu/en/products/eu-hydro/eu-hydro-river-network-database>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Do not confuse river lines with water depth, levee positions or live discharge; reconcile geometry age and projection against existing JRC river flood maps.

## COASTPROS-EU coastal flood protection standards

**Candidate ID:** `eu.coastpros-eu.v2`  
**Provider:** De Plaen and collaborators / Zenodo  
**Categories:** `coastal_flood`, `flood_defence`, `europe`  
**Spatial scope:** European coasts  
**Temporal scope:** Version 2 published March 2025  
**Resolution / granularity:** European coastal-defence information and region-linked design/policy protection standards  
**Potential roles:** `coastal_protection_prior`, `coastal_defence_uncertainty`  
**Access hint:** `public_research_files_rights_and_fields_review`  
**Authoritative source:** <https://zenodo.org/records/15024139>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Observed defence structure, policy standard and modeled proxy must be separately labelled. No blanket claim of exact levee geometries or zero flooding below design return period; model overtopping and failure uncertainties.

## FLOPROS flood protection standards

**Candidate ID:** `global.flopros.protection-standards.2016`  
**Provider:** Scussolini et al.  
**Categories:** `river_flood`, `protection`, `vulnerability`  
**Spatial scope:** Global, Europe included  
**Temporal scope:** 2016 reference; protection levels evolve  
**Resolution / granularity:** Three design, policy and modeled flood standard layers expressed as return periods  
**Potential roles:** `river_protection_prior`, `flood_sensitivity_analysis`  
**Access hint:** `research_article_source_data_license_check`  
**Authoritative source:** <https://nhess.copernicus.org/articles/16/1049/2016/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Policy and modeled layers are NOT measured engineering characteristics. Freeze data/source version and spatial support before combining with 2026 JRC hazard rasters. Do not double-count overlapping input with COASTPROS-EU.

## EEA Floods Directive reference spatial datasets V3.0

**Candidate ID:** `eea.floods-directive.spatial.v3`  
**Provider:** European Environment Agency / EU Member States  
**Categories:** `flood`, `government_maps`, `spatial_validation`, `europe`  
**Spatial scope:** EU reporting countries  
**Temporal scope:** V3 March 2025; reporting since 2011  
**Resolution / granularity:** GeoPackage and services for management units and potentially significant flood risk areas  
**Potential roles:** `official_flood_region_crosswalk`, `hazard_coverage_validation`  
**Access hint:** `public_download_eea_member_state_terms_review`  
**Authoritative source:** <https://www.eea.europa.eu/en/datahub/datahubitem-view/9b7b6eb4-ac38-40a8-bb91-7c92da523bc9>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official flood area reporting is not continuous flood-depth geometry or a probabilistic event set. Align national reporting epoch, exact map class, geometry and source licensing.

## JRC global flood depth-damage functions and maximum loss values

**Candidate ID:** `ec.jrc.huizinga.flood-depth-damage.2017`  
**Provider:** Huizinga, de Moel, Szewczyk / JRC  
**Categories:** `flood`, `damage_curves`, `vulnerability`, `europe`  
**Spatial scope:** Global with country-level maxima  
**Temporal scope:** 2017 research baseline  
**Resolution / granularity:** Fractional damage by depth and asset/land-use class plus country maximum damage benchmarks  
**Potential roles:** `flood_damage_function`, `replacement_cost_comparison`  
**Access hint:** `public_report_and_curve_file_rights_check`  
**Authoritative source:** <https://publications.jrc.ec.europa.eu/repository/handle/JRC105688>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Key peril-to-loss conversion. Curves use expert judgement and literature; preserve class, units, damage definition, currency year, flood depth datum and uncertainty. Damage value is not insured loss or insurer-specific deductible result.

## EFEHR European Building Vulnerability Data Repository v2.1

**Candidate ID:** `eu.efehr.building-vulnerability.v2.1`  
**Provider:** EFEHR / EUCENTRE / SERA  
**Categories:** `earthquake`, `fragility`, `vulnerability`, `europe`  
**Spatial scope:** Europe, classes in GEM Building Taxonomy  
**Temporal scope:** V2.1 used for ESRM20  
**Resolution / granularity:** Seismic capacity, fragility, damage-to-loss and vulnerability functions for building taxonomies  
**Potential roles:** `seismic_vulnerability`, `seismic_loss_model_validation`  
**Access hint:** `public_gitlab_files_exact_version_and_rights_review`  
**Authoritative source:** <https://eu-risk.eucentre.it/physical-vulnerability/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Compare intensity measure (PGA/SA etc), soil/site response and class mappings with GEM exposure. Release is scientific curves not empirical insured claims. Rights of specific files require review.

## EEA economic losses from climate-related extremes in Europe

**Candidate ID:** `eea.economic-losses-climate-extremes.2026`  
**Provider:** European Environment Agency  
**Categories:** `losses`, `economic_losses`, `insured_losses`, `europe`  
**Spatial scope:** EU and EEA countries  
**Temporal scope:** 1980-2024; 2025 revision published 2026  
**Resolution / granularity:** Country/hazard/period aggregate economic and insured loss observations and estimates  
**Potential roles:** `historical_loss_benchmark`, `national_coverage_rate_validation`  
**Access hint:** `public_eea_data_release_copyright_and_underlying_sources_review`  
**Authoritative source:** <https://www.eea.europa.eu/en/datahub/datahubitem-view/77389680-ecd2-4f56-926f-8106061a5570>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not individual insurer claims, event damage footprint or independent proof of local vulnerability. Preserve indexation, base year, source lineage and missing insured values, including EIOPA dashboard overlap.

## EIOPA Catastrophe Data Hub for insured exposure and losses

**Candidate ID:** `eiopa.catastrophe-data-hub`  
**Provider:** European Insurance and Occupational Pensions Authority  
**Categories:** `insured_exposure`, `insurance_losses`, `europe`  
**Spatial scope:** Limited sample of European non-life insurers  
**Temporal scope:** Public dashboard data vintages vary  
**Resolution / granularity:** Residential/commercial flood and windstorm insured exposure; reported incurred building losses for flood, wildfire and windstorm events  
**Potential roles:** `insured_exposure_calibration`, `insured_loss_validation`  
**Access hint:** `public_dashboard_exact_download_data_reuse_check`  
**Authoritative source:** <https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EIOPA specifies 35 large groups and 9 solo undertakings; no 100% market representativeness. Preserve peril, geography, insurer reporting population, coverage and incurred-vs-paid basis. No individual policy inference.

## EIOPA insurance protection gap dashboard

**Candidate ID:** `eiopa.natcat-protection-gap-dashboard`  
**Provider:** European Insurance and Occupational Pensions Authority  
**Categories:** `insurance_penetration`, `insured_losses`, `europe`  
**Spatial scope:** 30 European countries  
**Temporal scope:** Historical dashboard through 2024  
**Resolution / granularity:** Peril/country protection gap indicators, modeled risk and insurance coverage context  
**Potential roles:** `insurance_penetration_prior`, `country_peril_validation`  
**Access hint:** `public_dashboard_download_inputs_licence_check`  
**Authoritative source:** <https://www.eiopa.europa.eu/tools-and-data/dashboard-insurance-protection-gap-natural-catastrophes_en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Country/peril aggregates, not contract-level exposure. Dashboard may re-use EEA historical data; overlapping lineage is not independent model validation.

## Copernicus CEMS historical fire danger indices

**Candidate ID:** `copernicus.cems.fire-danger-history.v1`  
**Provider:** ECMWF / CEMS / EFFIS  
**Categories:** `wildfire`, `fire_weather`, `europe`  
**Spatial scope:** Global land, Europe included  
**Temporal scope:** 1940-present; continually extended  
**Resolution / granularity:** ERA5-derived gridded historical wildfire danger and Fire Weather Index variables  
**Potential roles:** `wildfire_danger_prior`, `wildfire_stochastic_weather_calibration`  
**Access hint:** `copernicus_ewds_account_product_licence_review`  
**Authoritative source:** <https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1?tab=overview>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Fire-weather potential does not provide observed burned perimeters, ignition points, exposure loss or direct flame intensity; compare against existing EFFIS burned area without treating shared forcing as independent.

## XWS European extreme windstorm tracks and footprints

**Candidate ID:** `xws.european-extreme-windstorms`  
**Provider:** European Windstorm Catalogue research team  
**Categories:** `windstorm`, `historical_events`, `europe`  
**Spatial scope:** Europe  
**Temporal scope:** Selected historical extreme storm events  
**Resolution / granularity:** 50 significant storm tracks and modelled peak gust footprints at about 25 km, raw and recalibrated  
**Potential roles:** `storm_holdout_validation`, `event_identity_crosswalk`  
**Access hint:** `public_research_catalogue_file_and_reuse_review`  
**Authoritative source:** <https://www.europeanwindstorms.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A selected-extremes catalogue cannot establish annual storm frequency. Preserve overlap with C3S and CLIMK, footprint resolution and source calibration; avoid double counting.

## European Tsunami Risk Service data products

**Candidate ID:** `eu.eurotsunamirisk.vulnerability-products`  
**Provider:** ETRiS project consortium  
**Categories:** `tsunami`, `coastal`, `vulnerability`, `europe`  
**Spatial scope:** European coastal regions, product-dependent  
**Temporal scope:** Dataset-specific projects and release dates  
**Resolution / granularity:** Research-accessible tsunami fragility, consequence and vulnerability product listings  
**Potential roles:** `tsunami_fragility_research`, `coastal_peril_extension`  
**Access hint:** `public_project_catalogue_specific_asset_rights_review`  
**Authoritative source:** <https://eurotsunamirisk.org/dataproducts/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Catalogued research candidate only; need identify actual quantitative file, Europe coverage, wave depth/velocity/intensity metric, licensing and exposure taxonomy before using.

## Pan-European coastal flood probability data for present and future climate

**Candidate ID:** `eu.coastal-flood-probability.4tu.2020`  
**Provider:** Paprotny and colleagues / 4TU.ResearchData  
**Categories:** `coastal_flood`, `climate_scenarios`, `europe`  
**Spatial scope:** European coasts  
**Temporal scope:** 2020 research release  
**Resolution / granularity:** Coastal flood probability products comparing present/future climate scenario assumptions  
**Potential roles:** `coastal_flood_risk_prior`, `scenario_sensitivity`  
**Access hint:** `public_research_repo_exact_file_licence_review`  
**Authoritative source:** <https://data.4tu.nl/articles/Pan-European_data_sets_of_coastal_flood_probability_of_occurrence_under_present_and_future_climate/12717446>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Inspect actual file semantics before inferring inundation depth. Local sea-level datum, defence assumptions, climate scenario and vintage must align with coastal building/exposure layers.
