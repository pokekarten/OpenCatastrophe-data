<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-event-geocoding-infra-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-event-geocoding-infra-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery from Exa and authoritative provider pages of five globally relevant event geocoding, impact reporting and US infrastructure/Storm Events derivatives; no dataset or insurer model input is approved.

**Entries:** 5

## NASA SEDAC Geocoded Disasters (GDIS) v1.00

**Candidate ID:** `nasa.sedac.gdis.v1.00`  
**Provider:** NASA SEDAC / Rosvold and Buhaug  
**Categories:** `multi_peril`, `historical_disasters`, `event_geocoding`, `administrative_areas`, `validation`  
**Spatial scope:** Global geocodable EM-DAT event locations, with variable national and subnational administrative coverage  
**Temporal scope:** 1960-2018 historic events (dataset released 2021)  
**Resolution / granularity:** 39,953 geocoded locations associated with 9,924 disasters; GADM v3.6 administrative polygons and centroids, generally Admin1 and at best Admin3  
**Potential roles:** `historical_disaster_location_crosswalk`, `event_region_validation_challenge`, `independent_geometry_method_comparison`  
**Access hint:** `NASA_SEDAC_catalogue_CSV_GeoPackage_GDB_RData_Earthdata_access_and_upstream_rights_review`  
**Authoritative source:** <https://www.earthdata.nasa.gov/data/catalog/sedac-ciesin-sedac-pend-gdis-1.00>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GDIS adds location geometries to selected EM-DAT events, not measured flood/wind/quake intensity footprints or insured losses. Geometry of an affected administrative unit must not be treated as a physically affected perimeter. EM-DAT/GADM lineage means GDIS is not independent loss observation; country-specific coverage, access registration, source data rights and snapshot checks remain to be reviewed.

## LLM-GeoDis global EM-DAT event geocoding dataset (2025)

**Candidate ID:** `emdat.llm-geodis.2025`  
**Provider:** EM-DAT geocoding research / Zenodo (Ronco et al.)  
**Categories:** `multi_peril`, `historical_disasters`, `event_geocoding`, `nlp_derived`, `validation`  
**Spatial scope:** Global EM-DAT events with reported locality descriptions and GADM/OSM/Wikidata georeferences  
**Temporal scope:** 2000-2024 EM-DAT events, deposited 2025  
**Resolution / granularity:** 14,215 events and 17,948 unique geocoded locations; administrative unit geometries, extracted locality evidence and location reliability measures; five compressed dataset parts  
**Potential roles:** `gdis_emdat_event_geometry_comparison`, `historical_event_location_confidence`, `subnational_event_exposure_overlay_challenge`  
**Access hint:** `public_Zenodo_multifile_dataset_large_archive_rights_and_upstream_EMDAT_GADM_review_before_acquisition`  
**Authoritative source:** <https://zenodo.org/records/17544932>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** LLM-assisted geoparsing of EM-DAT text is neither independent event occurrence evidence nor a measured hazard polygon or insurer loss. Some locations are inferred or ambiguous. Preserve original EM-DAT DisNo, algorithm/version, GADM version, uncertainty, provider release and source lineage. About 30 GB expanded scope is documented; no download or license clearance is claimed. Reproducibility code at github.com/em-dat/emdat_geocoding, related Zenodo code record 17544931.

## Wikimpacts global climate impact database v1.0.final

**Candidate ID:** `vub.hydr.wikimpacts.v1.0.final`  
**Provider:** Bolin Centre / VUB-HYDR and research collaborators  
**Categories:** `climate_extremes`, `historical_impacts`, `reported_damage`, `subnational_validation`, `nlp_derived`  
**Spatial scope:** Global historical disasters represented in selected Wikipedia articles; uneven geographic and disaster-type coverage  
**Temporal scope:** Research release 2026-04-05; records from 1034-2024  
**Resolution / granularity:** 2,726 event records and 32,343 subnational impact records in SQLite database, with reported damage and impact ranges and event/locality metadata  
**Potential roles:** `noncommercial_historical_impact_comparison`, `reported_event_damage_cross_reference`, `reporting_bias_and_uncertainty_research`  
**Access hint:** `open_research_SQLite_CC_BY_NC_SA_4_0_explicit_noncommercial_gate_no_insurer_production_reuse`  
**Authoritative source:** <https://doi.org/10.17043/li-2025-wikimpacts-1.0.final>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official final release is CC BY-NC-SA 4.0: commercial insurance reuse or redistribution is NOT authorized by public download; preserve a hard commercial-rights blocker. Wikipedia/LLM extraction, event selection, uncertain damage units and estimates prevent use as independent insured-loss truth. Do not confuse the older 2,928-event v1.0 initial release with the revised 2,726-event v1.0.final. No dataset bytes acquired.

## SeerAI Source Cooperative HIFLD archived infrastructure GeoParquet

**Candidate ID:** `seerai.hifld.archive.2025`  
**Provider:** SeerAI / Source Cooperative, republishing historical HIFLD collections  
**Categories:** `critical_infrastructure`, `exposure_context`, `united_states`, `geoparquet`, `historical_archive`  
**Spatial scope:** United States; varies strongly by underlying HIFLD collection and original publication vintage  
**Temporal scope:** Archive published 2025 after public HIFLD source portal retirement in August 2025; original layer dates differ  
**Resolution / granularity:** Individual infrastructure/thematic vector collections re-encoded as per-layer Parquet with dataset inventory and metadata  
**Potential roles:** `critical_facility_exposure_context`, `infrastructure_dependency_overlay`, `us_cat_event_service_disruption_screen`  
**Access hint:** `public_Source_Cooperative_GeoParquet_aggregate_archive_collection_by_collection_original_rights_review`  
**Authoritative source:** <https://source.coop/seerai/hifld>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Republisher describes CC BY 4.0 archive rights, but underlying source ownership, exact layer redistribution and source vintages require per-collection clearance. Discontinued original HIFLD portal prevents treating a mirror as independently maintained current data. Sensitive facilities and national-security context require additional screening. Archive attributes are not insured sums or validated occupancy/vulnerability. No source bytes imported.

## Earth Genome Source Cooperative Storm Events GeoParquet

**Candidate ID:** `earthgenome.noaa.storm-events.geoparquet.2025`  
**Provider:** Earth Genome / Internet of Water Coalition (NOAA NCEI derived)  
**Categories:** `severe_convective_weather`, `hail`, `tornado`, `flood`, `reported_damage`, `event_geocoding`, `united_states`  
**Spatial scope:** United States, selected territories and event-dependent historic coverage  
**Temporal scope:** NOAA Storm Events history from 1950 onward; Source Cooperative distribution first published 2025, update recency must be checked  
**Resolution / granularity:** More than two million NOAA-derived storm records in approximately 188 MB GeoParquet, including event_id/episode_id, date, reported property and crop damage, and representative Point geometries  
**Potential roles:** `noaa_event_id_and_episode_crosswalk`, `severe_convective_historical_loss_challenge`, `bounded_geoparquet_read_preflight`  
**Access hint:** `public_HTTP_GeoParquet_and_year_CSV_provider_rights_exact_snapshot_schema_hash_review`  
**Authoritative source:** <https://source.coop/earthgenome/storm-events-db>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is a downstream cleaned/reprojected NOAA NCEI Storm Events derivative, not an independent observed loss dataset. Many point locations are first reported event coordinates or synthetic county/zone centroids and do NOT represent physical storm footprints; some are null. Property and crop damages are reported economic estimates, never observed insured losses. Preserve original NOAA event_id, episode_id and source version, and verify exact release snapshot, freshness, attribution and producer terms before ingest.
