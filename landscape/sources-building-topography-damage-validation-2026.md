<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-building-topography-damage-validation-2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-building-topography-damage-validation-2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of source-specific high-resolution terrain, LiDAR and observed-versus-modelled building damage evidence for bounded catastrophe exposure and vulnerability validation. No external data bytes, model approval or redistribution rights are conferred.

**Entries:** 6

## USGS 3DEP seamless 1-meter bare-earth digital elevation model (S1M)

**Candidate ID:** `usgs.3dep.seamless-1m-dem`  
**Provider:** U.S. Geological Survey / The National Map  
**Categories:** `terrain`, `high_resolution_dem`, `flood`, `exposure_context`, `united_states`  
**Spatial scope:** United States and territories where S1M tiles have been produced; tile availability is incomplete and expands over time  
**Temporal scope:** S1M production since mid-2025; underlying LiDAR acquisition years differ by project and tile  
**Resolution / granularity:** 1-meter ground spacing; cloud-optimized GeoTIFF tiles of approximately 10 km by 10 km, incorporating project-source metadata  
**Potential roles:** `ground_elevation_reference`, `terrain_control_for_flood_model_validation`, `building_elevation_context`  
**Access hint:** `official_public_domain_tile_catalog_metadata_only_no_acquisition`  
**Authoritative source:** <https://www.usgs.gov/3d-elevation-program/about-3dep-products-services>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** S1M is bare-earth elevation, not roof/building height and not a parcel flood-water-depth surface. Freeze exact tile/product URL, byte SHA-256, acquisition/production date, CRS, vertical reference/datum, source LiDAR quality, no-data rules and pixel footprint before any use. Do not infer building-first-floor or insured-value data; compare modelled flood depths only with matched elevation datums. USGS publishes 3DEP as free and unrestricted, but exact artifact/use scope and scientific suitability are not yet reviewed in this repository.

## USGS 3DEP original lidar point-cloud (LPC) collection

**Candidate ID:** `usgs.3dep.lidar-point-cloud`  
**Provider:** U.S. Geological Survey / The National Map  
**Categories:** `lidar`, `point_cloud`, `building_geometry`, `terrain`, `united_states`  
**Spatial scope:** United States and territories, by individual acquired lidar project and available coverage  
**Temporal scope:** Acquisition vintages from 2004 onward vary by project; selected source work-unit must be pinned  
**Resolution / granularity:** Project-native 3D point clouds in lossless LAZ/LAS with acquisition metadata, classification and variable quality levels  
**Potential roles:** `independent_roof_terrain_height_test`, `observed_building_geometry_context`, `lidar_to_dem_lineage_audit`  
**Access hint:** `official_public_domain_per_project_metadata_only_no_acquisition`  
**Authoritative source:** <https://data.usgs.gov/datacatalog/data/USGS%3Ab7e353d2-325f-4fc6-8d95-01254705638a>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** LPC is an underlying source family of 3DEP DEMs, so LPC-vs-S1M agreement is NOT independent replication. Required checks: exact work-unit, source date, LAZ/LAS classifications, coordinates/units, vertical datum, quality level, point density, building-versus-vegetation confusion and alignment to a footprint observation date. Dataset is not a ready-made building-footprint, building-material or insurance exposure file. Public-domain publisher statements do not substitute for exact-file identification.

## FEMA Historical Geospatial Damage Assessment Database public feature layer

