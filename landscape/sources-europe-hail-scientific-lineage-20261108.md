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
**Purpose:** Non-admission scientific source-lineage candidates for European hail modelled swaths, control/future climate simulations, spatially-resampled probabilistic catalogues, ML comparison and radar-based benchmarks.

**Entries:** 6

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

**Note:** Brennan et al. (2025), NHESS 25, 3693-3712, DOI 10.5194/nhess-25-3693-2025; tracking code DOI 10.5281/zenodo.12685276. NOT historical measured hail, insurer damage, an IID storm population, or 39,594 independently simulated years. Child tracks depend on the same COSMO simulations as ETH 701925 and 747355 below: not independent model validation. Check exact asset files, stated rights, model calendar, storm/year grouping, masks, climatological frequency, CRS, units and geographic coverage before model use.

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

## 330-year spatially-resampled European hail hazard event set v2

**Candidate ID:** `ethz.schmid.330yr-europe-hail.v2`  
**Provider:** ETH Zurich / Timo Schmid, Valentin Gebhart, David Bresch / Zenodo  
**Categories:** `hail`, `synthetic_hazard`, `event_catalogue`, `climate_scenarios`, `probabilistic_model`  
**Spatial scope:** 28 European countries in Zenodo v2 metadata.csv; per-country event files, including DEU and LUX  
**Temporal scope:** Synthetic 330-year spatial resampling from eleven simulated present-day years (2011-2021) and separately +3 °C pseudo-global-warming; Zenodo version v2 published 2025-12-08  
**Resolution / granularity:** 56 HDF5 .h5 country/scenario files (28 REF and 28 PGW) plus 3.2 kB metadata.csv; 2.2 km model grid; 19.9 GB total archive, linked CLIMADA data API  
**Potential roles:** `probabilistic_hail_hazard_candidate`, `country_pilot_luxembourg`, `oasis_hazard_adapter_research`, `spatial_resampling_sensitivity`  
**Access hint:** `zenodo_public_v2_bytes_and_publisher_md5_listed_exact_file_license_and_use_rights_pending`  
**Authoritative source:** <https://doi.org/10.5281/zenodo.17860440>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Schmid et al., Climate Services 41 (2026), 100630, DOI 10.1016/j.cliser.2025.100630. Original Zenodo v2 lists metadata.csv publisher md5 6b6b1d4ec919f56ded7669da3f3b2b82; Germany REF hail_DEU_ref.h5 md5 d4fdbacb9f68af041190a869cfb0cf8d (916.6 MB), PGW hail_DEU_PGW.h5 md5 28f4054eaa7b62eb6468061741f13fe1 (921.2 MB); Luxembourg REF hail_LUX_ref.h5 md5 1d66d63e84d44565c35461c0b8457a57 (8.3 MB), PGW hail_LUX_PGW.h5 md5 2f92c82a25f73e33f93e494abbc2a610 (5.6 MB). Release has published checksums only: NO bytes downloaded or independently hashed. The 330 years are spatial resampling of eleven simulation years, NOT 330 independent weather years or observations. Same simulation parent as COSMO and Brennan swaths; countries can share physical storm parents and CANNOT be concatenated as independent totals. Climate PGW kept separate. License of exact archive HDF5 not yet verified; model NOT_ADMITTED.

## European XGBoost versus HAILCAST hail projections model-output comparison

**Candidate ID:** `chericoni.europe-hail-ml-physics.2026`  
**Provider:** Marco Chericoni, Giorgia Fosser, Alessandro Anav, Iris Thurnherr and Andreas F. Prein / Zenodo  
**Categories:** `hail`, `model_comparison`, `climate_scenarios`, `machine_learning`, `uncertainty`  
**Spatial scope:** Europe, same COSMO 2.2 km domain for present and +3 °C pseudo-global-warming  
**Temporal scope:** Eleven simulation years 2011-2021 plus +3 °C counterfactual; published 2026-05-08  
**Resolution / granularity:** Derived XGBoost and HAILCAST hail output from same parent COSMO simulations; exact release files, spatial structure and units to inspect  
**Potential roles:** `hail_model_structural_uncertainty`, `climate_nonstationarity_diagnostic`, `independent_method_comparison_not_independent_data`  
**Access hint:** `public_zenodo_comparison_output_release_license_and_exact_assets_not_yet_reviewed`  
**Authoritative source:** <https://doi.org/10.5281/zenodo.18243342>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Chericoni et al. (2026), npj Natural Hazards, DOI 10.1038/s44304-026-00218-3. XGBoost trained on ERA5 hail environment versus physically based online HAILCAST yields divergent future hail trends because warmer-climate inputs can be out of training distribution. This is a method comparison on the SAME COSMO simulations, not a second independent 11-year catalogue. Companion code at github.com/marcochericoni95/hail_xgboost_hailcast_ncc; model XGBoost at github.com/borusseee/XGBoost_hail. Dataset rights and exact bytes pending. Do NOT blend model outputs into independent events or use as calibrated building-loss vulnerability.
