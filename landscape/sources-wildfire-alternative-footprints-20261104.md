<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-wildfire-alternative-footprints-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-wildfire-alternative-footprints-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission original-source discovery of alternative observed and reconstructed wildfire event perimeters, daily spread, multiagency event lists and independent validation candidates; no original dataset bytes, commercial rights, CAT model approval or portfolio loss admission.

**Entries:** 5

## NASA-led Fire Events Data Suite (FEDS) CONUS Archive 2012-2025, Zenodo October 2026

**Candidate ID:** `us.nasa.feds.conus.viirs.2026.v1`  
**Provider:** NASA GSFC / university coauthors / Zenodo  
**Categories:** `wildfire`, `viirs_active_fire`, `subdaily_event_perimeters`, `fire_behavior`, `satellite_research`  
**Spatial scope:** Contiguous United States; published CONUS data archive; original source metadata must be checked for exact coverage  
**Temporal scope:** 2012-2025 archival event coverage; Zenodo release 2026-10-02, version 1; 12-hour reconstructed fire growth intervals  
**Resolution / granularity:** VIIRS 375 m active fire derived event polygons and firelines at 12-hour intervals. Fully postprocessed large-fire fgb products cover fires above 4 km2; raw daily/parquet backing outputs are not equivalent to curated fire perimeters.  
**Potential roles:** `wildfire_subdaily_spread_challenge`, `non_mtbs_fire_event_research`, `fire_duration_hazard_candidate`, `vendor_event_polygon_benchmark`  
**Access hint:** `zenodo_record_public_but_files_RESTRICTED_20261104_needs_original_asset_access_and_terms_review`  
**Authoritative source:** <https://zenodo.org/records/22921773>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Critical access blocker: the original Zenodo 2026-10-02 v1 record advertises Files: Restricted, zero publicly downloadable bytes in the listing. Do not confuse a visible metadata page or a secondary CC BY 4.0 tag with accessible asset bytes or granted rights. Algorithm v1.4.1, Suomi-NPP VIIRS VNP14IMGML collection 2 v4, 12-hour alpha-shape reconstructions; FEDS postprocessed FGB large-fire assets (&gt;4 km2) differ materially from raw allfires/allpixels outputs (merge history not corrected). This product is not an all-fire census or independently validated insured-loss outcome. Investigate alternative authorized access, archive filename, source hash, VIIRS detection biases and multi-fire merge semantics before use.

## WUMI2026a Western US MTBS-Interagency compiled wildfire event and perimeter dataset (Dryad 2026 update)

**Candidate ID:** `us.dryad.wumi.2026a.version2`  
**Provider:** Williams / Juang / Short / Dryad  
**Categories:** `wildfire`, `multiagency_event_fusion`, `mapped_fire_perimeters`, `fire_complexes`, `historical_research`  
**Spatial scope:** Dryad WUMI2026a change log extends the 11 westernmost contiguous US states to include Texas, Oklahoma, Kansas, Nebraska, South Dakota and North Dakota (17 states). Older 2024a abstract/study-region prose still says 11; exact per-file extension and completeness need original asset validation.  
**Temporal scope:** Original WUMI2026a publisher README specifies 1984-01-01 to 2026-08-06, with the most recent year partial; prior WUMI2024a 1984-2024 is a separate version. Dryad update 2026-08-24.  
**Resolution / granularity:** Original Dryad v2026a /api/v2/versions/458442/files: WUMI2026a_final_wildfire_lists.zip 4,683,571 bytes with distinct parent-only and parent-replaced-by-subfires event lists; fire_lists.zip 26,481,076 bytes, fire_maps.zip 822,779,079 bytes, original_data.zip 100,715,033,562 bytes. Source polygon observability and adjusted area differ by file/version.  
**Potential roles:** `western_us_fire_event_census_crosscheck`, `mtbs_parent_subfire_reconciliation`, `observed_vs_synthetic_perimeter_validation`, `fire_area_source_version_holdout`  
**Access hint:** `dryad_public_versioned_files_with_2026_lineage_and_exact_license_asset_review_before_use`  
**Authoritative source:** <https://datadryad.org/dataset/doi:10.5061/dryad.63xsj3vd4>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original Dryad API version 458442 (2026-08-24) lists WUMI2026a_final_wildfire_lists.zip, 4,683,571 bytes, sha-256=8d8a59588935b832bf8e382a0c94b8a6705e6a8fa2bed161bacf1d9fe78726d0, original metadata https://datadryad.org/api/v2/versions/458442/files . This is a PUBLISHER file metadata SHA, not locally verified bytes. Its original README/changelog explicitly extends coverage beyond the original 11 western states to TX/OK/KS/NE/SD/ND, updates inputs including FPA FOD v7 and WFIGS through 2026-08-06; older abstract and study-region prose still reference 2024a/11 states. Parent-only and subfire-replacement event lists are alternative accounts of the same complex wildfire; subfire burned areas may be rescaled to parent totals, so never aggregate both or assume raw independent loss events. Publisher fireid is a composite derived from start date and rounded coordinates, not insurance event identity. Freeze exact Dryad version and bytes, verify state-level coverage, observability and upstream identity. The 2025 WUMI2024a peer-reviewed 22,234 11-state wildfires count is not a WUMI2026a population count. WUMI integrates MTBS and FPA and cannot independently validate their counts. Rights and scientific/model admission not reviewed; use the 4.68 MB list as a future permitted byte-level pilot.

