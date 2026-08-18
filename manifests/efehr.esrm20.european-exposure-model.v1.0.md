<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/efehr.esrm20.european-exposure-model.v1.0.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `efehr.esrm20.european-exposure-model.v1.0.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** efehr.esrm20.european-exposure-model.v1.0

**Provider:** European Facilities for Earthquake Hazard and Risk (EFEHR)

**Product name:** European Exposure Model for ESRM20

**Version or release:** v1.0

**Canonical source:** <https://gitlab.seismo.ethz.ch/efehr/esrm20_exposure/-/tree/v1.0>

**Retrieved at:** 2026-08-10T00:55:00Z

**Retrieval query or filters:** Metadata review plus exact bounded Kosovo-residential evidence. The selected source object is EFEHR project 186, immutable commit 900433ada80fbb424c0976c34d72eeef97bab1af, path _exposure_models/Exposure_Model_Kosovo_Res.csv, 316789 bytes, SHA-256 4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea. Provider bytes remain outside Git. The only repository-approved derivative is the exact canonical TAXONOMY-set byte stream identified below.

**Access class:** open

**Modelling layer:** exposure

**Intended use:** Open European building-stock exposure reference for catastrophe-risk research, exposure-contract testing and hazard/vulnerability linkage. The approved derived scope is limited to the exact Kosovo-residential source TAXONOMY set identity; this is not an insured portfolio, policy file, claims dataset or direct statement of total insured value.

## Raw artifact

**Byte size:** `316789`

**Sha256:** 4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea

**Storage reference:** external://source/efehr.esrm20.european-exposure-model.v1.0/kosovo-residential/raw/4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea

## Derived artifact

**Byte size:** `2666`

**Sha256:** d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945

**Storage reference:** external://derived/efehr.esrm20.european-exposure-model.v1.0/kosovo-residential/taxonomy/oc-taxonomy-u64be-utf8-sorted-v1

## Licensing

**Status:** verified

**Spdx expression:** CC-BY-4.0

**Licence name:** Creative Commons Attribution 4.0 International

**Terms reference:** <https://www.efehr.org/Earthquake-risk/data-access/>

**Terms reviewed at:** 2026-08-15T17:34:00Z

**Terms version or date:** EFEHR seismic-risk data-access and download guidance rechecked 2026-08-15; European Exposure Model release v1.0

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** Provide CC BY 4.0 attribution and cite the applicable ESRM20 scientific products, including the ESRM20 technical report and exposure-model documentation when the exposure data or the approved Kosovo TAXONOMY-set derivative are used. Identify the derivative as an exact no-normalization extraction from the v1.0 Kosovo-residential exposure object.

**Share alike or derivative requirements:** CC BY 4.0 permits adaptation without a share-alike requirement; attribution, licence reference and indication of changes remain required.

**Notes:** EFEHR states that scientific risk data available through risk.EFEHR and its public GitLab are licensed under CC BY 4.0. EFEHR's current download guidance explicitly permits private, scientific, commercial and non-commercial use with adequate citation. The repository approval in this manifest is intentionally narrower than the source-rights ceiling: it covers only the exact canonical Kosovo TAXONOMY-set derivative, not the raw exposure CSV. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** Source rights support raw and derived redistribution under CC BY 4.0 subject to attribution. OpenCatastrophe repository review currently approves only the exact 2666-byte canonical Kosovo-residential TAXONOMY-set derivative identified here; the raw Kosovo CSV and all other source artifacts remain outside repository publication scope.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The reviewed product is a public scientific exposure model describing aggregated European building stock and occupants, not person-level records or confidential insured portfolios. The approved derivative contains building-taxonomy identifiers only.

## Spatial

**Crs:** `null`

**Extent:** Europe at product level; the approved derivative is taxonomy-only metadata derived from the predeclared Kosovo-residential source slice and carries no geometry or coordinate values

## Temporal

**Extent:** European Exposure Model release v1.0; this is a modelled building-stock exposure snapshot rather than an event time series, and the approved derivative preserves only source taxonomy identity

## Variables and units

### Item 1

**Name:** building count

**Unit:** count

**Description:** Modelled building-stock quantity by exposure class/spatial unit.

### Item 2

**Name:** building area

**Unit:** m2

**Description:** Modelled building area where supplied by the selected exposure-model component.

### Item 3

**Name:** occupants

**Unit:** count

**Description:** Modelled occupant quantity associated with exposure classes; not person-level data.

### Item 4

**Name:** replacement cost

**Unit:** `null`

**Description:** Modelled replacement-cost value. Currency/value basis must be taken from the exact selected source file and must not be reinterpreted as insured TIV.


## Transformation

**Code reference:** f2fcfa1d94f1a44f738353ef0bae8d467351a2eb:scripts/acquire_efehr_kosovo_taxonomy.py

**Config identity:** canonicalizer-_canonical_artifact_identity/upstream-extractor-scripts-extract_efehr_kosovo_taxonomy.py/issue-363-result-5303346187/source-receipt-5300981864/source-sha256-4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea/TAXONOMY/count-86/oc-taxonomy-u64be-utf8-sorted-v1/no-normalization

## Review

**Status:** approved_derived

**Reviewed at:** 2026-08-15T17:34:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Asset-specific approval is limited to the exact canonical taxonomy-set byte stream produced from the frozen Kosovo-residential exposure source: 2666 bytes, SHA-256 d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945, representation oc-taxonomy-u64be-utf8-sorted-v1, literal source field TAXONOMY, count 86, no normalization. Canonical byte construction is bound to f2fcfa1d94f1a44f738353ef0bae8d467351a2eb:scripts/acquire_efehr_kosovo_taxonomy.py::_canonical_artifact_identity; scripts/extract_efehr_kosovo_taxonomy.py at the same execution SHA remains the upstream verified extraction dependency. Trusted identity evidence is GitHub Action result comment 5303346187 on Issue \#363, executed from f2fcfa1d94f1a44f738353ef0bae8d467351a2eb. Current EFEHR CC BY 4.0 data-access and download guidance was rechecked on 2026-08-15. This approval does not admit the 316789-byte raw Kosovo CSV, alternate serializations of the taxonomy values, mapping outcomes, vulnerability selections, model inputs, insured-loss semantics or any broader ESRM20 artifact. The raw_artifact field records the exact trusted Kosovo-residential source-byte identity for reproducibility/run-evidence binding only; review.status remains approved_derived and does not authorize raw publication, model-input admission or model use.
