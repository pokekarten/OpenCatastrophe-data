<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EQ1 Earthquake Data Package v0.1

This document is the durable public handoff for the bounded EQ1 earthquake data package
tracked by issue #287.

The initial assembly fence was OpenCatastrophe-data `main` commit
`bd3417740a61d8f03427b72391bb7bc2ecb14bc3`; the PR that carries this document must be
validated against its current merge base before integration.

## Status

**v0.1 component-data package: assembled.**

**Faithful end-to-end ESRM20 loss reproduction: not authorized by v0.1.**

The package fixes public source identities, byte receipts, deterministic selection
contracts and scientific boundaries needed by a consumer. It does not turn unresolved
runtime, site, component, valuation or validation questions into assumptions.

External provider bytes are not copied into this repository. Consumers materialize
source bytes outside Git, verify exact byte counts and SHA-256 values before decoding,
and use reviewed source-specific workers and validators.

## Two execution modes must remain separate

EQ1 contains two related but scientifically distinct earthquake lanes. They are both
useful package components, but they are **not interchangeable**.

### Mode A — ESHM20 hazard-reference reproduction

This is the exact ESHM20 hazard-reference configuration in provider project 197. Its
root, first-order dependencies and selected source-model children are byte-grounded.
It is the strongest current hazard-data reference lane.

Mode A must use the site artifact selected by its own ESHM20 root configuration. The
project-269 Kosovo site XML from Mode B must not be substituted merely because both are
site models.

### Mode B — ESRM20 Kosovo-residential risk-input / full-risk candidate lane

This is the ESRM20 risk-side chain in provider projects 186, 188 and 269: Kosovo
residential exposure, exact taxonomy mapping, final v2.1 vulnerability selection,
Kosovo site XML, ESRM20 event-hazard roots and the ESRM20 GMM tree.

Mode B has enough exact identity evidence to lock the selected risk-data components,
but it does **not** yet have a source-authorized unique historical/default Kosovo
`ebrisk` execution root. Therefore Mode B is not called a faithful full-risk run in
v0.1.

Never use evidence from one mode to silently satisfy a semantic or runtime gate in the
other.

## Mode A — exact ESHM20 hazard-reference data

### A1. Calculation root

Provider identity:

- project: `efehr/eshm20` / project 197;
- immutable commit: `fbd334de68f85d72669f73fc5a314a113db67317`;
- path:
  `oq_computational/oq_configuration_eshm20_v12e_region_main/config_eshm20_v12e_main_region.ini`;
- byte count: `2719`;
- SHA-256: `f1f4dabc48e1b8a478dbdb96b01c8f58cc68c98abd6f9004671c5fba9eb7e714`.

The exact root bytes deterministically select exactly three first-order dependencies.

### A2. First-order dependencies

All three objects are from project 197 at the same immutable commit.

| Role | Path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| site model | `oq_computational/oq_configuration_eshm20_v12e_region_main/eshm20_site_model_v06d.csv` | 3873324 | `d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529` |
| GMM logic tree | `oq_computational/oq_configuration_eshm20_v12e_region_main/gmpe_complete_logic_tree_5br.xml` | 33760 | `e2c53f11174b8cd4de1f65af4dafc5af2e7a6848563e8a4c0ada44a54f22ff62` |
| source-model logic tree | `oq_computational/oq_configuration_eshm20_v12e_region_main/source_model_logic_tree_eshm20_model_v12e.xml` | 17579 | `97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867` |

The frozen selected-prefix inventory contains no `.hdf5` and no ZIP entries inside the
selected ESHM20 configuration prefix. That is an inventory statement, not authority to
invent absent dependencies.

### A3. Source-model children

The exact source-model logic-tree bytes resolve to exactly `51` canonical non-HDF5
source-model child paths.

- canonical child count: `51`;
- canonical ordered path-set SHA-256:
  `2fcc885dc9fbbd8e9ee45b185dc9f2339af3654e9976ae5f07d4d097551944b7`;
