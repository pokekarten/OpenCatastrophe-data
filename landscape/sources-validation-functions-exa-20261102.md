<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-validation-functions-exa-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-validation-functions-exa-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery of three original or research-curated catastrophe model validation source products found in an Exa/GitHub cross-check, covering observed flood extents, infrastructure vulnerability curves and historical seismic fragility; no data acquisition or model approval.

**Entries:** 3

## Global Flood Inundation Map Repository (GloFIMR) historical event extents

**Candidate ID:** `ua.sdml.glofimr.historical-flood-extents`  
**Provider:** University of Alabama Surface Dynamics Modeling Lab / contributing Dartmouth Flood Observatory and satellite sources  
**Categories:** `flood`, `observed_inundation`, `remote_sensing`, `validation`  
**Spatial scope:** Selected river flood events, primarily United States with some other countries (including Bangladesh); not a globally complete event archive  
**Temporal scope:** Historical individual flood dates visible in provider inventory, including events from 1997 to 2017; current update completeness unverified  
**Resolution / granularity:** Event-specific Shapefile flood inundation polygons derived from Landsat and Sentinel satellite images, nominal sensor input 10 m or 30 m  
**Potential roles:** `observed_flood_footprint_validation`, `event_hazard_spatial_crosswalk`, `flood_model_calibration_challenge`  
**Access hint:** `public_event_shapefile_links_documented_terms_not_reviewed_no_automated_download`  
**Authoritative source:** <https://sdml.ua.edu/glofimr/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider page has per-event inventory with platform, date, river, mapped extent and some Shapefile links, but its global title does not mean comprehensive global coverage or ongoing operations. Selected records are sourced from DFO; identify original event/scene/source lineage and do not treat DFO and GloFIMR copies as independent hazard observations. Water extent is not depth or insured loss. Review each file's licence, download reliability, geometry validity and remote sensing classification uncertainty before a bounded source receipt.

## Infrastructure Vulnerability Curves CSV collection (394 curves)

**Candidate ID:** `sebkrantz.infrastructure-vulnerability-curves.2026`  
**Provider:** Sebastian Krantz / derived from Nirandjan et al. 2024 global critical infrastructure vulnerability research  
**Categories:** `vulnerability`, `critical_infrastructure`, `flood`, `earthquake`, `wind`, `landslide`  
**Spatial scope:** Globally applicable research curves conditional on infrastructure asset types and original source applicability; not location-specific field validation  
**Temporal scope:** GitHub repository established March 2026; curves derived from 2024 peer-reviewed research  
**Resolution / granularity:** 394 per-curve two-column CSV files grouped by peril, physical intensity metric and sector; intensities span mm, cm/s, cm/s2, g, km/h and other source-native units  
**Potential roles:** `infrastructure_vulnerability_library`, `multi_peril_damage_function_benchmark`, `loss_engine_unit_contract_tests`  
**Access hint:** `public_github_csv_cc0_repository_claim_original_paper_and_derived_dataset_rights_need_review`  
**Authoritative source:** <https://github.com/SebKrantz/VulnerabilityCurves>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Repository states 394 CSV vulnerability curves from Nirandjan et al. (2024, DOI 10.5194/nhess-24-4341-2024) and displays CC0, but check upstream supplementary-data terms and provenance before commercial adoption. Not all outputs are damage ratios: specific earthquake water/wastewater curves represent pipe repair rates or damaged pipes per km. Preserve exact asset taxonomy, hazard intensity units, curve bounds a/b and source DOI; never apply a generic damage factor to mismatched assets or derive insured TIV from a curve. This is a repackaging of research evidence, not an independent loss observation.

## Martins and Silva global seismic fragility and vulnerability functions (2020 historical set)

**Candidate ID:** `martins.silva.global-seismic-fragility-vulnerability.2020`  
**Provider:** Luis Martins and Vitor Silva / original authors, GEM-linked research  
**Categories:** `earthquake`, `seismic_fragility`, `vulnerability`, `research_benchmark`  
**Spatial scope:** Generic global building classes within the taxonomy and engineering assumptions of the original study; local transferability requires validation  
**Temporal scope:** Companion repository for Martins and Silva 2020 study; subsequent model improvements and later GEM versions exist  
**Resolution / granularity:** Downloadable building-class seismic fragility and vulnerability function tables associated with a 2020 publication  
**Potential roles:** `historical_seismic_vulnerability_benchmark`, `building_taxonomy_crosswalk`, `seismic_loss_sensitivity_comparison`  
**Access hint:** `public_author_repository_downloadable_functions_citation_required_exact_data_rights_not_reviewed`  
**Authoritative source:** <https://github.com/lmartins88/global_fragility_vulnerability>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Managed by the study authors, who request citation of Martins and Silva (2020) and refer users to GEM for newer versions. Treat this as a historical lineage/validation benchmark, not a separate or newer independent dataset alongside already registered gem.global-vulnerability-model.v2026.0.0 or EFEHR regional curves. Verify repository contents, construction-system taxonomy, ground-motion intensity definition, loss metric, interpolation assumptions, licence and whether each function has subsequent corrections before admitting any use.
