<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/run-evidence-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `run-evidence-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:run-evidence:1.0.0

**Title:** OpenCatastrophe Run Evidence Profile v1

**Description:** Closed scientific execution receipt for deterministic or stochastic OpenCatastrophe work, including bounded interoperability claims.

**Type:** object

**Additional properties:** `false`

## Required

- profile_version
- run_id
- repository
- execution
- inputs
- randomness
- outputs
- validation
- status
- claims
- limitations

## $defs

### Command

**Type:** object

**Additional properties:** `false`

#### Required

- argv
- purpose

#### Properties

##### Argv

**Type:** array

**Min items:** `1`

###### Items

**Type:** string

**Min length:** `1`

##### Purpose

**Type:** string

**Min length:** `1`

##### Cwd

**Type:** string

**Min length:** `1`

**Pattern:** ^(?\!/)(?\!\[A-Za-z\]:\[\\\\/\])(?\!.\*\\\\)(?\!.\*(?:^\|/)\\.\{1,2\}(?:/\|$))(?\!.\*//)\[^\\x00\]+$

### Sha256

**Type:** string

**Pattern:** ^\[a-f0-9\]\{64\}$

### Commit

**Type:** string

**Pattern:** ^\[a-f0-9\]\{40\}$

### Relative path

**Type:** string

**Min length:** `1`

**Pattern:** ^(?\!/)(?\!\[A-Za-z\]:\[\\\\/\])(?\!.\*\\\\)(?\!.\*(?:^\|/)\\.\{1,2\}(?:/\|$))(?\!.\*//)\[^\\x00\]+$

### Timestamp

**Type:** string

**Format:** date-time

## Properties

### Profile version

**Const:** 1.0.0

### Run id

**Type:** string

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._:-\]\{0,127\}$

### Repository

**Type:** object

**Additional properties:** `false`

#### Required

- name
- commit
- dirty

#### Properties

##### Name

**Type:** string

**Pattern:** ^\[A-Za-z0-9_.-\]+/\[A-Za-z0-9_.-\]+$

##### Commit

**$ref:** \#/$defs/commit

##### Tree

**$ref:** \#/$defs/commit

##### Dirty

**Type:** boolean

### Execution

**Type:** object

**Additional properties:** `false`

#### Required

- commands
- started_at
- ended_at
- exit_code

#### Properties

##### Commands

**Type:** array

**Min items:** `1`

###### Items

**$ref:** \#/$defs/command

##### Started at

**$ref:** \#/$defs/timestamp

##### Ended at

**$ref:** \#/$defs/timestamp

##### Exit code

**Type:** integer

### Inputs

**Type:** array

#### Items

**Type:** object

**Additional properties:** `false`

##### Required

- id
- kind
- identity

##### Properties

###### Id

**Type:** string

**Min length:** `1`

###### Kind

**Type:** string

**Min length:** `1`

###### Identity

**Type:** string

**Min length:** `1`

###### Sha256

**$ref:** \#/$defs/sha256

###### Version

**Type:** string

**Min length:** `1`

###### Not

**Const:** latest

### Randomness

#### One of

##### Item 1

**Type:** object

**Additional properties:** `false`

###### Required

- mode

###### Properties

###### Mode

**Const:** deterministic

##### Item 2

**Type:** object

**Additional properties:** `false`

###### Required

- mode
- algorithm
- implementation
- seed_material
- stream_identity
- draw_protocol

###### Properties

###### Mode

**Const:** stochastic

###### Algorithm

**Type:** string

**Min length:** `1`

###### Implementation

**Type:** string

**Min length:** `1`

###### Seed material

**Type:** string

**Min length:** `1`

###### Stream identity

**Type:** string

**Min length:** `1`

###### Draw protocol

**Type:** string

**Min length:** `1`


### Outputs

**Type:** array

#### Items

**Type:** object

**Additional properties:** `false`

##### Required

- path
- sha256
- byte_size
- media_type

##### Properties

###### Path

**$ref:** \#/$defs/relativePath

###### Sha256

**$ref:** \#/$defs/sha256

###### Byte size

**Type:** integer

**Minimum:** `0`

###### Media type

**Type:** string

**Min length:** `1`

### Validation

**Type:** array

**Min items:** `1`

#### Items

**Type:** object

**Additional properties:** `false`

##### Required

- check
- status

##### Properties

###### Check

**Type:** string

**Min length:** `1`

###### Status

###### Enum

- pass
- fail
- blocked
- not_comparable

###### Evidence

**Type:** string

**Min length:** `1`

### Status

#### Enum

- pass
- fail
- blocked
- not_comparable

### Claims

**Type:** array

#### Items

**Type:** object

**Additional properties:** `false`

##### Required

- statement
- evidence_class
- references

##### Properties

###### Statement

**Type:** string

**Min length:** `1`

###### Evidence class

###### Enum

- repository_source
- external_evidence
- inference
- design_proposal

###### References

**Type:** array

**Unique items:** `true`

###### Items

**Type:** string

**Min length:** `1`

### Limitations

**Type:** array

#### Items

**Type:** string

**Min length:** `1`

### Environment

**Type:** object

**Additional properties:** `false`

#### Required

- os
- architecture
- runtime

#### Properties

##### Os

**Type:** string

**Min length:** `1`

##### Architecture

**Type:** string

**Min length:** `1`

##### Runtime

**Type:** string

**Min length:** `1`

##### Dependency lock sha256

**$ref:** \#/$defs/sha256

### Semantics

**Type:** object

**Additional properties:** `false`

#### Properties

##### Currency

**Type:** string

**Min length:** `1`

##### Loss stage

###### Enum

- ground_up
- gross
- insured
- ceded
- recoverable
- net

##### Horizon

**Type:** string

**Min length:** `1`

##### Valuation basis

**Type:** string

**Min length:** `1`

##### Model view

**Type:** string

**Min length:** `1`

### Interoperability

**Type:** array

#### Items

**Type:** object

**Additional properties:** `false`

##### Required

- target
- version
- role
- status
- evidence

##### Properties

###### Target

**Type:** string

**Min length:** `1`

###### Version

**Type:** string

**Min length:** `1`

###### Role

###### Enum

- import
- export
- compare
- execute
- metadata

###### Status

###### Enum

- planned
- experimental
- tested
- unsupported
- not_comparable

###### Profile

**Type:** string

**Min length:** `1`

###### Comparison mode

###### Enum

- deterministic
- common_innovations
- distributional
- not_comparable

###### Evidence

**Type:** array

**Unique items:** `true`

###### Items

**Type:** string

**Min length:** `1`

##### All of

###### Item 1

###### If

###### Properties

###### Status

**Const:** tested

###### Required

- status

###### Then

###### Properties

###### Evidence

**Min items:** `1`

###### Version

###### Not

**Const:** latest


## All of

### Item 1

#### If

##### Properties

###### Status

**Const:** pass

##### Required

- status

#### Then

##### Properties

###### Validation

###### Items

###### Properties

###### Status

**Const:** pass

###### Required

- status

### Item 2

#### If

##### Properties

###### Status

**Const:** fail

##### Required

- status

#### Then

##### Properties

###### Validation

###### Contains

###### Properties

###### Status

**Const:** fail

###### Required

- status

### Item 3

#### If

##### Properties

###### Status

**Const:** blocked

##### Required

- status

#### Then

##### Properties

###### Validation

###### Contains

###### Properties

###### Status

**Const:** blocked

###### Required

- status

### Item 4

#### If

##### Properties

###### Status

**Const:** not_comparable

##### Required

- status

#### Then

##### Properties

###### Validation

###### Contains

###### Properties

###### Status

**Const:** not_comparable

###### Required

- status
