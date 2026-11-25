<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/hong.modis.ot.climatology.2023.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `hong.modis.ot.climatology.2023.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** hong.modis.ot.climatology.2023.documented

## Source ids

- hong.modis.ot.climatology.2023

**Provider:** Hong, Nesbitt, Trapp and Di Girolamo

**Interface type:** web_portal

**Status:** documented_only

**Documentation url:** <https://doi.org/10.5194/amt-16-1391-2023>

**Service root:** <https://doi.org>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** other

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /10.5194/amt-16-1391-2023

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- text/html

**Format:** 1 km thermal IR imagery; logistic OT detection model

**Scientific semantics:** Original MODIS/CloudSat/GPM sources cited in study; downloadable derived individual OT catalogue not established. Polar-orbiting sampling and local overpass-time bias preclude continuous tracks. Obtain derived data or reproduce detection with observation opportunity normalization. Rights for source files and derived product separate.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Published method, no derived catalogue download established. Request exact detection data and reuse terms, or reproduce from separately reviewed MODIS archive; account for orbital sampling.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5194/amt-16-1391-2023>

**Notes:** Open-first qualification queue. Published method, no derived catalogue download established. Request exact detection data and reuse terms, or reproduce from separately reviewed MODIS archive; account for orbital sampling. Discovery/access only: no admission, no external bytes in Git, no model approval.