**Candidate ID:** `us.fema.historical-geospatial-damage-assessments`  
**Provider:** U.S. Federal Emergency Management Agency (FEMA)  
**Categories:** `observed_impacts`, `building_damage`, `event_validation`, `flood`, `wind`, `earthquake`, `united_states`  
**Spatial scope:** United States historical disaster-event coverage limited to events assessed and published in the FEMA layer; not a complete national census  
**Temporal scope:** Past FEMA event assessments; service metadata reports last content edit 2021-06-22; feature EVENT_DATE, IMG_DATE and PROD_DATE determine per-record vintages  
**Resolution / granularity:** Point features with DMG_LEVEL, DMG_TYPE, ASMT_TYPE, IN_DEPTH in feet, disaster ID and event dates; ArcGIS layer supports JSON/GeoJSON; max record count 2000  
**Potential roles:** `field_observed_damage_holdout_candidates`, `remote_sensed_damage_comparison`, `modelled_damage_leakage_detection`  
**Access hint:** `public_arcgis_feature_service_exact_export_reuse_and_currentness_review`  
**Authoritative source:** <https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Crucial provenance boundary: ASMT_TYPE=FA is field-assessed; RS is remote-sensing classification; MOD and other methods are model predictions and cannot serve as independent measured damage truth against the same model. Inundation depth can itself be modelled and its unit is feet, not metres. Event_name, disaster number, date and feature ID require exact-snapshot identity and deduplication; point location alone does not prove a building identity or insured claim. Old service edit date requires freshness check. 'Public use' on the feature layer has not been promoted to source-specific commercial or redistribution approval.

## xBD / xView2 pre-post disaster building-damage annotation dataset

**Candidate ID:** `xview2.xbd.building-damage`  
**Provider:** Defense Innovation Unit / xView2 challenge and Carnegie Mellon Software Engineering Institute  
**Categories:** `remote_sensing`, `building_damage`, `damage_labels`, `vulnerability_validation`, `global_events`  
**Spatial scope:** Selected disaster-affected image scenes worldwide; highly nonrandom coverage rather than global building census  
**Temporal scope:** Event-specific pre- and post-disaster satellite image acquisitions in published xBD training and evaluation splits; freeze exact download release  
**Resolution / granularity:** Very-high-resolution paired imagery, building outlines and ordinal damage classes (no damage, minor, major, destroyed)  
**Potential roles:** `noncommercial_research_benchmark_candidate`, `damage_classification_quality_assessment`, `event_holdout_leakage_audit`  
**Access hint:** `registration_and_provider_license_noncommercial_restriction_must_be_verified`  
**Authoritative source:** <https://xview2.org/dataset>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The project is documented as CC BY-NC-SA 4.0/noncommercial in dataset catalogues; exact xView2 provider terms and image/subset rights must be checked independently before any use, especially commercial CAT or model training. Labels describe visible damage rather than loss ratios or paid insurance claims; pre/post scenes, event overlap and geographic splits can leak between training and validation. This is research discovery only: do not download, redistribute, train or publish source imagery/labels under the current record.

## 2018 NOAA NGS Emergency Response Imagery: Hurricane Michael

