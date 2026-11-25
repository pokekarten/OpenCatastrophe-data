<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.langley.svrstormsig.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.langley.svrstormsig.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.langley.svrstormsig.documented

## Source ids

- nasa.langley.svrstormsig

**Provider:** NASA Langley / Cooney, Bedka and Liles

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://github.com/nasa/svrstormsig>

**Service root:** <https://science-data.larc.nasa.gov>

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

- /LaRC-SD-Publications/2023-05-05-001-JWC/data/ML_data.zip

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/zip

**Format:** Semantic segmentation of overshooting tops and above-anvil cirrus plumes from satellite imagery and atmospheric inputs

**Scientific semantics:** Paper https://doi.org/10.1175/AIES-D-24-0037.1; training labels, inputs and checkpoints listed at https://science-data.larc.nasa.gov/LaRC-SD-Publications/2023-05-05-001-JWC/data/. Repository contains License.pdf and License_Appendix.pdf; inspect code, checkpoints, training data and dependencies separately before reuse. Freeze commit, model config and sensor compatibility; compare MSG/MTG performance independently and correct parallax. OT and AACP are correlated severe-convection signatures, not surface hail labels; no code executed. On 2026-11-25 GitHub REST metadata identified license as Other / NOASSERTION, so inspect actual License.pdf and appendix rather than assume Apache. README documents native MTG-1 support from release V3 (April 2025), not verified MSG support; no inference run. Public checkpoint URL https://science-data.larc.nasa.gov/LaRC-SD-Publications/2023-05-05-001-JWC/data/ML_data.zip returned HEAD 200 application/zip, Content-Length 8182492479; too large for bounded sample, request smaller pinned weights or inspect archive index safely. No weights downloaded.

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

**Notes:** Public HEAD returned 8.18 GB; code licence Other/NOASSERTION, separate code/weights/training rights. Read actual licence and request smaller pinned checkpoints; test MTG sensor support in isolation; MSG transfer not established. No automated huge download.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://github.com/nasa/svrstormsig>

**Notes:** Open-first qualification queue. Public HEAD returned 8.18 GB; code licence Other/NOASSERTION, separate code/weights/training rights. Read actual licence and request smaller pinned checkpoints; test MTG sensor support in isolation; MSG transfer not established. No automated huge download. Discovery/access only: no admission, no external bytes in Git, no model approval.
