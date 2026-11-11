<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-observed-water-damage-wildfire-20261111.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-observed-water-damage-wildfire-20261111.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-11`  
**Purpose:** Non-admission source discovery for four official 2025-2026 water occurrence, observed disaster damage and wildfire monitoring products; original bytes, commercial rights and scientific model-input status remain separate gates.

**Entries:** 4

## Global 2025 OPERA DSWx-S1-derived open-water and inundated-vegetation occurrence v1

**Candidate ID:** `opengeohub.opera-dswx-s1.water-occurrence.2025.v1`  
**Provider:** OpenGeoHub Foundation / Isik, Parente and Hengl (NASA OPERA DSWx-S1 upstream)  
**Categories:** `flood`, `surface_water`, `inundated_vegetation`, `remote_sensing`, `derived_observation`  
**Spatial scope:** Global mapped coverage of valid Sentinel-1 OPERA DSWx-S1 observations; valid-observation count and spatial support vary by location  
**Temporal scope:** 2025-01-01 through 2025-12-31; derived release v1, published 2026-05-05; filenames dated v20260425  
**Resolution / granularity:** Two EPSG:4326 ~0.00027-degree (~30 m) annual integer percentage-of-valid-observation GeoTIFF layers: open water (13.1 GB), inundated vegetation (21.0 GB); nodata 255  
**Potential roles:** `permanent_water_mask_research`, `flood_extent_context`, `wetland_exposure_context`, `independent_classification_comparison_with_lineage_check`  
**Access hint:** `public_zenodo_large_tiff_cc_by_4_0_metadata_only_no_original_bytes_probed`  
**Authoritative source:** <https://zenodo.org/records/20021037>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher version-specific Zenodo record 20021037 identifies CC BY 4.0 and publishes source-listed MD5s for the 13.1-GB open-water and 21.0-GB inundated-vegetation TIFFs. This is a 2025 annual frequency-of-detection product derived from NASA OPERA DSWx-S1, not daily flood event footprints, water depth, flood return periods, claims, or statistically independent of the underlying DSWx-S1 collection already catalogued in OpenCatastrophe-data. For a later bounded original-byte challenge, record exact TIFF filename, original MD5 and locally computed SHA-256, geotransform, nodata=255, valid-observation denominator and coverage. Distinguish derived-product CC BY 4.0 from upstream/hosting and attribution obligations; never auto-admit data or 34.1 GB in Git.

## Indonesia BNPB 2025 provincial disaster events, damaged houses and human impacts XLSX compilation

**Candidate ID:** `id.bnpb.2025.provincial-disaster-damage-20260708`  
**Provider:** Badan Nasional Penanggulangan Bencana (BNPB), Indonesia  
**Categories:** `multi_peril`, `reported_disaster_damage`, `building_damage`, `event_impacts`, `regional_validation`  
**Spatial scope:** Indonesia; province-level national statistical compilation; no geocoded individual damaged buildings  
**Temporal scope:** Disaster incidents occurring in 2025; BNPB public source created 2026-07-01, last updated 2026-07-08  
**Resolution / granularity:** Multiple downloadable original official XLSX resources for incidents, casualties, affected/displaced people and number of damaged houses by province; published snapshot is aggregated and may require a separate peril classification  
**Potential roles:** `independent_regional_building_damage_challenge`, `multi_peril_incident_plausibility`, `reported_impacts_holdout_design`  
**Access hint:** `official_public_ckan_style_xlsx_catalogue_exact_file_and_license_review_pending`  
**Authoritative source:** <https://data.bnpb.go.id/dataset/kompilasi-data-kejadian-dan-dampak-bencana-2025>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official BNPB portal identifies the 2025 compilation and provincial XLSX resources; Indonesia's national data.go.id mirror records release on 2026-07-24 and warns that its One Data Indonesia compliance remains in progress. The source portal's July 8 modification date is not the event year. Public classification 'terbuka' indicates discoverability, not proven commercial redistribution or machine-bulk rights. No original XLSX downloaded or hashed here. Identify exact house-damage severity categories, province boundaries, duplicated event reporting and peril mix before quantitative comparison; regional reported counts are neither building-level footprints nor insured losses, and absent entries are not zero losses. Earlier BNPB DIBI 2015-2024 and InaRISK map candidates are different products.

## Malaysia DOSM Special Report on Impact of Floods 2025 by state and sector

**Candidate ID:** `my.dosm.flood-impact-losses.2025.release20260415`  
**Provider:** Department of Statistics Malaysia (DOSM)  
**Categories:** `flood`, `historical_economic_loss`, `observed_impacts`, `housing_damage`, `sectoral_loss_validation`  
**Spatial scope:** Malaysia; reported national, state and selected district aggregates; no identified insured property or event polygon  
**Temporal scope:** Flood damage during calendar year 2025; official release 2026-04-15 and 2024 comparatives  
**Resolution / granularity:** Official survey-based and administrative-source aggregate flood damage in Malaysian ringgit by state and sector including residential, vehicles, business, manufacturing, agriculture and public infrastructure; reported national loss 636.9 million MYR  
**Potential roles:** `historical_flood_damage_sector_challenge`, `regional_economic_loss_prior`, `flood_vulnerability_external_validation`  
**Access hint:** `official_report_web_and_downloaded_publication_terms_and_reuse_rights_review_pending`  
**Authoritative source:** <https://www.dosm.gov.my/portal-main/release-content/special-report-on-impact-of-floods-in-malaysia2025>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher states living-quarters, vehicle, business and manufacturing amounts arise from a January-December 2025 special survey, while agricultural and public-asset infrastructure values use government-agency information; the national aggregate is MYR 636.9 million (vs MYR 933.4 million in 2024), NOT insured claims. The publisher page and downloadable infographic may have inconsistent state-sector labels, so freeze the exact official report/metadata and resolve tabular values before ingesting any subnational cell. No exact original publication bytes or independent rights/redistribution authorisation obtained. Preserve MYR reference year, sector treatment, sampling uncertainty, reporting bias and possible overlaps; do not treat aggregates as event-specific building loss or direct GUL/IL/RI/OEP/AEP.

## DLR EOC Burnt Area Daily NRT Global v2.2, 2026 product

**Candidate ID:** `dlr.eoc.burnt-area.global-nrt.v2.2`  
**Provider:** German Aerospace Center (DLR), EOC Geoservice  
**Categories:** `wildfire`, `burnt_area`, `remote_sensing`, `near_real_time`, `event_footprint_validation`  
**Spatial scope:** Global DLR product; exact footprint availability and observation support must be checked for the selected data tile/time window  
**Temporal scope:** Version 2.2 released 2026-06-23; provider listed a recent rolling 2026 observation window on its public product page, not a complete historic catalogue  
**Resolution / granularity:** Public DLR EOC Data Portal near-real-time burnt-area dataset metadata; exact native grid, variable classification, original event identity, update interval, access endpoint and bounding window pending original product probe  
**Potential roles:** `independent_wildfire_perimeter_challenge`, `burned_area_dynamics_validation`, `effis_lineage_comparison`  
**Access hint:** `public_portal_metadata_cc_by_nc_4_0_noncommercial_commercial_model_use_blocked`  
**Authoritative source:** <https://eodata.dlr.de/en/datasets/burntarea/burntarea_v2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DLR's original EOC Data Portal lists global Burnt Area Daily NRT version 2.2, release 2026-06-23, under CC BY-NC 4.0. This explicitly blocks assuming permitted commercial insurer/risk-model use without another licence. Keep it distinct from DLR's separate Europe Sentinel-3 daily/monthly/yearly products and from JRC EFFIS; shared sensors or algorithms may make comparisons non-independent. No original pixels/feature data, endpoint contract, SHA-256 or scientific validation obtained. Resolve spatial coverage, time-window completeness, fire/perimeter semantics, cloud/false positives, and rights before a one-event probe.
