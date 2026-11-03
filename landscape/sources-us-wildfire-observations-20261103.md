<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-us-wildfire-observations-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-us-wildfire-observations-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery of original US wildfire event observations with complementary mapped fire severity and harmonized incident-point records; no source acquisition, reuse rights, CAT scientific approval or loss-model admission.

**Entries:** 2

## USGS/USFS Monitoring Trends in Burn Severity (MTBS) current Burn Severity Portal products

**Candidate ID:** `us.usgs.mtbs.burn-severity-perimeters.2026`  
**Provider:** US Geological Survey / USDA Forest Service (MTBS)  
**Categories:** `wildfire`, `observed_fire_perimeters`, `burn_severity`, `historical_events`, `validation`  
**Spatial scope:** United States including CONUS, Alaska, Hawaii and Puerto Rico; only fires exceeding region-specific mapping thresholds and suitable imagery  
**Temporal scope:** 1984-2026 selectable in live portal as of 2026-11-03; recent fire seasons may be incomplete, releases revise historical pixels  
**Resolution / granularity:** Fire-level mapped boundaries and points in vector national products; burn-severity raster mosaics and per-fire mapping products; specific pixel size and projection vary by product  
**Potential roles:** `wildfire_perimeter_event_holdout`, `observed_burn_severity_challenge`, `fpa_fod_mtbs_id_event_linkage`, `wildfire_exposure_intersection`  
**Access hint:** `official_public_viewer_direct_download_and_map_services_exact_product_release_terms_and_asset_review`  
**Authoritative source:** <https://burnseverity.cr.usgs.gov/products/mtbs>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original USGS/USFS product; MTBS includes some prescribed fires and primarily large fires (generally &gt;=1000 acres West or &gt;=500 acres East), not a census of all ignitions or burned buildings. In 2026 the Burn Severity Portal reprocessed historical Landsat products and some pixel severity, projection and area measurements may change; freeze download UTC, product, region, fire identifier, vintage, CRS, severity classes, nodata, pixel lineage and original SHA-256. Not statistically independent of FPA FOD when linked via MTBS_ID, or of USFS/NIFC reporting. Burn severity is not building damage or insured loss. Do not automatically fetch or redistribute bytes before specific access/rights and scientific review.

## US Forest Service FPA FOD Seventh Edition spatial wildfire occurrence dataset (FPA_FOD_20260615)

**Candidate ID:** `us.usfs.fpa-fod.20260615.ed7`  
**Provider:** USDA Forest Service Research Data Archive / Karen C. Short  
**Categories:** `wildfire`, `fire_occurrence`, `ignition_points`, `historical_events`, `incident_identifiers`  
**Spatial scope:** United States and included reported territories, with variable reporting completeness across agencies and time  
**Temporal scope:** Wildfire discovery years 1992-2024; Seventh Edition released 2026-08-04, file edition FPA_FOD_20260615  
**Resolution / granularity:** Approximately 2.66 million harmonized incident-point records, reported final fire area, event dates, causes and cross-system keys; downloadable ACCDB, GDB, GPKG or SQLite (SpatiaLite) publication  
**Potential roles:** `historical_wildfire_frequency_holdout`, `us_wildfire_ignition_and_size_context`, `mtbs_id_and_ics209_incident_crosswalk`, `regional_reporting_bias_study`  
**Access hint:** `official_versioned_archive_multiple_gis_formats_and_mutable_current_edition_arcgis_rest_exact_asset_rights_review`  
**Authoritative source:** <https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7/_metadata_RDS-2013-0009.7.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The seventh edition is not a perimeter or burn-severity raster and is not a complete national wildfire census; only minimum precision at PLSS section (approximately one square mile) is required for reported points. USFS standardizes mixed agency records and deduplicates where possible; investigate reporting changes, duplicate incidents, source agencies and spatial uncertainty. Fields include MTBS_ID and ICS_209_PLUS_INCIDENT_JOIN_ID for bounded identity crosswalk, but linking does not prove independent observations. The live EDW ArcGIS MapServer is labelled current edition and may change without a URL change; pin the archive edition, original file, hash, event date and variable dictionary. No claims, insured amounts or building losses; no automated data acquisition, reuse or CAT admission approved by this candidate.
