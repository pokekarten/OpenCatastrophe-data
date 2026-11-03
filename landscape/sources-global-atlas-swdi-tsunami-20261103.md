<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-atlas-swdi-tsunami-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-atlas-swdi-tsunami-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery registry of three independently checked additional hazard curves, U.S. severe-weather signatures and global tsunami screening products for multi-peril CAT research.

**Entries:** 3

## GEM ATLAS 2.0 global seismic hazard curves

**Candidate ID:** `gem.atlas.global-seismic-hazard-curves.v2`  
**Provider:** Global Earthquake Model (GEM) Foundation  
**Categories:** `earthquake`, `seismic_hazard`, `hazard_curves`, `global`, `modelled_product`  
**Spatial scope:** Global H3 grid, approximately 3.6 million sites spaced about 6.5 km apart  
**Temporal scope:** ATLAS 2.0 draws on the GEM Global Mosaic released in 2023; hazard is probabilistic, not an event-time observation series  
**Resolution / granularity:** PGA and spectral accelerations at 0.2, 0.3, 0.6 and 1.0 seconds, as rock- and site-condition-specific hazard curves  
**Potential roles:** `global_seismic_hazard_curve_comparison`, `site_condition_sensitivity`, `probabilistic_earthquake_benchmark`  
**Access hint:** `web_portal_and_api_custom_commercial_subscription_or_public_good_request`  
**Authoritative source:** <https://www.globalquakemodel.org/products/atlas>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A derived GEM seismic-hazard service, not an independent earthquake catalogue or OpenQuake rupture event set. API and public-good access require provider engagement; insurance/commercial reuse needs a suitable explicit licence. Before model use, pin mosaic edition, intensity measure, soil/Vs30 basis, exceedance semantics and spatial interpolation. Crosswalk to the already catalogued GEM Global Seismic Hazard Map without counting both outputs as independent evidence.

## NOAA NCEI Severe Weather Data Inventory (SWDI) 2.0

**Candidate ID:** `noaa.ncei.swdi.v2`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `severe_convective_weather`, `hail`, `tornado`, `radar_signatures`, `observations`, `united_states`  
**Spatial scope:** United States, subject to radar coverage and reporting completeness  
**Temporal scope:** Historic datasets with provider- and layer-dependent periods; the online SWDI interface identifies version 2.0 (January 2022)  
**Resolution / granularity:** Layer-specific NEXRAD storm-cell, hail, mesocyclone and tornado signatures plus preliminary reports; downloadable CSV/shapefile and documented web services  
**Potential roles:** `hail_and_tornado_signature_challenge`, `storm_event_to_radar_spatial_linkage`, `post_event_hazard_footprint_validation`  
**Access hint:** `public_web_services_and_http_bulk_csv_layer_specific_rights_review`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/severe-weather-data-inventory>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Radar signatures indicate likely conditions, not confirmed hail sizes or losses. SWDI includes preliminary reports and lightning sourced from Vaisala NLDN; do not infer redistribution/commercial permission for every layer from NOAA hosting. Review layer IDs, historic completeness, quality warnings and versioned download receipts, and reconcile shared NWS Storm Data lineage with the already audited NOAA Storm Events source.

## NGI / Geoscience Australia global probabilistic tsunami hazard 2017 (Zenodo v1)

**Candidate ID:** `ngi.ga.global-tsunami-hazard-2017.v1`  
**Provider:** Norwegian Geotechnical Institute and Geoscience Australia  
**Categories:** `tsunami`, `coastal_hazard`, `probabilistic_hazard`, `global`, `validation`  
**Spatial scope:** Global coastline-oriented tsunami hazard screening points, subject to original dataset geometry and coverage  
**Temporal scope:** Modelled 2017 global probabilistic tsunami hazard assessment, republished as a Zenodo v1 dataset on 2025-08-27  
**Resolution / granularity:** Semicolon-delimited globalPTHA.txt with coordinate fields, annual mean-exceedance rates for 5-2000 cm thresholds and return-period heights in metres including uncertainty variants  
**Potential roles:** `global_tsunami_return_level_benchmark`, `coastal_hazard_screening`, `tsunami_curve_unit_and_uncertainty_validation`  
**Access hint:** `public_zenodo_file_download_rights_scope_unreviewed`  
**Authoritative source:** <https://zenodo.org/records/16964551>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher identifies CC BY 3.0 AU; exact redistribution and derivative scope still require formal repository review. Global model is explicitly not recommended for local-scale risk assessments and contains exceedance curves, not a stochastic event catalogue or insured loss data. Check censored 0.1/20 m values, rate_N centimetre thresholds vs ariN metres, site-coordinate/datum and actual header; Zenodo preview uses ari500ZL while explanatory text says ari500LZ.
