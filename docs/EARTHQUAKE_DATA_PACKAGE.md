<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EQ1 Earthquake Data Package v0.1

This document is the first durable public handoff for the bounded EQ1 earthquake data package tracked by issue #287.

It is assembled against OpenCatastrophe-data `main` commit
`bd3417740a61d8f03427b72391bb7bc2ecb14bc3`.

## Status

**Data-identity handoff: complete for the selected EQ1 Kosovo-residential component set.**

**End-to-end ESRM20 loss reproduction: not yet authorized.**

The distinction is intentional. This package fixes the exact public source identities,
byte receipts, deterministic exposure-to-vulnerability selection, site input, hazard
roots and reconstructed reference-runtime evidence needed by a consumer. It does not
turn unresolved scientific compatibility, historical-runtime or validation questions
into implicit assumptions.

External provider bytes are not copied into this repository. The package is a
receipt-bound handoff: consumers materialize source bytes outside Git, verify the exact
byte count and SHA-256 before decoding, and use the repository's reviewed source-specific
workers and validators.

## Scope lock

The v0.1 bounded reference slice is:

- peril: earthquake;
- risk-model lineage: ESRM20 v1.0 plus the final ESRM20 vulnerability database v2.1;
- exposure slice: Kosovo residential exposure;
- public-data role: reproducible component/reference research and interoperability;
- excluded claims: production fitness, regulatory fitness, insured loss, pricing,
  capital, benchmark reproduction, publication authority and model-use authority.

The package does not require the historical Athens/Thessaloniki scenario lane. Those
scenario/observational assets remain useful validation work, but they are not required
to identify the selected Kosovo-residential input chain.

## Locked component identities

### 1. Exposure

Provider identity:

- dataset: `efehr.esrm20.european-exposure-model.v1.0`;
- project: `efehr/esrm20_exposure` / project 186;
- immutable commit: `900433ada80fbb424c0976c34d72eeef97bab1af`;
- path: `_exposure_models/Exposure_Model_Kosovo_Res.csv`;
- byte count: `316789`;
- SHA-256: `4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea`.

The receipt-bound value/spatial profiler is integrated on `main` by PR #518. Its
aggregate evidence does not publish raw rows, place/region labels or provider payload
values, and it does not promote valuation-vintage, CRS, publication or model-use
authority.

### 2. Exposure taxonomy projection

The exact receipted exposure contains:

- literal taxonomy column: `TAXONOMY`;
- distinct literal taxonomy values: `86`;
- canonical projection byte count: `2666`;
- canonical taxonomy-set SHA-256:
  `d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945`.

No taxonomy normalization, aliasing or fuzzy matching is allowed in the EQ1 selection
path.

### 3. Exposure-to-vulnerability mapping

Provider identity:

- project: `efehr/esrm20` / project 269;
- immutable ESRM20 v1.0 commit:
  `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Vulnerability/esrm20_exposure_vulnerability_mapping.csv`;
- byte count: `83585`;
- SHA-256: `94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c`.

Trusted EQ1 joining resolves all `86/86` Kosovo-residential source taxonomies by exact
literal matching:

- resolved: `86`;
- unsupported: `0`;
- ambiguous: `0`;
- unique resulting Risk IDs: `47`;
- canonical Risk-ID-set SHA-256:
  `1ea96cb5a62b864c20ffa056e0f7937d006ab6f6d57b2f4286c22112ca311102`.

### 4. Vulnerability selection

Final ESRM20 vulnerability lineage:

- project: `efehr/esrm20_vulnerability` / project 188;
- immutable v2.1 commit:
  `0183a72bc7ebf71a0b7dca41f6e92adb968c98a2`;
- selected mapping-derived Risk IDs: `47`;
- resolved provider-native candidate files: `47/47`;
- aggregate selected-file byte count: `3774`;
- canonical selected receipt-set SHA-256:
  `395b4cf044ab0f263fee88becd0ad9b957c9f7e92f8ecc3b22e023c591b2e951`.

