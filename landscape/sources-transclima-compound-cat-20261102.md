<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-transclima-compound-cat-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-transclima-compound-cat-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery and deduplicated research of additional compound-event, tropical-cyclone, storm-surge and flood-screening products from Exa and original provider evidence, checked against current main and open 2026-11-02 CAT source PRs; all rights and scientific admission remain blocked pending explicit review.

**Entries:** 7

## European Multi-Hazard Dataset in Sparse Array Format v1

**Candidate ID:** `nl.vu.european-multihazard-sparse-events.v1`  
**Provider:** Vrije Universiteit Amsterdam / University of Oxford (Claassen, Koks)  
**Categories:** `multi_hazard`, `compound_events`, `flood`, `windstorm`, `wildfire`, `heatwave`  
**Spatial scope:** Europe, varying by hazard source and observation window  
**Temporal scope:** Flood 2015-2024; windstorm 2015-2024; wildfire 2008-2026; heatwave 2008-2025  
**Resolution / granularity:** NetCDF sparse spatial/temporal event arrays and CSV event/pair indexes; about 6.1 GB published, pairs flood-windstorm and heatwave-wildfire  
**Potential roles:** `compound_event_copula_validation`, `cross_peril_footprint_alignment`, `post_event_independent_challenge`  
**Access hint:** `public_zenodo_metadata_and_download_exact_file_rights_review`  
**Authoritative source:** <https://zenodo.org/records/22080546>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** New dataset package is a transformation of separately known ERA5-Land, EFFIS, C3S windstorm tracks/footprints and JRC flood depth; not an independent observational source for those hazards. Each event has own id/time and sparse coordinate representation; flood intensity is centimetres, wind gust m/s, wildfire burned-area binary. Preserve event IDs, sparse grid/CRS, original input provenance, overlap algorithm and original source rights. Dataset page lists file hashes as MD5; compute SHA-256 for a bounded rights-cleared artifact. License and use scope require direct provider confirmation. Do not interpret overlap pairs as simultaneous insured losses.

## Global 12000-year synthetic tropical cyclone track ensembles by ENSO regime

**Candidate ID:** `ihcantabria.ih-storm.enso-synthetic-tracks.v2`  
**Provider:** IHCantabria TRANSCLIMA / Odériz and Losada  
**Categories:** `tropical_cyclone`, `stochastic_events`, `climate_variability`, `windstorm`  
**Spatial scope:** Global tropical-cyclone basins  
**Temporal scope:** Climatology 1980-2021; release 2025-03-27 v2; 12000 simulated years per climate regime/basin  
**Resolution / granularity:** ZIP archives by historical baseline, neutral ENSO, El Niño, and La Niña; stochastic track records and city return-period summary  
**Potential roles:** `climate_conditioned_stochastic_event_sets`, `windstorm_event_frequency_sensitivity`, `secondary_uncertainty_research`  
**Access hint:** `public_zenodo_archives_dataset_specific_license_and_storm_code_review`  
**Authoritative source:** <https://zenodo.org/records/15097665>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IH-STORM model code: https://github.com/IHCantabria/IH-STORM and https://zenodo.org/records/23763850 (2026-10-29); original STORM lineage: https://github.com/NBloemendaal/STORM. Synthetic model output, not historical observations or wind-field footprints. Preserve basin, stochastic year, track id, ENSO regime, baseline and exact release; review license of dataset and model separately. Check dependencies with IBTrACS and any previously registered STORM-derived sources to avoid treating the ensemble as independent truth.

## Global cyclone-attributed storm-surge hydrographs GTSMv3/GESLAv3

**Candidate ID:** `ihcantabria.transclima.tc-surge-hydrographs.2026`  
**Provider:** IHCantabria TRANSCLIMA / Deltares / Vrije Universiteit Amsterdam  
**Categories:** `coastal_flood`, `storm_surge`, `tropical_cyclone`, `historical_events`, `observations`  
**Spatial scope:** Global coastal stations/basins represented by station and storm IDs  
**Temporal scope:** Historical tropical cyclones and GTSMv3 1980-2022 reanalysis; source-specific GESLAv3 observations  
**Resolution / granularity:** Storm- and basin-partitioned NetCDF event/full time series and CSV per-station hydrographs; published about 456 MB files  
**Potential roles:** `surge_hydrograph_event_validation`, `compound_cyclone_coastal_risk`, `cyclone_storm_surge_event_id_crosswalk`  
**Access hint:** `public_zenodo_basin_archives_source_specific_rights_and_gauge_provenance_review`  
**Authoritative source:** <https://zenodo.org/records/18170693>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Derived via DKM-DBSCAN Hazard Tracker (https://github.com/IHCantabria/TRANSCLIMA.hazard_tracker; https://zenodo.org/records/23765126) and GTSMv3/GESLAv3. Companion method describes 2723 historical cyclones. GTSM modelled and GESLA gauge paths are not independent if collated into one target; preserve original station/SID, time units, vertical reference, gauge quality, and storm-event identity. Hydrograph is water level surge, not inundation depth or damage. Rights on all contributing data and derived outputs require review.

## TRANSCLIMA tropical cyclone and coastal climate risk source catalogue (262 entries)