**Candidate ID:** `noaa.ngs.hurricane-michael-2018-emergency-imagery`  
**Provider:** NOAA National Geodetic Survey / Remote Sensing Division  
**Categories:** `aerial_imagery`, `post_event_observation`, `building_damage`, `wind`, `united_states`  
**Spatial scope:** Selected coastal and inland areas of the Florida Panhandle and adjacent southeast United States; published bounding extent is not an image-coverage mask  
**Temporal scope:** Post-landfall image collection 2018-10-11 to 2018-10-14, with individual flight/scene timestamps requiring retrieval and verification  
**Resolution / granularity:** 9,580 aerial images across approximately 10,756 square kilometres; approximate 15-30 cm image sample spacing and location accuracy not independently certified  
**Potential roles:** `independent_imagery_source_candidate`, `fema_remote_sensing_label_challenge`, `event_timing_and_coverage_review`  
**Access hint:** `noaa_public_emergency_imagery_browse_and_selective_download_exact_tile_rights_review`  
**Authoritative source:** <https://www.fisheries.noaa.gov/inport/item/57759>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NOAA provider metadata reports no access restriction, warns against critical-use and legal-use reliance, documents partial coverage, clouds and estimated positional accuracy; exact derivative/commercial scope and attribution for a selected image still need review. Source NOAA photographs are direct event observations, but FEMA RS annotations might have USED NOAA imagery: audit image/label lineage before claiming an independent visual test. Record original scene ID/time/footprint, flight mission, ortho/oblique geometry and source byte identity. A photo alone is NOT a verified building-loss label or financially insured loss. Verified 2026-11-01 official NOAA Digital Coast ID 8883 exposes individual GeoTIFFs, a tile-index ZIP, a metadata XML and a STAC catalog with source-native item JSON; full bulk acquisition is ~85 GB and must NOT be automatic. Two inspected items declare EPSG:4326, 9,340x9,340 RGBA pixels and a coarse collection datetime, not independently verified individual flight time. NOAA InPort item 57759 explicitly states CC0-1.0, while those STAC items declare license=NLPL (SPDX No Limit Public License, independently verified against https://spdx.org/licenses/NLPL.html). Both are permissive; identifier difference alone does NOT prove restrictive rights. Exact item-level applicability and the source-to-derived-GeoTIFF licence crosswalk still require review before commercial/image-model admission. A 2026-11-01 bounded HTTP Range request read only the first 4,096 bytes of NOAA tile 20181011aC0844330w294330n.tif and confirmed original little-endian TIFF, 9340x9340 RGBA, Deflate compression, 512x512 tiled layout (361 blocks) and original GeoKey EPSG:4326; no original imagery bytes were committed, no full-file hash or pixel mask was verified. Provider item bbox/polygon/alpha is NOT proof of scene completeness or FEMA label independence. See docs/research/noaa-hurricane-michael-stac-metadata-receipt-20261101.md. **SCIENCE CORRECTION 2026-11-01:** the first three source STAC tile **projected envelope** counts were 0/8/0, but WGS84 **true polygon** counts are 0/7/0. NOAA tile 20181011aC0853300w302100n has seven true-polygon DR-4399 RS/WI AFF classifications and seven total DR-4399 entries, whereas the original projected WGS84 envelope query overcounted one due to non-additive EPSG:4326-envelope versus EPSG:32616-layer geometry. All downstream source-area intersections must use explicit WGS84 polygon rings and reconcile subdivisions. Alpha-visible pixels, complete image bytes, unique structures and FEMA image-label independence remain unproven. See docs/research/noaa-fema-michael-2018-three-tile-spatial-receipt-20261101.md. Original NOAA image proof (2026-11-01): exact center 512x512 raster block index 180 of tile 20181011aC0853300w302100n was read as one 1,039-byte HTTP Range (64665046-64666084); SHA256 1e6d5d105f8ee78fd7a403adeac8aef4913dc356ac3f66d3ab300309a1ca8a66, Deflate expands into 1,048,576 all-zero RGBA bytes. Therefore 262,144 source pixels in this specific block have transparent alpha, not necessarily other blocks or the eight FEMA bbox hits. Count-only exact original raster-block geographic query returned 0 FEMA DR-4399 RS/WI points; west/east coarse tile halves returned 8/0. No complete TIFF bytes or hash, full alpha coverage, source-label independence, policy exposure or commercial admission verified. See docs/research/noaa-michael-original-center-alpha-block-20261101.md. Additional original byte checks: source blocks 18 and 360 each independently returned 1,039 compressed bytes identical to the proven all-zero Deflate stream of block 180; thus at least 341,008 disjoint valid raster pixels are demonstrated alpha-transparent across exactly these three original blocks. Public NOAA index claims 18.94 MB for this named TIFF, but verified first original IFD tile offsets and lengths require at least 67,126,397 file bytes, corroborated by a successful source HTTP byte range ending at offset 67,126,396. Do not treat directory MB label as exact Content-Length or assert file corruption; current authoritative size, ETag and full SHA-256 remain unverified. Source-specific evidence: docs/research/noaa-michael-original-center-alpha-block-20261101.md. This corrected 0/7/0 source overlap supersedes any unqualified 0/8/0 or eight-building text in earlier receipts; see docs/research/noaa-fema-michael-2018-three-tile-spatial-receipt-20261101.md. Live 2026-11-01 corrected true-polygon 12-block source partition: all seven FEMA DR-4399 RS/WI AFF aggregate counts fall in NOAA TIFF rows 16-18, columns 0-3. Four exact original compressed source blocks 305/306/325/326 match the independently decoded all-zero 1,039-byte Deflate stream byte-for-byte (block SHA256 1e6d5d105f8ee78fd7a403adeac8aef4913dc356ac3f66d3ab300309a1ca8a66): five of seven aggregate counts occur in entirely transparent NOAA raster blocks; two counts occur in blocks 324 and 344 with unverified alpha. Not original-image-validatable observations, not unique properties, and never model-admitted. No complete full-file TIFF hash or independently documented building/claim/source labels. See docs/research/noaa-fema-michael-seven-count-alpha-negative-blocks-20261101.md. FOLLOW-UP ORIGINAL DATA 2026-11-01 (supersedes earlier size/alpha gaps): GitHub successful live original TIFF HTTP206/ETag-pinned run https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41329301340 confirmed total TIFF object 67,126,397 bytes (the public HTML 18.94 MB listing is not the authoritative current object size). Exact compressed block 324 (81,979 bytes; SHA256 61640a5e3a0ab60f46eb257f27089ea792f28239be0ff44f32931bc0de8461ff) Adler-32/Predictor2 yields 39,316 alpha-positive pixels of 262,144; block 344 (21,239 bytes; SHA256 3bf7fffaf8f6acb516e12001d27b4e28077174596ffea5d186a003282d1e5eef) yields 7,948 alpha-positive pixels of 63,488. Actual FEMA true-polygon count of source block 344 is 1 but count in conservative polygon enclosing ALL alpha-positive pixels is 0. Thus 5+1=6 of 7 corrected FEMA RS/WI source count scopes cannot be validated as visible pixels in this NOAA tile; remaining block 324 count1 lies only in an alpha-bbox and is NOT proven pixel visible or independently labeled. Full original TIFF SHA256, building identity and model admission remain unverified. See docs/research/noaa-michael-324-344-original-alpha-provenance-20261101.md.

