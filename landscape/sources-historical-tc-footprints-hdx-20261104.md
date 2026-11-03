<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-historical-tc-footprints-hdx-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-historical-tc-footprints-hdx-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission original-source discovery for historical event-based tropical cyclone wind footprint challenges and separately aggregated CLIMADA-on-HDX hazard exports. The sources have different physical/event semantics and are not approved model inputs, downloads, insurer exposures or loss records.

**Entries:** 2

## Willis Research Network global historical tropical cyclone wind footprints (Figshare collection v1)

**Candidate ID:** `global.wrn.historical-tc-wind-footprints.figshare-v1`  
**Provider:** Willis Research Network / James Done and coauthors via Figshare  
**Categories:** `tropical_cyclone`, `windstorm`, `historical_events`, `modelled_footprints`, `validation`  
**Spatial scope:** Global landfalling and selected near-miss tropical cyclones with regional historical-coverage differences  
**Temporal scope:** Figshare collection version 1 published 2022-02-17; historical storms through 2019; basin start dates depend on available input track and radius-of-maximum-wind observations  
**Resolution / granularity:** 1,046 modelled historical cyclone footprints; storm-lifetime maximum one-minute-average 10-m sustained wind in m/s on lat/lon grids at approximately 3 km globally and 4 km for Caribbean and US regions; source describes 17 regional gzipped TAR archives nested inside a parent TAR  
**Potential roles:** `historical_cyclone_wind_footprint_model_challenge`, `event_identity_and_ibtracs_lineage_crosswalk`, `storm_landfall_wind_footprint_sensitivity_validation`  
**Access hint:** `public_figshare_collection_v1_metadata_original_item_and_file_licence_hash_inventory_unverified`  
**Authoritative source:** <https://figshare.com/collections/Willis_Research_Network_Global_Tropical_Cyclone_Wind_Footprint_Dataset/5843453>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original Figshare collection DOI 10.6084/m9.figshare.c.5843453.v1 describes modelled Willoughby/Kepert-Wang wind fields informed by historical Extended Best Track/JTWC and IBTrACS lineage, including a 1.225 urban wind-speed adjustment. A footprint is a lifetime peak sustained wind envelope, NOT a gust, time-series event track, measured wind observation, insured loss, complete set of cyclones or stochastic annual-frequency catalogue. Missing storms can result from missing rmax observations. Collection-level metadata does not establish each original item/asset licence, stable checksum, event naming convention, file count, or safe commercial reuse. No source file, metadata API response, model-input artefact or byte hash was acquired. Original full-dataset parent-TAR is the distinct Figshare dataset article DOI 10.6084/m9.figshare.19178426.v1 (collection DOI is not itself the archived data file). The underlying 2020 method paper describes 714 modeled storms, while this later 2022 collection states 1,046: preserve collection/release vintage, do not merge or silently equate the counts.

## ETH CLIMADA tropical cyclone country and admin-level hazard CSV exports on HDX

**Candidate ID:** `eth.climada.hdx.tc-hazard-country-csv.2025`  
**Provider:** ETH Zurich Weather and Climate Risks / UN OCHA HDX exporter  
**Categories:** `tropical_cyclone`, `windstorm`, `hazard`, `historical_events`, `country_grids`, `aggregation`, `validation`  
**Spatial scope:** Selected humanitarian-response countries with country 150-arcsecond raster-like point grids and administrative summaries; not uniformly global building-level coverage  
**Temporal scope:** HDX tropical-cyclone product catalogued with historical coverage 1980-01-02 through 2020-12-25; HDX page last modified 2025-09-06; actual temporal meaning is resource and indicator specific  
**Resolution / granularity:** 35 reported HDX resources, typically about 4 km at the equator; country-level gridded CSV, admin1 summary CSV, and where available admin-level event-date time-series summary, with second-row HXL tags. Values and aggregation semantics (sum/max) differ by indicator and resource  
**Potential roles:** `cross_country_tc_wind_hazard_baseline_comparison`, `event_date_and_administrative_impact_reconciliation`, `climada_model_output_and_hdx_export_lineage_audit`  
**Access hint:** `public_hdx_csv_cc_by_dataset_notice_upstream_and_per_resource_rights_versions_and_exporter_private_boundary_review`  
**Authoritative source:** <https://data.humdata.org/dataset/climada-tropical-cyclone-dataset>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official HDX product declares CC BY 4.0, but exact resource and upstream dataset rights, file vintage and attribution must be checked. OCHA exporter source at https://github.com/OCHA-DAP/hdx-scraper-climada documents CSV fields and HXL tag row, and its build uses a private UNMAP boundary dataset; do not copy or assume rights in those upstream boundaries. The CSV export may contain grids, admin summaries or event_date values but no validated globally unique event IDs, common stochastic event catalogue, annual frequency or insured-loss mapping. Data last dated 2020 cannot represent current hazard monitoring. No original HDX CSV bytes, file checksums or live retrieval response were acquired.
