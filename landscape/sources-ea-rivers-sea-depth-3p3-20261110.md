<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-ea-rivers-sea-depth-3p3-20261110.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-ea-rivers-sea-depth-3p3-20261110.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-10`  
**Purpose:** Non-admission original Environment Agency source discovery of two distinct defended 3.3 percent AEP river/sea depth products missing from the existing 2026 EA flood family; research-only metadata, no original geospatial assets or approved loss model.

**Entries:** 2

## England Environment Agency 3.3% AEP defended river and sea flood depths - present day

**Candidate ID:** `uk.ea.rivers-sea-depth-3p3.present.2026`  
**Provider:** Environment Agency / Defra Data Services Platform  
**Categories:** `flood`, `river_flood`, `coastal_flood`, `defended`, `hazard_depth`, `england`  
**Spatial scope:** England where the national flood-zone modelling depth layers are available; the original publisher marks unsupported areas as Unavailable  
**Temporal scope:** Present-day static scenario, official catalogue last modified 2026-10-30  
**Resolution / granularity:** Seven flood-depth bands in mm (up to 150; 150-300; 300-600; 600-900; 900-1200; 1200-2300; over 2300), 3.3% AEP (approximately 1-in-30 years) river/sea; EPSG:27700; catalogue lists WFS, OGC API Features, WMS, GPKG/GeoJSON/GDB ZIP  
**Potential roles:** `aep_3p3_river_sea_hazard_screening`, `defended_1in30_flood_depth_scenario_benchmark`, `england_hazard_curve_shape_sanity_check`  
**Access hint:** `public_ea_ckan_2026_ogl_label_machine_asset_rights_and_service_terms_not_admitted`  
**Authoritative source:** <https://www.data.gov.uk/dataset/2b1dc7a4-ff9f-42fd-9971-11638eabf814/rivers-and-sea-3-3-defended-flood-risk-depths-present-day>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original data.gov.uk CKAN package UUID 2b1dc7a4-ff9f-42fd-9971-11638eabf814, modified 2026-10-30T14:00:33.438078, with exactly nine documented catalogue resources: 3 archive formats, product PDF, layer style, download landing page, WFS/WMS and OGC API Features. UK OGL label in product catalogue does not equal exact asset right/admission. Defences are assumed to operate as designed; failure not represented. Unavailable must never be mapped to zero. This 3.3% AEP defended scenario has no undefended companion in this product and is not the independent third stochastic flood event or observed property depth. Shared national modelling lineage with the EA present-day 0.1% and river 1%/sea 0.5% products; do not add scenario counts or multiply loss curves independently. AEP is a scenario exceedance probability, not an event-frequency/occurrence catalogue.

## England Environment Agency 3.3% AEP defended river and sea flood depths - climate change

**Candidate ID:** `uk.ea.rivers-sea-depth-3p3.climate.2026`  
**Provider:** Environment Agency / Defra Data Services Platform  
**Categories:** `flood`, `river_flood`, `coastal_flood`, `defended`, `climate_scenario`, `hazard_depth`, `england`  
**Spatial scope:** England where national flood-zone depth simulations are available, with explicit Unavailable attribute outside supported areas  
**Temporal scope:** Projected 2080s river central allowance 2070-2125 and upper-end coastal sea-level rise allowance to 2125 under UKCP18 RCP8.5; catalogue last modified 2026-10-30  
**Resolution / granularity:** Seven flood-depth bands up to and above 2300 mm, 3.3% AEP defended river/sea climate-change scenario, EPSG:27700; nine catalogue resources including GPKG/GeoJSON/GDB ZIP, WFS, WMS and OGC API  
**Potential roles:** `climate_1in30_flood_scenario_sensitivity`, `regional_hazard_scenario_alignment`, `defence_assumption_counterfactual_comparison`  
**Access hint:** `public_ea_ckan_2026_ogl_label_exact_asset_and_api_terms_unreviewed_not_admitted`  
**Authoritative source:** <https://www.data.gov.uk/dataset/9d5e56d5-7713-42a1-890f-3d0a3e895cd5/rivers-and-sea-3-3-defended-flood-risk-depths-climate-change>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original data.gov.uk CKAN package UUID 9d5e56d5-7713-42a1-890f-3d0a3e895cd5, modified 2026-10-30T14:00:32.171469; nine documented catalogue resources: three formats, product PDF, style, download landing, WFS/WMS and OGC API. Publisher models UKCP18 RCP8.5 climate allowances; existing flood defences assumed unchanged, not a projection of future defence works or failure. This cannot be interpreted as an independent historical 1-in-30 event, insured-building water depth, claims dataset, or calibrated climate-change AEP curve. Scenario lineage overlaps present-day and EA river/sea climate datasets. Missing Unavailable support is not zero. Rights and source-scientific reviews remain required for actual spatial feature access.
