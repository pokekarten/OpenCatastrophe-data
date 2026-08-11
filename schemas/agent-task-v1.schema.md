<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/agent-task-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `agent-task-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:agent-task:1.0.0

**Title:** OpenCatastrophe Agent Task Profile v1

**Description:** Closed, provider-neutral execution contract for a bounded human or AI-agent task.

**Type:** object

**Additionalproperties:** `false`

## Required

- profile_version
- task_id
- repository
- state
- agent_ready
- workstream
- reviewed_against
- shared_surfaces
- dependencies
- next_action
- hard_stop
- acceptance

## Properties

### Profile version

**Const:** 1.0.0

### Task id

**Type:** string

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._:-\]\{0,127\}$

### Repository

**Type:** string

**Pattern:** ^\[A-Za-z0-9_.-\]+/\[A-Za-z0-9_.-\]+$

### State

#### Enum

- ready
- blocked
- active
- validation_only
- research_only
- complete

### Agent ready

**Type:** boolean

### Workstream

**Type:** string

**Minlength:** `1`

### Reviewed against

**Type:** object

**Additionalproperties:** `false`

#### Required

- ref
- commit
- checked_at

#### Properties

##### Ref

**Const:** refs/heads/main

##### Commit

**Type:** string

**Pattern:** ^\[a-f0-9\]\{40\}$

##### Checked at

**Type:** string

**Format:** date-time

### Shared surfaces

**Type:** array

**Uniqueitems:** `true`

#### Items

**Type:** string

**Minlength:** `1`

**Pattern:** ^(?\!/)(?\!\[A-Za-z\]:\[\\\\/\])(?\!.\*\\\\)(?\!.\*(?:^\|/)\\.\{1,2\}(?:/\|$))(?\!.\*//)\[^\\x00\]+$

### Dependencies

**Type:** array

**Uniqueitems:** `true`

#### Items

**Type:** string

**Minlength:** `1`

### Next action

**Type:** string

**Minlength:** `1`

### Hard stop

**Type:** string

**Minlength:** `1`

### Acceptance

**Type:** object

**Additionalproperties:** `false`

#### Required

- criteria
- commands
- evidence

#### Properties

##### Criteria

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

###### Items

**Type:** string

**Minlength:** `1`

##### Commands

**Type:** array

**Minitems:** `1`

###### Items

**Type:** object

**Additionalproperties:** `false`

###### Required

- argv
- purpose

###### Properties

###### Argv

**Type:** array

**Minitems:** `1`

###### Items

**Type:** string

**Minlength:** `1`

###### Purpose

**Type:** string

**Minlength:** `1`

###### Cwd

**Type:** string

**Minlength:** `1`

**Pattern:** ^(?\!/)(?\!\[A-Za-z\]:\[\\\\/\])(?\!.\*\\\\)(?\!.\*(?:^\|/)\\.\{1,2\}(?:/\|$))(?\!.\*//)\[^\\x00\]+$

##### Evidence

**Type:** array

**Uniqueitems:** `true`

###### Items

**Type:** string

**Minlength:** `1`

**Pattern:** ^(?\!/)(?\!\[A-Za-z\]:\[\\\\/\])(?\!.\*\\\\)(?\!.\*(?:^\|/)\\.\{1,2\}(?:/\|$))(?\!.\*//)\[^\\x00\]+$

### External sources

**Type:** array

#### Items

**Type:** object

**Additionalproperties:** `false`

##### Required

- uri
- role
- reviewed_at

##### Properties

###### Uri

**Type:** string

**Pattern:** ^(https://\|urn:).+

###### Role

**Type:** string

**Minlength:** `1`

###### Reviewed at

**Type:** string

**Format:** date-time

###### Version

**Type:** string

**Minlength:** `1`

###### Not

**Const:** latest

### Data boundary

**Type:** object

**Additionalproperties:** `false`

#### Required

- bytes_policy

#### Properties

##### Bytes policy

###### Enum

- none
- synthetic_only
- metadata_only
- admitted_public_only
- restricted_external_only

##### Source identity

**Type:** string

**Minlength:** `1`

## Allof

### Item 1

#### If

##### Properties

###### State

###### Enum

- blocked
- complete

##### Required

- state

#### Then

##### Properties

###### Agent ready

**Const:** `false`
