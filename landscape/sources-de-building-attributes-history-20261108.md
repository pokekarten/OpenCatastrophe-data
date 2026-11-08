<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-de-building-attributes-history-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-de-building-attributes-history-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission discovery of three distinct German building material, historical cadastral footprint and labelled roof-feature source products. No access, rights, scientific fitness or insurance-model admission is granted by this registry.

**Entries:** 3

## Germany IOER 2022 building material cadastre (matcad2022)

**Candidate ID:** `de.ioer.material-cadastre.2022`  
**Provider:** Leibniz Institute of Ecological Urban and Regional Development (IOER FDZ)  
**Categories:** `exposure`, `buildings`, `building_materials`, `construction_typology`, `germany`  
**Spatial scope:** Germany; 16 federal states; building, 500 m and 1 km grid, and administrative aggregations  
**Temporal scope:** Building-stock reference 2022; original dataset published 2025-04-02, version 1.0  
**Resolution / granularity:** GeoPackage archive family; 44 building-material groups plus an 11-group aggregate, with building-level modelled material quantities and global-warming indicators; 41 published file entries (36 restricted)  
**Potential roles:** `construction_material_archetype_prior`, `regional_structure_cost_sensitivity`, `typology_distribution_challenge`, `building_model_lineage_audit`  
**Access hint:** `metadata_public_cc_by_4_dataset_notice_36_of_41_original_files_restricted_registration_and_permission_required`  
**Authoritative source:** <https://data.fdz.ioer.de/dataset.xhtml?persistentId=doi%3A10.71830%2FV2STEU>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Material quantities are typology-modelled, not directly observed masonry, roof material or structural condition for each building. Derived from IOER 3D Building Metrics 2022 and official LoD2, which overlap existing building geometry and cannot serve as independent footprint ground truth. The original data portal displays 36 restricted files out of 41 despite the dataset-level CC BY 4.0 notice; verify exact file rights, allowed commercial/derivative use and original file hashes before retrieval. Do not infer GEM construction taxonomy, insured TIV or calibrated vulnerability without distinct evidence.

## North Rhine-Westphalia official historical house outlines 2016 to 2022

**Candidate ID:** `de.nrw.geobasis.historical-house-outlines.2016-2022`  
**Provider:** Geobasis NRW / Bezirksregierung Koeln; official GovData catalogue  
**Categories:** `buildings`, `historical_footprints`, `cadastral`, `exposure_history`, `germany`  
**Spatial scope:** North Rhine-Westphalia, Germany; historical state-wide ALKIS-derived outlines  
**Temporal scope:** Annual historical releases for 2016-2022; catalogue metadata amended 2026-09-03  
**Resolution / granularity:** Shapefile polygon stock with over 10 million building and above-ground surface-structure outlines per historical vintage; municipality code from 2016, source object ID, function and currency date from 2020  
**Potential roles:** `historical_exposure_reconstruction`, `building_change_detection`, `footprint_version_holdout`, `cadastral_identity_matching`  
**Access hint:** `public_official_catalogue_historical_shapefile_original_year_archives_licence_and_download_path_review`  
**Authoritative source:** <https://data.gov.de/suche/daten/historische-hausumringe-nw>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Different product from current NRW LoD2 OGC API source in PR #1425 and from the specific 2022 HU original-byte OED sample in PR #1373. All footprints originate from ALKIS and share source lineage with contemporary state cadastral data. Before comparing years, pin exact original archive/year, CRS, licence, stable IDs (only provided starting 2020), update timing and polygon change/split rules. Appearance, disappearance or changed geometry in a snapshot does not alone prove a real construction, demolition, insurance inception or historical hazard exposure.

## TUM RID 2022 annotated roof segments and superstructures

**Candidate ID:** `de.tum.rid.roof-labels.2022`  
**Provider:** Technical University of Munich (TUMFTM) / TUM university library  
**Categories:** `buildings`, `rooftops`, `imagery_annotations`, `roof_obstructions`, `training_sample`, `germany`  
**Spatial scope:** Limited annotated building/roof-centred research sample; not a Germany-wide roof inventory  
**Temporal scope:** Original data and associated peer-reviewed paper published 2022; exact image acquisition dates require checking  
**Resolution / granularity:** 1,880 labelled building-centred aerial images; masks for roof segment direction/flat areas and roof superstructures including dormers, chimneys, windows and photovoltaic panels; code and image archives separately distributed  
**Potential roles:** `roof_annotation_quality_challenge`, `roof_feature_class_dictionary`, `image_segmentation_research`, `pv_roof_equipment_presence_benchmark`  
**Access hint:** `public_research_metadata_and_download_potential_separate_code_lgpl3_and_aerial_image_commercial_reuse_review`  
**Authoritative source:** <https://doi.org/10.14459/2022mp1655470>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Related code and annotations at https://github.com/TUMFTM/RID and research paper https://doi.org/10.3390/rs14102299. The 1,880 annotated roofs are not a random or representative national sample and neither roof obstruction class nor roof orientation identifies roofing material or wind/hail resistance. Repository LGPL-3.0 applies to code and does NOT grant commercial-training or redistribution rights to underlying third-party aerial/satellite imagery (README mentions Google imagery with noncommercial/fair-use framing). Verify individual asset licensing, retention and model training rights before downloading images or using labels in a CAT pipeline.