The final ESRM20 vulnerability NRML also contains all 47 canonical Risk IDs. The
selected functions are vulnerability functions, not fragility functions. Their bounded
semantics are:

- asset category: buildings;
- loss category: structural;
- response: structural loss ratio on a total-replacement-cost basis;
- conditional uncertainty family: Beta (`BT`), represented by mean loss ratio and CoV;
- required IMTs: `PGA`, `SA(0.3)`, `SA(0.6)`, `SA(1.0)`;
- intensity unit: `g`.

These semantics do not convert the result into insured loss, TIV, policy loss,
Gross/Ceded/Net loss or capital. Intended ESRM20 use is established; independent
Kosovo-specific empirical predictive validity is not.

### 5. Kosovo site model

Provider identity:

- dataset: `efehr.esrm20.risk-inputs.v1.0`;
- project: `efehr/esrm20` / project 269;
- immutable commit: `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Vs30/Site_model_Kosovo.xml`;
- byte count: `5891`;
- SHA-256: `746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd`.

The reconstructed OpenQuake 3.14 ingestion path accepts 37 site records and exposes the
required parameter names:

- `geology`;
- `region`;
- `slope`;
- `vs30`;
- `xvf`.

Runtime value acceptance and GSIM parameter sufficiency have been demonstrated for the
bounded reconstructed reference path. CRS/coordinate semantics, missingness semantics,
site-parameter units and full site-model compatibility remain separately gated.

### 6. ESRM20 event-hazard roots

Both roots are from project 269 / `efehr/esrm20` at the immutable v1.0 commit
`05f83bbc9df81d02ee8ddb1801d9d781355ce783`.

Group 1:

- path: `Configuration_files/config_event_hazard_Group1.ini`;
- byte count: `1766`;
- SHA-256: `709168614dc4260a982fb4cc18956e1d4e236626efcc49bf1f1b9b4ff79969de`.

Group 2:

- path: `Configuration_files/config_event_hazard_Group2.ini`;
- byte count: `1673`;
- SHA-256: `eb74edd2168bad20c23d4b0e1a99f5ed97ef28606a9ebfef6b8c8191d35dd34c`.

These are exact-byte-grounded **event-hazard / risk-hazard roots** used to produce
stochastic catalogues and ground-motion fields. They are not sufficient full
risk-execution roots.

### 7. ESRM20 GMM logic tree

Provider identity:

- project: `efehr/esrm20` / project 269;
- immutable commit: `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Hazard/gmpe_logic_tree_5br_slope_geology.xml`;
- byte count: `34018`;
- SHA-256: `f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4`.

The exact five resolved GSIM classes are grounded against a reconstructed frozen
OpenQuake reference environment. Their native horizontal-component declarations are
mixed: the path contains both `RotD50` and `GEOMETRIC_MEAN` semantics.

### 8. Reconstructed OpenQuake reference runtime

Reference runtime identity:

- repository: `gem/oq-engine`;
- tag: `v3.14.0`;
- commit: `9f044c93d72846421a8faa90ebf0a6afacdf3c20`.

The current EQ1 reference lane establishes `provider_native_mixed_no_conversion` for
the selected GSIM set. It rejects an implicit `ModifiableGMPE` /
`horiz_comp_to_geom_mean` conversion and has produced finite native-component numeric
probes. This is reconstructed-reference evidence, not proof of an original historical
production environment and not numerical hazard validation.

## Compatibility matrix

