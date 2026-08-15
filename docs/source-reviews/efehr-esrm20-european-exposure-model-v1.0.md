<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: ESRM20 European Exposure Model v1.0

- Initial metadata review: **2026-08-10**
- Exact derived-artifact review: **2026-08-15**
- Admission state: **approved derived — exact canonical Kosovo-residential `TAXONOMY` stream only; raw source bytes remain unapproved**
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

The public `esrm20_exposure` GitLab repository has a tagged `v1.0` release for version 1.0 of the European Exposure Model. The tag resolves to immutable commit `900433ada80fbb424c0976c34d72eeef97bab1af` for the bounded work in Issue #282.

The predeclared P0 source object is:

- project: `186` / `efehr/esrm20_exposure`;
- commit: `900433ada80fbb424c0976c34d72eeef97bab1af`;
- path: `_exposure_models/Exposure_Model_Kosovo_Res.csv`;
- exact source byte count: `316789`;
- exact source SHA-256: `4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea`;
- trusted source receipt comment: `5300981864`;
- source receipt execution SHA: `46d054930025553ad19d8b05fff9018dc2a49b5f`.

Those facts identify the source used to derive the approved taxonomy artifact. They do **not** approve the 316789 source bytes for Git publication. `raw_artifact` remains null in the manifest.

## Exact derived-artifact admission — Kosovo residential taxonomy set

Trusted-main Issue #363 execution produced a durable identity-only result in comment `5303346187`. It did not return or persist the 86 taxonomy strings. The result independently binds the source receipt above and establishes:

- literal source field: `TAXONOMY`;
- exact distinct count: `86`;
- normalization: **none**;
- canonical representation: `oc-taxonomy-u64be-utf8-sorted-v1`;
- canonical representation rule: sort the exact source strings and concatenate `uint64_be(len(utf8(value))) || utf8(value)` for every value in order;
- exact canonical byte count: `2666`;
- exact canonical SHA-256: `d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945`;
- canonicalization implementation: `f2fcfa1d94f1a44f738353ef0bae8d467351a2eb:scripts/acquire_efehr_kosovo_taxonomy.py::_canonical_artifact_identity`;
- upstream verified extractor: `f2fcfa1d94f1a44f738353ef0bae8d467351a2eb:scripts/extract_efehr_kosovo_taxonomy.py::extract_verified_kosovo_taxonomy`;
- trusted action execution SHA: `f2fcfa1d94f1a44f738353ef0bae8d467351a2eb`.

The manifest therefore admits **that exact 2666-byte canonical stream and no other derived serialization**. Its `external://` reference is a logical external artifact identity under repository policy; it does not claim that provider bytes or the derived stream are committed to Git, and it does not change the trusted action's `derived_artifact_persisted=false` observation.

This exact-byte boundary matters. The same 86 semantic strings serialized as JSON, CSV, newline-delimited text, a Python representation or an Agent Action evidence array would have different bytes and are **not automatically covered** by this admission. Any durable public alternate serialization requires its own exact artifact identity or a separately reviewed publication contract. Transient use inside a fail-closed mapping operation is a separate engineering decision.

## Rights assessment

EFEHR's authoritative seismic-risk data-access page states that the scientific data available from risk.EFEHR and the public EFEHR GitLab are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). EFEHR's download/information guidance states that the scientific products can be used for private, scientific, commercial and non-commercial purposes provided adequate citation is given.

Engineering interpretation for this source:

- licence identity: `CC-BY-4.0`;
- access: public download;
- commercial use: allowed under the stated CC BY terms;
- redistribution/adaptation: allowed subject to attribution and indication of changes;
- source-rights ceiling: raw redistribution is permitted by the recorded terms;
- repository scope: the exact canonical Kosovo `TAXONOMY` derivative is approved; raw exposure bytes and all other derivatives remain unapproved unless separately reviewed.

The approved derivative inherits the CC BY attribution obligation. Publications or materializations of that exact derivative must identify EFEHR/ESRM20, reference CC BY 4.0, cite the applicable ESRM20 technical/exposure documentation, and state that the artifact is an exact no-normalization extraction from the v1.0 Kosovo-residential exposure object.

