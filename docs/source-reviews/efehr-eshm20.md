<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: EFEHR 2020 European Seismic Hazard Model (ESHM20)

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/efehr.eshm20.json`
- Provider: European Facilities for Earthquake Hazard and Risk (EFEHR)
- Product: 2020 European Seismic Hazard Model (ESHM20)
- Documentation identity: EFEHR Technical Report 001, `v1.0.0`
- DOI: `10.12686/a15`

## Why this source is useful

ESHM20 is a strong first earthquake-hazard source for the OpenCatastrophe data foundation. EFEHR provides public access to the scientific model data and input files, including OpenQuake-compatible material, and publishes a clear source-specific licence statement.

It complements the current wind-focused admissions without pretending that a hazard model supplies exposure, vulnerability, insured loss, policy terms, or financial-model semantics.

## Source identity and mutability

The reviewed public product is ESHM20. EFEHR cites the model overview as Technical Report 001, version `v1.0.0`, DOI `10.12686/a15`, and exposes scientific data through its public data-access surfaces and GitLab repository.

That documentation version is not, by itself, a byte identity for every file currently reachable from the data repository. Any later raw admission must independently identify the exact artifact or repository state used. Depending on the selected product, that means pinning items such as:

- exact EFEHR repository path and commit/tag/release where available;
- exact source-model, logic-tree, configuration, NRML/XML, shapefile, raster, table, or other file identity;
- download URL or stable repository locator;
- retrieval timestamp;
- byte size and SHA-256;
- any required companion files and their identities.

No EFEHR dataset bytes are admitted by this review.

## Rights assessment

EFEHR's authoritative hazard licence page states that products of the 2020 European Seismic Hazard Model are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. The page explicitly allows sharing and adaptation for any purpose, including commercially, subject to attribution, licence linking, and indicating changes.

Engineering interpretation for this metadata review:

- licence identity: `CC-BY-4.0`;
- commercial use: allowed under the stated licence;
- redistribution/adaptation: allowed subject to CC BY 4.0 conditions;
- attribution: use the source/model citation supplied by EFEHR and meet CC BY 4.0 attribution/change-indication requirements;
- repository review scope: metadata only.

OpenCatastrophe deliberately keeps the repository review narrower than the source-rights ceiling. At this source review time, no raw ESHM20 artifact had been selected, acquired, hashed, or approved for Git publication. Later external receipts do not retroactively alter that review-time statement or authorize Git publication.

## Scientific semantics

### Hazard is not risk

ESHM20 is admitted here as an **earthquake hazard** source. A future adapter must not turn the presence of a hazard model into an implicit claim about:

- building inventory or insured exposure;
- vulnerability or damage ratios;
- claims or insured loss;
- policy or reinsurance terms;
- event-loss tables or year-loss tables;
- pricing, capital, regulatory adequacy, or production fitness.

Those layers require independent sources, semantics, and validation.

### Keep model components explicit

EFEHR exposes multiple scientific products and input materials. Future work must retain the identity and role of each selected component rather than collapsing the product into a generic `earthquake data` object. At minimum, source-model inputs, ground-motion logic, configuration, hazard outputs, and any event/catalogue material must remain distinguishable when used.

A hazard curve, hazard map, source-model file, earthquake catalogue, and stochastic-event representation are not interchangeable merely because they originate from the same broader model programme.

### OpenQuake interoperability

The availability of OpenQuake-compatible input material is useful for reproducibility and independent execution. It does not make a particular OpenQuake software version part of this dataset identity, and the OpenQuake software licence does not determine the rights of ESHM20 data. Software and data remain separately pinned and reviewed.

## Suitable initial OpenCatastrophe uses

Good initial uses:

- European earthquake-hazard source discovery;
- transparent hazard-model provenance tests;
- exact-source-model and configuration identity exercises;
- OpenQuake interoperability research after software version pinning;
- comparison of hazard outputs with separately admitted exposure/vulnerability sources;
- testing cross-peril repository contracts without mixing scientific layers.

Not sufficient by itself for:

- property-level exposure;
- vulnerability or fragility calibration;
- insured-loss modelling;
- portfolio aggregation;
- financial terms or reinsurance;
- regulatory or production claims.

## Requirements before raw admission

Before any ESHM20 bytes can move beyond metadata-only status, a proposal must:

1. re-check the current EFEHR product and licence pages;
2. identify the exact ESHM20 asset(s) and repository state/version;
3. acquire the bytes outside Git;
4. record byte size and SHA-256 for every admitted asset;
5. preserve the scientific role and dependencies of each selected file;
6. document units, coordinate/reference conventions and other material metadata for the selected product;
7. record any transformation independently from acquisition;
8. satisfy the exact EFEHR citation/attribution requirements; and
9. obtain explicit asset-specific publication review.

Until then, no ESHM20 raw or derived bytes belong in this repository.

## Authoritative public references

- EFEHR seismic hazard data access: `https://www.efehr.org/earthquake-hazard/data-access/`
- EFEHR ESHM2020 licence/copyright: `https://hazard.efehr.org/en/licenses-copyright/`
- ESHM2020 overview: `https://hazard.efehr.org/en/Documentation/specific-hazard-models/europe/eshm2020-overview/`
- Model overview DOI: `https://doi.org/10.12686/a15`
