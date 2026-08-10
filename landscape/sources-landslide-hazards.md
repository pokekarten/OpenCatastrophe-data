<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-landslide-hazards.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-landslide-hazards.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of landslide and mass-movement hazard sources relevant to catastrophe modelling, validation and compound-hazard analysis.

**Entries:** 2

## USGS Landslide Inventories across the United States v3.0

**Candidate ID:** `usgs.landslide-inventories.v3`  
**Provider:** U.S. Geological Survey Landslide Hazards Program  
**Categories:** `landslides`, `mass_movements`, `spatial_inventory`, `event_catalogue`, `hazard_validation`  
**Spatial scope:** United States  
**Temporal scope:** version 3.0 release dated February 2025; constituent inventories span heterogeneous historical periods and event-date precision  
**Resolution / granularity:** integrated point and polygon inventories distributed as GPKG, SHP and CSV with USGS_ID, source-inventory linkage, machine-readable date bounds, landslide type and relative confidence metadata  
**Potential roles:** `landslide_inventory_validation`, `spatial_susceptibility_benchmarking`, `source_lineage_analysis`, `regional_generalization_checks`  
**Access hint:** `public_data_release_multiple_geospatial_formats`  
**Authoritative source:** <https://www.usgs.gov/data/landslide-inventories-across-united-states-ver-30-february-2025>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** USGS identifies DOI 10.5066/P14AJF8I and marks the v3.0 release CC0 1.0, but any future admission still needs exact file identities and scope review. The integrated database intentionally preserves heterogeneous constituent inventories: date ranges may be uncertain, classification methods vary, confidence is relative rather than a formal field-attribute accuracy score, and some retained features are not strictly landslides, including gullies or avalanche chutes. Preserve Inventory/Inv_URL provenance instead of treating the compilation as homogeneous ground truth.

## NASA Landslide Hazard Assessment for Situational Awareness (LHASA) 2.1

**Candidate ID:** `nasa.lhasa.2.1`  
**Provider:** NASA Goddard Space Flight Center  
**Categories:** `landslides`, `hazard_nowcast`, `model_output`, `rainfall_triggered_hazards`, `compound_hazards`  
**Spatial scope:** global  
**Temporal scope:** public web-map metadata states April 2021 to present with twice-daily updates at review time  
**Resolution / granularity:** approximately 30 arcseconds (~1 km) global model-derived hazard nowcast/exposure layers using satellite and forecast inputs  
**Potential roles:** `landslide_nowcast_benchmarking`, `rainfall_triggered_hazard_context`, `compound_hazard_screening`, `operational_model_comparison`  
**Access hint:** `public_arcgis_feature_and_imagery_services`  
**Authoritative source:** <https://gis.earthdata.nasa.gov/portal/home/item.html?id=9e65a60a305b458bba6330baa93c0238>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NASA describes LHASA 2.1 as a global monitoring/nowcast product and explicitly says it is not a substitute for local site investigations. This is model-derived hazard output, not observed landslide truth; public metadata cites GPM/SMAP inputs and a machine-learning nowcast. Because NASA landslide catalog observations are used to develop or verify landslide models, any future evaluation must establish lineage and split independence before using COOLR/GLC and LHASA together as supposedly independent evidence.