| Interface / gate | v0.1 status | Evidence boundary |
| --- | --- | --- |
| Exposure byte identity | **PASS** | exact project/commit/path/bytes/SHA-256 |
| Exposure taxonomy extraction | **PASS** | 86 exact literal values; no normalization |
| Taxonomy → mapping join | **PASS** | 86/86 resolved; 0 unsupported; 0 ambiguous |
| Mapping → vulnerability selection | **PASS** | exactly 47 canonical Risk IDs |
| Vulnerability byte selection | **PASS** | 47/47 selected files receipted |
| Vulnerability IMT-name contract | **PASS** | `PGA`, `SA(0.3)`, `SA(0.6)`, `SA(1.0)` |
| Vulnerability intensity unit | **PASS** | `g` |
| Site byte identity | **PASS** | exact project/commit/path/bytes/SHA-256 |
| Site OpenQuake parser acceptance | **PASS** | 37 records; required five site parameters accepted |
| Event-hazard root byte identity | **PASS** | Group1 and Group2 exact receipts |
| GMM logic-tree byte identity | **PASS** | exact project/commit/path/bytes/SHA-256 |
| Reconstructed OQ3.14 GSIM resolution | **PASS** | five direct classes; no alias/conversion activation |
| Hazard ↔ vulnerability IMT names | **PASS** | same four canonical IMT names on the bounded lane |
| Hazard output unit ↔ vulnerability unit | **PASS** | bounded OQ3.14 PGA/SA reference output is in `g` |
| Horizontal-component interoperability | **BLOCKED** | mixed `RotD50` + `GEOMETRIC_MEAN`; no source authority for conversion |
| Site CRS / coordinate semantics | **BLOCKED** | current site evidence intentionally leaves this false |
| Site missingness semantics | **BLOCKED** | current site evidence intentionally leaves this false |
| Site-parameter unit closure | **BLOCKED** | runtime acceptance does not itself prove all semantic units |
| Exposure valuation vintage / exact value-basis compatibility | **BLOCKED** | aggregate value evidence exists; valuation authority remains separate |
| Vulnerability Kosovo empirical applicability | **BLOCKED** | intended ESRM20 European use is not independent Kosovo validation |
| Historical/default Kosovo `ebrisk` root | **BLOCKED** | provider v1.0 does not uniquely bind Kosovo to one default risk group |
| Historical ESRM20 risk runtime | **BLOCKED** | reconstructed OQ3.14 reference is not historical-risk-runtime proof |
| Numerical hazard agreement | **BLOCKED** | mechanics/runtime evidence only |
| End-to-end ground-up loss input readiness | **BLOCKED** | component/site/value-basis gates above remain open |
| Faithful ESRM20 benchmark reproduction | **BLOCKED** | full risk configuration/runtime plus science gates remain open |
| Independent validation / holdout | **BLOCKED** | no such claim is made by this package |
| Publication / production / model use | **BLOCKED** | explicitly outside v0.1 authority |

A `BLOCKED` row does not invalidate a preceding byte-identity `PASS`. It prevents that
identity evidence from being silently promoted into a stronger scientific or model-use
claim.

## Risk-configuration boundary

The immutable ESRM20 v1.0 provider evidence distinguishes the event-hazard configuration
family above from three separate `ebrisk` configurations used for full risk
calculations.

For country-specific calculations, provider guidance permits constructing a run by
modifying one of those configurations so that only the selected country site/exposure
files are called. That does **not** establish a unique historical/default `ebrisk` group
for Kosovo. Therefore this package does not guess a group from geography, numbering or
the two-group event-hazard partition.

A deliberately Kosovo-only reconstructed `ebrisk` configuration can be useful later,
but it must be labelled as a reconstructed experiment configuration rather than as the
historical bytes of the published full-Europe ESRM20 run.

## Admission and `model-input-v1`

This package does not create a second bundle schema and does not weaken the existing
admission contract.

`model-input-v1` binds one exact artifact that is already admitted by an accepted
manifest. It should be emitted only where the relevant manifest's artifact identity and
admission scope actually permit that binding.

Some EQ1 source families are still represented by metadata-only admission records or by
public trusted receipts rather than an admitted multi-file artifact. This package keeps
those components receipt-bound instead of fabricating a manifest artifact merely to
make a descriptor pass.

