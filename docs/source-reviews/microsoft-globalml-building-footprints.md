<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Microsoft Global ML Building Footprints

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/microsoft.globalml-building-footprints.json`
- Provider: Microsoft
- Product: Global ML Building Footprints
- Release model: rolling/mutable distribution; no GitHub release is used as a frozen dataset identity

## Why this source is useful

Microsoft's Global ML Building Footprints are a strong open candidate for the **exposure-geometry** layer. The public distribution contains building-footprint polygons at broad geographic scale and, for some structures, model-derived height and confidence attributes.

This source adds a materially different layer from the admitted hazard and modelled-exposure sources. It can support geometry coverage, spatial joins, exposure-taxonomy research and independent comparison, while remaining clearly separated from property values, occupancy, construction, policy data and insured exposure.

## Source identity and mutability

The public repository describes a rolling dataset distribution and maintains `dataset-links.csv` as a large country/quadkey-partition index. It also documents repeated updates to building footprints and height estimates. The repository does not publish formal GitHub dataset releases that would make `latest` a durable byte identity.

Accordingly, this metadata review deliberately records `version_or_release: null`.

A reproducible raw acquisition must pin more than the repository URL. It must record at least:

- an exact snapshot/identity for `dataset-links.csv` or an equivalent stable distribution index;
- selected country and quadkey partition(s);
- the exact returned asset URL or stable locator;
- retrieval timestamp;
- byte size and SHA-256 for every selected partition;
- schema/field interpretation used for that snapshot;
- any separately selected coverage, height, or other companion layer.

No Microsoft building-footprint bytes are admitted by this review.

## Rights assessment

The Microsoft repository states that the data are licensed under **Community Data License Agreement – Permissive, Version 2.0 (CDLA-Permissive-2.0)** and are freely available for download and use.

The authoritative CDLA-Permissive-2.0 agreement allows a data recipient to use, modify, and share data under the agreement. When sharing the data, the recipient must make the text of the agreement available with the shared data.

Engineering interpretation for this metadata review:

- licence identity: `CDLA-Permissive-2.0`;
- commercial use: allowed; the agreement does not impose a non-commercial restriction on use, modification, or sharing;
- redistribution/adaptation: allowed subject to the agreement's sharing conditions;
- repository review scope: metadata only.

The licence of the released building dataset does not grant OpenCatastrophe permission to redistribute underlying third-party imagery or any other upstream asset that Microsoft does not itself publish under the dataset licence. This review is limited to the released Global ML Building Footprints product.

## Scientific semantics

### Model output, not cadastral truth

The footprints are machine-learning-derived outputs from imagery. They must not be represented as authoritative cadastral records, legal property boundaries, occupancy records, construction records, insured locations or proof that a building exists at a particular valuation date.

Microsoft documents spatially varying model quality and missing coverage. A future adapter must preserve provenance and allow downstream workflows to represent missingness and uncertainty rather than converting absence into a known negative.

### Footprint geometry

The dataset contains polygon geometries in longitude/latitude coordinates. Microsoft identifies the coordinate reference system as EPSG:4326.

Footprint geometry is useful for spatial exposure research, but a building polygon alone does not supply occupancy/use, construction/material class, storeys, replacement cost, insured value, policy information, or vulnerability.

### Height

Microsoft describes building height as a neural-network estimate of height above ground, averaged within the building polygon, expressed in metres. Structures without a height estimate use `-1`.

A future adapter must therefore treat `-1` as unavailable/missing, not as a physical height. Model-estimated height must remain distinguishable from observed height, storey count or an authoritative building-register attribute.

### Confidence

Microsoft documents a building confidence score between 0 and 1 for applicable newer footprints and `-1` as a placeholder for older structures. The score is based on building-pixel probabilities and is a **footprint detection confidence**, not a confidence score for height or other building attributes.

A future schema must keep that meaning explicit and must not silently reuse it as general exposure confidence.

### Time and imagery vintage

The extraction depends on source imagery vintages that vary by geography and update. The presence of a footprint in the rolling distribution therefore must not be treated as a universal observation at one common date. Exact acquisition and any time-sensitive use require snapshot-specific evidence.

## Suitable initial OpenCatastrophe uses

Good initial uses:

- global/regional building-footprint coverage research;
- exposure-geometry ingestion and spatial-index tests;
- comparison against separately admitted building/exposure sources;
- height-availability and uncertainty experiments;
- peril-to-building spatial overlay experiments after the hazard source is separately admitted;
- synthetic downstream taxonomy/inference tests that do not reproduce confidential portfolios.

Not sufficient by itself for authoritative property identity, occupancy/construction truth, replacement or insured value, policy/claims/treaty information, vulnerability calibration, or production portfolio completeness.

## Requirements before raw admission

Before any Microsoft Global ML Building Footprints bytes can move beyond metadata-only status, a proposal must:

1. re-check the current Microsoft repository licence statement and CDLA-Permissive-2.0 terms;
2. freeze the exact distribution-index snapshot or equivalent asset locator;
3. select exact country/quadkey partition(s) and any companion products;
4. acquire bytes outside Git;
5. record byte size and SHA-256 for every selected asset;
6. verify the selected snapshot's field/schema semantics, including geometry, height, confidence and missing-value conventions;
7. document spatial coverage and relevant source-imagery vintage information without overstating precision;
8. preserve the CDLA sharing condition if data are ever approved for redistribution;
9. record transformations independently from acquisition; and
10. obtain explicit asset-specific publication review.

Until then, no raw or derived Microsoft building-footprint bytes belong in this repository.

## Authoritative public references

- Microsoft Global ML Building Footprints: `https://github.com/microsoft/GlobalMLBuildingFootprints`
- CDLA-Permissive-2.0: `https://cdla.dev/permissive-2-0/`