- project: `efehr/eshm20` / 197;
- immutable commit: `fbd334de68f85d72669f73fc5a314a113db67317`;
- trusted-main terminal receipt run: `31940875325`;
- terminal result comment: `5306897047`;
- result: exact byte-count + SHA-256 receipts for all `51/51` selected paths;
- persistence: no provider bytes persisted by the receipt path.

The fixed reviewed worker
`scripts/acquire_eshm20_source_model_child_receipts.py` is the repository-side canonical
selection contract for those 51 paths. The individual provider-byte receipts remain in
the terminal trusted-main evidence; this package does not duplicate provider payloads.

These receipts close selected child-byte identity. They do not automatically authorize
transitive source-internal dependency expansion, source-physics interpretation,
publication or model use.

### A4. Mode-A site boundary

Mode A's site authority is the exact project-197
`eshm20_site_model_v06d.csv` object above. Its byte identity is closed.

Column/unit/CRS/coordinate/interpolation semantics and faithful runtime site-response
claims remain separate science gates. The Mode-B Kosovo XML is not a substitute.

### A5. Published horizontal-component boundary

The peer-reviewed ESHM20 results publication by Danciu et al. (NHESS 2024,
DOI `10.5194/nhess-24-3049-2024`) states that the published ESHM20 hazard results are
valid for `RotD50` of the horizontal components.

This is direct Mode-A model-output evidence. It must not be promoted into a claim that
Mode B's mixed native ESRM20 risk-runtime branches or vulnerability calibration traces
share a `RotD50` basis.

## Mode B — exact ESRM20 Kosovo-residential risk-side data

### B1. Exposure

Provider identity:

- dataset: `efehr.esrm20.european-exposure-model.v1.0`;
- project: `efehr/esrm20_exposure` / project 186;
- immutable commit: `900433ada80fbb424c0976c34d72eeef97bab1af`;
- path: `_exposure_models/Exposure_Model_Kosovo_Res.csv`;
- byte count: `316789`;
- SHA-256: `4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea`.

The receipt-bound value/spatial profiler is integrated on `main` by PR #518. Aggregate
profiling does not publish raw rows, place/region labels or provider payload values, and
it does not promote valuation vintage, CRS, publication or model-use authority.

Runtime OpenQuake exposure identity:

- dataset: `efehr.esrm20.risk-inputs.v1.0`;
- project: `efehr/esrm20` / project 269;
- immutable ESRM20 v1.0 commit:
  `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Exposure/OQ_Exposure_Input_Kosovo_Res.csv`;
- byte count: `160627`;
- SHA-256: `12a20d393c8d677d304263aed96eb05f81098104fd7e3fb0d119aafc336aa00f`;
- exact record count: `1093`;
- exact header:
  `id,lon,lat,taxonomy,number,structural,night,day,transit,occupancy,name_2,id_2,id_1,name_1`.

The exact project-269 NRML wrapper declares category `buildings`, GEM taxonomy,
`structural` cost type `aggregated` in `EUR`, occupancy periods `day/night/transit`, and
tags `occupancy,name_2,id_2,id_1,name_1`. Under the frozen OpenQuake exposure contract,
the bounded runtime field meanings are therefore:

- `id`: asset identifier;
- `lon` / `lat`: longitude / latitude in decimal degrees; exact datum/EPSG remains
  unverified;
- `taxonomy`: runtime OpenQuake building taxonomy token;
- `number`: structural-unit count;
- `structural`: aggregated structural replacement-cost input in EUR;
- `day` / `night` / `transit`: occupant counts for those declared occupancy periods;
- the five wrapper-declared tag fields: aggregation tags only at this evidence strength.

Provider documentation establishes project 269's `Exposure` family as the OpenQuake-
formatted final-model distribution corresponding to the ESRM20 exposure-model family.
It does **not** yet prove the exact project-186 source-file -> project-269 runtime-file
transformation, row identity, or `TOTAL_REPL_COST_EUR` -> `structural` generation rule.

The exact-Decimal comparator integrated by PR #599 now provides a fail-closed,
receipt-bound mechanism for comparing the frozen source/runtime pair without publishing
raw rows. A trusted-main provider execution/result is separate evidence and is not
pre-claimed by this package.

### B2. Exposure taxonomy projection

