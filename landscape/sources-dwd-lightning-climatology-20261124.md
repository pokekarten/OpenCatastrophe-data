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
**Spatial scope:** Central Europe in product title; Germany in metadata coverage field; actual grid bounds unverified  
**Temporal scope:** January 2007 onward; monthly additions per DWD documentation  
**Resolution / granularity:** Monthly NetCDF grids at 0.05 x 0.05 degrees, EPSG:4326; flash counts and mean current in kA  
**Potential roles:** `convective_climatology`, `hail_frequency_covariate`, `regional_model_calibration`  
**Access hint:** `public_http_download`  
**Authoritative source:** <https://opendata.dwd.de/climate_environment/CDC/grids_europe/monthly/lightning/BESCHREIBUNG_1c266171-e0fe-446e-b88c-43a508d900ad_de.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official product description dated 2025-10-02 explicitly states CC BY 4.0 for the gridded product; do not extend this to raw LINET data. DWD describes a spatial association between mean current and hail probability, not event-level hail size or causation. Method reference: https://doi.org/10.20944/preprints202502.1749.v2 (preprint). Monthly counts cannot reconstruct storm tracks or lightning jumps. Confirm actual coverage, fill values, count definition, current sign/aggregation, missing observation intervals, grid-cell area and network changes before analysis; never interpret missing coverage as zero hazard. Exact historical file bytes and directory access not verified in this run; no data sample, database write or admission. A future test should compare matched monthly count/current rasters against independent radar hail climatology using held-out regions and years, including a count-only baseline and an ERA5 baseline.
