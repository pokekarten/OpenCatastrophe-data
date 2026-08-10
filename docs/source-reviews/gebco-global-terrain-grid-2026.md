<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: GEBCO_2026 global terrain grid

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/gebco.global-terrain-grid.2026.json`
- Provider: General Bathymetric Chart of the Oceans (GEBCO)
- Product: GEBCO_2026 Grid
- Release: published April 2026
- DOI: `10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa`

## Why this source is useful

GEBCO_2026 is a reusable physical-geography foundation rather than a catastrophe-event dataset. It provides a global ocean-and-land terrain surface that can support bounded tsunami, storm-surge, coastal-flood and terrain-context research while keeping the terrain source distinct from any later hydraulic or hazard model.

## Source identity and scientific semantics

The reviewed release is the **GEBCO_2026 Grid**, published in April 2026. GEBCO describes it as a global terrain model on a 15 arc-second interval grid, with elevation values in metres and a companion Type Identifier (TID) Grid that records the type of source information supporting each cell.

Important boundaries:

- the grid is an **interpolated information product**, not the underlying source bathymetric measurements;
- nominal grid spacing is not a claim that direct measurements exist at every cell;
- GEBCO combines heterogeneous contributing datasets and documents variable quality and coverage;
- source vertical datums can differ, especially in shallow water, even though the compilation assumes a mean-sea-level basis;
- the Grid is not for navigation or safety-at-sea use;
- the TID Grid and current errata are material provenance/quality evidence for later selected assets.

## Access and rights assessment

The authoritative GEBCO terms place the Grid information product in the public domain and permit copying, publication, distribution, adaptation and commercial exploitation. They require source acknowledgement and prohibit implied endorsement or source misrepresentation.

This admission does **not** infer rights for the underlying source survey/bathymetric datasets merely because they contributed to the Grid.

## Suitable initial OpenCatastrophe uses

- terrain/bathymetry discovery and source-contract testing;
- tsunami and coastal-hazard research inputs with an explicit downstream model;
- bounded coastal-flood and storm-surge experiments;
- terrain-context features for cross-peril analysis;
- comparison with regional higher-resolution elevation/bathymetry sources.

The grid is not sufficient by itself for navigation, inundation depth, storm-surge intensity, tsunami propagation, property damage or insured loss.

## Requirements before raw admission

A raw proposal must select the exact GEBCO_2026 variant and file/subset, re-check current terms/errata, acquire bytes outside Git, record size/SHA-256, preserve horizontal/vertical-reference assumptions and determine whether the companion TID information is needed for the scientific claim. Provider attribution/disclaimer conditions remain mandatory.

## Authoritative public references

- Product: `https://www.gebco.net/data-products-gridded-bathymetry-data/gebco2026-grid`
- Terms: `https://www.gebco.net/data-products/gridded-bathymetry/terms-of-use`
- DOI: `https://doi.org/10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa`