The exact receipted exposure contains:

- literal taxonomy column: `TAXONOMY`;
- distinct literal taxonomy values: `86`;
- canonical projection byte count: `2666`;
- canonical taxonomy-set SHA-256:
  `d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945`.

No taxonomy normalization, aliasing or fuzzy matching is allowed in the EQ1 selection
path.

### B3. Exposure-to-vulnerability mapping

Provider identity:

- project: `efehr/esrm20` / project 269;
- immutable ESRM20 v1.0 commit:
  `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Vulnerability/esrm20_exposure_vulnerability_mapping.csv`;
- byte count: `83585`;
- SHA-256: `94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c`.

The exact literal join resolves the Kosovo-residential taxonomy set:

- resolved: `86/86`;
- unsupported: `0`;
- ambiguous: `0`;
- unique resulting Risk IDs: `47`;
- canonical Risk-ID-set SHA-256:
  `1ea96cb5a62b864c20ffa056e0f7937d006ab6f6d57b2f4286c22112ca311102`.

### B4. Vulnerability selection

Provider-native mapping-derived selection lineage:

- project: `efehr/esrm20_vulnerability` / project 188;
- immutable v2.1 commit:
  `0183a72bc7ebf71a0b7dca41f6e92adb968c98a2`;
- selected mapping-derived Risk IDs: `47`;
- resolved provider-native candidate files: `47/47`;
- aggregate selected-file byte count: `3774`;
- canonical selected receipt-set SHA-256:
  `395b4cf044ab0f263fee88becd0ad9b957c9f7e92f8ecc3b22e023c591b2e951`.

These 47 provider-native files establish the mapping-derived v2.1 selection/provenance
layer. They are not the executable final NRML object.

Executable final ESRM20 vulnerability NRML identity:

- dataset: `efehr.esrm20.risk-inputs.v1.0`;
- project: `efehr/esrm20` / project 269;
- immutable ESRM20 v1.0 commit:
  `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml`;
- byte count: `908623`;
- SHA-256: `22f699ef9b649f388f850551066847ff02f36c72606dc9c615f05d454f1f918e`.

The trusted-main final-NRML profile under #478 verifies this exact byte identity and
contains all 47 canonical Risk IDs. The selected functions are vulnerability functions,
not fragility functions. Their bounded semantics are:

- asset category: buildings;
- loss category: structural;
- response: structural loss ratio on a total-replacement-cost basis;
- conditional uncertainty family: Beta (`BT`), represented by mean loss ratio and CoV;
- required IMTs: `PGA`, `SA(0.3)`, `SA(0.6)`, `SA(1.0)`;
- intensity-unit interpretation: `g` under the frozen OpenQuake 3.14 runtime convention
  for these exact PGA/SA IMT tokens; the final NRML XML does not itself declare the
  intensity unit.

These semantics do not turn the result into insured loss, TIV, policy loss,
Gross/Ceded/Net loss or capital. Intended ESRM20 use is established; independent
Kosovo-specific empirical predictive validity is not.

The released v2.1 calibration/reproducibility GMR corpus is source-linkage lossy at the
horizontal-component boundary. The public reproduction code consumes one scalar
`[time, acceleration]` trace per prepared record, while the first public reproducibility
commit introduces the already-prepared `scaled_record_*` corpus without an upstream
record/channel/orientation mapping. Direct methodology and public Git history therefore
do not establish whether the exact calibration traces represent `RotD50`, horizontal
geometric mean, one named component, or another construction. The vulnerability
horizontal-component convention remains `UNKNOWN` / fail-closed.

### B5. Kosovo site model

Provider identity:

- dataset: `efehr.esrm20.risk-inputs.v1.0`;
- project: `efehr/esrm20` / project 269;
- immutable commit: `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Vs30/Site_model_Kosovo.xml`;
- byte count: `5891`;
- SHA-256: `746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd`.

The reconstructed OpenQuake 3.14 runtime path accepts all `37/37` exact site records
against the exact ESRM20 GMM tree and its required site-parameter names
`geology`, `region`, `slope`, `vs30` and `xvf`. This closes bounded runtime-value
acceptance and GSIM site-parameter sufficiency for the reconstructed reference path.

