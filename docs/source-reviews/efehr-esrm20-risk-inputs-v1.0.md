<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: ESRM20 OpenQuake-engine risk inputs v1.0

- Review date: **2026-08-13**
- Admission state: **metadata only**
- Manifest: `manifests/efehr.esrm20.risk-inputs.v1.0.json`
- Provider: European Facilities for Earthquake Hazard and Risk (EFEHR)
- Public repository: `efehr/esrm20`
- Reviewed release: `v1.0`

## Why this source needs its own identity

The public `efehr/esrm20` repository is a versioned set of ESRM20 inputs prepared for OpenQuake-engine risk calculations. It is scientifically related to the separately reviewed ESRM20 exposure and vulnerability repositories, but it is **not byte- or version-identical to either of them**.

OpenCatastrophe currently needs this repository for explicit interoperability/configuration dependencies that connect those separately admitted layers. The first P0 examples are:

- `Vulnerability/esrm20_exposure_vulnerability_mapping.csv` — exposure-taxonomy to vulnerability-model mapping used by the public ESRM20 calculation inputs;
- `Vs30/Site_model_Kosovo.xml` — a country-specific site-model input relevant to the separately predeclared Kosovo consumer slice.

Those examples do not broaden this metadata admission into approval for their bytes. Each exact file still requires immutable commit/path identity, byte count, SHA-256, scientific semantics and artifact-specific review before model use or publication.

## Source identity and version boundary

The reviewed provider repository is the separate public GitLab project `efehr/esrm20` (project ID 269) and exposes release `v1.0`.

A release tag is source-version evidence, not an immutable artifact identity by itself. Future exact-file acquisition must bind the full resolved commit SHA plus repository path and acquired byte hash. Current `main`, later tags or another ESRM20 component repository must not be silently substituted for v1.0.

This distinction is especially important for the exposure-to-vulnerability mapping: the mapping may point into vulnerability models from the separately versioned `esrm20_vulnerability` repository, but that relationship does not make the mapping file itself a byte from the separately versioned vulnerability dataset.

## Rights assessment

EFEHR's authoritative earthquake-risk data-access guidance states that scientific data available through risk.EFEHR and the public EFEHR GitLab are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)** and may be used for scientific, private, commercial and non-commercial purposes with adequate citation.

Engineering interpretation for this metadata review:

- licence identity: `CC-BY-4.0`;
- commercial use: allowed under the stated terms;
- sharing/adaptation: allowed subject to attribution, licence reference and indication of changes;
- repository review scope: metadata only.

No provider file has been acquired or approved for Git publication by this review.

## Scientific semantics

### Configuration and relationship evidence are not a new physical model layer

The repository combines executable/configuration inputs needed by a reference risk workflow. Individual files can have materially different scientific roles: taxonomy mapping, site-model input, OpenQuake configuration or other calculation support.

OpenCatastrophe must therefore preserve each selected file's own role instead of treating the repository as one homogeneous `risk data` object.

### Mapping is not vulnerability

An exposure-to-vulnerability mapping defines compatibility/selection between source taxonomies and vulnerability model identifiers. It does not itself define fragility, vulnerability response, damage ratios or claims loss.

A future consumer must preserve:

- exact mapping repository/version/path/hash;
- source exposure taxonomy fields;
- referenced vulnerability IDs;
- unresolved/unmapped categories;
- relation to the separately identified vulnerability source/version.

Unsupported mappings must fail closed rather than use a guessed generic class.

### Site input is not hazard or universal site truth

A country/site-model XML can carry spatial site-response inputs used by the ESRM20 reference workflow. It must not be relabelled as ESHM20 hazard, observed strong motion or a universally valid site-amplification model.

Any exact site file requires separate review of fields, coordinate/reference system, units, missingness, upstream lineage and applicability before use.

### OpenQuake interoperability is a benchmark boundary

The repository is useful because it provides public inputs for reproducible reference calculations. That does not make OpenQuake output authoritative for OpenCatastrophe, and it does not permit source-code copying or silently collapse software and data licences.

## Suitable initial OpenCatastrophe uses

Good initial uses:

- exact exposure-to-vulnerability mapping provenance;
- explicit site-input provenance for a bounded ESRM20 reference calculation;
- reproducible OpenQuake interoperability/benchmark configuration;
- testing cross-component compatibility while keeping hazard, exposure and vulnerability sources separately identified.

Not sufficient by itself for:

- earthquake occurrence/frequency;
- vulnerability calibration;
- observed damage truth;
- insured claims or policy/reinsurance terms;
- production pricing, capital or regulatory claims.

## Requirements before exact artifact use

Before any v1.0 file becomes an OpenCatastrophe artifact or model input:

1. re-check the current EFEHR rights/citation guidance;
2. resolve the exact v1.0 tag to a full immutable commit SHA;
3. select the exact repository path for a predeclared scientific role;
4. acquire bytes through a reviewed bounded route;
5. record retrieval UTC, byte count and SHA-256;
6. document file-specific schema, units/reference systems, missingness and dependencies;
7. preserve relationships to separately admitted ESHM20/ESRM20 components without merging their identities;
8. record any transformation independently; and
9. obtain exact artifact-specific scientific/rights review before publication or model-input promotion.

Until those gates are met, no `efehr/esrm20` provider bytes belong in this repository.

## Authoritative public references

- EFEHR ESRM20 risk-input repository: `https://gitlab.seismo.ethz.ch/efehr/esrm20`
- EFEHR ESRM20 v1.0 tree: `https://gitlab.seismo.ethz.ch/efehr/esrm20/-/tree/v1.0`
- EFEHR earthquake-risk data access: `https://www.efehr.org/Earthquake-risk/data-access/`
- ESRM20 documentation: `https://risk.efehr.org/documentation/`
