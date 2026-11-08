<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-swiss-crop-hail-linked-assets-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-swiss-crop-hail-linked-assets-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission discovery of four distinct reproducible Swiss crop-hail research assets (exposure, reported damage grids, radar hazard and model code); original file checks, data rights, dependence and scientific use remain open.

**Entries:** 4

## Swiss 2021 crop exposure grids used in the 12-event hail study

**Candidate ID:** `ch.portmann.crop-hail.2024.exposure-grid`  
**Provider:** Portmann, Schmid, Villiger, Bresch and Calanca / Zenodo / CLIMADA  
**Categories:** `agriculture`, `crop_exposure`, `switzerland`, `hail`, `geospatial`  
**Spatial scope:** Switzerland, agricultural crop exposure; not individual insured parcel boundaries or policy records  
**Temporal scope:** Reference exposure year 2021; published research version v1 in 2024  
**Resolution / granularity:** Published gridded Swiss crop exposure for wheat, maize, barley, rapeseed and grapevine; exact files, grid geometry, units and land-use provenance to verify per asset  
**Potential roles:** `crop_exposure_holdout`, `synthetic_crop_portfolio_geography_challenge`, `hail_crop_density_validation`  
**Access hint:** `public_zenodo_v1_gridded_exposure_original_bytes_and_license_not_yet_checked`  
**Authoritative source:** <https://doi.org/10.5281/zenodo.11064756>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The peer-reviewed NHESS crop-hail paper 10.5194/nhess-24-2541-2024 explicitly cites Zenodo 11064756 for gridded crop exposure and explains crop-density dependence of hail damage-footprint skill. This source is linked to the same 12-event research as the damage and hazard datasets below: never count the linked assets as independent validation samples. No insurance TIV, insured parcel membership, carrier allocation or crop policy terms established. The exact Zenodo release/file license, hashes, spatial reference, time alignment and crop-code mapping must be checked before source admission.

## Reported crop hail damage grids for 12 Swiss historical events

**Candidate ID:** `ch.portmann.crop-hail.2024.reported-damage-grids`  
**Provider:** Portmann, Schmid, Villiger, Bresch and Calanca / Zenodo / CLIMADA  
**Categories:** `agriculture`, `hail`, `reported_damage`, `event_validation`, `switzerland`  
**Spatial scope:** Switzerland; spatially aggregated reported damage related to 12 historical crop-hail events  
**Temporal scope:** Twelve study events used in the 2024 published analysis; exact event days and observation vintage pending original-asset review  
**Resolution / granularity:** Published gridded reported crop-damage information; original insurer reports are not automatically public and are not interchangeable with these research grids  
**Potential roles:** `crop_hail_damage_footprint_holdout`, `observed_event_detection_benchmark`, `hail_model_false_alarm_validation`  
**Access hint:** `public_zenodo_v1_damage_grids_rights_confidential_source_derivation_and_coordinates_review_required`  
**Authoritative source:** <https://doi.org/10.5281/zenodo.11064767>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The NHESS Portmann et al. 2024 article explicitly identifies Zenodo 11064767 as 'Reported hail damage for 12 hail events in Switzerland' and says gridded damage information is available. This is a candidate for footprint occurrence validation, not permission to distribute underlying insurer claims, loss amounts or identifiable records. Review the precise Zenodo license, anonymization/aggregation, per-event units and linkage to hazard and exposure before download, rehosting or use. The same insured source data were used to design/assess the published method, so no independent holdout is implied.

## Swiss radar hail-intensity grids for 12 historical events

**Candidate ID:** `ch.portmann.crop-hail.2024.radar-hazard-grids`  
**Provider:** Portmann, Schmid, Villiger, Bresch and Calanca / Zenodo / MeteoSwiss research context  
**Categories:** `hail`, `hazard`, `radar`, `historical_events`, `switzerland`  
**Spatial scope:** Switzerland, 12 event footprints; not an annual nationwide stochastic event frequency catalogue  
**Temporal scope:** Twelve observed study hail events cited in the 2024 article; exact event timestamps pending file review  
**Resolution / granularity:** Gridded radar Maximum Expected Severe Hail Size (MESHS) research event data; published method compares crop resolutions of 8 km and vineyard resolutions of 1 km  
**Potential roles:** `crop_hail_hazard_event_replay`, `hail_spatial_skill_challenge`, `synthetic_hail_footprint_overlay`  
**Access hint:** `zenodo_radar_grids_version_license_provider_rights_and_intensity_units_pending`  
**Authoritative source:** <https://doi.org/10.5281/zenodo.11064781>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The NHESS article cites Zenodo 11064781 as 'Radar data for 12 hail events in Switzerland'. MESHS is an inferred radar hail-size indicator, not direct point-measured hailstone size, a building-damage vulnerability function, or a stochastic event frequency. Review upstream MeteoSwiss rights separately from the paper license and Zenodo record; verify NetCDF/other format, CRS, cell size, units, nodata and event-year identity. No OEP/AEP or insurer loss calibration is warranted by 12 selected historical events.

## Open crop-hail damage-footprint study model and reproducibility code

**Candidate ID:** `ch.portmann.crop-hail.2024.model-code`  
**Provider:** Portmann, Schmid and Villiger / Zenodo / CLIMADA-project  
**Categories:** `hail`, `open_source_model`, `agriculture`, `reproducibility`, `vulnerability_research`  
**Spatial scope:** Swiss crop-hail methodology; external geographic transfer and asset-class use unvalidated  
**Temporal scope:** Research code version 1.0 published 2024 alongside NHESS 24:2541-2558  
**Resolution / granularity:** Python 3.9 study-specific model/reproduction code; dependency CLIMADA platform and public crop/radar/damage-grid research records  
**Potential roles:** `crop_hail_method_reproduction`, `threshold_and_resolution_sensitivity`, `oasis_adapter_feasibility_research`  
**Access hint:** `open_research_code_exact_archive_license_dependencies_and_api_review_pending`  
**Authoritative source:** <https://doi.org/10.5281/zenodo.12784190>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NHESS 10.5194/nhess-24-2541-2024 provides DOI 10.5281/zenodo.12784190 for the published study code, as well as links to the three separately identified data assets in this shard. CLIMADA's cited platform license is GPL-3.0; do not assume the same license applies to all study code or linked third-party datasets. This is a hail crop-damage footprint classification research model, not an Oasis-ready insured loss model: pin archive checksum, code/dependency versions, valid tests and scientific limits before use.