CRS/datum authority, provider missing/sentinel semantics and broader historical
site-generation provenance remain separately gated; parser/runtime acceptance must not
be promoted into those claims.

### B6. ESRM20 event-hazard roots

Both roots are from project 269 / `efehr/esrm20` at immutable ESRM20-v1.0 commit
`05f83bbc9df81d02ee8ddb1801d9d781355ce783`.

Group 1:

- path: `Configuration_files/config_event_hazard_Group1.ini`;
- byte count: `1766`;
- SHA-256: `709168614dc4260a982fb4cc18956e1d4e236626efcc49bf1f1b9b4ff79969de`.

Group 2:

- path: `Configuration_files/config_event_hazard_Group2.ini`;
- byte count: `1673`;
- SHA-256: `eb74edd2168bad20c23d4b0e1a99f5ed97ef28606a9ebfef6b8c8191d35dd34c`.

These are exact-byte-grounded **event-hazard roots** used for stochastic catalogues and
ground-motion fields. They are not sufficient full-risk `ebrisk` execution roots.

### B7. ESRM20 GMM logic tree

Provider identity:

- project: `efehr/esrm20` / project 269;
- immutable commit: `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Hazard/gmpe_logic_tree_5br_slope_geology.xml`;
- byte count: `34018`;
- SHA-256: `f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4`.

The exact five resolved GSIM classes are grounded against the frozen reconstructed
reference runtime. Their native horizontal-component declarations are mixed: the path
contains both `RotD50` and `GEOMETRIC_MEAN` semantics.

### B8. Reconstructed OpenQuake reference runtime

Reference runtime identity:

- repository: `gem/oq-engine`;
- tag: `v3.14.0`;
- commit: `9f044c93d72846421a8faa90ebf0a6afacdf3c20`.

The current EQ1 reference lane establishes `provider_native_mixed_no_conversion` for
the selected ESRM20 GSIM set. Trusted runtime evidence records native components
`RotD50` and `GEOMETRIC_MEAN`, `mixed_component_basis=true`, no requested horizontal-
component conversion and no activated `ModifiableGMPE` / `horiz_comp_to_geom_mean`
conversion.

This is reconstructed-reference evidence. It is not proof of the original historical
ESRM20 production environment, not proof that mixed native components equal the
vulnerability calibration component, and not numerical hazard validation.

### B9. Immutable ESRM20 technical-report identity

The frozen ESRM20 v1.0 documentation object is separately receipt-bound:

- project: `efehr/esrm20` / project 269;
- immutable commit: `05f83bbc9df81d02ee8ddb1801d9d781355ce783`;
- path: `Documentation/EFEHR_TR002_ESRM20.pdf`;
- edition: EFEHR Technical Report 002 V1.0.0;
- page count: `84`;
- byte count: `19153998`;
- SHA-256: `b4b533e673a542ee796cc6e80db4d7a4232ead9220afd2d1a4fa5a3fa4bedf3d`.

This immutable release object differs byte-for-byte from the separately receipted
mutable/current V1.0.1 report. Current/mutable documentation must therefore not be used
as a silent substitute for V1.0.0 authority. Exact V1.0.0 renderability is established,
but a durable exact-object component/conversion term-and-page disposition is still
missing; no report-level component claim is inferred from the runtime result above.

## Compatibility matrix

