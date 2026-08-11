<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/efehr.esrm20.european-exposure-model.v1.0.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `efehr.esrm20.european-exposure-model.v1.0.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Dataset id:** efehr.esrm20.european-exposure-model.v1.0

**Provider:** European Facilities for Earthquake Hazard and Risk (EFEHR)

**Product name:** European Exposure Model for ESRM20

**Version or release:** v1.0

**Canonical source:** <https://gitlab.seismo.ethz.ch/efehr/esrm20_exposure/-/tree/v1.0>

**Retrieved at:** 2026-08-10T00:55:00Z

**Retrieval query or filters:** Metadata-only source review of the tagged v1.0 European Exposure Model. No GitLab archive, model file or derived exposure bytes were acquired. Any later raw-artifact proposal must identify exact tagged files/archive bytes and hash them independently.

**Access class:** open

**Modelling layer:** exposure

**Intended use:** Open European building-stock exposure reference for catastrophe-risk research, exposure-contract testing and future hazard/vulnerability linkage. It is not an insured portfolio, policy file, claims dataset or direct statement of total insured value.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** CC-BY-4.0

**Licence name:** Creative Commons Attribution 4.0 International

**Terms reference:** <https://www.efehr.org/Earthquake-risk/data-access/>

**Terms reviewed at:** 2026-08-10T00:55:00Z

**Terms version or date:** EFEHR seismic-risk data-access and download guidance reviewed 2026-08-10; European Exposure Model release v1.0

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** Provide CC BY 4.0 attribution and cite the applicable ESRM20 scientific products, including the ESRM20 technical report and exposure-model documentation when the exposure data are used.

**Share alike or derivative requirements:** CC BY 4.0 permits adaptation without a share-alike requirement; attribution, licence reference and indication of changes remain required.

**Notes:** EFEHR states that scientific risk data available through risk.EFEHR and its public GitLab are licensed under CC BY 4.0. EFEHR's download guidance explicitly permits private, scientific, commercial and non-commercial use with adequate citation. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** Source rights support redistribution under CC BY 4.0 subject to attribution. OpenCatastrophe currently approves metadata only; no ESRM20 exposure artifact has been selected, acquired, hashed or approved for Git publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The reviewed product is a public scientific exposure model describing aggregated European building stock and occupants, not person-level records or confidential insured portfolios.

## Spatial

**Crs:** `null`

**Extent:** Europe; exact spatial units, geometries and resolution depend on the selected v1.0 exposure-model files and must be preserved by any future adapter

## Temporal

**Extent:** European Exposure Model release v1.0; this is a modelled building-stock exposure snapshot rather than an event time series, and exact source vintages must be preserved from the selected files

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


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-10T00:55:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only engineering approval based on authoritative EFEHR data-access/licensing pages and the tagged v1.0 exposure repository. No source archive or exposure-model bytes are admitted. Raw or derived publication remains blocked pending exact artifact identity and asset-specific review.
