<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-cross-domain-exposure-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-cross-domain-exposure-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of construction-typology priors, country-level modelled CAT exposure and US electricity generation assets for cross-domain exposure enrichment; all data rights and scientific model-input scopes remain unapproved.

**Entries:** 3

## UCAD global architectural and construction-material typologies v5

**Candidate ID:** `cnrm.ucad.architectural-typologies.v5`  
**Provider:** CNRM / Météo-France / CNRS and UCAD collaborators  
**Categories:** `buildings`, `construction_materials`, `building_typologies`, `vulnerability_covariates`  
**Spatial scope:** Country-level residential architectural archetypes worldwide; generic non-residential typologies  
**Temporal scope:** Zenodo v5 published 2026-09-09, correcting mid-rise Norway wall material compared with earlier releases; heterogeneous original survey vintages  
**Resolution / granularity:** Residential typology CSV tables and GeoPackage, global non-residential CSV, survey methodology and imputation/correction evidence; wall, roof, window, HVAC and infiltration attributes  
**Potential roles:** `construction_material_prior`, `fragility_typology_research`, `building_attribute_imputation_challenge`  
**Access hint:** `public_versioned_zenodo_csv_gpkg_download_cc_by_4_0_record_file_rights_recheck`  
**Authoritative source:** <https://zenodo.org/records/22674166>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher Zenodo v5 record (DOI 10.5281/zenodo.22674166) declares CC BY 4.0; exact file scope and attribution still require source-specific rights admission. v5 explicitly corrects Norway mid-rise wall material compared with previous versions, so v3 must not be silently combined with v5. Country/typology-level surveys and imputed attributes are NOT verified material facts for individual EUBUCCO/Overture footprints; preserve survey/imputation flags and source versions when deriving uncertain vulnerability priors.

## METEOR Level 1 modelled exposure and Oasis OED sample files

**Candidate ID:** `meteor.global-exposure.oed.level1.2020`  
**Provider:** METEOR Project Consortium / ImageCat  
**Categories:** `modelled_exposure`, `buildings`, `oasis_oed`, `replacement_value_proxy`  
**Spatial scope:** Selected low- and middle-income countries across Africa, Asia, Pacific and Haiti; not comprehensive global exposure coverage  
**Temporal scope:** Original 2020 public exposure publication; individual country input and rebuilding cost vintages differ  
**Resolution / granularity:** Approximately 15-arcsecond grid (~500 m equator) point cell totals for estimated buildings, area and rebuilding value; separate OED location and placeholder-account CSV files  
**Potential roles:** `oasis_oed_import_reference`, `coarse_exposure_model_challenge`, `residential_structural_taxonomy_research`  
**Access hint:** `public_country_download_cc_by_nc_sa_4_0_no_commercial_automated_admission`  
**Authoritative source:** <https://meteor-project.org/data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider states Creative Commons BY-NC-SA 4.0: do NOT promote this source into a commercial insurance model or redistribute downstream assets without an explicit legal scope decision. Gridded counts/values are estimates rather than insured policy counts or actual addresses. OED Accounts use intentionally default placeholders (e.g. AccNum=1), not actual contracts. Freeze individual country release, cost basis, currency/year, and upstream census/EO assumptions.

## EIA-860M preliminary monthly electric generator inventory

**Candidate ID:** `us.eia.operable-generator-inventory.860m`  
**Provider:** United States Energy Information Administration  
**Categories:** `critical_infrastructure`, `power_plants`, `energy`, `exposure_context`  
**Spatial scope:** United States and Puerto Rico; power plants with combined capacity at least 1 MW  
**Temporal scope:** Monthly preliminary inventory; September 2026 data published 2026-10-23, superseded by later corrections and annual EIA-860  
**Resolution / granularity:** Plant and generator records including EIA identifiers, generator status/capacity, primary fuel and plant coordinates; published XLS and related EIA API reporting  
**Potential roles:** `power_plant_location_context`, `critical_infrastructure_hazard_overlay`, `generator_status_time_crosswalk`  
**Access hint:** `public_monthly_xls_and_eia_operable_generator_api_exact_vintage_reuse_review`  
**Authoritative source:** <https://www.eia.gov/electricity/data/eia860m/index.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official EIA-860M is a preliminary generator inventory and can change with revised reporting; exact monthly workbook and record status must be pinned. The EIA FAQ identifies county/state/lat/long in the monthly survey and public API route for operable-generator capacity, but API version and field equivalence to workbook must be tested independently. Generator capacity is not replacement value, business-interruption loss or insurer coverage. Join by stable EIA plant ID and verified coordinates, not name-only fuzzy matching.
