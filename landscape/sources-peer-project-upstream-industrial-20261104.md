<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-peer-project-upstream-industrial-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-peer-project-upstream-industrial-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of original industrial and built-environment providers found by inspecting NCCS mining and GFDRR Urban Validation configuration sources; no asset bytes, approved rights or scientific admission.

**Entries:** 3

## PANGAEA Maus Global-scale Mining Polygons Version 2

**Candidate ID:** `pangaea.maus.global-mining-polygons.v2.2022`  
**Provider:** Maus et al. / PANGAEA repository  
**Categories:** `industrial_exposure`, `mining`, `land_use`, `infrastructure`  
**Spatial scope:** Global locations within sampled mining areas; not complete mines or ownership  
**Temporal scope:** 2019 satellite background, published 2022-03-14  
**Resolution / granularity:** 44,929 polygons, 101,583 square km; GPKG, CSV and grids at 30 arc seconds / 5 arc minutes / 30 arc minutes; area in square kilometres  
**Potential roles:** `synthetic_industrial_footprint_prior`, `mining_area_validation`, `sector_spatial_allocation`  
**Access hint:** `public_repository_original_cc_by_sa4_secondary_catalog_conflict_review`  
**Authoritative source:** <https://doi.org/10.1594/PANGAEA.942325>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NCCS original mining README cites the PANGAEA v2 DOI and 30 arc-second global_miningarea_v2_30arcsecond.tif as its industry allocation grid. Original PANGAEA page specifies CC BY-SA 4.0, whereas secondary EC Africa Knowledge Platform catalog shows CC BY 4.0: original provider terms are authoritative, but exact selected asset and third-party source imagery rights require review. Derived from visual interpretation of 2019 Sentinel-2, with 34,820 S&amp;P mining location sample/10-km buffer and supplementary Google/Bing viewing; spatial selection and human judgement bias apply. Validation reported 88.3% accuracy and 0.87 F1. Mining polygons/area are not unique facility owners, production or insured TIV.

## Microsoft AI for Good global temporal building density and height COGs

**Candidate ID:** `microsoft.aiforgood.building-density-height.temporal-v1`  
**Provider:** Microsoft AI for Good / Microsoft Buildings  
**Categories:** `exposure`, `buildings`, `height`, `change_detection`, `remote_sensing`  
**Spatial scope:** Global ~100 m public raster for two snapshots; 40 m quarterly tiles cover five named regions only  
**Temporal scope:** Global 2020 Q4 and 2023 Q4; selected-site quarters 2020 Q2 through 2025 Q2  
**Resolution / granularity:** GeoPackage tile index at https://opendata.aiforgood.ai/building-density/tile_index.gpkg, COG two bands: density 0..1 and height_norm 0..1 (multiply by 100 metres), nodata -1; 100 m global grids  
**Potential roles:** `built_volume_proxy`, `urban_growth_prior`, `geospatial_footprint_validation`  
**Access hint:** `public_tile_index_and_cog_data_software_mit_data_and_planet_imagery_terms_unreviewed`  
**Authoritative source:** <https://github.com/microsoft/buildings>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GFDRR urban_validation uses original Microsoft TEMPO tile_index.gpkg; original microsoft/buildings README pins v1 (2020q4 and 2023q4) and spatial/temporal band semantics. Derived from PlanetScope quarterly imagery via machine learning; not observed roof polygons, floor area or insured TIV. MIT repository LICENSE is software permission and does not automatically grant redistribution/commercial rights to third-party Planet imagery or all generated data layers. Record selected quarter, tile coordinates, EPSG:3857 index, COG geotransform and exact URL before model work.

## Austrian World Mining Data 2026 mineral commodity production statistical tables

**Candidate ID:** `austria.bmf.world-mining-data.2026`  
**Provider:** Republic of Austria Federal Ministry of Finance  
**Categories:** `mining`, `economic_production`, `commodities`, `sector_exposure`  
**Spatial scope:** 168 producing countries, 65 mineral commodities; reporting completeness country dependent  
**Temporal scope:** Edition 2026: production years 2020-2024; historical editions separate  
**Resolution / granularity:** Annual official report PDF and Excel chapters 6.1-6.6 with national production by commodity and comparison tables  
**Potential roles:** `national_mining_production_prior`, `sector_value_allocation`, `industrial_exposure_crosscheck`  
**Access hint:** `public_pdf_and_excel_official_statistical_publication_commercial_reuse_terms_unverified`  
**Authoritative source:** <https://www.bmf.gv.at/en/topics/mining/mineral-resources-policy/wmd.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original Austrian ministry page identifies World Mining Data 2026 as current edition and associated Excel tables, based on national surveys, BGS/USGS crosschecks and some explicitly estimated production. NCCS mining code cites WorldMiningData 2021 for ROW value allocation, not the 2026 edition: later 2020-2024 figures cannot silently replace WIOD 2011 production values or retrospective original 2021 model inputs. Production tonnage or economic activity is not replacement cost/insured value; datafile licence, units and prices require original review.
