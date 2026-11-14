<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-windstorm-europe-tc-official-20261114.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-windstorm-europe-tc-official-20261114.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-14`  
**Purpose:** Non-admission source discovery for independent European wind observation challenges and observed Atlantic tropical cyclone best-track comparison. Provider pages and rights labels have been inspected; no original observation files or authenticated API data were acquired or admitted.

**Entries:** 5

## Meteo-France historical hourly base climate station observations

**Candidate ID:** `fr.meteofrance.hourly-climate-stations.openlicence-v2`  
**Provider:** Meteo-France via data.gouv.fr  
**Categories:** `windstorm`, `station_observations`, `hourly_weather`, `historical_validation`  
**Spatial scope:** Metropolitan France and French overseas departments; station coverage varies by site and observation history  
**Temporal scope:** Station histories since commissioning; department/period partitioned historic hourly bundles, with updates across decades and recent years  
**Resolution / granularity:** Department-and-period compressed CSV bundles with hourly climatologically quality-controlled observations; variable-specific gust presence, sensor height and unit definitions must be established from exact field dictionary  
**Potential roles:** `cross_border_europe_gust_station_holdout`, `ciara_and_kyrill_weather_counter_challenge`, `station_model_time_alignment`  
**Access hint:** `public_data_gouv_catalogue_open_licence_2_0_csv_gz_original_resource_bytes_unverified`  
**Authoritative source:** <https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-horaires>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official data.gouv.fr product labels Licence Ouverte / Open Licence v2.0. On 2026-11-14 its public dataset JSON metadata endpoint https://www.data.gouv.fr/api/1/datasets/donnees-climatologiques-de-base-horaires/ returned JSON in an independent web read; this was catalogue metadata ONLY, not a resource or gust measurement. Mainland timestamps are UTC; overseas timestamps use FU and require explicit time convention. Before model use select one department/time resource, pin resource URL/version/SHA-256, check field dictionary (gust versus mean wind, averaging and height), station relocation/QC and source licence attribution. This is independent measured-station challenge evidence, not an annual event catalogue or damage data. Follow-up execution in draft PR #1590: one original public department 75/2020-2024 hourly gzip was fetched and parsed with 261860 source rows, six stations and 72467 quality-1 three-second gust entries. Exact original SHA-256 and source-specific NO-admission/uncertainty boundaries are in docs/research/meteofrance-hourly-original-3second-gust-preflight-v0.md. No original source bytes were committed.

## KNMI validated hourly Netherlands in-situ observations via EDR

**Candidate ID:** `nl.knmi.kdp.hourly-validated-edr.v1`  
**Provider:** Royal Netherlands Meteorological Institute (KNMI)  
**Categories:** `windstorm`, `station_observations`, `hourly_weather`, `edr_api`, `historical_validation`  
**Spatial scope:** Netherlands; station network may include sea platforms, airports and BES islands, which are not continental European exposure  
**Temporal scope:** Variable and station dependent; official station aggregation lineage includes hourly observations from 1951, but exact EDR validated collection interval must be queried  
**Resolution / granularity:** OGC Environmental Data Retrieval location/time query with CoverageJSON or GeoJSON; target collection hourly-in-situ-meteorological-observations-validated; variables and wind-gust semantics require collection metadata  
**Potential roles:** `north_sea_cross_border_storm_validation`, `wind_station_era5_independent_challenge`, `hourly_event_utc_alignment`  
**Access hint:** `open_data_registered_edr_api_key_required_dataset_specific_licence_review_and_no_original_sample`  
**Authoritative source:** <https://developer.dataplatform.knmi.nl/edr-api>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official KNMI EDR documentation explicitly lists validated hourly in-situ collection and requires an account-issued EDR API key. No API key, live collection response, data sample or station observations were acquired in this review. Do NOT place API keys in Git, do NOT assume that a documented collection is an executed API test, and verify the requested parameter-name/wind-gust definition before comparison. Distinguish validated historical hourly observations from near-real-time 10-minute collections and from modeled WINS50.

## Met Office MIDAS Open UK hourly land observations v202607

**Candidate ID:** `uk.metoffice.midas-open-hourly.v202607`  
**Provider:** UK Met Office / CEDA  
**Categories:** `windstorm`, `station_observations`, `hourly_weather`, `historical_validation`  
**Spatial scope:** UK mainland land observing stations in MIDAS Open subset, excluding full restricted MIDAS and METAR messages  
**Temporal scope:** 1875-2025; citable v202607 published 2026-07-23  
**Resolution / granularity:** Hourly wind speed and direction plus other station meteorology; BADC-CSV, approximately 54,590 files and 34 GB in the official product; gust-variable coverage must be verified at original-file level  
**Potential roles:** `british_isles_windstorm_holdout`, `kyrill_ciara_station_validation`, `source_instrument_and_qc_change_challenge`  
**Access hint:** `ceda_registration_required_open_government_licence_v3_attribution_and_citation_original_bytes_unverified`  
**Authoritative source:** <https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CEDA lists Permitted Use Any, UK Open Government Licence 3, registration required for data access, BADC-CSV, 2026-07-23 release DOI 10.5285/d04207b551674c07801b7d4e6d883e50. This open subset excludes METAR and differs from restricted MIDAS; preserve src_id 99999 commissioning-trial exclusion, QC flags and site changes. Catalogue wind speed/direction does NOT prove an original station gust series or source averaging duration. Check exact source file and station before wind-gust calibration; no asset was downloaded or hashed here.

## ECA&amp;D non-blended European station observations via MeteoGate RODEO

**Candidate ID:** `eu.ecad.meteogate.nonblended-stations.2026`  
**Provider:** European Climate Assessment and Dataset (ECA&amp;D) / KNMI / MeteoGate  
**Categories:** `windstorm`, `station_observations`, `daily_weather`, `api_access`, `noncommercial_research`  
**Spatial scope:** Europe and Mediterranean network; station and variable availability vary by contributing provider  
**Temporal scope:** ECA&amp;D daily historic station series; MeteoGate non-blended endpoint announced June 2026; station coverage/vintage require per-query checks  
**Resolution / granularity:** Non-blended daily station observation location/time queries, offered in JSON or NetCDF; ECA&amp;D dictionary includes wind speed, wind gust and direction but per-station coverage must be checked  
**Potential roles:** `europe_wide_independent_station_coverage_screen`, `cross_country_daily_gust_index_validation`, `storm_event_station_completeness_diagnostics`  
**Access hint:** `official_meteogate_api_announced_nonblended_data_noncommercial_research_and_education_only_rights_permission_required_for_insurance_use`  
**Authoritative source:** <https://www.ecad.eu/dailydata/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ECA&amp;D announced a June 2026 MeteoGate RODEO API route for non-blended station data. Public ECA&amp;D station observations and E-OBS state strictly non-commercial research/education use under the published ECA&amp;D data policy, while some station series are not downloadable. A new API endpoint does NOT remove source-specific restrictions. No authenticated MeteoGate API probe or original data bytes were acquired; prohibit commercial insurance-model admission without explicit permission. Do not label ECA&amp;D or E-OBS as unrestricted, and do not confuse station gusts with gridded daily mean wind.

## NOAA NHC Atlantic HURDAT2 best-track revision September 2026

**Candidate ID:** `us.noaa.nhc.hurdat2.atlantic.2026-09`  
**Provider:** NOAA National Hurricane Center  
**Categories:** `tropical_cyclone`, `best_track`, `observed_events`, `atlantic_basin`, `validation`  
**Spatial scope:** Atlantic tropical and subtropical cyclone basin; not comprehensive European extratropical winter storms  
**Temporal scope:** Historical Atlantic HURDAT2 1851-2025; September 2026 official archive revisions of 1971-1975 storms  
**Resolution / granularity:** Public text best-track archive, roughly six-hour positions, maximum sustained wind and central pressure, with wind radii from 2004; storm IDs and non-synoptic special records need original-format parsing  
**Potential roles:** `atlantic_tropical_track_crosscheck`, `ibtracs_atlantic_agency_consistency_challenge`, `historical_storm_intensity_and_revision_provenance`  
**Access hint:** `official_public_nhc_text_archive_exact_revision_sha256_and_reuse_notice_not_reviewed`  
**Authoritative source:** <https://www.nhc.noaa.gov/data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NHC archive describes Atlantic HURDAT2 1851-2025 and 2026 September historical revisions; the official page describes six-hour locations/winds/pressure and radii since 2004. This is an observational best-track product, not wind gust footprints, 72-hour European extratropical event fields, tropical cyclone losses or synthetic annual tracks. IBTrACS may incorporate NHC/HURDAT track information: do not count agreement as independent validation or double-count individual storms. The exact 2026 revision filename, licence/reuse notice and original byte SHA-256 are NOT validated by this entry.
