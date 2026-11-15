<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-observation-gaps-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-observation-gaps-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery of four independently identified global coastal, ecosystem, station-metadata and revised seismic-catalogue products; rights, original bytes and scientific fitness remain unapproved.

**Entries:** 4

## Deltares GTSM-ERA5-E global extreme sea-level statistics v2

**Candidate ID:** `deltares.gtsm-era5-e.extreme-sea-level-statistics.v2`  
**Provider:** Deltares / Vrije Universiteit Amsterdam  
**Categories:** `coastal_flood`, `storm_surge`, `tides`, `extreme_sea_levels`, `global`  
**Spatial scope:** Global ocean coasts and GTSM model output locations; geographic coverage and coastal point spacing require asset-level audit  
**Temporal scope:** Reanalysis model period 1950-2024; Zenodo v2 released 2025-02-25  
**Resolution / granularity:** 9.7 MB NetCDF statistics ds_GTSM-ERA5-E_1950-2024_stats.nc; percentiles and 1, 2, 5, 10, 25, 50, 75 and 100-year return levels; underlying time series are a separate Climate Data Store product  
**Potential roles:** `coastal_extreme_water_level_reference`, `storm_surge_validation_challenge`, `coastal_hazard_boundary_condition_context`  
**Access hint:** `public_zenodo_statistical_file_exact_release_and_licence_review`  
**Authoritative source:** <https://zenodo.org/records/14671593>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider lists original NetCDF file and MD5 0f2b7071c6ec3585768be6cf427e6eab; no original SHA-256 independently verified here. This is reanalysis-driven model output, not observed flood extent/depth, a surge inundation map, a stochastic loss event set, or insurer exposure. Preserve tidal/total-level variable definitions, vertical datum, spatial coordinates, fitting method, uncertainty and historical ERA5 dependence. Check overlap/lineage with WRI Aqueduct coastal hazard and any already registered coastal models; access to CDS time series and redistribution/commercial rights are separate checks.

## JAXA Global Mangrove Watch annual mangrove extent v4.1.12

**Candidate ID:** `jaxa.global-mangrove-watch.extent.v4.1.12`  
**Provider:** JAXA / Aberystwyth University / Global Mangrove Watch partners  
**Categories:** `coastal_exposure_context`, `ecosystem`, `mangrove_extent`, `land_cover`, `remote_sensing`, `global`  
**Spatial scope:** Worldwide mangrove coastlines where remotely sensed mapping coverage is available  
**Temporal scope:** Annual epochs 1985-2025; v4.1.12 public release announced 2026-08-03  
**Resolution / granularity:** 30 m binary mangrove-presence GeoTIFF; 41 annual bands; EPSG:4326; DN=1 mangrove and DN=0 non-mangrove  
**Potential roles:** `coastal_nature_based_protection_context`, `ecosystem_change_covariate`, `coastal_risk_stratification`  
**Access hint:** `public_jaxa_tile_download_research_data_terms_and_attribution_review`  
**Authoritative source:** <https://www.eorc.jaxa.jp/ALOS/en/dataset/gmw_e.htm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** JAXA documents free public use under its research-data Terms of Use with specific credit rules; exact commercial derivative, redistribution and attribution scope still require review. Satellite coverage and omission/commission error vary by place and historical epoch. Binary mangrove cover is not measured surge attenuation, flood defence height, building stock, insured value or hazard intensity; do not apply protective loss discounts without independent physical and vulnerability calibration. Check overlaps with ESA WorldCover mangrove class and source-input dependence.

## WMO OSCAR/Surface global observing-station metadata

**Candidate ID:** `wmo.oscar.surface.station-metadata.2026`  
**Provider:** World Meteorological Organization / WIGOS  
**Categories:** `station_metadata`, `weather_observations`, `climate`, `validation`, `global`  
**Spatial scope:** Global WMO-member observing stations and platforms represented in OSCAR/Surface  
**Temporal scope:** Continuously updated station metadata; research snapshot to be pinned in 2026  
**Resolution / granularity:** Station and instrument capability/variable metadata keyed by WIGOS Station Identifier; live registry with no frozen dataset release here  
**Potential roles:** `weather_station_identity_crosswalk`, `observing_network_coverage_audit`, `event_observation_quality_context`  
**Access hint:** `official_wmo_metadata_portal_api_protocol_terms_and_snapshot_review`  
**Authoritative source:** <https://wmo.int/activities/global-observing-system-gos/global-observing-system-gos>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official WMO documentation identifies OSCAR/Surface as the authoritative station/platform observation-capability metadata registry, not the underlying wind, rain or temperature observation time series. Before retrieval pin API/version, lawful allowed request, WIGOS ID normalization, station effective date, relocation history and licence. Exclude personal/contact fields and disallow unrestricted bulk harvest. Do not infer spatial observation coverage or measured extremes from registration alone; assess correspondence with NOAA GHCN and national networks.

## ISC-GEM Global Instrumental Earthquake Catalogue v13.0

**Candidate ID:** `isc-gem.global-instrumental-earthquake-catalogue.v13.0`  
**Provider:** International Seismological Centre / GEM Foundation  
**Categories:** `earthquake`, `event_catalogue`, `seismicity`, `validation`, `global`  
**Spatial scope:** Global instrumental earthquake catalogue with magnitude- and epoch-dependent completeness  
**Temporal scope:** Version 13.0 released 2026-10-21; includes revised historical earthquakes and data through the end of 2022  
**Resolution / granularity:** Provider CSV main and supplementary catalogues; historical reassessment of 2,762 events in 1940-1963, with 1,070 newly listed, and 1,755 events at Mw down to 5.0 for 2022  
**Potential roles:** `global_earthquake_event_validation`, `seismicity_rate_research`, `catalogue_version_comparison`  
**Access hint:** `public_provider_csv_download_cc_by_sa_3_0_and_exact_asset_hash_review`  
**Authoritative source:** <https://www.isc.ac.uk/iscgem/download.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Supersedes existing non-admission candidate isc-gem.global-instrumental-earthquake-catalogue.v12.1; preserve both identities and compare original event IDs/relocations/magnitude uncertainties before an event-table version switch. Provider states CC BY-SA 3.0; commercial deployment, derived databases and redistribution require specific ShareAlike/legal review. A magnitude- and region-dependent earthquake catalogue is not an occurrence-rate model, complete small-event set, ground-motion field or insured loss. No provider bytes acquired or SHA-256 verified in this contribution.
