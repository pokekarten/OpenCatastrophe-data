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

This is valuable for OpenCatastrophe precisely because a cross-peril terrain layer can be referenced by many workflows without duplicating peril-specific data collections.

## Source identity and scientific semantics

The reviewed release is the **GEBCO_2026 Grid**, published in April 2026. GEBCO describes it as a global terrain model on a 15 arc-second interval grid, with elevation values in metres and a companion Type Identifier (TID) Grid that records the type of source information supporting each cell.

Important boundaries:

- the grid is an **interpolated information product**, not the underlying source bathymetric measurements;
- nominal grid spacing is not a claim that direct measurements exist at every cell;
- GEBCO combines heterogeneous contributing datasets and documents variable quality and coverage;
- GEBCO warns that source vertical datums can differ, especially in shallow-water areas, even though the global compilation assumes a mean-sea-level basis;
- GEBCO explicitly states that the grid is not for navigation or safety-at-sea use;
- the TID Grid is useful provenance context and should remain associated with any later selected grid artifact;
- known issues and errata must be re-checked for any selected geographic subset.

## Access and rights assessment

The authoritative GEBCO terms state that the Grid information product is placed in the public domain and may be used free of charge. Users may copy, publish, distribute, transmit, adapt and commercially exploit it.

The same terms require source acknowledgement and prohibit uses that imply official endorsement or misrepresent the Grid or its source.

Engineering interpretation for this admission:

- commercial use: allowed;
- redistribution/adaptation: allowed under the reviewed GEBCO conditions;
- attribution: required by the provider terms;
- repository review scope: metadata only;
- underlying survey/source bathymetric datasets: **not covered by this admission merely because they contributed to the Grid**.

No SPDX expression is invented for GEBCO's public-domain-with-conditions wording.

## Suitable initial OpenCatastrophe uses

Good initial uses include:

- terrain/bathymetry discovery and source-contract testing;
- tsunami and coastal-hazard research inputs with an explicit downstream model;
- bounded coastal-flood and storm-surge experiments;
- terrain-context features for cross-peril analysis;
- comparison with regional higher-resolution elevation/bathymetry sources.

The grid is not sufficient by itself for navigation, inundation depth, storm-surge intensity, tsunami propagation, property damage or insured loss.

## Requirements before raw admission

Before any GEBCO bytes can move beyond metadata-only status, a proposal must:

1. select the exact GEBCO_2026 variant and geographic/file scope;
2. re-check the current GEBCO terms and release errata;
3. acquire bytes outside Git and record exact byte size and SHA-256;
4. preserve horizontal/vertical reference assumptions and selected file format;
5. identify whether the companion TID information is required for the intended scientific claim;
6. preserve GEBCO attribution, disclaimer and non-endorsement requirements; and
7. obtain explicit asset-specific publication review.

## Authoritative public references

- Product: `https://www.gebco.net/data-products-gridded-bathymetry-data/gebco2026-grid`
- Terms: `https://www.gebco.net/data-products/gridded-bathymetry/terms-of-use`
- DOI: `https://doi.org/10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa`
