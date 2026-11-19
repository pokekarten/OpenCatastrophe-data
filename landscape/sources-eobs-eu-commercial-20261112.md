<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-eobs-eu-commercial-20261112.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-eobs-eu-commercial-20261112.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-12`  
**Purpose:** Non-admission discovery registry for the newly separated, commercially reusable Copernicus E-OBS_EU product and its strict difference from research-only E-OBS.

**Entries:** 1

## E-OBS_EU daily gridded European observations (open-licence product)

**Candidate ID:** `copernicus.c3s.e-obs-eu.open-20261104`  
**Provider:** Copernicus Climate Change Service / ECMWF / ECA&amp;D  
**Categories:** `climate_observations`, `precipitation`, `temperature`, `wind`, `validation`, `commercial_use_candidate`  
**Spatial scope:** European Union member states plus Norway, Switzerland, Iceland and the United Kingdom; do not treat as the broader Europe-wide E-OBS product  
**Temporal scope:** New separately licensed product announced 2026-11-04; exact requested field, temporal extent and version must be frozen per retrieved CDS product  
**Resolution / granularity:** Station-derived, spatially interpolated daily gridded observations on 0.1 and 0.25 degree latitude-longitude grids; product-dependent versions and uncertainty fields  
**Potential roles:** `commercially_licensed_climate_observation_candidate`, `extreme_precipitation_validation`, `temperature_extremes_validation`, `wind_context_validation`  
**Access hint:** `cds_account_and_licence_acceptance_required_for_data_download_cc_by_4_0_product_only`  
**Authoritative source:** <https://cds.climate.copernicus.eu/datasets/insitu-gridded-observations-europe>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official product-specific licence https://cds.climate.copernicus.eu/licences/licence-to-use-E-OBS-and-E-OBS-EU-products (reviewed 2026-11-12) declares E-OBS_EU CC BY 4.0, including commercial reuse subject to attribution. Whole-Europe E-OBS is separate and strictly non-commercial research/education only. ECMWF announced the revised CDS implementation on 2026-11-04; old API request syntax must not be assumed valid. Station-network lineage is shared with E-OBS and weather fields are not independent raw station truths. This candidate is not dataset admission, not verified API execution, not permission to copy station input bytes, and not yet an authorized source sample.