## Earth Lab FIREDpy global country-level MODIS burned-area event polygons and daily perimeter products

**Candidate ID:** `global.earthlab.firedpy.country-products.2025`  
**Provider:** CU Boulder Earth Lab / Balch Fire Lab  
**Categories:** `wildfire`, `modis_burned_area`, `event_delineation`, `global_country_products`, `daily_perimeters`  
**Spatial scope:** Multiple global country and regional datasets; coverage differs by country/version and MODIS processing mode  
**Temporal scope:** FIREDpy available country products span approximately 2000/2001-2021 to 2024/2025 depending on country and version; never assume global uniform year coverage  
**Resolution / granularity:** MODIS MCD64A1 burn-area pixels grouped by space-time window into final event and optional daily perimeter GeoPackage/shapefile files; exact space-time thresholds and CRS vary by version.  
**Potential roles:** `non_mtbs_mapped_fire_holdout`, `global_event_delineation_pilot`, `wildfire_spatiotemporal_growth_research`, `cross_sensor_event_identity_challenge`  
**Access hint:** `public_software_and_mixed_cu_scholar_product_access_newer_unpublished_versions_require_creator_permission`  
**Authoritative source:** <https://github.com/earthlab/firedpy>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** FIREDpy 1.0, 2.0 (2024f) and 2.1 (2025var) differ in algorithm thresholds and outputs. Original GitHub README states newer unpublished versions/data require PI Jennifer Balch permission before publications/presentations/public dissemination; do NOT treat software open-source license as permission to redistribute newly generated country data. README warns some Fall 2021 datasets can have a half-pixel shift or missing CRS. Keep publisher exact file, vintage, coverage, original DOI/asset bytes, CRS and suspected geometric shift in review. MODIS burned pixels may combine prescribed fires, crop burning, fires and multiple fire detections; not automatically independent of other MCD64A1-derived catalogues.

## NASA ORNL DAAC integrated Wildfire Event Dataset (iWED) v1, 1992-2021

**Candidate ID:** `us.nasa.ornl.iwed.v1.2452`  
**Provider:** NASA ORNL Distributed Active Archive Center / Kasischke and colleagues  
**Categories:** `wildfire`, `incident_event_catalogue`, `multiagency_source_consolidation`, `historical_fire_size`, `event_quality_review`  
**Spatial scope:** United States, contiguous states plus Alaska as represented by NASA's original source description; state-level event geography in this version  
**Temporal scope:** 1992-2021, published 2026-07-31 per NASA Earthdata catalogue; version 1  
**Resolution / granularity:** Three CSV files (wildfire events, event notes and source list); only state geographic labels, no individual latitude/longitude in v1; selection wildfire events &gt;=100 ha.  
**Potential roles:** `us_wildfire_event_frequency_holdout`, `source_lineage_and_agency_crosswalk`, `historical_fire_size_comparison`, `mtbs_fpa_overlap_quality_review`  
**Access hint:** `nasa_earthdata_open_citation_and_metadata_zip_on_protected_endpoint_may_require_earthdata_login`  
**Authoritative source:** <https://doi.org/10.3334/ORNLDAAC/2452>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NASA Earthdata catalogue says freely shared without restriction, but the zipped data distribution resolves via a protected Earthdata route that may require sign-in; no authenticated asset fetch has been completed. v1 does not include individual event geocoordinates and therefore cannot be directly intersected with buildings; retain state-level use only. This integrated dataset draws from agency reports and MTBS; it is not independent validation of FPA-FOD or MTBS counts. Freeze DOI/version, exact three CSV hashes and data-source attribution plus missing/censoring patterns before any model use.

## European Commission JRC GWIS GlobFire v2 daily fire-event perimeters (Earth Engine)

**Candidate ID:** `global.ec.jrc.globfire.v2.daily.2001-2020`  
**Provider:** European Commission Joint Research Centre / Global Wildfire Information System  
**Categories:** `wildfire`, `global_fire_perimeters`, `daily_event_patches`, `modis_burned_area`, `historical_satellite`  
**Spatial scope:** Global satellite-derived coverage subject to MODIS land, cloud, resolution and detection limitations  
**Temporal scope:** 2001-01-01 to 2021-01-01 service window (nominal fire events during 2001-2020); fixed Earth Engine collection identity v2  
**Resolution / granularity:** MODIS MCD64A1 burned-area-derived daily fire event geometries and source-local event IDs, accessible via Google Earth Engine dataset JRC/GWIS/GlobFire/v2/DailyPerimeters.  
**Potential roles:** `global_wildfire_event_perimeter_context`, `historical_fire_growth_crosscheck`, `country_peril_source_coverage_pilot`, `daily_event_identity_research`  
**Access hint:** `google_earth_engine_collection_and_cc_by_4_dataset_page_require_platform_entitlements_and_original_license_provenance_review`  
**Authoritative source:** <https://developers.google.com/earth-engine/datasets/catalog/JRC_GWIS_GlobFire_v2_DailyPerimeters>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official dataset page lists CC BY 4.0 and daily perimeters through Jan 2021 but that does not itself grant any project-specific admission. Derived from MODIS MCD64A1, like FIREDpy, so the two sources share observational ancestry and cannot be counted as independent evidence. Verify the Earth Engine account/access path, event-ID uniqueness across years and continents, difference between final and daily perimeters, fire-event merge semantics and historical latency. Cloud/radiometric detection limits can miss small, short or low-severity events. Not equivalent to reported FPA ignitions, CAL FIRE destroyed buildings or insured claims.
