<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-hail-satellite-lightning-20261125.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-hail-satellite-lightning-20261125.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-25`  
**Purpose:** Non-admission discovery registry for satellite severe convection, lightning and hail proxy sources with distinct observational and research lineage.

**Entries:** 13

## NASA SMASH European overshooting-top frequency

**Candidate ID:** `nasa.smash.eu.ot.climatology`  
**Provider:** NASA  
**Categories:** `hail`, `satellite_observations`, `convective_storm`, `climatology`  
**Spatial scope:** European domain; live monthly ImageServer extent approximately 32.29 to 60 N and -11.71 to 39.64 E  
**Temporal scope:** 2004-2024 climatology  
**Resolution / granularity:** Monthly, annual and hourly-binned OT days; monthly service pixel step 0.0357143 degrees, EPSG:4326  
**Potential roles:** `convective_frequency_calibration`, `regional_hazard_context`  
**Access hint:** `public_arcgis_metadata_and_image_service`  
**Authoritative source:** <https://gis.earthdata.nasa.gov/portal/rest/services/SMASH/eu_monthly_ot_frequency_allhours/ImageServer>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Live macOS HTTPS metadata response verified ImageServer scientific service, extent and pixel size. Provider lists daily-occurrence aggregates, not individual OT time/position detections. Preserve calendar/hour bins, coverage, nodata and exact units; never treat OT days as hail days. Rights for exact layer and image export not yet reviewed; no raster bytes sampled.

## NASA severe-storm-signatures OT/AACP software and training assets

**Candidate ID:** `nasa.langley.svrstormsig`  
**Provider:** NASA Langley / Cooney, Bedka and Liles  
**Categories:** `hail`, `satellite_observations`, `convective_storm`, `research_software`  
**Spatial scope:** Geostationary imager domains; regional transfer unvalidated  
**Temporal scope:** 2025 peer-reviewed method; evolving repository  
**Resolution / granularity:** Semantic segmentation of overshooting tops and above-anvil cirrus plumes from satellite imagery and atmospheric inputs  
**Potential roles:** `historical_event_detection`, `convective_severity_feature`  
**Access hint:** `public_source_code_and_model_assets`  
**Authoritative source:** <https://github.com/nasa/svrstormsig>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Paper https://doi.org/10.1175/AIES-D-24-0037.1; training labels, inputs and checkpoints listed at https://science-data.larc.nasa.gov/LaRC-SD-Publications/2023-05-05-001-JWC/data/. Repository contains License.pdf and License_Appendix.pdf; inspect code, checkpoints, training data and dependencies separately before reuse. Freeze commit, model config and sensor compatibility; compare MSG/MTG performance independently and correct parallax. OT and AACP are correlated severe-convection signatures, not surface hail labels; no code executed.

## Hong et al. near-global MODIS overshooting-top climatology

**Candidate ID:** `hong.modis.ot.climatology.2023`  
**Provider:** Hong, Nesbitt, Trapp and Di Girolamo  
**Categories:** `satellite_observations`, `hail`, `climatology`  
**Spatial scope:** Near-global Terra/Aqua MODIS swaths  
**Temporal scope:** Approximately 20 years, study published 2023  
**Resolution / granularity:** 1 km thermal IR imagery; logistic OT detection model  
**Potential roles:** `global_convective_frequency_context`, `algorithm_reference`  
**Access hint:** `publication_and_upstream_satellite_archive`  
**Authoritative source:** <https://doi.org/10.5194/amt-16-1391-2023>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original MODIS/CloudSat/GPM sources cited in study; downloadable derived individual OT catalogue not established. Polar-orbiting sampling and local overpass-time bias preclude continuous tracks. Obtain derived data or reproduce detection with observation opportunity normalization. Rights for source files and derived product separate.

## NASA Passive Microwave Hail Climatology V1

**Candidate ID:** `nasa.ghrc.pmhailclim.v1`  
**Provider:** NASA GHRC DAAC  
**Categories:** `hail`, `satellite_observations`, `climatology`  
**Spatial scope:** Global catalogue extent; actual observation coverage constrained by TRMM and GPM orbits  
**Temporal scope:** 1998-01-01 to 2026-03-31 per live CMR granules; TRMM through 2014-09-30; GPM from 2014-04-01  
**Resolution / granularity:** 2-degree NetCDF-3 annual severe-hailstorm frequency estimates; three CMR granules  
**Potential roles:** `global_hail_frequency_calibration`, `regional_hazard_benchmark`  
**Access hint:** `earthdata_login_protected_download`  
**Authoritative source:** <https://doi.org/10.5067/MODEL/DATA101>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Live CMR collection C2196515446-GHRC_DAAC returned COMBO_HailClimatology_BC2019_2deg.nc, TRMM_HailClimatology_BC2019_2deg.nc and GPM_HailClimatology_BC2019_2deg.nc with protected Earthdata URLs; metadata only, no NetCDF downloaded. Older NASA landing page ended March 2025; live CMR confirms March 2026. Severe-hail frequency inferred from passive microwave ice scattering; coarse climatology, not observed hail diameter or swath. Account, licence and granule variable/normalization check needed.

## GPM DPR Level 2A precipitation profiles V07

**Candidate ID:** `nasa.jaxa.gpm.dpr.v07`  
**Provider:** NASA / JAXA  
**Categories:** `hail`, `radar`, `satellite_observations`  
**Spatial scope:** Approximately 70 S to 70 N orbital coverage  
**Temporal scope:** March 2014 onward  
**Resolution / granularity:** HDF5 orbital swaths, nominal 5 km footprints; V07 hail classification  
**Potential roles:** `spaceborne_hail_proxy_validation`, `vertical_storm_structure`  
**Access hint:** `earthdata_login_and_opendap`  
**Authoritative source:** <https://doi.org/10.5067/GPM/DPR/GPM/2A/07>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Catalogue https://disc.gsfc.nasa.gov/datasets/GPM_2ADPR_07/summary; algorithm basis https://gpm.nasa.gov/sites/default/files/2022-06/ATBD_DPR_V07A.pdf. flagHail/flagGraupelHail are algorithmic hydrometeor indicators, not ground diameter. Validate exact field path and flags with small authenticated subset before bulk download; full granules large. Orbit sampling, attenuation and nonuniform beam filling matter.

## EUMETSAT MSG SEVIRI High Rate Level 1.5

**Candidate ID:** `eumetsat.msg.hrseviri.l15`  
**Provider:** EUMETSAT  
**Categories:** `satellite_observations`, `convective_storm`, `hail`  
**Spatial scope:** Meteosat full disk, Europe/Africa  
**Temporal scope:** 19 January 2004 onward per catalogue  
**Resolution / granularity:** 12 spectral channels, historical 15-minute nominal imagery; latency-dependent availability  
**Potential roles:** `historical_ot_reconstruction`, `cloud_top_cooling`, `storm_tracking`  
**Access hint:** `eumetsat_data_store`  
**Authoritative source:** <https://user.eumetsat.int/catalogue/EO:EUM:DAT:MSG:HRSEVIRI>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Exact collection EO:EUM:DAT:MSG:HRSEVIRI. Preserve platform transitions, spectral response, scan timing, calibration and parallax; review historical archive completeness and product-specific licence before authenticated acquisition. Raw imagery, not OT catalogue. Pair with published OT detector rather than assuming GOES model transfers.

## WWLLN Global Lightning Climatology v2026.0.0

**Candidate ID:** `wwlln.wglc.v2026`  
**Provider:** Jed O. Kaplan / WWLLN  
**Categories:** `lightning`, `climatology`, `convective_storm`  
**Spatial scope:** Global WGS84  
**Temporal scope:** 2010-2025  
**Resolution / granularity:** NetCDF; monthly 5 arc-minute and 0.5 degree; daily 0.5 degree; stroke density and power  
**Potential roles:** `global_convective_frequency_calibration`, `lightning_power_covariate`  
**Access hint:** `public_versioned_download_rights_conflict`  
**Authoritative source:** <https://zenodo.org/records/20277101>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Live Zenodo API returned 7 files totaling 3299540376 bytes, metadata license cc-by-4.0; deposit description explicitly states CC BY-SA 4.0. Treat rights as conflicting until publisher confirms; no WGLC data downloaded or admitted. README is 2747 bytes, 30m monthly climatology 27325956 bytes. Detection-efficiency-adjusted stroke density is not optical flash count; no event-level tracks or jumps. Do not generalize derived grid licence to raw WWLLN.

## NASA ISS Lightning Imaging Sensor quality-controlled V3

**Candidate ID:** `nasa.iss.lis.v3.fin`  
**Provider:** NASA GHRC DAAC  
**Categories:** `lightning`, `satellite_observations`, `convective_storm`  
**Spatial scope:** 55 S to 55 N  
**Temporal scope:** 2017-03-01 to 2023-11-16  
**Resolution / granularity:** NetCDF-4/HDF4 optical total-lightning detections  
**Potential roles:** `historical_lightning_proxy`, `cross_sensor_calibration`  
**Access hint:** `earthdata_login`  
**Authoritative source:** <https://doi.org/10.5067/LIS/ISSLIS/DATA114>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CMR collection C3838944284-GHRC_DAAC. Intermittent ISS observation windows require exposure normalization; flash/stroke distinction and detection efficiency must be retained. Not continuous tracks. Exact granule rights and bytes untested.

## NOAA GOES GLM L2 events groups flashes

**Candidate ID:** `noaa.goes.glm.l2.lcfa`  
**Provider:** NOAA NCEI / GOES-R Program  
**Categories:** `lightning`, `satellite_observations`, `convective_storm`  
**Spatial scope:** Americas geostationary fields of view  
**Temporal scope:** GOES-R era from 2017/2018; satellite-specific archive dates  
**Resolution / granularity:** Time-stamped optical lightning events, groups and flashes; NetCDF  
**Potential roles:** `lightning_jump_feature`, `storm_tracking`, `cross_sensor_validation`  
**Access hint:** `public_cloud_archive`  
**Authoritative source:** <https://doi.org/10.7289/V5KH0KK6>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NCEI catalog gov.noaa.ncdc:C01527; public archive https://registry.opendata.aws/noaa-goes/. Freeze satellite and exact file, account for viewing geometry, outages, flash clustering and sensor transitions. No live granule downloaded. Not hail measurements.

## TORRO / Hayward Northwest Europe thunderstorm catalogue

**Candidate ID:** `torro.atdnet.thunderstorm.catalogue.2008-2018`  
**Provider:** Hayward et al. / TORRO / UK Met Office ATDnet  
**Categories:** `lightning`, `convective_storm`, `event_tracks`  
**Spatial scope:** 48 to 65 N, 15 W to 10 E  
**Temporal scope:** 2008-2018  
**Resolution / granularity:** Tracked lightning clusters of at least three flashes; duration, motion, flash rate  
**Potential roles:** `historical_thunderstorm_tracking`, `event_geometry_context`  
**Access hint:** `public_catalogue_link_rights_unverified`  
**Authoritative source:** <https://www.torro.org.uk/research/thunderstorm-observer>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher links a catalogue; paper https://doi.org/10.1002/joc.8123. Underlying Met Office ATDnet is third party; public link and open-access article do not establish commercial reuse. Confirm catalogue terms and file identity before downloading or ingesting. Thunderstorms are not hail events.

## KIT TRACE3D potential hail tracks Germany

**Candidate ID:** `kit.trace3d.pht.2005-2024`  
**Provider:** KIT / Mohr et al. / DWD radar  
**Categories:** `hail`, `radar`, `event_tracks`  
**Spatial scope:** Germany  
**Temporal scope:** April-September 2005-2024; 2005 partial coverage  
**Resolution / granularity:** 15577 potential hail tracks from 3D radar PZ volumes  
**Potential roles:** `hail_track_geometry_calibration`, `historical_frequency_benchmark`  
**Access hint:** `publication_upstream_data_author_request`  
**Authoritative source:** <https://doi.org/10.3389/fenvs.2026.1736782>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Published 2026-02-06. Article validated against building insurance data; no public direct track-file link established. Data availability statement points to https://opendata.dwd.de/weather/radar/sites/pz/ and ERA5 regimes https://zenodo.org/records/17080146; confirm historic PZ access separately from operational directory. Paper does not provide hailstone diameter distribution. Request derived tracks and explicit rights or reproduce method with authorized radar archive.

## Giordani et al. OT and SPHERA hail-environment method

**Candidate ID:** `giordani.ot.sphera.hail.2024`  
**Provider:** University of Bologna / KIT / NASA / ARPAE  
**Categories:** `hail`, `convective_storm`, `research_software`  
**Spatial scope:** South-central Europe  
**Temporal scope:** Study published 2024  
**Resolution / granularity:** OT detections joined to convection-permitting reanalysis and hail reports  
**Potential roles:** `feature_selection_reference`, `hail_environment_model`  
**Access hint:** `public_code_data_on_request`  
**Authoritative source:** <https://doi.org/10.5194/nhess-24-2331-2024>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Code https://github.com/agiord/hail-analysis; SPHERA from corresponding author; NASA OT data via provider request; ESWD reports separate restricted terms. Inspect code licence and verify exact feature definitions. No external data downloaded. Avoid circular validation against reports used for training.

## NASA experimental US severe-weather OT/AACP product April 2025

**Candidate ID:** `nasa.smash.ot.aacp.experimental.202504`  
**Provider:** NASA Earthdata GIS / Langley  
**Categories:** `hail`, `satellite_observations`, `event_footprint`  
**Spatial scope:** United States event domain  
**Temporal scope:** 2025-04-02 to 2025-04-06  
**Resolution / granularity:** Experimental raster detections derived from GOES 500 m imagery at 5-minute cadence  
**Potential roles:** `algorithm_output_benchmark`, `storm_track_context`  
**Access hint:** `public_gis_item_metadata`  
**Authoritative source:** <https://gis.earthdata.nasa.gov/portal/home/item.html?id=b1dbafac653b41e8b4716de1020a201e>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider marks product experimental. Time-aggregated repeated detections may indicate severe storm tracks but not hail swaths. Check exact raster service/licence and independent surface hail reports before quantitative use.
