<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-open-lightning-climatology-alternatives-20261125.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-open-lightning-climatology-alternatives-20261125.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-25`  
**Purpose:** Non-admission discovery of independently versioned open-first global lightning climatology alternatives.

**Entries:** 2

## WGLC 2019 PANGAEA global lightning climatology and monthly density

**Candidate ID:** `pangaea.wglc.lightning.2019`  
**Provider:** Kaplan and Lau / PANGAEA  
**Categories:** `lightning`, `climatology`, `convective_storm`  
**Spatial scope:** Global WGS84  
**Temporal scope:** 2010-2018  
**Resolution / granularity:** 0.5 degree monthly NetCDF4, 108 months and 12 climatological bins  
**Potential roles:** `global_convective_frequency_calibration`, `lightning_climatology_benchmark`  
**Access hint:** `public_versioned_download`  
**Authoritative source:** <https://doi.pangaea.de/10.1594/PANGAEA.904253>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct immutable DOI release; not a licence for 2026 WGLC or raw WWLLN. PANGAEA landing page explicitly CC BY 4.0 and gives ZIP locator https://store.pangaea.de/Publications/KaplanJ-LauH_2019/WWLLN.zip. On 2026-11-25 bounded HTTPS GET on macOS downloaded 37038662 bytes, SHA-256 ef9ef83797f861c68930856ab4f57e392d575c79e7ca46bc7c2f8cf13e19f7d5. ZIP CRC check passed; two entries WWLLN_climatology.nc (5947906 bytes) and WWLLN_monthly.nc (31343698 bytes). HDF5 inspection of climatology verified lon 720, lat 360, time 12, lightning shape 12 x 360 x 720, units strokes km-2, CF-1.7 and source AE detection-efficiency corrected stroke counts. Calendar units days since 0000-01-01 00:00:00 require explicit CF calendar handling; monthly file not yet parsed. Stroke counts not optical flashes; monthly density cannot track storms. Open-first priority: complete exact archive reuse/API review, inspect monthly data/missingness/cell-area and compare to independent radar hail frequencies. No raw bytes in Git or Neon; not admitted.

## NASA LIS/OTD Reprocessed Flash Climatology

**Candidate ID:** `nasa.ghrc.lis-otd.reprocessed.lorfc`  
**Provider:** NASA GHRC DAAC / Cecil et al.  
**Categories:** `lightning`, `climatology`, `convective_storm`  
**Spatial scope:** Near-global orbital coverage; mission-dependent latitudes  
**Temporal scope:** OTD April 1995-March 2000; TRMM LIS December 1997-April 2015; ISS LIS March 2017-November 2023, 27 sampled calendar years  
**Resolution / granularity:** 0.1 degree gridded annual mean flash rate, annual/diurnal cycle and mission-specific time series  
**Potential roles:** `global_convective_frequency_calibration`, `lightning_climatology_benchmark`  
**Access hint:** `earthdata_login_protected_download`  
**Authoritative source:** <https://doi.org/10.5067/LIS/LISCLIMO/DATA101>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NASA catalog https://catalog.data.gov/dataset/lis-otd-reprocessed-flash-climatology identifies US government works rights label and collection C3671144020-GHRC_DAAC; paper https://doi.org/10.1175/JAMC-D-25-0110.1. Live anonymous CMR granule query on 2026-11-25 returned COMB_OTD_TRMM_ISS_AnnualMean.hdf, COMB_OTD_TRMM_ISS_AnnualDiurnalCycle.hdf, COMB_OTD_TRMM_ISS_AnnualCycle.hdf and OTD monthly/annual files under https://data.ghrc.earthdata.nasa.gov/ghrcw-protected/lorfc__2/. Combined granules span 1995-04-13 to 2023-11-16; not continuous observing time. CMR reported granule_size 0, not evidence files are empty or free to acquire. Exact version, Earthdata account and HDF reader required; review mission-specific rights, detection efficiency, observation opportunity, time bins and units. No original payload downloaded. Use as frequency/diurnal context, not hail events.
