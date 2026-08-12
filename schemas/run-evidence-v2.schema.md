<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/run-evidence-v2.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Run Evidence Profile v2

> This file is a deterministic human-readable projection of `schemas/run-evidence-v2.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/run-evidence-v2.schema.json`](run-evidence-v2.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:run-evidence:2.0.0`  

Closed scientific execution receipt with explicit model-data roles, manifest-artifact bindings and resolvable claim references.

**Executable authority note:** scripts/validate_agent_artifact.py is the authoritative executable validator. For data inputs it validates the referenced manifest and requires identity and SHA-256 to match the selected raw/derived artifact. It also resolves typed references and enforces unique exact input identities/content. Schema validity alone does not establish rights, scientific fitness or absence of data leakage.

## Contract structure

Closed scientific execution receipt with explicit model-data roles, manifest-artifact bindings and resolvable claim references.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `profile_version`, `run_id`, `repository`, `execution`, `inputs`, `randomness`, `outputs`, `validation`, `status`, `claims`, `limitations`

### Properties

#### `claims` — **required**

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `statement`, `evidence_class`, `references`, `scope`, `limitations`

###### Properties

###### `evidence_class` — **required**

**Constraints:** `enum`=`["repository_source","external_evidence","inference","design_proposal"]`

###### `limitations` — **required**

**Constraints:** type=`array`; `uniqueItems`=`true`

###### Array items

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `references` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

###### Array items

**Constraints:** `$ref`=`#/$defs/claimReference`

###### `scope` — **required**

**Constraints:** `$ref`=`#/$defs/claimScope`

###### `statement` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `environment`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `os`, `architecture`, `runtime`

##### Properties

###### `architecture` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `dependency_lock_sha256`

**Constraints:** `$ref`=`#/$defs/sha256`

###### `os` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `runtime` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

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

**Required here:** `id`, `kind`, `identity`, `scientific_role`

###### Properties

###### `artifact`

**Constraints:** `enum`=`["raw","derived"]`

###### `id` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `identity` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `kind` — **required**

**Constraints:** `enum`=`["data","model","config","code","fixture","literature","other"]`

###### `manifest`

**Constraints:** type=`string`; `pattern`=`^manifests/[A-Za-z0-9._-]+\.json$`

###### `scientific_role` — **required**

**Constraints:** `enum`=`["training","calibration","validation","holdout","benchmark","context","configuration","software","model","test_fixture"]`

###### `sha256`

**Constraints:** `$ref`=`#/$defs/sha256`

###### `version`

**Constraints:** type=`string`; `minLength`=`1`

###### not

**Constraints:** `const`=`latest`

###### allOf

###### Branch 1

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `kind`

###### Properties

###### `kind` — **required**

**Constraints:** `const`=`data`

###### then

**Constraints:** type=`object (implicit)`

**Required here:** `manifest`, `artifact`, `sha256`

###### Properties

###### `scientific_role`

**Constraints:** `enum`=`["training","calibration","validation","holdout","benchmark","context"]`

###### Branch 2

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `kind`

###### Properties

###### `kind` — **required**

**Constraints:** `const`=`fixture`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `scientific_role`

**Constraints:** `enum`=`["validation","benchmark","context","test_fixture"]`

###### Branch 3

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `kind`

###### Properties

###### `kind` — **required**

**Constraints:** `const`=`model`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `scientific_role`

**Constraints:** `const`=`model`

###### Branch 4

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `kind`

###### Properties

###### `kind` — **required**

**Constraints:** `const`=`config`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `scientific_role`

**Constraints:** `const`=`configuration`

###### Branch 5

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `kind`

###### Properties

###### `kind` — **required**

**Constraints:** `const`=`code`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `scientific_role`

**Constraints:** `const`=`software`

###### Branch 6

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `kind`

###### Properties

###### `kind` — **required**

**Constraints:** `enum`=`["literature","other"]`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `scientific_role`

**Constraints:** `const`=`context`

###### Branch 7

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `kind`

###### Properties

###### `kind` — **required**

###### not

**Constraints:** `const`=`data`

###### then

###### not

###### anyOf

###### Branch 1

**Required here:** `manifest`

###### Branch 2

**Required here:** `artifact`

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

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `profile`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `role` — **required**

**Constraints:** `enum`=`["import","export","compare","execute","metadata"]`

###### `status` — **required**

**Constraints:** `enum`=`["planned","experimental","tested","unsupported","not_comparable"]`

###### `target` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

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

**Constraints:** type=`array`; `uniqueItems`=`true`

##### Array items

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `outputs` — **required**

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `path`, `sha256`, `byte_size`, `media_type`

###### Properties

###### `byte_size` — **required**

**Constraints:** type=`integer`; `minimum`=`0`

###### `media_type` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `path` — **required**

**Constraints:** `$ref`=`#/$defs/relativePath`

###### `sha256` — **required**

**Constraints:** `$ref`=`#/$defs/sha256`

#### `profile_version` — **required**

**Constraints:** `const`=`2.0.0`

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

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `draw_protocol` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `implementation` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `mode` — **required**

**Constraints:** `const`=`stochastic`

###### `seed_material` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `stream_identity` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

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

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `horizon`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `loss_stage`

**Constraints:** `enum`=`["ground_up","gross","insured","ceded","recoverable","net"]`

###### `model_view`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `valuation_basis`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `status` — **required**

**Constraints:** `enum`=`["pass","fail","blocked","not_comparable"]`

#### `validation` — **required**

**Constraints:** type=`array`; `minItems`=`1`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `check`, `status`

###### Properties

###### `check` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `evidence`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `status` — **required**

**Constraints:** `enum`=`["pass","fail","blocked","not_comparable"]`

### $defs

#### `claimReference`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `kind`, `ref`

##### Properties

###### `kind` — **required**

**Constraints:** `enum`=`["input","output","validation","manifest","source_review","repository_path","external_uri"]`

###### `ref` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `claimScope`

**Constraints:** type=`object`; `minProperties`=`1`; `additionalProperties`=`false`

##### Properties

###### `geography`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `model_context`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `peril`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `temporal`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `variable`

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `command`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `argv`, `purpose`

##### Properties

###### `argv` — **required**

**Constraints:** type=`array`; `minItems`=`1`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `cwd`

**Constraints:** `$ref`=`#/$defs/relativePath`

###### `purpose` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `commit`

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

#### `nonBlankText`

**Constraints:** type=`string`; `pattern`=`\S`

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
