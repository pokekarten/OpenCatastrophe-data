<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-paper-upstream-research-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-paper-upstream-research-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission research registry of original datasets traced from scientific flood and building-damage papers, requiring independent source rights, data provenance and model-use checks.

**Entries:** 5

## CFDID China Flood Disaster Impact Database v1.1

**Candidate ID:** `cn.cfdid.flood-impacts.1994-2023.v1-1`  
**Provider:** Cui et al. / Tsinghua University / Zenodo  
**Categories:** `flood`, `reported_impacts`, `agricultural_damage`, `residential_damage`, `china`, `event_catalogue`  
**Spatial scope:** Chinese mainland; chiefly province-level reported locations, sometimes more detailed text names  
**Temporal scope:** Original events 1994-2023; frozen dataset v1.1 released 2026-09-23; paper published 2026-11-05  
**Resolution / granularity:** 1,716 reported hierarchical event records: 1,391 parent L1, 300 nested L2, 25 nested L3; eight human/economic/cropland/dwelling impact indicators from 66 official documents; v1.1 includes data dictionary, code, annual benchmark totals and EM-DAT event crosswalk  
**Potential roles:** `china_flood_historical_loss_benchmark`, `reported_crop_and_dwelling_damage_challenge`, `event_identity_reconciliation`, `modelled_loss_holdout`  
**Access hint:** `public_zenodo_v1_1_original_files_and_rights_not_yet_admitted`  
**Authoritative source:** <https://zenodo.org/records/22918521>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Peer reviewed https://doi.org/10.5194/essd-18-8129-2026. Sources include China Water Resources Yearbook, Yearbook of Meteorological Disasters in China, and Top Ten Natural Disasters in China; China Flood and Drought Bulletin duplicates some yearbook statistics. Never add L2/L3 economic losses to their L1 parents. Original 2026 EGU conference abstract mentions different 1949-2023 / 15k scope: do not conflate with published 1994-2023 / 1,716 v1.1. Derived aggregate reported impacts are not measured flood depth, insured property losses, or a complete event-frequency catalogue. Missing values not zero, CNY nominal vs 2023-constant disjoint. Version rights, per-file SHA and official-document third-party re-use not independently reviewed.

## EO4FLOOD Advanced Open Earth Observation Dataset v2

**Candidate ID:** `eu.eo4flood.multibasin-hydrology.v2`  
**Provider:** Tarpanelli et al. / ESA EO4FLOOD consortium / Zenodo  
**Categories:** `flood`, `hydrology`, `earth_observation`, `river_basin`, `validation`, `global`  
**Spatial scope:** Nine basins: Brahmaputra, Congo, Danube, Ebro, Negro, Niger, Po, Rhine and Torne  
**Temporal scope:** Research dataset v2 released 2026-07-30; sensor-specific observation coverage and temporal alignment vary  
**Resolution / granularity:** About 60.2 GB across basin ZIP archives; precipitation, soil moisture, river water level, river discharge, flood extent, river width, snow and remote-sensing features plus Jupyter notebooks  
**Potential roles:** `rhein_donau_po_hydrologic_hazard_check`, `multi_basin_flood_forcing_comparison`, `flood_extent_event_holdout`  
**Access hint:** `public_zenodo_v2_multibasin_bulk_original_asset_license_and_checksums_pending`  
**Authoritative source:** <https://zenodo.org/records/21699983>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Associated 2026 paper https://doi.org/10.1007/s10712-026-09935-w. Preserve v2 distinct from superseded v1 17787732. Public Zenodo CC BY 4.0 record does not settle embedded satellite/provider rights. This compilation contains multiple distinct observed and processed variables, not uniform independent measurements; evaluate each layer's origin, timestamps, CRS, datum, missingness and downstream derivative rights. No original ZIP, data values or insured losses imported.

## European multi-input observed-flood-inundation patches v1 (Randall 2026)

