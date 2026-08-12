<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/agent-task-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Agent Task Profile v1

> This file is a deterministic human-readable projection of `schemas/agent-task-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/agent-task-v1.schema.json`](agent-task-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:agent-task:1.0.0`  

Closed, provider-neutral execution contract for a bounded human or AI-agent task.

**Authority note:** The canonical JSON Schema governs portable structure; repository Python validators may impose additional fail-closed semantic or security checks where documented.

## Contract structure

Closed, provider-neutral execution contract for a bounded human or AI-agent task.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `profile_version`, `task_id`, `repository`, `state`, `agent_ready`, `workstream`, `reviewed_against`, `shared_surfaces`, `dependencies`, `next_action`, `hard_stop`, `acceptance`

### Properties

#### `acceptance` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `criteria`, `commands`, `evidence`

##### Properties

###### `commands` — **required**

**Constraints:** type=`array`; `minItems`=`1`

###### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `argv`, `purpose`

###### Properties

###### `argv` — **required**

**Constraints:** type=`array`; `minItems`=`1`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `cwd`

**Constraints:** type=`string`; `pattern`=`^(?!/)(?![A-Za-z]:[\\/])(?!.*\\)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*//)[^\x00]+$`; `minLength`=`1`

###### `purpose` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `criteria` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `evidence` — **required**

**Constraints:** type=`array`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `pattern`=`^(?!/)(?![A-Za-z]:[\\/])(?!.*\\)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*//)[^\x00]+$`; `minLength`=`1`

#### `agent_ready` — **required**

**Constraints:** type=`boolean`

#### `data_boundary`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `bytes_policy`

##### Properties

###### `bytes_policy` — **required**

**Constraints:** `enum`=`["none","synthetic_only","metadata_only","admitted_public_only","restricted_external_only"]`

###### `source_identity`

**Constraints:** type=`string`; `minLength`=`1`

#### `dependencies` — **required**

**Constraints:** type=`array`; `uniqueItems`=`true`

##### Array items

**Constraints:** type=`string`; `minLength`=`1`

#### `external_sources`

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `uri`, `role`, `reviewed_at`

###### Properties

###### `reviewed_at` — **required**

**Constraints:** type=`string`; `format`=`date-time`

###### `role` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `uri` — **required**

**Constraints:** type=`string`; `pattern`=`^(https://|urn:).+`

###### `version`

**Constraints:** type=`string`; `minLength`=`1`

###### not

**Constraints:** `const`=`latest`

#### `hard_stop` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `next_action` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `profile_version` — **required**

**Constraints:** `const`=`1.0.0`

#### `repository` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`

#### `reviewed_against` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `ref`, `commit`, `checked_at`

##### Properties

###### `checked_at` — **required**

**Constraints:** type=`string`; `format`=`date-time`

###### `commit` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

###### `ref` — **required**

**Constraints:** `const`=`refs/heads/main`

#### `shared_surfaces` — **required**

**Constraints:** type=`array`; `uniqueItems`=`true`

##### Array items

**Constraints:** type=`string`; `pattern`=`^(?!/)(?![A-Za-z]:[\\/])(?!.*\\)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*//)[^\x00]+$`; `minLength`=`1`

#### `state` — **required**

**Constraints:** `enum`=`["ready","blocked","active","validation_only","research_only","complete"]`

#### `task_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`

#### `workstream` — **required**

**Constraints:** type=`string`; `minLength`=`1`

### allOf

#### Branch 1

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `state`

###### Properties

###### `state` — **required**

**Constraints:** `enum`=`["blocked","complete"]`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `agent_ready`

**Constraints:** `const`=`false`