Repository approval is intentionally narrower than the source-rights ceiling. A permissive upstream licence is not itself a repository publication decision.

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

The public EFEHR documentation distinguishes residential, commercial and industrial buildings. The admitted P0 taxonomy derivative preserves the exact Kosovo-residential source `TAXONOMY` identities with no trim, case-fold, alias mapping or replacement by OpenCatastrophe/OED defaults.

`MACRO_TAXONOMY` is a distinct field and must not substitute for `TAXONOMY`. Mapping completeness and interpretation remain outside this admission.

Where building count, area, occupants or replacement cost are supplied, their source spatial unit, value basis and classification must remain linked to the original v1.0 files.

### Spatial resolution is part of scientific meaning

Regional exposure results depend on the spatial resolution at which exposure is represented. A future adapter must therefore preserve the exact source spatial units/geometries and must not claim that reaggregation or disaggregation is lossless.

The approved taxonomy derivative contains no geometry or coordinate values and does not establish CRS completeness for the source exposure artifact.

## Relationship to hazard and vulnerability

ESRM20 is a risk model assembled from distinct components: exposure, vulnerability, hazard/site response and risk calculations. This admission covers the exposure product and only one exact derived taxonomy artifact from the bounded Kosovo-residential slice.

It does not automatically admit or establish:

- ESHM20 hazard inputs;
- ESRM20 fragility/vulnerability functions;
- the exposure-to-vulnerability mapping artifact;
- mapping completeness or one-to-one semantics;
- IMT/component/unit/value-basis compatibility;
- site-response models;
- scenario files;
- OpenQuake configuration/results;
- model-input admission;
- any derived risk or loss output.

Those components need their own exact source identities and reviews. In particular, #283/#340 remain responsible for the independently byte-grounded mapping/vulnerability path.

## Suitable initial OpenCatastrophe uses

Good initial uses:

- testing exposure manifests and provenance;
- testing exact taxonomy identity and no-normalization contracts;
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
- vulnerability selection or mapping authority;
- production capital or regulatory conclusions.

## Raw admission remains blocked

Approval of the exact taxonomy derivative is **not** approval of the Kosovo CSV or any other ESRM20 source file. Before raw ESRM20 exposure bytes can be admitted, a separate proposal must:

1. re-check the current EFEHR licence/citation guidance close to publication;
2. bind the exact raw artifact identity and intended raw-publication scope;
3. document exact spatial units, taxonomy, currencies/value bases and source vintages from the selected file;
4. define any transformation or OED mapping explicitly, including losses/defaults/inference;
5. validate that no personal or restricted source material is introduced;
6. obtain explicit independent raw asset publication review.

Until then, the raw Kosovo CSV and all other ESRM20 exposure source bytes remain outside Git and outside `approved_raw` scope.

## Independent review fence

This candidate admission should not be integrated merely because the source licence is permissive or the manifest is schema-valid. Before merge, require fresh independent Science/Provenance/Data-Rights review on the exact candidate head, plus the repository manifest/admission checks. Review must verify at least:

- trusted #363 result comment `5303346187` and its exact 2666-byte/SHA identity;
- source receipt identity, exact canonicalization implementation and no-normalization transformation lineage;
- CC BY 4.0 attribution binding to this derivative scope;
- `raw_artifact=null` and continued raw-publication failure;
- successful `assert_public_asset_allowed(..., "derived")` for the candidate manifest;
- absence of taxonomy literals/provider bytes/private paths in the patch;
- no implication of mapping, vulnerability, model-input or loss authority.

## Authoritative public references

- EFEHR risk data access: `https://www.efehr.org/Earthquake-risk/data-access/`
- EFEHR ESRM20 documentation: `https://risk.efehr.org/documentation/`
- EFEHR exposure repository `v1.0`: `https://gitlab.seismo.ethz.ch/efehr/esrm20_exposure/-/tree/v1.0`
- EFEHR download/licensing guidance: `https://www.efehr.org/explore/Downloads-information-material/`
