<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/run-evidence-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Run Evidence Profile v1

> This file is a deterministic human-readable projection of `schemas/run-evidence-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/run-evidence-v1.schema.json`](run-evidence-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:run-evidence:1.0.0`  

Closed scientific execution receipt for deterministic or stochastic OpenCatastrophe work, including bounded interoperability claims.

**Authority note:** The canonical JSON Schema governs portable structure; repository Python validators may impose additional fail-closed semantic or security checks where documented.

## Contract structure

Closed scientific execution receipt for deterministic or stochastic OpenCatastrophe work, including bounded interoperability claims.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `profile_version`, `run_id`, `repository`, `execution`, `inputs`, `randomness`, `outputs`, `validation`, `status`, `claims`, `limitations`

### Properties

#### `claims` — **required**

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `statement`, `evidence_class`, `references`

###### Properties

###### `evidence_class` — **required**

**Constraints:** `enum`=`["repository_source","external_evidence","inference","design_proposal"]`

###### `references` — **required**

**Constraints:** type=`array`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `statement` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `environment`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `os`, `architecture`, `runtime`

##### Properties

###### `architecture` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `dependency_lock_sha256`

**Constraints:** `$ref`=`#/$defs/sha256`

###### `os` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `runtime` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `execution` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `commands`, `started_at`, `ended_at`, `exit_code`

##### Properties

###### `commands` — **required**

**Constraints:** type=`array`; `minItems`=`1`

###### Array items

**Constraints:** `$ref`=`#/$defs/command`

###### `ended_at` — **required**

**Constraints:** `$ref`=`#/$defs/timestamp`

###### `exit_code` — **required**

**Constraints:** type=`integer`

###### `started_at` — **required**

**Constraints:** `$ref`=`#/$defs/timestamp`

#### `inputs` — **required**

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `id`, `kind`, `identity`

###### Properties

###### `id` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `identity` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `kind` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `sha256`

**Constraints:** `$ref`=`#/$defs/sha256`

###### `version`

**Constraints:** type=`string`; `minLength`=`1`

###### not

**Constraints:** `const`=`latest`

#### `interoperability`

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `target`, `version`, `role`, `status`, `evidence`

###### Properties

###### `comparison_mode`

**Constraints:** `enum`=`["deterministic","common_innovations","distributional","not_comparable"]`

###### `evidence` — **required**

**Constraints:** type=`array`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `profile`

**Constraints:** type=`string`; `minLength`=`1`

###### `role` — **required**

**Constraints:** `enum`=`["import","export","compare","execute","metadata"]`

###### `status` — **required**

**Constraints:** `enum`=`["planned","experimental","tested","unsupported","not_comparable"]`

###### `target` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `version` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### allOf

###### Branch 1

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`tested`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

**Constraints:** `minItems`=`1`

###### `version`

###### not

**Constraints:** `const`=`latest`

#### `limitations` — **required**

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`string`; `minLength`=`1`

#### `outputs` — **required**

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `path`, `sha256`, `byte_size`, `media_type`

###### Properties

###### `byte_size` — **required**

**Constraints:** type=`integer`; `minimum`=`0`

###### `media_type` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `path` — **required**

**Constraints:** `$ref`=`#/$defs/relativePath`

###### `sha256` — **required**

**Constraints:** `$ref`=`#/$defs/sha256`

#### `profile_version` — **required**

**Constraints:** `const`=`1.0.0`

#### `randomness` — **required**

##### oneOf

###### Branch 1

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `mode`

###### Properties

###### `mode` — **required**

**Constraints:** `const`=`deterministic`

###### Branch 2

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `mode`, `algorithm`, `implementation`, `seed_material`, `stream_identity`, `draw_protocol`

###### Properties

###### `algorithm` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `draw_protocol` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `implementation` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `mode` — **required**

**Constraints:** `const`=`stochastic`

###### `seed_material` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `stream_identity` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `repository` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `name`, `commit`, `dirty`

##### Properties

###### `commit` — **required**

**Constraints:** `$ref`=`#/$defs/commit`

###### `dirty` — **required**

**Constraints:** type=`boolean`

###### `name` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`

###### `tree`

**Constraints:** `$ref`=`#/$defs/commit`

#### `run_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`

#### `semantics`

**Constraints:** type=`object`; `additionalProperties`=`false`

##### Properties

###### `currency`

**Constraints:** type=`string`; `minLength`=`1`

###### `horizon`

**Constraints:** type=`string`; `minLength`=`1`

###### `loss_stage`

**Constraints:** `enum`=`["ground_up","gross","insured","ceded","recoverable","net"]`

###### `model_view`

**Constraints:** type=`string`; `minLength`=`1`

###### `valuation_basis`

**Constraints:** type=`string`; `minLength`=`1`

#### `status` — **required**

**Constraints:** `enum`=`["pass","fail","blocked","not_comparable"]`

#### `validation` — **required**

**Constraints:** type=`array`; `minItems`=`1`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `check`, `status`

###### Properties

###### `check` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `evidence`

**Constraints:** type=`string`; `minLength`=`1`

###### `status` — **required**

**Constraints:** `enum`=`["pass","fail","blocked","not_comparable"]`

### $defs

#### `command`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `argv`, `purpose`

##### Properties

###### `argv` — **required**

**Constraints:** type=`array`; `minItems`=`1`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `cwd`

**Constraints:** type=`string`; `pattern`=`^(?!/)(?![A-Za-z]:[\\/])(?!.*\\)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*//)[^\x00]+$`; `minLength`=`1`

###### `purpose` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `commit`

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

#### `relativePath`

**Constraints:** type=`string`; `pattern`=`^(?!/)(?![A-Za-z]:[\\/])(?!.*\\)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*//)[^\x00]+$`; `minLength`=`1`

#### `sha256`

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

#### `timestamp`

**Constraints:** type=`string`; `format`=`date-time`

### allOf

#### Branch 1

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`pass`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `validation`

###### Array items

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`pass`

#### Branch 2

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`fail`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `validation`

**Other schema keywords:**

- `contains`: `{"properties":{"status":{"const":"fail"}},"required":["status"]}`

#### Branch 3

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`blocked`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `validation`

**Other schema keywords:**

- `contains`: `{"properties":{"status":{"const":"blocked"}},"required":["status"]}`

#### Branch 4

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`not_comparable`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `validation`

**Other schema keywords:**

- `contains`: `{"properties":{"status":{"const":"not_comparable"}},"required":["status"]}`