**Candidate ID:** `ihcantabria.transclima.tropical-cyclone-data-catalogue.v1`  
**Provider:** IHCantabria / Odériz (TRANSCLIMA)  
**Categories:** `data_catalogue`, `tropical_cyclone`, `coastal_flood`, `storm_surge`, `exposure`, `vulnerability`  
**Spatial scope:** Global with diverse region-specific referenced products  
**Temporal scope:** Catalog published 2026-10-28; source vintages vary by entry  
**Resolution / granularity:** Excel workbook with 262 referenced datasets/models/tools over 14 themes including waves, wind, surge, sea level, exposure, losses and vulnerability  
**Potential roles:** `source_discovery_crosswalk`, `source_rights_gap_detection`, `model_component_gap_inventory`  
**Access hint:** `public_metadata_catalogue_cc_by4_catalogue_only_upstream_rights_separate`  
**Authoritative source:** <https://doi.org/10.5281/zenodo.23736379>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Catalogue is a discovery aid, NOT 262 unique admitted or rights-cleared datasets. Recorded entries expose provider, original link, spatial/temporal resolution, protocols, access and license hints. CC BY 4.0 applies to the catalogue compilation only; individual data products have their own rights. Deduplicate with existing registry and freeze original provider/product identity before creating new candidates. Never copy source data or assume commercial licensing from catalogue entries.

## GTSM-ERA5-E extreme sea level percentile and return-level statistics 1950-2024

**Candidate ID:** `nl.deltares.gtsm-era5-e.extreme-sea-level-stats.v2`  
**Provider:** Deltares / Vrije Universiteit Amsterdam  
**Categories:** `coastal_flood`, `storm_surge`, `extreme_sea_level`, `hazard`, `return_period`  
**Spatial scope:** Global coastal model stations/grid described in release  
**Temporal scope:** 1950-2024 model hindcast; Zenodo release v2 2025-02-25  
**Resolution / granularity:** NetCDF ~9.7 MB; percentiles and 1/2/5/10/25/50/75/100-year water-level return values with GPD parameters  
**Potential roles:** `coastal_hazard_return_level_benchmark`, `coastal_surge_model_challenge`, `regional_coastal_sensitivity`  
**Access hint:** `public_zenodo_stats_netCDF_source_and_climate_data_store_rights_review`  
**Authoritative source:** <https://zenodo.org/records/14671593>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Derived from ECMWF CDS GTSM-ERA5-E water-level time series DOI 10.24381/cds.a6d42d60, code https://github.com/VU-IVM/gtsm3-era5-nrt. Do not confuse statistical water-level return values with actual 2D flood depths or coastal defences. Review vertical datum, tide/surge treatment, ensemble/forcing and provider licensing before model use. Check overlap with GESLA gauge validation and other GTSM/Deltares products.

## EO4MULTIHAZARDS Events Database PostgREST query service

**Candidate ID:** `it.eurac.eo4multihazards.event-crosswalk-api`  
**Provider:** Eurac Research / EO4MULTIHAZARDS  
**Categories:** `multi_hazard`, `event_catalogue`, `historical_disasters`, `event_source_crosswalk`  
**Spatial scope:** Europe and additional countries represented by underlying event provider; portal shows NUTS2 overview  
**Temporal scope:** 2020-2025 initial overview; live provider records extend beyond according to catalog  
**Resolution / granularity:** PostgREST JSON event query interface /api/events_light; event type, date, country and original provider ID  
**Potential roles:** `event_crosswalk`, `compound_event_case_selection`, `observed_event_provenance_review`  
**Access hint:** `public_documented_query_api_but_bulk_source_download_restricted_by_upstream_rights`  
**Authoritative source:** <https://edp-portal.eurac.edu/eo4multihazards_doc/eo4multiha/download/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official docs show public example GET https://eo4multihazards.eurac.edu/api/events_light?e_type=eq.Drought&amp;e_date=gt.2023-01-01. The complete dataset is not downloadable due to source license restrictions; source providers include EM-DAT, EFFIS, and BGS, so their records must not be duplicated as independent events. No live network probe or full API validation performed. Review rights before bulk extraction or redistribution.

## GFSM v1 global 30 m flood susceptibility tiles

**Candidate ID:** `waleedgeo.gfsm.global-flood-susceptibility.v1`  
**Provider:** Mirza Waleed / Hong Kong Baptist University / KAUST  
**Categories:** `flood`, `hazard_screening`, `flood_susceptibility`, `geospatial_raster`  
**Spatial scope:** Global land approximately 80N to 60S with regional gaps  
**Temporal scope:** Published 2026; baseline flood susceptibility, not event calendar  
**Resolution / granularity:** GeoTIFF 30 m tiled regional ZIP archives with GeoPackage tile index; regional classes 1 to 5  
**Potential roles:** `screening_hazard_hotspots`, `cross_model_flood_susceptibility_challenge`, `asset_risk_prioritization_context`  
**Access hint:** `public_zenodo_large_regional_zip_tiles_license_terms_and_training_lineage_review`  
**Authoritative source:** <https://zenodo.org/records/20568218>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Trained using WRI Aqueduct Flood Hazard Maps as labels plus topographic and other environmental covariates, therefore derived/overlapping with existing Aqueduct candidate; NOT a new independent flood event or a flood depth/annual-probability product. Susceptibility class cut-offs 1-5 must not be read as calibrated loss probabilities. No flood defences or future climate changes represented. Check exact license/attribution, tile index, 30 m grid CRS EPSG:3395 and regional missing coverage before using; avoid large bulk downloads before access approval.