## Florida DEP Hurricane Michael field-assessed coastal structural damage report (2019)

**Candidate ID:** `florida.dep.hurricane-michael-2018-coastal-structural-damage`  
**Provider:** Florida Department of Environmental Protection, Coastal Engineering and Geology  
**Categories:** `field_assessment`, `observed_structural_damage`, `coastal_buildings`, `wind`, `storm_surge`, `united_states`  
**Spatial scope:** Northwest Florida coastal building zone, specifically selected surveyed coastlines in Bay, Gulf, Franklin and Wakulla counties; not an inland or complete statewide census  
**Temporal scope:** Field surveys immediately after 2018-10-10 landfall; final report and revisions published 2019  
**Resolution / granularity:** Expert-compiled report, field observations, photos and area/type summary counts; no independently verified openly downloadable building-level machine table confirmed  
**Potential roles:** `independent_field_damage_report_candidate`, `coastal_damage_definition_comparison`, `external_validation_scope_limit`  
**Access hint:** `public_government_report_pdf_and_photos_no_machine_readable_microdata_admission`  
**Authoritative source:** <https://floridadep.gov/rcp/coastal-engineering-geology/documents/hurricane-michael-post-storm-beach-conditions-and-coastal>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Florida DEP explicitly documents damage-assessment team field observations in Bay, Gulf, Franklin and Wakulla counties, with NOAA imagery also used. The report concerns coastal structures and erosion, not all FEMA DR-4399 structures or purely wind damage: surge, wave and erosion mechanisms must be disentangled. Its report totals and methods could offer a bounded independent challenge only after geography, damage definitions, survey selection, lineage and precise reuse rights are verified. Do NOT divide FEMA RS point counts by coastal field survey totals, infer parcel-level matches, claim an independent label at every location, or redistribute report imagery as unrestricted model training data.
