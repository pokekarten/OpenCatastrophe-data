<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/agent-action-result-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `agent-action-result-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:agent-action-result:1.0.0

**Title:** OpenCatastrophe Agent Action Result v1

**Description:** Portable closed result receipt for the owner-authorized trusted-main Agent Action Dispatch control plane. scripts/validate_agent_action_result.py is authoritative for exact Python scalar types, UTC ordering and cross-field checks.

**$comment:** This initial result profile records request-validation/duplicate evidence only. It does not claim that sample_audit acquired external bytes or completed a scientific sample operation.

**Type:** object

**Additional properties:** `false`

## Required

- schema_version
- semantic_request_id
- repository
- action
- source_issue
- source_comment_id
- target_sha
- dataset_id
- execution_sha
- run_id
- run_attempt
- started_at
- finished_at
- phase
- status
- external_bytes_persisted
- evidence
- duplicate_result_comment_id
- failure_class

## Properties

### Schema version

**Const:** oc-action-result-v1

### Semantic request id

**Type:** string

**Pattern:** ^\[a-f0-9\]\{64\}$

### Repository

**Type:** string

**Pattern:** ^\[A-Za-z0-9-\]+/\[A-Za-z0-9._-\]+$

### Action

#### Enum

- sample_audit

### Source issue

**Type:** integer

**Minimum:** `1`

### Source comment id

**Type:** integer

**Minimum:** `1`

### Target sha

**Type:** string

**Pattern:** ^\[a-f0-9\]\{40\}$

### Dataset id

**Type:** string

**Min length:** `1`

**Max length:** `160`

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._:-\]\*$

### Execution sha

**Type:** string

**Pattern:** ^\[a-f0-9\]\{40\}$

### Run id

**Type:** integer

**Minimum:** `1`

### Run attempt

**Type:** integer

**Minimum:** `1`

### Started at

**Type:** string

**Pattern:** ^\\d\{4\}-\\d\{2\}-\\d\{2\}T\\d\{2\}:\\d\{2\}:\\d\{2\}Z$

### Finished at

**Type:** string

**Pattern:** ^\\d\{4\}-\\d\{2\}-\\d\{2\}T\\d\{2\}:\\d\{2\}:\\d\{2\}Z$

### Phase

**Const:** request_validation

### Status

#### Enum

- pass
- duplicate
- blocked

### External bytes persisted

**Const:** `false`

### Evidence

**Type:** object

**Additional properties:** `false`

#### Required

- request_validated
- ledger_scan_complete
- prior_result_reused

#### Properties

##### Request validated

**Const:** `true`

##### Ledger scan complete

**Type:** boolean

##### Prior result reused

**Type:** boolean

### Duplicate result comment id

#### Type

- integer
- null

**Minimum:** `1`

### Failure class

#### Type

- string
- null

#### Enum

- `null`
- duplicate_request
- ledger_incomplete

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

###### Evidence

###### Properties

###### Ledger scan complete

**Const:** `true`

###### Prior result reused

**Const:** `false`

###### Duplicate result comment id

**Type:** null

###### Failure class

**Type:** null

### Item 2

#### If

##### Properties

###### Status

**Const:** duplicate

##### Required

- status

#### Then

##### Properties

###### Evidence

###### Properties

###### Ledger scan complete

**Const:** `true`

###### Prior result reused

**Const:** `true`

###### Duplicate result comment id

**Type:** integer

**Minimum:** `1`

###### Failure class

**Const:** duplicate_request

### Item 3

#### If

##### Properties

###### Status

**Const:** blocked

##### Required

- status

#### Then

##### Properties

###### Evidence

###### Properties

###### Ledger scan complete

**Const:** `false`

###### Prior result reused

**Const:** `false`

###### Duplicate result comment id

**Type:** null

###### Failure class

**Const:** ledger_incomplete
