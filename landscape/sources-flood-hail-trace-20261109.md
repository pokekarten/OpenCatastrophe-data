<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-flood-hail-trace-20261109.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-flood-hail-trace-20261109.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-09`  
**Purpose:** Non-admission original-provider discovery of six Germany/England/Europe flood-depth, radar-hail and regional climate-risk research products; no source bytes, data admission, model approval or publication permission.

**Entries:** 6

## Germany HWRM-RL cycle 3 harmonised river and coastal flood-depth classes

**Candidate ID:** `de.bfg.hwrm3-flood-depth.2026`  
**Provider:** Bundesanstalt fuer Gewaesserkunde (BfG) / WasserBLIcK / German federal and state water authorities  
**Categories:** `flood`, `river_flood`, `coastal_flood`, `hazard_depth`, `germany`  
**Spatial scope:** Germany; national harmonised reporting coverage, regional higher-resolution original layers may differ  
**Temporal scope:** EU Floods Directive HWRM-RL third cycle 2022-2027; GovData publication 2026-03-06, reporting snapshot not an annual event chronology  
**Resolution / granularity:** Flood-depth polygon classes 0-0.5, 0.5-1, 1-2, 2-4 and over 4 metres; low/medium/high probability and river/coastal scenarios; T_class combines area type with depth class  
**Potential roles:** `germany_flood_depth_hazard_prior`, `synthetic_property_flood_screening`, `regional_flood_model_crosscheck`  
**Access hint:** `public_govdata_catalogue_bin_resource_exact_service_and_terms_review_required`  
**Authoritative source:** <https://data.gov.de/suche/daten/uberflutungstiefen-de-hochwasserrisikomanagement-rl-3-zyklus-2022-2027>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official GovData page describes HWRM third-cycle reporting, probability classes and depth-band T_class encoding (for example 23 indicates the informational flood area and 1-2 m depth). This is a nationally harmonised static scenario product; it is not a gauge-observed historic event, individual-property water depth, annual occurrence model, insured loss, or proof of local completeness. Verify the original BfG service endpoints, CRS, source authority, exact source vintage, provider-specific terms and state-level alternatives before access or commercial model use. Publisher metadata defines river/inland depth relative to the watercourse bed and coastal depth relative to seabed/chart datum and tide; this is not independently validated inundation above building ground elevation. Area-type digit 3 of T_class is a flood-protected area, not evidence of a flooded insured building. Do not translate these classes directly into building-depth loss without original service schema, terrain reference and spatial support verification.

## England Environment Agency rivers and sea defended and undefended flood depths present day

**Candidate ID:** `uk.ea.rivers-sea-flood-depth.present.2026`  
**Provider:** UK Environment Agency / Defra Data Services Platform  
**Categories:** `flood`, `river_flood`, `coastal_flood`, `defences`, `hazard_depth`, `england`  
**Spatial scope:** England; only areas with national flood-zone modelling, with explicit Unavailable attribute elsewhere  
**Temporal scope:** Present-day risk scenarios; metadata updated 2026-10-30  
**Resolution / granularity:** Seven depth bands up to and over 2300 mm; defended and undefended 0.1% AEP; river 1% AEP and sea 0.5% AEP; OGC API Features, WFS, WMS and GeoJSON/Geodatabase ZIP links listed  
**Potential roles:** `england_flood_defence_sensitivity`, `probabilistic_flood_depth_screening`, `synthetic_property_flood_hazard_prior`  
**Access hint:** `public_catalogue_ogc_and_geojson_downloads_ogl_reported_exact_assets_and_service_terms_review`  
**Authoritative source:** <https://www.data.gov.uk/dataset/e4698ae1-184b-4b5d-801a-90364a93e229/rivers-and-sea-defended-and-undefended-flood-risk-depths-present-day>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher lists Open Government Licence, EPSG:27700 and explicit Unavailable regions. Defended assumes flood defences perform as designed; no defence-failure scenario. Depths are categorical scenario estimates, not exact depth at an individual insured building or event observations. Confirm the exact 2026 revised asset/OGC layer URL, request limits, geographic completeness, attribution and commercial automation before download or modelling. Never coerce Unavailable to zero depth.

## England Environment Agency rivers and sea flood-depth climate-change scenarios

**Candidate ID:** `uk.ea.rivers-sea-flood-depth.climate.2026`  
**Provider:** UK Environment Agency / Defra Data Services Platform  
**Categories:** `flood`, `river_flood`, `coastal_flood`, `climate_scenario`, `hazard_depth`, `england`  
**Spatial scope:** England; national flood-zone modelling supported polygons, local depth may be Unavailable  
**Temporal scope:** Climate-change scenario dataset updated 2026-10-30; river 2080s epoch 2070-2125 and coastal sea-level-rise allowance to 2125  
**Resolution / granularity:** Seven depth bands in defended/undefended 0.1% AEP and river 1% / sea 0.5% AEP cases; UKCP18 RCP8.5 allowances  
**Potential roles:** `climate_flood_sensitivity`, `england_flood_hazard_scenario_benchmark`, `portfolio_climate_stress_test`  
**Access hint:** `public_catalogue_ogc_and_geojson_downloads_provider_rights_and_scenario_review`  
**Authoritative source:** <https://www.data.gov.uk/dataset/67a734bb-2b7b-491a-aafd-3f7e52c8d7f3/rivers-and-sea-defended-and-undefended-flood-risk-depths-climate-change>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official climate-change product is scenario-conditioned, not observed annual losses and not a current-baseline flood-frequency distribution. River central allowance for the 2080s and coastal upper-end allowance to 2125 use UKCP18/RCP8.5; defences assumed to function unchanged. Preserve scenario, epoch, exceedance definition, Unavailable cells, and shared lineage with the corresponding present-day product; these two products are not independent observed evidence.

## England Environment Agency surface-water spatial-planning flood-depth classes present day

**Candidate ID:** `uk.ea.surface-water-depth.present.2026`  
**Provider:** UK Environment Agency / Defra Data Services Platform  
**Categories:** `flood`, `surface_water_flood`, `pluvial`, `hazard_depth`, `england`  
**Spatial scope:** England, within coverage and planning-product limitations  
**Temporal scope:** Present-day planning scenario product published 2026-05-28, catalogue updated 2026-07-06  
**Resolution / granularity:** Depth bands up to 150 mm, 150-300, 300-600, 600-900, 900-1200, 1200-2300 and over 2300 mm; 3.3%, 1% and 0.1% AEP scenarios; WMS and download links  
**Potential roles:** `england_pluvial_flood_screening`, `multi_peril_flood_benchmark`, `building_exposure_pluvial_hazard_prior`  
**Access hint:** `public_catalogue_wms_download_ogl_listed_exact_service_asset_terms_review`  
**Authoritative source:** <https://www.data.gov.uk/dataset/b0bbfacf-ccf7-4ed9-a94c-be18d91c258d/flood-map-for-planning-surface-water-spatial-planning-depths-present-day>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A separate pluvial/surface-water source, not a replacement for fluvial/coastal depth mapping. The Environment Agency explicitly says planning depth bands are not suitable for determining whether an individual property floods. Retain AEP, spatial support, depth bins, release and lineage; avoid counting overlap with river/sea flooding as independent losses. Review service access and original product licence for automated commercial use.

## DWD single-radar PZ volume reflectivity data for historical hail-cell research

**Candidate ID:** `de.dwd.radar-pz-volume.hailresearch.2026`  
**Provider:** Deutscher Wetterdienst (DWD); 2026 analysis by KIT and CEDIM (Mohr et al.)  
**Categories:** `hail`, `convective_storm`, `radar`, `weather_observation`, `germany`  
**Spatial scope:** German DWD radar stations; individual station footprints may cross national borders  
**Temporal scope:** DWD directory observed 2026-11; 2026 paper analyses summer seasons 2005-2024 using archived PZ volumes, but public directory's exact historical availability is not yet established  
**Resolution / granularity:** Per-station 3D radar reflectivity PZ files, 12 altitude layers and six reflectivity classes in the study; original study uses a homogeneous 15-minute composite for 2005-2024  
**Potential roles:** `hail_storm_cell_hazard_research`, `radar_track_reconstruction`, `regional_hail_frequency_validation`  
**Access hint:** `public_dwd_station_file_directory_licence_and_historical_exact_byte_receipt_required`  
**Authoritative source:** <https://opendata.dwd.de/weather/radar/sites/pz/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The original station directory contains PZ radar files and station folders; the 2026 peer-reviewed publication https://doi.org/10.3389/fenvs.2026.1736782 reports 15,577 potential hail tracks for 2005-2024, not a publicly verified separately downloadable PHT dataset. Reflectivity indicates potential hail cells, not confirmed hailstone size, individual insured property loss or independent claims. Historical file retention, polarimetric/version changes, outage coverage, machine access, exact DWD weather-radar terms and licence need source-specific verification. Do not extend CDC-specific CC BY terms to this weather-radar product without review.

## JRC TRACE / PESETA V pan-European regional climate-risk and economic-impact scenarios

**Candidate ID:** `eu.jrc.trace.pesetav-regional-risk.2026`  
**Provider:** European Commission Joint Research Centre (JRC) / Disaster Risk Management Knowledge Centre  
**Categories:** `multi_peril`, `climate_scenario`, `regional_risk`, `economic_impacts`, `europe`  
**Spatial scope:** European regions covered by JRC TRACE / PESETA V regional dashboard  
**Temporal scope:** Dashboard announced 2026-10-30; regional modelled impacts across global warming levels and socioeconomic scenarios  
**Resolution / granularity:** Regional economic impact and exposure scenario tables by risk, geography and warming level; underlying table reported downloadable from dashboard  
**Potential roles:** `european_regional_climate_impact_benchmark`, `multi_peril_scenario_consistency`, `aggregate_economic_loss_sanity_check`  
**Access hint:** `public_jrc_dashboard_table_download_claim_api_auth_and_exact_table_license_review`  
**Authoritative source:** <https://drmkc.jrc.ec.europa.eu/risk-data-hub/projects/PesetaV>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** JRC official 2026-10-30 announcement https://joint-research-centre.ec.europa.eu/jrc-news-and-updates/jrc-makes-climate-risk-data-europes-regions-available-through-single-dashboard-2026-10-30_en describes region/hazard/warming-level comparability and downloadable dashboard tables. These are modelled economic damages/exposures, not independent insurer claims or catastrophe event losses; preserve inflation base year, scenario, spatial aggregation, hazard models and common upstream assumptions. Risk Data Hub API portal documents EU Login/API-token requirements; do not assume that dashboard tables are available through an anonymous API, or that the API licence covers every table. Obtain exact table receipt and publication terms separately.
