<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-fao-cropgrids-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-fao-cropgrids-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission source discovery of a modelled global crop-area comparator to MapSPAM 2020; original CROPGRIDS and derived FAO/CGIAR file identities, data rights and scientific dependence require independent review.

**Entries:** 1

## FAO CROPGRIDS 2020 global crop and harvested area maps

**Candidate ID:** `fao.cropgrids.2020.global`  
**Provider:** Food and Agriculture Organization of the United Nations (FAO) / CROPGRIDS research consortium  
**Categories:** `agriculture`, `crop_exposure`, `crop_area`, `harvested_area`, `geospatial`, `model_comparison`  
**Spatial scope:** Global land grid, 0.05 degree (~5.6 km at equator); maps are modelled allocation, not field or insured parcel observations  
**Temporal scope:** Crop physical and harvested area for reference year 2020; original scientific data descriptor published 2024 and FAO page updated 2025, distinct from 2026 CGIAR COG rehosting  
**Resolution / granularity:** 173 crop identities at approximately 0.05-degree grid with physical crop area and harvested area; original research release NetCDF on Figshare DOI 10.6084/m9.figshare.22491997, FAO CGIAR 2.0 cloud COG layer offers 171 distinct per-crop file entries  
**Potential roles:** `crop_area_exposure_prior`, `crop_specific_spatial_distribution_challenge`, `mapspam_2020_cross_source_comparator`, `synthetic_agriculture_portfolio_geography`  
**Access hint:** `public_fao_catalogue_figshare_netcdf_and_2026_cgiar_cog_exact_file_version_license_review_pending`  
**Authoritative source:** <https://www.fao.org/agroinformatics/training-and-resources/data-sets/data-set-detail/cropgrids-data-on-harvested-and-crop-areas/en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** FAO and the 2024 Scientific Data paper describe 173 crops with original research NetCDF files (DOI 10.6084/m9.figshare.22491997); a 2026 CGIAR catalog presents a derived FAO COG representation with 171 unique crop file choices plus aliases. Do not silently equate 171 files with 173 crop concepts, or physical area with harvested area: multiple harvests can make harvested area greater. CROPGRIDS uses the older MRF dataset, gridded research products, 52-country subnational observations and FAOSTAT 2020 national totals; it is NOT an independent national-total validation for MapSPAM or FAOSTAT. Provider derivative catalog says CC BY 4.0 and a Figshare record v9 is indexed as CC BY 4.0; pin original exact file rights, version, provenance, crop-code mapping, nodata and aggregation before use. No TIV or observed insurer losses.
