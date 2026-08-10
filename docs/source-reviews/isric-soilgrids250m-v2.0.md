<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: ISRIC SoilGrids250m 2.0

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/isric.soilgrids250m.v2.0.json`
- Provider: ISRIC - World Soil Information
- Product: SoilGrids250m version 2.0
- Licence: CC BY 4.0

## Why this source is useful

SoilGrids is a reusable physical-state layer rather than a catastrophe catalogue. Soil texture, bulk density, organic carbon and related properties can provide scientifically explicit context for infiltration/runoff, drought, wildfire and slope-failure research.

## Scientific semantics and limitations

SoilGrids 2.0 uses machine-learning models calibrated from soil-profile observations and environmental covariates to produce globally consistent soil-property predictions at 250 m resolution and six standard depth intervals. Prediction uncertainty is represented by lower and upper limits of a 90% prediction interval.

The rasters are **predictions**, not direct field measurements at each cell. Native stored units and scale factors are material: for example clay/sand are mapped in `g/kg` with a conversion factor, bulk density in `cg/cm3`, and soil organic carbon in `dg/kg`. An adapter must not silently reinterpret stored integers as conventional-unit values.

ISRIC also documents current known missing tiles for some property/depth/regions and states that the complementary REST API is temporarily paused; stable access paths such as WCS/WebDAV should be preferred for reproducible acquisition until that status changes.

## Access and rights assessment

ISRIC's current data-sharing documentation states that SoilGrids products have been provided under CC BY 4.0 since 2019. This source review applies to the SoilGrids output products, not automatically to the underlying WoSIS profiles or third-party covariates as independent sources.

Engineering interpretation:

- commercial use: allowed under CC BY 4.0;
- redistribution/adaptation: allowed with attribution;
- access: public through documented services;
- repository scope: metadata only.

## Suitable initial OpenCatastrophe uses

- soil and infiltration context for flood research;
- soil-state features for landslide susceptibility experiments;
- drought/fire environmental context;
- uncertainty-aware geospatial feature pipelines;
- comparison with national or field-observation sources where available.

SoilGrids alone is not a flood, landslide, fire or drought event/footprint dataset.

## Requirements before raw admission

A raw proposal must select exact property, statistic/quantile, depth interval and geographic extent; preserve native units/scale factors, grid/projection and uncertainty semantics; re-check known missing tiles/service status; acquire bytes outside Git; and record exact hashes/sizes before asset-specific publication review.

## Authoritative public references

- Product overview: `https://docs.isric.org/globaldata/soilgrids/index.html`
- Version 2.0 description: `https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html`
- Data-sharing/access policy: `https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html`
- Layer units and scaling: `https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html`
