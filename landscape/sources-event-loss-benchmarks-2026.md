<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-event-loss-benchmarks-2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-event-loss-benchmarks-2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-10-31`  
**Purpose:** Non-admission discovery registry of event-level CAT observations, empirical-loss references, exposure values and restricted data candidates for future scientific evaluation.

**Entries:** 8

## HANZE Historical Flood Impacts Europe v3.0.2 beta

**Candidate ID:** `hanze.historical-flood-impacts.v3.0.2-beta`  
**Provider:** Dominik Paprotny / Potsdam Institute for Climate Impact Research  
**Categories:** `flood`, `historical_loss`, `event_catalogue`, `validation`  
**Spatial scope:** 42 European countries, mostly subnational NUTS3 and UK ITL3 regions, vintage 2024  
**Temporal scope:** 1870-2025, 2780 events; version v3.0.2 beta published 2026-10-30  
**Resolution / granularity:** UTF-8 event/reference CSV tables and NUTS/ITL 2024 regional GIS shapefile ZIP  
**Potential roles:** `historical_flood_validation`, `economic_loss_reference`, `event_geography_validation`  
**Access hint:** `public_download_cc_by_4.0_declared_pending_review`  
**Authoritative source:** <https://zenodo.org/records/23670886>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Historical economic impacts in original currencies and 2025 EUR, NOT insured loss, exact hazard footprint or policy claims. Missing impacts are not zero; preserve unique event IDs and source revision. Version v3.0.2 beta supersedes previous candidate v3.0.1 beta. Pin full CSV, region vintage and per-file SHA before scientific use.

## Residential Exposure to Natural Hazards in Europe v2025

**Candidate ID:** `paprotny.residential-exposure-europe.v2025`  
**Provider:** Dominik Paprotny / Potsdam Institute for Climate Impact Research  
**Categories:** `residential_exposure`, `valuation`, `replacement_cost`, `synthetic_portfolio`  
**Spatial scope:** 33 European countries, national averages only  
**Temporal scope:** Annual 2000-2024; published 2025-12-05, version v2025  
**Resolution / granularity:** CSV containing 18 indicators with country code and year; XLSX and methodological PDF; building/contents replacement values per square metre  
**Potential roles:** `synthetic_residential_valuation`, `exposure_benchmark`, `valuation_sensitivity`  
**Access hint:** `public_download_cc_by_4.0_declared_pending_review`  
**Authoritative source:** <https://zenodo.org/records/17828544>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A country/year mean per square metre does not identify an individual building, floor area, coverage, TIV or insured loss. Keep separate structure and contents categories, nominal versus real price basis and currency/year. Series revised versus v2022; freeze exact v2025 bytes and independent floor-space assumptions.

## EURADHAIL European Radar Hail Occurrence 2013-2021

**Candidate ID:** `ethz.euradhail.2013-2021`  
**Provider:** ETH Zurich / Ruoyi Cui and Iris Thurnherr  
**Categories:** `hail`, `radar`, `observation`, `validation`  
**Spatial scope:** Europe with heterogeneous OPERA network coverage, including gaps and terrain artefacts  
**Temporal scope:** 2013-2021; released 2024-06-13  
**Resolution / granularity:** Monthly tar.gz archives of hourly NetCDF binary hail masks (0/1); 2 km Lambert azimuthal equal-area grid  
**Potential roles:** `hail_occurrence_validation`, `peril_footprint_benchmark`, `radar_coverage_audit`  
**Access hint:** `open_access_cc_by_4.0_declared_pending_review`  
**Authoritative source:** <https://www.research-collection.ethz.ch/handle/20.500.11850/701924>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Binary radar-inferred hail occurrence, NOT hail diameter or ground truth. ETH README documents 53 dBZ inference threshold and incomplete geographic coverage; portal displays review state. Check individual file rights, projection, artefacts, unit interpretation and holdout independence before use.

## CLIMK-WINDS Extreme European Winter Storm Footprints v2

**Candidate ID:** `climk.winds.storm-footprints.v2`  
**Provider:** Clare Flynn and coauthors / Zenodo  
**Categories:** `windstorm`, `footprint`, `reanalysis`, `validation`  
**Spatial scope:** Europe  
**Temporal scope:** 1995-2015 winter storms; version 2 published 2025-04-29  
**Resolution / granularity:** Four NetCDF files, each selecting 50 extreme events from ERA5, COSMO-REA6, CCLM_ERA5_EUR-11 and CCLM_ERA5_CEU-3  
**Potential roles:** `wind_footprint_benchmark`, `model_intercomparison`, `storm_validation`  
**Access hint:** `public_download_cc_by_4.0_declared_pending_review`  
**Authoritative source:** <https://zenodo.org/records/15305753>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Follow-up verified provider bytes in Linux on 2026-11-07: all four CLIMK NetCDFs were obtained outside Git, including COSMO-REA6 (83,807,744 bytes; provider MD5 and SHA-256 verified). Kyrill (2007-01-18) from the four source-specific CLIMK selections and both XWS representations was mapped to one fictional 7,998-interest German building book and executed together through Oasis. Twelve aggregate gross/insured comparisons and 95,976 conditional per-interest checks passed. Separately, raw NetCDF rosters contain 28 storm names in all four CLIMK 50-event files and 78 distinct names overall, with only 19 exact name/date matches; four separate Oasis runs evaluated those exact matches, passing 152 aggregate checks and 1,215,696 conditional per-interest checks with zero failures. Flynn et al. (2025) state 29 common storms and 76 unique events; Table 2 has six date-string disagreements and malformed CEU-3 Mike-Niklas date 2015-30-30. The paper reports Gunter as 2015-01-10 in all four products, but acquired CEU-3 v2 contains GUNTER at 2005-01-10. Of the 29 paper common rows, u19950216 occurs only in ERA5 and CEU-3; 28 rows are present in all four files allowing for the paper's spelling/alias variants. Raw name frequencies are 20 single-source, 8 in two or three sources, and 28 in all four. The paper prose says 15 single-source storms but its source-wise list sums to 16 and omits CEU-3 GERDA-HANNE; full roster tally does not reconcile with the published prose. The referenced Top50Storms_All_Summary.csv is absent from Zenodo v2 and the article-hosted CSV URL returns 404, so full source-by-source reconciliation remains unresolved; no dates or names were corrected or fuzzy-matched. The 19-event Oasis results exclude Gunter and remain valid. These are same-storm/source software-path checks, not actual loss validation, calibration or annual-frequency evidence. CLIMK regional models are alternatives, not unmasked replacements; raw source date disagreements were not fuzzy-matched. XWS rawFootUncon is decontaminated/uncontaminated. Check event identities, wind windows, units, CRS, selection bias and independence from C3S/ERA5 before benchmark claims. Exact public download/model receipts are summarized in docs/research/public-wind-source-followup-2026-11-07.md. Rights, scientific review and admission statuses remain not_reviewed/not_admitted.

## Global Fire Atlas v20260408

**Candidate ID:** `global.fire-atlas.v20260408`  
**Provider:** Niels Andela and Matthew William Jones / Zenodo  
**Categories:** `wildfire`, `burned_area`, `event_perimeter`, `observation`  
**Spatial scope:** Global MODIS coverage  
**Temporal scope:** 2002-February 2026, locally defined fire seasons; published 2026-07-22  
**Resolution / granularity:** WGS84 ignition/perimeter shapefiles; 500 m daily spread/burn raster data in MODIS sinusoidal projection  
**Potential roles:** `wildfire_event_validation`, `burned_area_footprints`, `fire_spread_research`  
**Access hint:** `public_dataset_record_licence_scope_pending_review`  
**Authoritative source:** <https://zenodo.org/records/17669692>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher explicitly warns NOT to append newer-year files to previous releases because per-tile whole-series model parameters change. File year denotes local fire season, NOT calendar year; recent 2025-2026 fire seasons may be incomplete. Burned area does not imply insured loss or measured asset damage.

## EFFIS Burnt Area and Fire Severity Services

**Candidate ID:** `ec-jrc.effis.burnt-area-services`  
**Provider:** European Commission JRC / European Forest Fire Information System  
**Categories:** `wildfire`, `burned_area`, `remote_sensing`, `monitoring`  
**Spatial scope:** Europe and EFFIS surrounding monitoring domain  
**Temporal scope:** Time-indexed operational products; provider exposes severity imagery for multiple years including 2018-2025  
**Resolution / granularity:** Public WMS with TIME parameter, burnt-area monitoring and severity image/TIFF data; country aggregate spreadsheets  
**Potential roles:** `wildfire_extent_validation`, `fire_severity_reference`, `monitoring_context`  
**Access hint:** `public_wms_download_provider_data_licence_review_required`  
**Authoritative source:** <https://forest-fire.emergency.copernicus.eu/downloads-instructions>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from the already catalogued GWIS fire-danger FORECAST. WMS map pixels and country statistics are not automatically lossless event vectors, intensity fields or property-level losses. Pin exact layer, legend, date, returned media/CRS, licence and data export method before use.

## MeteoSwiss Operational Hail POH/MESHS STAC

**Candidate ID:** `meteoswiss.operational-hail-radar-stac`  
**Provider:** Federal Office of Meteorology and Climatology MeteoSwiss  
**Categories:** `hail`, `radar`, `near_real_time`, `weather`  
**Spatial scope:** Swiss operational radar coverage, LV95 EPSG:2056  
**Temporal scope:** 1 April-30 September; public rolling last 14 days; archives available by request  
**Resolution / granularity:** FSDI STAC collection ch.meteoschweiz.ogd-radar-hail; 5-minute ODIM HDF5; POH percent; MESHS millimetres  
**Potential roles:** `hail_intensity_proxy`, `near_real_time_hazard_validation`, `hail_footprint_validation`  
**Access hint:** `public_stac_last_14_days_older_archive_on_request`  
**Authoritative source:** <https://opendatadocs.meteoswiss.ch/d-radar-data/d3-hail-radar-products>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Different operational access product from registered MeteoSwiss national hail climatology. POH probability and MESHS severe-hail size are not EURADHAIL binary hail observations. 24-hour aggregate files coexist with 5-minute UTC files; protect temporal and spatial semantics and attribution. No long-term feed assumed.

## HOWAS 21 Flood Damage Database

**Candidate ID:** `gfz.howas21.flood-damage-database`  
**Provider:** GFZ Helmholtz Centre for Geosciences  
**Categories:** `flood`, `damage_observation`, `vulnerability`, `restricted_data`  
**Spatial scope:** Germany and Austria; site locations generalised for privacy  
**Temporal scope:** Historical reported flood damage observations; exact scope determined by approved access  
**Resolution / granularity:** Registered filtered Excel downloads with anonymised/generalised damage records  
**Potential roles:** `flood_damage_function_research`, `vulnerability_validation`, `empirical_holdout_if_licensed`  
**Access hint:** `registration_and_signed_data_agreement_required`  
**Authoritative source:** <https://howas21.gfz.de/usage.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NOT openly reusable raw data. External scientific/non-commercial users may receive restricted access only after registration and signed agreement; data providers have separate permissions. Never scrape, publish raw rows, infer exact addresses or train/calibrate proprietary/production models without explicit terms.