| Interface / gate | v0.1 status | Mode / evidence boundary |
| --- | --- | --- |
| ESHM20 root byte identity | **PASS** | A — exact project/commit/path/bytes/SHA-256 |
| ESHM20 first-order dependency bytes | **PASS** | A — exact 3/3 receipts |
| ESHM20 source child selection | **PASS** | A — exactly 51 canonical paths |
| ESHM20 source child byte identity | **PASS** | A — exact 51/51 terminal trusted-main receipts |
| ESHM20 site byte identity | **PASS** | A — exact selected project-197 site CSV |
| ESHM20 published output horizontal component | **PASS** | A — peer-reviewed model-output statement: `RotD50` |
| ESHM20 site semantic/runtime closure | **BLOCKED** | A — CRS/units/interpolation/runtime semantics not fully authorized |
| ESHM20 numerical hazard agreement | **BLOCKED** | A — byte/reference mechanics do not equal numerical validation |
| ESRM20 source exposure byte identity | **PASS** | B — exact project-186 project/commit/path/bytes/SHA-256 |
| ESRM20 runtime exposure byte identity | **PASS** | B — exact project-269 project/commit/path/160627 bytes/SHA-256 |
| ESRM20 runtime exposure native-field semantics | **PASS** | B — wrapper-bound structural aggregated EUR, unit-count, occupancy and tag roles; datum/EPSG excluded |
| Project-186 source → project-269 runtime exact transform | **BLOCKED** | B — same provider model family established; exact generator/row/value transform not yet proven |
| Exposure taxonomy extraction | **PASS** | B — 86 exact literal values; no normalization |
| Taxonomy → mapping join | **PASS** | B — 86/86 resolved; 0 unsupported; 0 ambiguous |
| Mapping → vulnerability selection | **PASS** | B — exactly 47 canonical Risk IDs |
| Vulnerability provider-native byte selection | **PASS** | B — project-188 v2.1 47/47 selected files receipted |
| Final vulnerability NRML byte identity | **PASS** | B — exact project-269 commit/path/908623 bytes/SHA-256 |
| Final vulnerability NRML Risk-ID coverage | **PASS** | B — exact #478 profile contains all 47 canonical Risk IDs |
| Vulnerability IMT-name contract | **PASS** | B — `PGA`, `SA(0.3)`, `SA(0.6)`, `SA(1.0)` |
| Vulnerability intensity-unit interpretation | **PASS** | B — frozen OQ3.14 maps the exact PGA/SA IMT tokens to `g`; XML has no unit declaration |
| Vulnerability horizontal-component convention | **BLOCKED** | B — released scalar calibration traces have no public source-channel/component binding |
| ESRM20 Kosovo site byte identity | **PASS** | B — exact project/commit/path/bytes/SHA-256 |
| ESRM20 Kosovo site OQ3.14 runtime-value acceptance | **PASS** | B — exact `37/37` records accepted against exact GMM runtime |
| ESRM20 Kosovo site GSIM parameter sufficiency | **PASS** | B — required `geology,region,slope,vs30,xvf` satisfied on bounded reconstructed path |
| ESRM20 event-hazard root identities | **PASS** | B — Group1 and Group2 exact receipts |
| ESRM20 GMM-tree byte identity | **PASS** | B — exact project/commit/path/bytes/SHA-256 |
| ESRM20 reconstructed OQ3.14 GSIM resolution | **PASS** | B — five direct classes; no alias/conversion activation |
| ESRM20 reconstructed runtime component behavior | **PASS** | B — provider-native mixed `RotD50` + `GEOMETRIC_MEAN`, no requested/activated conversion |
| ESRM20 hazard ↔ vulnerability IMT names | **PASS** | B — same four canonical IMT names on bounded lane |
| ESRM20 hazard output unit ↔ vulnerability unit | **PASS** | B — bounded OQ3.14 PGA/SA reference output and vulnerability IMT interpretation are in `g` |
| Hazard ↔ vulnerability horizontal-component interoperability | **BLOCKED** | B — vulnerability component is unbound; no RotD50↔GEOMETRIC_MEAN conversion authority |
| Immutable ESRM20 TR002 V1.0.0 byte identity | **PASS** | B — exact project/ref/path/19153998 bytes/SHA-256; 84 pages |
| Immutable TR002 component/conversion text authority | **BLOCKED** | B — exact report is renderable, but no durable exact-object term/page disposition yet |
| ESRM20 site CRS / coordinate semantics | **BLOCKED** | B — datum/EPSG and historical generator authority intentionally remain false |
| ESRM20 site missingness / unit semantics | **BLOCKED** | B — runtime acceptance does not prove all provider semantics |
| Exposure valuation vintage / source-value-generation compatibility | **BLOCKED** | B — runtime structural semantics are bounded; source→runtime generation/valuation authority remains separate |
| Vulnerability Kosovo empirical applicability | **BLOCKED** | B — intended ESRM20 use is not independent Kosovo validation |
| Historical/default Kosovo `ebrisk` root | **BLOCKED** | B — provider v1.0 does not uniquely bind Kosovo to one default risk group |
| Historical ESRM20 risk runtime | **BLOCKED** | B — reconstructed OQ3.14 is not historical-risk-runtime proof |
| End-to-end ground-up loss readiness | **BLOCKED** | B — component/site provenance/value-generation/configuration gates remain open |
| Faithful ESRM20 benchmark reproduction | **BLOCKED** | B — full-risk configuration/runtime + science gates remain open |
| Independent validation / holdout | **BLOCKED** | A/B — no such claim is made by v0.1 |
| Publication / production / model use | **BLOCKED** | A/B — explicitly outside v0.1 authority |