When a future scientific/model run materially uses these inputs, `run-evidence-v2`
should record the exact materially used artifacts, roles, hashes and evidence references
that were actually authorized at execution time.

## Consumer procedure

A consumer reproducing this v0.1 handoff should:

1. check out the exact OpenCatastrophe-data revision containing this package;
2. read the source-specific manifest/review plus the canonical issue evidence before
   acquiring external bytes;
3. materialize each required external source outside Git through the reviewed bounded
   acquisition path;
4. verify provider project/ref/path, byte count and SHA-256 **before decoding**;
5. run the exact taxonomy extraction and literal mapping join; reject normalization,
   unsupported or ambiguous taxonomies;
6. require the resulting canonical 47 Risk IDs before selecting vulnerability inputs;
7. independently verify the site, event-hazard and GMM identities above;
8. preserve the compatibility matrix: do not feed mixed-component hazard output into
   vulnerability under an invented conversion;
9. when the remaining gates are closed, bind the actual run with `run-evidence-v2`
   rather than treating this document as execution evidence.

## v0.1 definition of done

The earthquake **data package** is considered assembled at v0.1 when all of the
following remain true on the integrated repository state:

- [x] the selected exposure source has immutable public byte identity;
- [x] exposure taxonomy extraction is exact and deterministic;
- [x] exposure taxonomy maps fail-closed to 47 exact vulnerability Risk IDs;
- [x] all 47 selected vulnerability inputs have provider-grounded byte identities;
- [x] the Kosovo site input has immutable public byte identity;
- [x] the bounded event-hazard roots and GMM logic tree have immutable public byte identities;
- [x] the reconstructed reference runtime and its no-conversion component behavior are explicit;
- [x] no third-party provider bytes are committed by the package;
- [x] unresolved scientific/model-use gates are explicit rather than converted to assumptions;
- [x] the package reuses existing admission and run-evidence contracts instead of adding a competing schema.

This definition of done is deliberately narrower than **consumer-ready loss model** or
**faithful ESRM20 benchmark reproduction**.

## Next gates toward v0.2 / loss-run readiness

The shortest remaining sequence is:

1. close or deliberately label the horizontal-component treatment at the exact
   hazard→vulnerability consumer boundary;
2. close Kosovo site CRS/coordinate, missingness and unit semantics needed by that run;
3. close exposure value-basis/valuation compatibility with the replacement-cost
   vulnerability response;
4. select a source-authorized full-risk configuration or explicitly construct and label
   a Kosovo-only reconstructed experiment configuration;
5. execute one bounded end-to-end run and bind every materially used artifact and
   result with `run-evidence-v2`;
6. only then consider numerical agreement, benchmark-reproduction, validation,
   publication or production/model-use claims.

## Canonical evidence pointers

The public issue trail remains the source-specific evidence authority:

- #287 — first public earthquake consumer bundle / integration;
- #281 — hazard configuration, source/GMM and runtime evidence;
- #282 — Kosovo residential exposure;
- #283 — taxonomy mapping and vulnerability semantics;
- #291 / #284 — Kosovo site identity and site-response semantics;
- #449 / #461 / #478 — exact v2.1 vulnerability selection, receipts and function coverage;
- #481 / #493 / #508 / #519 — GMM byte identity, reconstructed runtime and mixed-component behavior.

Repository contracts remain authoritative for admission and run evidence:

- `schemas/model-input-v1.schema.json` / `schemas/model-input-v1.schema.md`;
- `schemas/run-evidence-v2.schema.json` / `schemas/run-evidence-v2.schema.md`;
- accepted source records in `manifests/` and `docs/source-reviews/`.

## Rights boundary

Provider/source licensing remains source-specific. Repository-authored metadata and
this document use the repository's Apache-2.0 license; that does not relicense external
ESRM20/EFEHR source bytes. Consumers must preserve the attribution and scope recorded in
the corresponding accepted source evidence.
