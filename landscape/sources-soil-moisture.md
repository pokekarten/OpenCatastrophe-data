<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-soil-moisture.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-soil-moisture.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of potentially useful catastrophe-risk data sources.

**Entries:** 1

## SMAP Enhanced L3 Radiometer Global and Polar Grid Daily 9 km EASE-Grid Soil Moisture, Version 6

**Candidate ID:** `nasa.nsidc.smap.spl3smp-e.v6`  
**Provider:** NASA National Snow and Ice Data Center Distributed Active Archive Center  
**Categories:** `soil_moisture`, `drought`, `remote_sensing`, `validation`  
**Spatial scope:** global land surface  
**Temporal scope:** 31 March 2015 to present  
**Resolution / granularity:** daily composite; surface-soil-moisture retrievals posted to 9 km EASE-Grid 2.0  
**Potential roles:** `soil_moisture_state_validation`, `drought_state_context`, `antecedent_wetness_context`  
**Access hint:** `earthdata_login_required`  
**Authoritative source:** <https://nsidc.org/data/spl3smp_e/versions/6>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Enhanced Level-3 passive-microwave retrieval derived through the SMAP radiometer L2/L1C processing chain and Backus-Gilbert interpolation; the 9 km posting grid is not parcel-scale in-situ truth. The repository also tracks SMAP L4 SPL4SMGP v8, a distinct model/assimilation-derived product; L3 and L4 share SMAP/upstream observation lineage and must not be treated as automatically independent validation evidence. Freeze version, subset, time range, AM/PM semantics and retrieval/surface quality flags before scientific use.