A `BLOCKED` row does not invalidate a preceding byte-identity or bounded-runtime
`PASS`. It prevents that evidence from being silently promoted into a stronger
scientific or model-use claim.

## Risk-configuration boundary

The immutable ESRM20 v1.0 provider evidence distinguishes the Mode-B event-hazard
configuration family from separate `ebrisk` configurations used for full risk
calculations.

Provider guidance permits constructing country-specific calculations by modifying an
`ebrisk` configuration so that only selected country site/exposure files are called.
That does **not** establish a unique historical/default `ebrisk` group for Kosovo.
Therefore v0.1 does not guess a group from geography, numbering or the two-group
event-hazard partition.

A Kosovo-only reconstructed `ebrisk` configuration can be useful later, but it must be
labelled as a reconstructed experiment configuration rather than historical published
ESRM20 execution bytes.

## Admission and repository contracts

This package does not create a second bundle schema and does not weaken existing
admission rules.

`model-input-v1` binds one exact artifact already admitted by an accepted manifest. It
should be emitted only where the relevant manifest artifact identity and admission
scope permit that binding.

Several EQ1 source families are represented by trusted public receipts or metadata-only
admission records rather than one admitted multi-file artifact. v0.1 keeps those
components receipt-bound instead of fabricating a manifest artifact merely to make a
descriptor pass.

When a scientific/model run materially uses these inputs, `run-evidence-v2` should bind
the exact materially used artifacts, roles, hashes and evidence references actually
authorized at execution time.

## Consumer procedure

A consumer reproducing v0.1 should:

1. check out the exact OpenCatastrophe-data revision containing this package;
2. choose **Mode A or Mode B explicitly** before materializing data;
3. read source-specific manifest/review and canonical issue evidence before acquisition;
4. materialize each required external source outside Git through the reviewed bounded
   acquisition path;
5. verify provider project/ref/path, byte count and SHA-256 **before decoding**;
6. for Mode A, require the exact ESHM20 root, exactly three first-order dependencies and
   the fixed 51-child source-model set; never substitute the Mode-B site model;
7. for Mode B exposure, keep the project-186 source exposure and project-269 runtime
   OpenQuake exposure as separate exact identities; do not infer the source→runtime
   transform from shared taxonomy/value-looking fields;
8. for Mode B, require the exact 86-taxonomy projection, exact literal mapping join and
   resulting canonical 47 Risk IDs before vulnerability selection;
9. for Mode B vulnerability, keep the project-188 v2.1 47-file selection/provenance
   layer distinct from the project-269 executable final NRML, and verify the final NRML
   project/ref/path/byte count/SHA-256 before profiling or execution;
10. preserve the compatibility matrix; in particular, do not invent a horizontal
    component conversion, a source→runtime value-generation rule, a site CRS/datum or a
    historical/default Kosovo `ebrisk` group;
11. when a model run is scientifically authorized, bind actual execution with
    `run-evidence-v2` rather than treating this document as execution evidence.

## v0.1 definition of done

The earthquake **component-data package** is assembled at v0.1 when all of the
following remain true on the integrated repository state:

