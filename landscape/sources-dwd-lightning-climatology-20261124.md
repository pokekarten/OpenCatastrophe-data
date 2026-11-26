<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-dwd-lightning-climatology-20261124.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-dwd-lightning-climatology-20261124.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-24`  
**Purpose:** Non-admission discovery record for DWD monthly lightning climatology as a hail hazard covariate.

**Entries:** 1

## DWD CDC monthly lightning climatology v1.0

**Candidate ID:** `dwd.cdc.lightning.monthly.v1`  
**Provider:** Deutscher Wetterdienst / LINET (Nowcasting AG)  
**Categories:** `lightning`, `hail`, `convective_storm`, `climatology`  
**Spatial scope:** Central Europe; July 2013 sample grid centers verified at 46 to 56 degrees N and 5 to 16 degrees E; rectangular extent does not certify detection coverage  
**Temporal scope:** January 2007 onward per documentation; December 2025 is the latest month listed in both directories checked on 2026-11-24; completeness across all months not tested  
**Resolution / granularity:** Monthly NetCDF4/HDF5 grids; July 2013 sample verified at 0.05 x 0.05 degrees, EPSG:4326, 1 x 201 x 221 (time, latitude, longitude); LInum (unit 1) and LIkA (kA)  
**Potential roles:** `convective_climatology`, `hail_frequency_covariate`, `regional_model_calibration`  
**Access hint:** `public_http_download`  
**Authoritative source:** <https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/BESCHREIBUNG_1c266171-e0fe-446e-b88c-43a508d900ad_de.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official product description (2025-10-02) and both sample file headers explicitly state CC BY 4.0 for the gridded product, not raw LINET. On 2026-11-24 a bounded HTTPS download of two July 2013 files succeeded via macOS, after Linux DNS failure. Original compressed bytes: https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/density/LInumsum201307.nc.gz (59485 bytes, SHA-256 2b6d5dfc1da8977e9a351dc2913cfd093c539bebde68b19911ff3224bfc320cf); https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/mean_amperage/LIkAmm201307.nc.gz (150582 bytes, SHA-256 d1e28898bc430c489bd4916b9a54dc90d1d3c82511f0d23a99adba872b2145da). Gzip integrity passed; h5py 3.16.0 and NumPy 2.5.5 read both HDF5 files. Both advertise CF-1.6, LIclim-Linet-v1, float64 data, fill/missing -0.01, and identical lat/lon/time arrays (time zero hours since 2013-07-01 00:00:00). All 44421 data cells finite and not fill in this sample; matching zero masks (11914 cells); 32507 positive count cells. LInum is integer-valued (0 to 672, sum 969164); LIkA ranges 0 to 5.998963253472441 kA. Pearson correlation of log1p(LInum) and LIkA over positive-count cells is 0.4297129826308147; this is descriptive, not hail validation. Method reference: https://doi.org/10.20944/preprints202502.1749.v2 (preprint), section 2, describes hourly summed amperage divided by hourly lightning count and then monthly averaging. Do not interpret LIkA as peak current or a monthly count-weighted mean; zero-current cells with zero count are not measured low-current strikes. Confirm exact current normalization, detection efficiency, network changes and missing-hour handling; never interpret missing coverage as zero hazard. Monthly data cannot reconstruct storm tracks, hail size or lightning jumps. Validate against independent radar hail climatology with held-out years and regions; compare count-only, ERA5-only and combined models. Original bytes remain outside Git; no database write, full-series test, formal rights or scientific approval, or admission.
