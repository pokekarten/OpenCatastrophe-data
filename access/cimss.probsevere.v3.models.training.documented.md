<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/cimss.probsevere.v3.models.training.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `cimss.probsevere.v3.models.training.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** cimss.probsevere.v3.models.training.documented

## Source ids

- cimss.probsevere.v3.models.training

**Provider:** CIMSS / NOAA

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/10891477>

**Service root:** <https://zenodo.org>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /records/10891477/files/phv3_lgb_classifier.pkl

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- application/octet-stream

**Format:** Python pickle model and storm attribute files

**Scientific semantics:** Live Zenodo metadata 2026-11-25: 7 files, 10760638082 total bytes, cc-by-4.0; hail classifier phv3_lgb_classifier.pkl 7819023 bytes, MD5 9c9b3d34b5bebda73ed0a6f92a4d50bf. Do not deserialize untrusted pickle or execute downloaded models; require trusted isolated conversion to auditable safe format, exact upstream rights review, feature and label definitions. Metadata only; no pickle downloaded.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** Review provider terms and explicit request/byte budget before any future execution.

**Mutability notes:** Freeze exact asset/version, UTC retrieval, size and SHA-256; mutable metadata is not data identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://about.zenodo.org/policies/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** CC BY 4.0 deposit, model and training lineage review needed. Do not deserialize untrusted pickle; ask for safe model export and small tabular feature subset.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://zenodo.org/records/10891477>

**Notes:** Open-first qualification. CC BY 4.0 deposit, model and training lineage review needed. Do not deserialize untrusted pickle; ask for safe model export and small tabular feature subset. No admission or authorization to acquire data.
