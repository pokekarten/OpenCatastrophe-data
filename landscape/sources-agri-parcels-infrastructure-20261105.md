<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-agri-parcels-infrastructure-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-agri-parcels-infrastructure-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Source discovery of original agricultural parcel and physical infrastructure inventories surfaced by Exa research on 2026-11-05. Candidate records only; no original assets, insurer locations, licenses approved for OpenCatastrophe, or model admission.

**Entries:** 4

## JRC EuroCropsV2 harmonised EU agricultural parcel crop declarations

**Candidate ID:** `eu.jrc.eurocropsv2.gsa-parcels`  
**Provider:** European Commission Joint Research Centre / EUROSTAT / national agricultural paying agencies  
**Categories:** `agriculture`, `crop_exposure`, `parcel_geometry`, `geospatial`, `historical_land_use`  
**Spatial scope:** Available regional coverage across participating European countries; not uniformly complete at country/region/year level  
**Temporal scope:** National source vintages from 2008 through 2023 where available; JRC EuroCropsV2 published 2025 and corrected in 2026  
**Resolution / granularity:** Harmonised parcel-level GeoParquet geometries (EPSG:3035), crop identifiers and harmonised HCAT4 mapping; nearly 47 million parcels reported in project documentation, across multiple non-uniform vintages  
**Potential roles:** `synthetic_agricultural_insurance_parcel_allocation`, `regional_crop_class_prior_for_hail_flood_drought`, `crop_exposure_independent_remote_sensing_challenge`  
**Access hint:** `public_jrc_gpq_and_original_cc_by4_notice_exact_release_and_member_state_terms_review`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original JRC distribution https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/ and 2026-03-05 copyright.txt declare EU CC BY 4.0 with attribution/change indication. Original repo https://github.com/Martincccc/EuroCropsV2 documents corrected gpqtv201 (stack) and gpqtv202 (overlapping polygons) versions; pin exact selected file, version, SHA256, geometry validity, CRS, codebook and source national usage rights before admission. National farmer declarations are self-reported, not observed plant cover, insured crop values, policy holdings or loss observations. EuroCropsV2 includes national paying-agency inputs (including Netherlands); never treat it as independent of Dutch BRP when the underlying parcel/source vintage overlaps.

## Netherlands RVO/PDOK Basisregistratie Gewaspercelen (BRP) agricultural parcels

**Candidate ID:** `nl.rvo.brp-gewaspercelen.2025`  
**Provider:** Rijksdienst voor Ondernemend Nederland (RVO) / PDOK  
**Categories:** `agriculture`, `crop_exposure`, `parcel_geometry`, `land_use`, `national_register`  
**Spatial scope:** Netherlands, annual agricultural/landscape parcels as filed by participating land users; not every insured farm or field  
**Temporal scope:** Annual observed declaration reference date 15 May; 2025 final dataset supplied 2026-03-17, historical exports exist for earlier years  
**Resolution / granularity:** Per-parcel geometry with crop category and crop codes, OGC API Features/WFS/WMS/ATOM dataset distribution; current OGC API returns most recent dataset  
**Potential roles:** `high_resolution_dutch_agricultural_exposure_prior`, `crop_rotation_and_geographic_concentration`, `crosscheck_eurocropsv2_2025_comparability_and_lineage`  
**Access hint:** `public_pdok_ogc_no_key_no_fee_public_domain_mark_listing_exact_extract_terms_review`  
**Authoritative source:** <https://api.pdok.nl/rvo/gewaspercelen/ogc/v1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official PDOK dated 2026-03-17 confirms 2025 final release https://www.pdok.nl/-/brp-gewaspercelen-2025-definitief and native OGC/WFS/ATOM endpoints. Official API advertises Public Domain Mark 1.0, zero charge and no authentication; Public Domain Mark is a copyright status marker, not by itself an independent rights grant or blanket privacy/contract approval. Declaration fields refer to crop filed on reference day 15 May, not confirmed actual growing season or policy-level crop/TIV. Parcel counts include landscape elements; do not equate parcel count with insurable fields. National source can underlie EuroCropsV2; maintain original ID, vintage, downstream provenance and avoid counting correlated evidence twice.

## GeoMermaids World Infrastructures Dataset (GMWID) global GeoParquet

**Candidate ID:** `global.geomermaids.gmwid.infrastructure`  
**Provider:** GeoMermaids / OpenStreetMap contributors / stated authoritative national infrastructure registers  
**Categories:** `infrastructure`, `power_grid`, `telecommunications`, `energy`, `business_interruption`, `geospatial`  
**Spatial scope:** Worldwide OSM-derived infrastructure plus separately attributed official source enrichments; coverage differs greatly by region and asset class  
**Temporal scope:** Provider advertises weekly rebuilt latest layers; historical snapshot preservation is not guaranteed, source vintages vary by upstream  
**Resolution / granularity:** 27 infrastructure layers described by provider as per-asset GeoParquet 2.0, including power plants, substations, power lines, telecom masts, pipelines, wells and water infrastructure; origin/source attributes  
**Potential roles:** `critical_infrastructure_synthetic_exposure_locations`, `power_network_business_interruption_dependency_priors`, `official_vs_osm_spatial_completeness_challenge`  
**Access hint:** `public_http_geoparquet_osm_odbl_1_sharealike_nsta_separate_noncommercial_do_not_bulk_admit`  
**Authoritative source:** <https://gmwid.geomermaids.com/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original provider documents global `gmwid/latest/` GeoParquet under ODbL 1.0, lineage `origin` and coverage receipts, plus per-build https://parquetry.geomermaids.com/gmwid/ATTRIBUTION.txt. National additions include EIA, FCC, Agence ORE and others, which are not statistically independent from matching originals already in OpenCatastrophe. UK NSTA data are in a separate explicitly noncommercial `gmwid/nsta/` scope and must never be silently merged into a commercially reusable file. ODbL attribution/share-alike, third-party restrictions, source family matching, weekly volatility and topology/attribute uncertainties need explicit legal/scientific review. Infrastructure presence is not insured replacement cost or modeled outage/loss.

## US FCC Antenna Structure Registration (ASR) public database downloads

**Candidate ID:** `us.fcc.asr.tower-registration`  
**Provider:** United States Federal Communications Commission (FCC)  
**Categories:** `telecommunications`, `critical_infrastructure`, `asset_register`, `geospatial`, `physical_exposure`  
**Spatial scope:** United States registered antenna structures, restricted to FCC ASR regulated structures; not all telecom towers or rooftop antennas  
**Temporal scope:** FCC publishes periodic complete and daily transaction download products; state, deletions and historical validity require original schema checks  
**Resolution / granularity:** Individual ASR registration and application records provided as tabular ZIP extracts, with separate FAA determination records; structure location and attributes may be present and require schema review  
**Potential roles:** `us_telecom_tower_location_prior`, `critical_infrastructure_wind_exposure_context`, `gMWID_fcc_origin_independence_and_coverage_audit`  
**Access hint:** `public_fcc_asr_bulk_zip_metadata_original_schema_and_current_download_receipt_pending`  
**Authoritative source:** <https://www.fcc.gov/wireless/data/public-access-files-database-downloads>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original FCC public database pages list ASR application, registration and FAA determination downloads with complete/daily transaction products. Verify a precise FCC-hosted ZIP path, latest source timestamps, registered/deleted flags, coordinate datum and any controlled/personally identifying fields before fetching or storing rows. GMWID explicitly cites FCC ASR for its added US telecom masts, therefore FCC and GMWID assets are not two independent tower observations; do not double count, and do not treat an FCC registration as insured owner, full asset replacement value or measured wind vulnerability.
