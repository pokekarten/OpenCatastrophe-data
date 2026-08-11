<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/source-landscape-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `source-landscape-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:source-landscape:1.0.0

**Title:** OpenCatastrophe Source Landscape v1

**Description:** Portable structural profile for the public non-admission source-discovery registry.

**$comment:** scripts/source_landscape_contract.py is the authoritative executable policy validator. It additionally enforces strict JSON parsing, real calendar dates, globally unique candidate IDs and public-URL safety constraints that are not fully represented by this portable structural schema. Passing this schema never implies rights review, scientific approval, admission or permission for model use.

**Type:** object

**Additional properties:** `false`

## Required

- schema_version
- purpose
- review_date
- entries

## $defs

### Non blank text

**Type:** string

**Pattern:** \\S

### Entry

**Type:** object

**Additional properties:** `false`

#### Required

- candidate_id
- name
- provider
- categories
- spatial_scope
- temporal_scope
- resolution_or_granularity
- potential_roles
- authoritative_url
- access_class_hint
- candidate_status
- rights_review_status
- scientific_review_status
- admission_status
- note

#### Properties

##### Candidate id

**Type:** string

**Pattern:** ^\[a-z0-9\]+(?:\[.-\]\[a-z0-9\]+)\*$

##### Name

**$ref:** \#/$defs/nonBlankText

##### Provider

**$ref:** \#/$defs/nonBlankText

##### Categories

**Type:** array

**Min items:** `1`

###### Items

**Type:** string

**Min length:** `1`

##### Spatial scope

**$ref:** \#/$defs/nonBlankText

##### Temporal scope

**$ref:** \#/$defs/nonBlankText

##### Resolution or granularity

**$ref:** \#/$defs/nonBlankText

##### Potential roles

**Type:** array

**Min items:** `1`

###### Items

**Type:** string

**Min length:** `1`

##### Authoritative url

**Type:** string

**Pattern:** ^https://\\S+$

##### Access class hint

**$ref:** \#/$defs/nonBlankText

##### Candidate status

**Const:** evidence_checked

##### Rights review status

**Const:** not_reviewed

##### Scientific review status

**Const:** not_reviewed

##### Admission status

**Const:** not_admitted

##### Note

**$ref:** \#/$defs/nonBlankText

## Properties

### Schema version

**Const:** 1.0.0

### Purpose

**Type:** string

**Pattern:** Non-admission

### Review date

**Type:** string

**Format:** date

**Pattern:** ^\\d\{4\}-\\d\{2\}-\\d\{2\}$

### Entries

**Type:** array

**Min items:** `1`

#### Items

**$ref:** \#/$defs/entry
