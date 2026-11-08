<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-europe-hail-scientific-lineage-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-europe-hail-scientific-lineage-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission scientific source-lineage candidates for European hail modelled swaths, control/future simulations and restricted independent radar-based benchmarks.

**Entries:** 4

## European model-derived hailstorm swaths and storm tracks for present and +3 K climates

**Candidate ID:** `ethz.brennan.hail-swaths.v2025`  
**Provider:** ETH Zurich / Killian Brennan, Iris Thurnherr, Michael Sprenger and Heini Wernli  
**Categories:** `hail`, `synthetic_hazard`, `event_footprints`, `climate_scenarios`  
**Spatial scope:** Europe covered by 2.2 km regional COSMO simulations; spatial domain and exact mask to confirm  
**Temporal scope:** Present-day 2011-2021 forcing and future +3 K pseudo-global-warming case; research publication 2025  
**Resolution / granularity:** 39,594 present-climate and 37,746 future-climate modelled hail swaths; compressed linked release approximately 0.7 GB; per-storm HAILCAST maximum hail sizes and tracks  
**Potential roles:** `hail_hazard_footprint_resampling`, `hail_event_family_analysis`, `climate_scenario_comparison`  
**Access hint:** `public_research_archive_exact_asset_rights_checksum_and_format_not_yet_reviewed`  
**Authoritative source:** <https://doi.org/10.3929/ethz-b-000745185>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Brennan et al. (2025), NHESS 25, 3693-3720, DOI 10.5194/nhess-25-3693-2025; tracking code DOI 10.5281/zenodo.12685276. NOT historical measured hail, insurer damage, an IID storm population, or 39,594 independently simulated years. Child tracks depend on the same COSMO simulations as ETH 701925 and 747355 below: not independent model validation. Check exact asset files, stated rights, model calendar, storm/year grouping, masks, climatological frequency, CRS, units and geographic coverage before model use.

## COSMO 2.2 km hail and lightning present-day simulation selected fields

**Candidate ID:** `ethz.thurnherr.cosmo-hail.2011-2021`  
**Provider:** ETH Zurich / Iris Thurnherr, Ruoyi Cui, Patricio Velasquez and Christoph Schär  
**Categories:** `hail`, `synthetic_hazard`, `weather_simulation`, `lightning`  
**Spatial scope:** Western to central Europe, rotated model grid; paper describes broader European analysis  
**Temporal scope:** 2011-2021 historical forcing from ERA5; linked Cui et al. 2025 publication  
**Resolution / granularity:** Selected high-frequency COSMO v6 + CAM-HAILCAST output; simulated maximum hail diameter every 5 min, hourly fields including LPI, rainfall, thermodynamic diagnostics  
**Potential roles:** `hail_hazard_intensity_research`, `multi_peril_hail_rain_correlation`, `hail_model_sensitivity`  
**Access hint:** `eth_research_collection_data_published_license_file_list_and_original_bytes_not_yet_audited`  
**Authoritative source:** <https://doi.org/10.3929/ethz-b-000701925>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Cui et al. (2025) DOI 10.1029/2024JD042828. Model output (not observed ground hail), driven by ERA5. Spurious hail activation needs published post-processing; LPI is lightning potential, not uncalibrated stroke counts. ETH EURADHAIL DOI 10.3929/ethz-b-000701924 is a separate OPERA-derived observational proxy used for evaluation, not independent of itself. These selected fields are parent data for Brennan modelled swaths, never count the two as separate independent event populations.

## COSMO +3 °C pseudo-global-warming European hail simulation selected fields

**Candidate ID:** `ethz.thurnherr.cosmo-hail.2085-2095`  
**Provider:** ETH Zurich / Iris Thurnherr, Ruoyi Cui, Patricio Velasquez and Christoph Schär  
**Categories:** `hail`, `synthetic_hazard`, `climate_scenario`  
**Spatial scope:** Western and central Europe under the 2.2 km COSMO simulation grid  
**Temporal scope:** 2085-2095 model years, constructed via +3 °C pseudo-global-warming delta applied to ERA5 2011-2021 forcing  
**Resolution / granularity:** Selected 5-minute and hourly COSMO model output including maximum hail diameter, precipitation, LPI and meteorological predictors  
**Potential roles:** `scenario_hail_footprint_stress_test`, `climate_sensitivity`, `cross_peril_scenario_dependence`  
**Access hint:** `eth_research_collection_data_published_license_file_list_and_original_bytes_not_yet_audited`  
**Authoritative source:** <https://doi.org/10.3929/ethz-b-000747355>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Thurnherr et al. (2025), DOI 10.1029/2025GL114811. Scenario is not a directly observed future forecast nor baseline annual event rate. Same physics/model lineage as 2011-2021 control and Brennan swaths. Preserve time, region, climate scenario and simulation ensembles; do not mix current and future event populations for return-period calibration.

## Observed-radar-derived hailstorm tracks for Germany France Belgium and Luxembourg

**Candidate ID:** `kit.fluck.hail-tracks.2005-2014`  
**Provider:** Karlsruhe Institute of Technology / Elody Fluck and Michael Kunz  
**Categories:** `hail`, `radar`, `historical_events`, `validation`  
**Spatial scope:** Germany, France, Belgium and Luxembourg; not all Europe  
**Temporal scope:** Summer half-years April-September 2005-2014  
**Resolution / granularity:** 2D weather radar and lightning composite, 1 km hail potential, convective cell tracks; derived tracks available upon author request  
**Potential roles:** `independent_hail_frequency_benchmark`, `historical_hail_track_validation`  
**Access hint:** `paper_open_cc_by_data_tracks_on_request_rights_and_access_unknown`  
**Authoritative source:** <https://doi.org/10.5194/nhess-21-683-2021>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Fluck et al. (2021) explicitly say track series require contacting Michael Kunz and French radar composites Météo-France. Open paper under CC BY 4.0 does not license unpublished tracks or original French radar data. German DWD radar upstream available via DWD separately. No source bytes acquired, no commercial-use permission, no insurer claims. Verify acquisition, rights and independence before calibration.
