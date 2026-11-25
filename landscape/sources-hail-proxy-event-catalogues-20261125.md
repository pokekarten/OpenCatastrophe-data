<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-hail-proxy-event-catalogues-20261125.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-hail-proxy-event-catalogues-20261125.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-25`  
**Purpose:** Non-admission discovery and bounded sample evidence for complementary hail event and multimodal convective datasets.

**Entries:** 8

## Nixon and Allen extreme hail storm interactions dataset

**Candidate ID:** `nixon.allen.storm-interactions.hail.2008-2021`  
**Provider:** Nixon and Allen / Central Michigan University  
**Categories:** `hail`, `storm_reports`, `convective_storm`  
**Spatial scope:** USA within 90 km of a WSR-88D radar  
**Temporal scope:** Hail subset 2008-2021; combined record has other hazard years  
**Resolution / granularity:** CSV point reports and surrounding cell characteristics  
**Potential roles:** `extreme_hail_case_validation`, `storm_interaction_feature`  
**Access hint:** `public_versioned_download`  
**Authoritative source:** <https://zenodo.org/records/10672225>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Zenodo API license cc-by-4.0. Bounded original GET on 2026-11-25 https://zenodo.org/records/10672225/files/StormInteractions_HAIL.csv?download=1 yielded 48878 bytes, SHA-256 1f5d061ddee6e721bbf356ede3358dcb667f0cc0fba64991a0df3ff1440cc696 and MD5 2fc284273a32085b35fb0b3d2c4e60a2 matching provider. CSV parsed 331 data rows; observed Date, Time, Radar, Lat, Lon, Mag, SM, Sample, Mode1-4, Orientation, neighboring Cell1-5 at 00/10/20/30 minute offsets and blank spacer columns. Selected >=3 inch hail reports, not representative occurrence sample; do not infer annual rates, treat blank headers explicitly, confirm magnitude units and date/time convention from authors. No original data in Git or database; third-party report lineage and scientific independence require review.

## NOAA/CIMSS ProbSevere storm-object archive

**Candidate ID:** `noaa.cimss.probsevere.archive`  
**Provider:** NOAA / University of Wisconsin CIMSS / Iowa State archive  
**Categories:** `hail`, `lightning`, `radar`, `convective_storm`  
**Spatial scope:** Contiguous United States  
**Temporal scope:** V3 operational since August 2025; historic archive availability varies  
**Resolution / granularity:** GeoJSON storm features, nominal 2 minute cadence; ProbHail, ProbWind, ProbTor  
**Potential roles:** `multimodal_feature_reference`, `model_output_benchmark`  
**Access hint:** `public_archive_rights_unverified`  
**Authoritative source:** <https://cimss.ssec.wisc.edu/probsevere/ps/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Exact bounded GET on 2026-11-25 https://mtarchive.geol.iastate.edu/2025/12/30/mrms/ncep/ProbSevere/MRMS_PROBSEVERE_20251230_000000.json returned 18033 bytes, SHA-256 2c51ef06867fe62c8e7f3c88c0b31d55755ea185cc730a1e4adf587864a5e6c8. JSON parsed 6 features; properties include MaxFED, MaxFCD, MUCAPE, EBSHEAR, MESH, EchoTop_50, VIL, FLASH_RATE, FLASH_DENSITY, WETBULB_0C_HGT, LJA, ProbHail, ID; many values encoded as strings. Provider live directory https://mrms.ncep.noaa.gov/ProbSevere/PROBSEVERE/. Model predicts severe hail >=1 inch, not observed hail or diameter; probabilities and input predictors are dependent. CIMSS product page https://cimss.ssec.wisc.edu/severe_conv/psv3.html displays a reproduction/dissemination restriction; clarify scope and contracted upstream data rights before retention or reuse. No raw data committed or ingested.

## ProbSevere v3 models and training dataset

**Candidate ID:** `cimss.probsevere.v3.models.training`  
**Provider:** CIMSS / NOAA  
**Categories:** `hail`, `convective_storm`, `research_software`, `machine_learning`  
**Spatial scope:** Contiguous United States  
**Temporal scope:** Training archive named 2018-2023  
**Resolution / granularity:** Python pickle model and storm attribute files  
**Potential roles:** `model_architecture_reference`, `predictor_benchmark`  
**Access hint:** `public_download_untrusted_pickle`  
**Authoritative source:** <https://zenodo.org/records/10891477>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Live Zenodo metadata 2026-11-25: 7 files, 10760638082 total bytes, cc-by-4.0; hail classifier phv3_lgb_classifier.pkl 7819023 bytes, MD5 9c9b3d34b5bebda73ed0a6f92a4d50bf. Do not deserialize untrusted pickle or execute downloaded models; require trusted isolated conversion to auditable safe format, exact upstream rights review, feature and label definitions. Metadata only; no pickle downloaded.

## HIToB GOES ABI hail-associated storm polygons Brazil

**Candidate ID:** `brazil.hitob.v1`  
**Provider:** HIToB research authors  
**Categories:** `hail`, `satellite_observations`, `event_tracks`  
**Spatial scope:** Brazil hail reports; GOES-16 South American domain  
**Temporal scope:** 2018-06-05 to 2023-09-30  
**Resolution / granularity:** 2 km grid infrared cloud objects tracked with TATHU; database file  
**Potential roles:** `storm_geometry_calibration`, `southern_hemisphere_transfer`  
**Access hint:** `public_large_database_download`  
**Authoritative source:** <https://zenodo.org/records/11152458>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Paper https://pmc.ncbi.nlm.nih.gov/articles/PMC11295460/. Live Zenodo API 2026-11-25 returned cc-by-4.0 and HIToB_v1.db 6911950848 bytes, MD5 2ae0f679345d7a97c9e825692359de17. Archive not downloaded due to size; seek bounded subset or author-provided export, do not claim a byte range is a valid SQLite database. Cold cloud threshold 235 K; storms selected by hail association and cloud polygons not actual hail damage swaths. Check report bias, geometry, time and third-party report rights.

## PyFLEXTRKR global MCS tracking V3

**Candidate ID:** `pnnl.pyflextrkr.global.mcs.v3`  
**Provider:** Feng and Zhang / PNNL  
**Categories:** `convective_storm`, `satellite_observations`, `event_tracks`  
**Spatial scope:** 60 S to 60 N, global longitude  
**Temporal scope:** January 1998 to September 2025  
**Resolution / granularity:** Hourly 0.1 degree merged IR and IMERG V07B, two MCS definitions  
**Potential roles:** `global_convective_system_context`, `storm_lifecycle_prior`  
**Access hint:** `public_large_versioned_download`  
**Authoritative source:** <https://zenodo.org/records/23523604>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Live Zenodo metadata 2026-11-25: 20 files, 29569660540 bytes, cc-by-4.0. Small README 6783 bytes and checksum file 1670 bytes; smallest climatology archive 270842421 bytes. MCS definition requires spatial/temporal persistence and precipitation thresholds; misses small isolated hailstorms, excludes tracks overlapping tropical cyclones, not a hail catalogue. Read README and choose bounded region/month export before full archive acquisition; no source data downloaded.

## Dong near-global 40-year MCS database

**Candidate ID:** `dong.global.mcs.1985-2024`  
**Provider:** Wenhao Dong  
**Categories:** `convective_storm`, `satellite_observations`, `climatology`  
**Spatial scope:** Near-global geostationary IR coverage  
**Temporal scope:** 1985-2024  
**Resolution / granularity:** KFyAO tracked systems from CLAUS and NCEP/CPC brightness temperature, CSV and NetCDF  
**Potential roles:** `long_term_convective_context`, `frequency_sensitivity`  
**Access hint:** `public_large_versioned_download`  
**Authoritative source:** <https://zenodo.org/records/19634724>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Live Zenodo metadata 2026-11-25: 6 files, 15032621710 bytes, cc-by-4.0; smallest CLAUS_CSVFILE.tar.gz 218241779 bytes. Transition adjustments are latitude/season dependent; check homogeneity and storm definition, avoid double-counting overlapping source years. No direct hail intensity or isolated cell representation. No source bytes downloaded.

## IPSL TOOCAN tropical deep convective system database

**Candidate ID:** `ipsl.toocan.dcs.v2.08`  
**Provider:** Fiolleau and Roca / IPSL ESPRI  
**Categories:** `convective_storm`, `satellite_observations`, `event_tracks`  
**Spatial scope:** 40 S to 40 N, five tropical regions  
**Temporal scope:** 2012-2020  
**Resolution / granularity:** 30 minute lifecycle statistics, regional monthly NetCDF4/ASCII and segmented images  
**Potential roles:** `tropical_storm_tracking_context`, `lifecycle_and_geometry_prior`  
**Access hint:** `provider_data_portal`  
**Authoritative source:** <https://doi.org/10.14768/1be7fd53-8b81-416e-90d5-002b36b30cf8>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Paper https://doi.org/10.5194/essd-16-4021-2024. Provider page https://toocan.ipsl.fr/toocandatabase/2012-2020tropicaltoocandataset/ names CC BY 4.0 with research/publication attribution wording; confirm exact product rights and required acknowledgment before commercial use. DCS cloud shield not hail footprint; misses Germany entirely, useful tropical context only. No original sample.

## OPERA-SEVIRI-NORDLIS ML/AI fusion dataset

**Candidate ID:** `eumetsat.opera.seviri.nordlis.fusion`  
**Provider:** EUMETSAT / EUMETNET / NORDLIS / European Weather Cloud  
**Categories:** `lightning`, `radar`, `satellite_observations`, `machine_learning`  
**Spatial scope:** European OPERA/SEVIRI overlap; lightning covers Northern Europe  
**Temporal scope:** 2018-2023 per EWC bucket listing  
**Resolution / granularity:** Co-registered OPERA radar composites, SEVIRI rapid scan radiances and ground lightning in Zarr  
**Potential roles:** `multimodal_hail_feature_training`, `satellite_radar_lightning_alignment`  
**Access hint:** `european_weather_cloud_access`  
**Authoritative source:** <https://europeanweather.cloud/index.php/news/update-opera-seviri-fusion-dataset>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EWC guide https://confluence.ecmwf.int/spaces/EWCLOUDKB/pages/488063253/Using%2BEUMETSAT%2Bdata%2Bbuckets%2Blocal%2Bdata%2Bpool lists bucket opera-seviri-nordlis.composite.zarr, endpoint https://s3.r1.cloud.eumetsat.int, 2018-2023. EWC-internal credential-free access does not imply public internet access or uniform rights. OPERA data policy https://www.eumetnet.eu/data-access/data-policy/ announces CC BY 4.0 via MeteoGate for qualifying products; SEVIRI and NORDLIS terms must be checked independently. No bucket bytes tested; verify Zarr chunk layout, spatial/time alignment, coverage masks and licensing per layer. Radar composites not necessarily hail size labels.
