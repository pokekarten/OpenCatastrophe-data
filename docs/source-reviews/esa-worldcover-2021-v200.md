<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: ESA WorldCover 10 m 2021 v200

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/esa.worldcover.2021.v200.json`
- Provider: European Space Agency (ESA) WorldCover consortium
- Product: WorldCover 2021
- Version: v200
- DOI: `10.5281/zenodo.7254221`

## Why this source is useful

WorldCover supplies a globally consistent land-cover classification at approximately 10 m resolution. For OpenCatastrophe it can act as reusable environmental/exposure context for several perils without pretending that land cover is itself a catastrophe or insured exposure dataset.

## Scientific semantics and limitations

WorldCover 2021 v200 is a classified product derived from Sentinel-1 and Sentinel-2 data and contains 11 land-cover classes. ESA reports an independently validated global overall accuracy of 76.7% for the 2021 product.

The 2020 and 2021 maps use different algorithm versions (`v100` and `v200`). Therefore apparent differences between the two maps can combine real land-cover change with algorithmic change; they must not be treated as a clean change-detection time series without an explicit method.

The map and InputQuality support layers also have different delivery availability. A downstream adapter must preserve class codes, nodata, resolution, CRS and quality semantics from the exact selected product.

## Access and rights assessment

ESA states that WorldCover products are provided free of charge, without restriction of use, under CC BY 4.0. The authoritative page supplies specific attribution/citation language.

Engineering interpretation:

- commercial use: allowed;
- redistribution/adaptation: allowed under CC BY 4.0;
- repository scope: metadata only;
- v200 identity is explicit and separate from v100 and successor Copernicus land-cover products.

## Suitable initial OpenCatastrophe uses

- land-cover stratification for hazard validation;
- vegetation/bare/water/urban context;
- runoff and surface-context features;
- open exposure-context research;
- cross-peril spatial joins with explicit resolution limits.

It is not an insured-asset inventory, building-value source, fire perimeter, flood map or vulnerability model.

## Requirements before raw admission

Select exact v200 tiles or macro-tiles and delivery path; acquire outside Git; record byte sizes/hashes; preserve EPSG:4326, class codes, nodata and quality-layer availability; include required attribution; and obtain an asset-specific review. Any resampling, remapping or class aggregation requires explicit transformation lineage.

## Authoritative public references

- Data access, licence, validation and citation: `https://esa-worldcover.org/en/data-access`
- Product DOI: `https://doi.org/10.5281/zenodo.7254221`