- [x] Mode A ESHM20 calculation root has immutable public byte identity;
- [x] Mode A exactly-three first-order dependencies have immutable public byte identities;
- [x] Mode A source-model tree selects exactly 51 canonical child paths;
- [x] all 51 Mode A selected source-model children have terminal exact byte receipts;
- [x] Mode-B project-186 Kosovo residential source exposure has immutable public byte identity;
- [x] Mode-B project-269 Kosovo residential runtime exposure has immutable public byte identity and bounded native OpenQuake field semantics;
- [x] Mode B exposure taxonomy extraction is exact and deterministic;
- [x] the taxonomy maps fail-closed to exactly 47 vulnerability Risk IDs;
- [x] all 47 selected provider-native vulnerability inputs have grounded byte identities;
- [x] the executable final vulnerability NRML has immutable public byte identity and
  exact 47/47 canonical Risk-ID coverage;
- [x] the Mode-B Kosovo site, event-hazard roots and GMM tree have immutable identities;
- [x] bounded OQ3.14 site runtime-value acceptance and GSIM parameter sufficiency are explicit;
- [x] the reconstructed reference-runtime mixed/no-conversion behavior is explicit;
- [x] the immutable ESRM20 TR002 V1.0.0 report identity is receipt-bound separately from mutable/current documentation;
- [x] Mode-A and Mode-B site/hazard/component authorities are not collapsed;
- [x] no third-party provider bytes are committed by the package;
- [x] unresolved scientific/model-use gates are explicit rather than converted to assumptions;
- [x] existing admission and run-evidence contracts are reused rather than replaced.

This definition of done is deliberately narrower than **consumer-ready loss model** or
**faithful ESRM20 benchmark reproduction**.

## Next gates toward loss-run readiness

The shortest remaining Mode-B sequence is:

1. preserve the vulnerability horizontal-component convention as UNKNOWN unless exact
   provider/author authority appears; do not invent a conversion from the mixed native
   hazard runtime;
2. close Kosovo site CRS/datum, missingness and historical-generation semantics actually
   needed by the run, while retaining the already-passing 37/37 runtime-value/GSIM gate;
3. close source→runtime exposure generation/value-basis provenance needed to interpret
   replacement-cost inputs beyond the already-bounded runtime `structural=aggregated EUR` contract;
4. select a source-authorized full-risk configuration or construct and explicitly label
   a Kosovo-only reconstructed experiment configuration;
5. execute one bounded end-to-end run and bind every materially used artifact/result
   with `run-evidence-v2`;
6. only then consider numerical agreement, benchmark reproduction, independent
   validation, publication or production/model-use claims.

Mode A can advance independently through its own site-semantics and numerical-reference
validation gates without being treated as a substitute for Mode B.

## Canonical evidence pointers

The public issue trail remains the source-specific evidence authority:

- #287 — first public earthquake consumer bundle / integration contract;
- #281 — ESHM20 hazard reference plus ESRM20 hazard/GMM research boundaries;
- #335 / #353 / #361 / #397 / #414 — Mode-A root/dependency/source-child closure;
- #282 — Kosovo residential source/runtime exposure identity and bounded field semantics;
- #283 — taxonomy mapping, vulnerability semantics and GMR component-provenance boundary;
- #291 / #284 — Mode-B Kosovo site identity and site-response semantics;
- #449 / #461 / #478 — exact v2.1 vulnerability selection, receipts and function coverage;
- #481 / #493 / #508 / #519 — ESRM20 GMM identity, reconstructed runtime and mixed-component behavior;
- #596 — immutable ESRM20 TR002 V1.0.0 receipt and mutable/current-report byte distinction.

Repository contracts remain authoritative for admission and run evidence:

- `schemas/model-input-v1.schema.json` / `schemas/model-input-v1.schema.md`;
- `schemas/run-evidence-v2.schema.json` / `schemas/run-evidence-v2.schema.md`;
- accepted source records in `manifests/` and `docs/source-reviews/`.

## Rights boundary

Provider/source licensing remains source-specific. Repository-authored metadata and
this document use the repository's Apache-2.0 license; that does not relicense external
ESHM20/ESRM20/EFEHR source bytes. Consumers must preserve attribution and scope recorded
in corresponding accepted source evidence.
