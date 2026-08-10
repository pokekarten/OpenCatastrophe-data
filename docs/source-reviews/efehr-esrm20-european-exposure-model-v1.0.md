<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: ESRM20 European Exposure Model v1.0

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/efehr.esrm20.european-exposure-model.v1.0.json`
- Provider: European Facilities for Earthquake Hazard and Risk (EFEHR)
- Product: European Exposure Model used by the 2020 European Seismic Risk Model (ESRM20)
- Exposure release: `v1.0`
- Tagged source repository: `https://gitlab.seismo.ethz.ch/efehr/esrm20_exposure/-/tree/v1.0`

## Why this source is useful

OpenCatastrophe-data already has wind-hazard evidence but no admitted exposure-layer source. ESRM20 provides a strong public scientific reference because EFEHR exposes the building-stock component independently from the hazard and vulnerability components and documents the model as part of a reproducible European risk framework.

EFEHR describes ESRM20 exposure as information about residential, commercial and industrial buildings and their occupants. The risk documentation describes exposure quantities including building count, area, occupants and replacement cost.

This makes the source useful for testing what an exposure contract must preserve without requiring any confidential insurance portfolio.

## Stable source identity

The public `esrm20_exposure` GitLab repository has a tagged `v1.0` release for version 1.0 of the European Exposure Model. The tag is the source-version identity used by this metadata review.

This review does **not** treat a Git tag as sufficient byte identity for publication. A later raw-artifact proposal must select the exact archive/files used, acquire them outside Git, and record byte size and SHA-256 independently. If the tag contents or hosting ever change, recorded bytes rather than the mutable remote state remain the reproducibility anchor.

## Rights assessment

EFEHR's authoritative seismic-risk data-access page states that the scientific data available from risk.EFEHR and the public EFEHR GitLab are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). EFEHR's download/information guidance states that the scientific products can be used for private, scientific, commercial and non-commercial purposes provided adequate citation is given.

Engineering interpretation for this source:

- licence identity: `CC-BY-4.0`;
- access: public download;
- commercial use: allowed under the stated CC BY terms;
- redistribution/adaptation: allowed subject to attribution and indication of changes;
- repository scope: metadata only until an exact source artifact is independently identified and reviewed.

The source should be cited using the applicable ESRM20 scientific references. The ESRM20 technical report is the overarching model reference; the exposure-model documentation and publications should additionally be cited when using the exposure component.

## Exposure semantics

### This is modelled exposure, not an insured portfolio

The ESRM20 exposure model describes built-environment exposure for seismic risk analysis. It must not be re-labelled as:

- an insurer's policy/location schedule;
- total insured value (TIV);
- insured market share;
- claims experience;
- policy terms, deductibles or limits.

Replacement-cost values are modelled exposure values. They are not automatically insured values, and any mapping into an insurance exposure standard must preserve that distinction.

### Building taxonomy and use classes matter

The public EFEHR documentation distinguishes residential, commercial and industrial buildings. A future adapter must preserve the source taxonomy and its mapping evidence rather than silently replacing missing or unfamiliar source categories with OpenCatastrophe or OED defaults.

Where building count, area, occupants or replacement cost are supplied, their source spatial unit, value basis and classification must remain linked to the original v1.0 files.

### Spatial resolution is part of scientific meaning

Regional exposure results depend on the spatial resolution at which exposure is represented. A future adapter must therefore preserve the exact source spatial units/geometries and must not claim that reaggregation or disaggregation is lossless.

No CRS or grid is frozen by this metadata admission because no exact v1.0 exposure file has yet been selected as an OpenCatastrophe artifact.

## Relationship to hazard and vulnerability

ESRM20 is a risk model assembled from distinct components: exposure, vulnerability, hazard/site response and risk calculations. This admission covers **only the exposure component**.

It does not automatically admit:

- ESHM20 hazard inputs;
- ESRM20 fragility/vulnerability functions;
- site-response models;
- scenario files;
- OpenQuake configuration/results;
- any derived risk or loss output.

Those components need separate source identities and reviews if OpenCatastrophe later uses them.

This separation is deliberate: a useful public risk-data stack should be able to swap or independently validate exposure, hazard and vulnerability rather than treating a complete model repository as one indivisible dataset.

## Suitable initial OpenCatastrophe uses

Good initial uses:

- testing exposure manifests and provenance;
- understanding public building-stock exposure semantics;
- developing explicit adapters to insurance exposure standards without using confidential portfolios;
- comparing source taxonomies and spatial aggregation choices;
- later coupling to independently admitted hazard/vulnerability sources in a reproducible pilot.

Not sufficient by itself for:

- windstorm vulnerability or Germany wind pricing;
- an insurer-specific portfolio;
- insured TIV or market share;
- policy/reinsurance calculations;
- claims calibration;
- production capital or regulatory conclusions.

## Requirements before raw admission

Before ESRM20 exposure bytes can move beyond metadata-only status, a proposal must:

1. re-check the current EFEHR licence/citation guidance;
2. select the exact v1.0 archive/files and preserve the source tag/commit context;
3. acquire the bytes outside Git;
4. record independent byte size and SHA-256 identities;
5. document exact spatial units, taxonomy, currencies/value bases and source vintages from those files;
6. define any transformation or OED mapping explicitly, including losses/defaults/inference;
7. validate that no personal or restricted source material is introduced;
8. obtain explicit asset-specific publication review.

Until then, no ESRM20 exposure data bytes belong in this repository.

## Authoritative public references

- EFEHR risk data access: `https://www.efehr.org/Earthquake-risk/data-access/`
- EFEHR ESRM20 documentation: `https://risk.efehr.org/documentation/`
- EFEHR exposure repository `v1.0`: `https://gitlab.seismo.ethz.ch/efehr/esrm20_exposure/-/tree/v1.0`
- EFEHR download/licensing guidance: `https://www.efehr.org/explore/Downloads-information-material/`