**Candidate ID:** `eu.randall.inundation-patches.2026.v1`  
**Provider:** Natasha Randall / Zenodo  
**Categories:** `flood`, `inundation_masks`, `satellite`, `ml_benchmark`, `europe`  
**Spatial scope:** Seven events in France, Italy, Greece, Poland, Slovakia, Hungary and Germany  
**Temporal scope:** European flood events 2019-2024; publication 2026-10-19, version v1  
**Resolution / granularity:** 3,027 geographically referenced 256 x 256 multi-resolution patches with local/nearby/context inputs and 3-class Copernicus EMS target labels  
**Potential roles:** `flood_footprint_model_holdout`, `meteorology_topography_flood_joint_input_challenge`, `model_leakage_research`  
**Access hint:** `public_zenodo_dataset_with_fabdem_noncommercial_derivative_boundary`  
**Authoritative source:** <https://zenodo.org/records/23470601>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Upstream inputs: FABDEM, NASA IMERG, Sentinel-2, ESA WorldCover, OSM water features, NASA SMAP, ISRIC SoilGrids. Label is CEMS flood extent; value 0 non-AOI must not be read as observed dry land. FABDEM's CC BY-NC-SA 4.0 rights are a commercial reuse blocker pending explicit permission. CEMS input labels cannot also be independent validation. Keep splits by physical event, not arbitrary chips. Model code: https://github.com/Natasha-R/Flood-Prediction-Deep-Learning. No claims of observed loss, return-period maps or insurer TIV.

## Keeney-Davenport EM-DAT/MODIS flood admin1-month research package v1

**Candidate ID:** `global.keeney.modis-emdat-flood-events.2025.v1`  
**Provider:** Nicole J. Keeney and Frances V. Davenport / Zenodo / Colorado State University  
**Categories:** `flood`, `remote_sensing`, `emdat`, `historical_events`, `global`, `event_geocoding`  
**Spatial scope:** 177 countries and 2,375 first-level administrative regions in 2000-2024 research sample  
**Temporal scope:** 2000-2024 event observations; source code v1 published 2025-12-12, 2026-09-29 peer-review preprint  
**Resolution / granularity:** Preprint reports 4,073 inland EM-DAT events disaggregated to 23,334 admin1-month records with MODIS detected flood area and gridded exposed population; public Zenodo v1 software archive about 42.6 MB including sample outputs and CSVs; full per-event floodmap set not established as published  
**Potential roles:** `global_flood_event_duration_benchmark`, `spatiotemporal_emdat_hazard_linkage`, `flood_exposed_population_method_challenge`  
**Access hint:** `public_code_release_not_full_global_floodmap_asset_license_unverified`  
**Authoritative source:** <https://zenodo.org/records/17905100>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ESSD 2026 peer-review preprint https://doi.org/10.5194/essd-2026-577, not yet a final accepted paper. Parent EM-DAT records and already registered event datasets are not independent loss observations. MODIS inundation estimates depend on clouds/detection method; administrative polygon and calendar-month labels are NOT observed exact flood footprints or dates. Dataset ZIP contains reference CSVs and only example floodmaps according to provider release. Recheck license of EM-DAT-derived data, satellite and gridded population inputs before redistribution or commercial use.

## Marche 2022 surveyed residential and business flood damage

**Candidate ID:** `it.marche.surveyed-flood-building-damage.2022.v1`  
**Provider:** Rrokaj et al. / University of Florence / Zenodo  
**Categories:** `flood`, `field_survey`, `building_damage`, `business_interruption`, `residential`, `italy`  
**Spatial scope:** Italian Marche region: Ostra, Senigallia, Trecastelli; Misa River basin  
**Temporal scope:** 2022-09-15 flood, field observations collected 2022-10 through 2022-12; paper published 2025-11-25  
**Resolution / granularity:** 256 building-level surveys: 133 business premises, 123 residential buildings; five linked xlsx workbooks/forms per population, data dictionaries and survey questions; mixed building, contents, business and indirect damage fields  
**Potential roles:** `flood_damage_ratio_observed_challenge`, `commercial_property_contents_loss_method`, `building_typology_flood_vulnerability`  
**Access hint:** `public_author_survey_workbooks_original_coordinates_privacy_rights_not_reviewed`  
**Authoritative source:** <https://zenodo.org/records/15591850>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Peer reviewed https://doi.org/10.5194/essd-17-6487-2025. Recorded site coordinates and property/business details require source-specific privacy and processing/redistribution scrutiny; NO raw survey rows or coordinates into Git. Keep residential and business populations disjoint and preserve form-A parent keys and one-to-many subforms. These are self-reported/field-survey physical/economic impacts, not verified insurer claims, not a national building census, not annual model frequency. Research-only scientific/rights checks remain open.
