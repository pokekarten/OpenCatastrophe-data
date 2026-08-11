<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/run-evidence-v2.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `run-evidence-v2.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:run-evidence:2.0.0

**Title:** OpenCatastrophe Run Evidence Profile v2

**Description:** Closed scientific execution receipt with explicit model-data roles, manifest-artifact bindings and resolvable claim references.

**$comment:** scripts/validate_agent_artifact.py is the authoritative executable validator. For data inputs it validates the referenced manifest and requires identity and SHA-256 to match the selected raw/derived artifact. It also resolves typed references and enforces unique exact input identities/content. Schema validity alone does not establish rights, scientific fitness or absence of data leakage.

**Type:** object

**Additionalproperties:** `false`

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

### Nonblanktext

**Type:** string

**Pattern:** \\S

### Command

**Type:** object

**Additionalproperties:** `false`

#### Required

- argv
- purpose

#### Properties

##### Argv

**Type:** array

**Minitems:** `1`

###### Items

**Type:** string

**Minlength:** `1`

##### Purpose

**$ref:** \#/$defs/nonBlankText

##### Cwd

**$ref:** \#/$defs/relativePath

### Sha256

**Type:** string

**Pattern:** ^\[a-f0-9\]\{64\}$

### Commit

**Type:** string

**Pattern:** ^\[a-f0-9\]\{40\}$

### Relativepath

**Type:** string

**Minlength:** `1`

**Pattern:** ^(?\!/)(?\!\[A-Za-z\]:\[\\\\/\])(?\!.\*\\\\)(?\!.\*(?:^\|/)\\.\{1,2\}(?:/\|$))(?\!.\*//)\[^\\x00\]+$

### Timestamp

**Type:** string

**Format:** date-time

### Claimreference

**Type:** object

**Additionalproperties:** `false`

#### Required

- kind
- ref

#### Properties

##### Kind

###### Enum

- input
- output
- validation
- manifest
- source_review
- repository_path
- external_uri

##### Ref

**$ref:** \#/$defs/nonBlankText

### Claimscope

**Type:** object

**Additionalproperties:** `false`

**Minproperties:** `1`

#### Properties

##### Peril

**$ref:** \#/$defs/nonBlankText

##### Geography

**$ref:** \#/$defs/nonBlankText

##### Temporal

**$ref:** \#/$defs/nonBlankText

##### Variable

**$ref:** \#/$defs/nonBlankText

##### Model context

**$ref:** \#/$defs/nonBlankText

## Properties

### Profile version

**Const:** 2.0.0

### Run id

**Type:** string

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._:-\]\{0,127\}$

### Repository

**Type:** object

**Additionalproperties:** `false`

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

**Additionalproperties:** `false`

#### Required

- commands
- started_at
- ended_at
- exit_code

#### Properties

##### Commands

**Type:** array

**Minitems:** `1`

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

**Additionalproperties:** `false`

##### Required

- id
- kind
- identity
- scientific_role

##### Properties

###### Id

**$ref:** \#/$defs/nonBlankText

###### Kind

###### Enum

- data
- model
- config
- code
- fixture
- literature
- other

###### Identity

**$ref:** \#/$defs/nonBlankText

###### Scientific role

###### Enum

- training
- calibration
- validation
- holdout
- benchmark
- context
- configuration
- software
- model
- test_fixture

###### Manifest

**Type:** string

**Pattern:** ^manifests/\[A-Za-z0-9._-\]+\\.json$

###### Artifact

###### Enum

- raw
- derived

###### Sha256

**$ref:** \#/$defs/sha256

###### Version

**Type:** string

**Minlength:** `1`

###### Not

**Const:** latest

##### Allof

###### Item 1

###### If

###### Properties

###### Kind

**Const:** data

###### Required

- kind

###### Then

###### Required

- manifest
- artifact
- sha256

###### Properties

###### Scientific role

###### Enum

- training
- calibration
- validation
- holdout
- benchmark
- context

###### Item 2

###### If

###### Properties

###### Kind

**Const:** fixture

###### Required

- kind

###### Then

###### Properties

###### Scientific role

###### Enum

- validation
- benchmark
- context
- test_fixture

###### Item 3

###### If

###### Properties

###### Kind

**Const:** model

###### Required

- kind

###### Then

###### Properties

###### Scientific role

**Const:** model

###### Item 4

###### If

###### Properties

###### Kind

**Const:** config

###### Required

- kind

###### Then

###### Properties

###### Scientific role

**Const:** configuration

###### Item 5

###### If

###### Properties

###### Kind

**Const:** code

###### Required

- kind

###### Then

###### Properties

###### Scientific role

**Const:** software

###### Item 6

###### If

###### Properties

###### Kind

###### Enum

- literature
- other

###### Required

- kind

###### Then

###### Properties

###### Scientific role

**Const:** context

###### Item 7

###### If

###### Properties

###### Kind

###### Not

**Const:** data

###### Required

- kind

###### Then

###### Not

###### Anyof

###### Item 1

###### Required

- manifest

###### Item 2

###### Required

- artifact



### Randomness

#### Oneof

##### Item 1

**Type:** object

**Additionalproperties:** `false`

###### Required

- mode

###### Properties

###### Mode

**Const:** deterministic

##### Item 2

**Type:** object

**Additionalproperties:** `false`

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

**$ref:** \#/$defs/nonBlankText

###### Implementation

**$ref:** \#/$defs/nonBlankText

###### Seed material

**$ref:** \#/$defs/nonBlankText

###### Stream identity

**$ref:** \#/$defs/nonBlankText

###### Draw protocol

**$ref:** \#/$defs/nonBlankText


### Outputs

**Type:** array

#### Items

**Type:** object

**Additionalproperties:** `false`

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

**$ref:** \#/$defs/nonBlankText

### Validation

**Type:** array

**Minitems:** `1`

#### Items

**Type:** object

**Additionalproperties:** `false`

##### Required

- check
- status

##### Properties

###### Check

**$ref:** \#/$defs/nonBlankText

###### Status

###### Enum

- pass
- fail
- blocked
- not_comparable

###### Evidence

**$ref:** \#/$defs/nonBlankText

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

**Additionalproperties:** `false`

##### Required

- statement
- evidence_class
- references
- scope
- limitations

##### Properties

###### Statement

**$ref:** \#/$defs/nonBlankText

###### Evidence class

###### Enum

- repository_source
- external_evidence
- inference
- design_proposal

###### References

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

###### Items

**$ref:** \#/$defs/claimReference

###### Scope

**$ref:** \#/$defs/claimScope

###### Limitations

**Type:** array

**Uniqueitems:** `true`

###### Items

**$ref:** \#/$defs/nonBlankText

### Limitations

**Type:** array

**Uniqueitems:** `true`

#### Items

**$ref:** \#/$defs/nonBlankText

### Environment

**Type:** object

**Additionalproperties:** `false`

#### Required

- os
- architecture
- runtime

#### Properties

##### Os

**$ref:** \#/$defs/nonBlankText

##### Architecture

**$ref:** \#/$defs/nonBlankText

##### Runtime

**$ref:** \#/$defs/nonBlankText

##### Dependency lock sha256

**$ref:** \#/$defs/sha256

### Semantics

**Type:** object

**Additionalproperties:** `false`

#### Properties

##### Currency

**$ref:** \#/$defs/nonBlankText

##### Loss stage

###### Enum

- ground_up
- gross
- insured
- ceded
- recoverable
- net

##### Horizon

**$ref:** \#/$defs/nonBlankText

##### Valuation basis

**$ref:** \#/$defs/nonBlankText

##### Model view

**$ref:** \#/$defs/nonBlankText

### Interoperability

**Type:** array

#### Items

**Type:** object

**Additionalproperties:** `false`

##### Required

- target
- version
- role
- status
- evidence

##### Properties

###### Target

**$ref:** \#/$defs/nonBlankText

###### Version

**Type:** string

**Minlength:** `1`

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

**$ref:** \#/$defs/nonBlankText

###### Comparison mode

###### Enum

- deterministic
- common_innovations
- distributional
- not_comparable

###### Evidence

**Type:** array

**Uniqueitems:** `true`

###### Items

**$ref:** \#/$defs/nonBlankText

##### Allof

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

**Minitems:** `1`

###### Version

###### Not

**Const:** latest


## Allof

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
