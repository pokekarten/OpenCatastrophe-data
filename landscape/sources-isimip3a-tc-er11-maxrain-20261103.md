<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-isimip3a-tc-er11-maxrain-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-isimip3a-tc-er11-maxrain-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery of exact ISIMIP3a historical tropical cyclone ER11/TCR maximum-rainfall source identity and rights/provenance gate; metadata-only investigation, no data ingestion.

**Entries:** 1

## ISIMIP3a historical tropical cyclone ER11/TCR maximum 24-hour precipitation fields (1950–2021)

**Candidate ID:** `isimip3a.tc.er11-wind.historical.maxrain.1950-2021`  
**Provider:** ISIMIP / Potsdam Institute for Climate Impact Research (PIK); derived from IBTrACS, ERA5 and TC intensity model output  
**Categories:** `tropical_cyclone`, `extreme_precipitation`, `event_hazard_footprint`, `derived_model_output`, `global`  
**Spatial scope:** Global tropical cyclones covered by historical IBTrACS 1950–2021; gridded footprint product on global 300 arc-second (~10 km) grid  
**Temporal scope:** 1950–2021 historical; one file per calendar year (72 files), containing event-derived maximum 24-hour rain; NOT 72 independent model years  
**Resolution / granularity:** ISIMIP3a historical obsclim ER11-wind directory, maxrain NetCDF annual files. 300 arc-second grid; maximum 24-hour rainfall over each cyclone event; exact NetCDF dimension names, units and event mapping not yet checked from original bytes  
**Potential roles:** `tropical_cyclone_rain_hazard_footprint_challenge`, `storm_rain_wind_surge_shared_event_identity_crosswalk`, `historical_modelled_rainfall_calibration_research`  
**Access hint:** `public_dataset_filelist_metadata_only_no_netcdf_sample_no_rights_clearance`  
**Authoritative source:** <https://www.isimip.org/gettingstarted/input-data-bias-adjustment/details/182/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Fixed official ISIMIP dataset UUID f08ab32e-b3ad-4984-81d1-495235765b6c; public filelist https://data.isimip.org/api/v1/datasets/f08ab32e-b3ad-4984-81d1-495235765b6c/filelist/ listed 72 URLs under obsclim/global/storm/historical/ER11-wind with filename er11-wind_obsclim_historical_maxrain_YYYY.nc (1950–2021). Despite directory ER11-wind, file is maxrain, not wind speed. Storm rain footprint is reconstructed/modelled from IBTrACS storm tracks and ERA5/physical algorithms and must not count as independent track measurement, observed loss or empirical vulnerability. The exact original ISIMIP dataset API for version 20240402 declares CC0 1.0 at dataset level and in all 72 file entries, and publishes 72 SHA-512 digests and total 1,911,545,255 bytes; these are publisher metadata claims, not independently checked original NetCDF bytes or complete insurer-reuse clearance. ISIMIP terms forbid sale of the data, while each assigned licence and upstream input provenance (IBTrACS and ERA5) still require review. No NetCDF original bytes, variable headers, source SHA or live availability validated. No source admission, automated data retrieval or Neon storage authorized.
