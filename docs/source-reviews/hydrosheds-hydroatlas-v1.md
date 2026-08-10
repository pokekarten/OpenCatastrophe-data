<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: HydroATLAS version 1

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/hydrosheds.hydroatlas.v1.json`
- Provider: HydroSHEDS / HydroATLAS
- Product: HydroATLAS version 1
- Licence: CC BY 4.0

## Why this source is useful

HydroATLAS supplies reusable hydrographic geometry plus environmental context rather than flood-event or discharge data. It can establish explicit catchment, river and lake relationships that later hazard and observation sources can join against without inventing project-specific hydrography.

## Scientific semantics

HydroATLAS version 1 comprises BasinATLAS, RiverATLAS and LakeATLAS. The provider describes about 1.0 million sub-basins, 8.5 million river reaches and 1.4 million lakes. Each sub-dataset carries 56 hydro-environmental variables partitioned into 281 attributes covering hydrology, physiography, climate, land cover/use, soils/geology and anthropogenic influences.

These attributes are compiled and reformatted from numerous global sources. Their source periods, units, definitions and uncertainty are therefore attribute-specific; the database must not be presented as a single contemporaneous observation campaign.

Hydrographic topology/context is also distinct from river discharge, inundation depth, flood extent or hydraulic connectivity at property scale.

## Access and rights assessment

The authoritative HydroATLAS product page states that the HydroATLAS database is licensed under CC BY 4.0 and provides requested citations.

This decision is deliberately **product-specific**. Other HydroSHEDS products have their own licence statements, so the HydroATLAS licence is not a provider-wide rights shortcut.

Engineering interpretation:

- commercial use: allowed under CC BY 4.0;
- redistribution/adaptation: allowed with attribution;
- access: open;
- repository review scope: metadata only.

## Suitable initial OpenCatastrophe uses

- basin/reach/lake identifiers and spatial joins;
- upstream/downstream context for hydrology research;
- catchment-level aggregation experiments;
- geographic indexing for gauge/model comparison;
- cross-peril environmental feature research.

Not sufficient by itself for observed flow, flood extent, water depth, damage or loss.

## Requirements before raw admission

A later raw proposal must select exact BasinATLAS/RiverATLAS/LakeATLAS files and level/resolution, record byte hashes/sizes, preserve attribute codes/units and source semantics, document geometry/CRS and citations, and obtain asset-specific review. Any filtering or aggregation must have deterministic lineage.

## Authoritative public references

- Product/licence: `https://www.hydrosheds.org/hydroatlas`
