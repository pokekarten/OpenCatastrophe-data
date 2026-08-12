<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/model-input-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Model Input Contract v1

> This file is a deterministic human-readable projection of `schemas/model-input-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/model-input-v1.schema.json`](model-input-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:model-input:1.0.0`  

Closed model-consumer binding for one exact admitted dataset artifact plus explicit model-facing scientific semantics. Executable validation against the referenced manifest is authoritative for cross-record identity parity.

**Executable authority note:** scripts/validate_model_input.py resolves the referenced manifest, validates it with the repository manifest validator, and requires dataset_id, artifact identity, SHA-256 and modelling_layer parity. Schema validity alone does not establish data rights, scientific fitness, calibration quality or production suitability.

## Contract structure

Closed model-consumer binding for one exact admitted dataset artifact plus explicit model-facing scientific semantics. Executable validation against the referenced manifest is authoritative for cross-record identity parity.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `manifest`, `dataset_id`, `artifact`, `storage_reference`, `sha256`, `modelling_layer`, `scientific_role`, `peril`, `measure`, `spatial`, `temporal`, `quality`

### Properties

#### `artifact` — **required**

**Constraints:** `enum`=`["raw","derived"]`

#### `dataset_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._-]*$`

#### `manifest` — **required**

**Constraints:** type=`string`; `pattern`=`^manifests/[A-Za-z0-9][A-Za-z0-9._-]*\.json$`

#### `measure` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `quantity`, `unit`, `aggregation`

##### Properties

###### `aggregation` — **required**

**Constraints:** `enum`=`["instantaneous","mean","maximum","minimum","accumulation","count","probability","categorical","other"]`

###### `quantity` — **required**

**Constraints:** `$ref`=`#/$defs/identifier`

###### `unit` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `modelling_layer` — **required**

**Constraints:** `enum`=`["event_catalogue","hazard","exposure","vulnerability","observed_loss","engine","standard","other"]`

#### `peril` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `id`, `subperil`

##### Properties

###### `id` — **required**

**Constraints:** `$ref`=`#/$defs/identifier`

###### `subperil` — **required**

###### oneOf

###### Branch 1

**Constraints:** `$ref`=`#/$defs/identifier`

###### Branch 2

**Constraints:** type=`null`

#### `quality` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `missing_value_policy`, `quality_flag_policy`

##### Properties

###### `missing_value_policy` — **required**

**Constraints:** `enum`=`["forbidden","explicit","source_defined"]`

###### `quality_flag_policy` — **required**

**Constraints:** `enum`=`["none","preserved","filtered","source_defined"]`

#### `schema_version` — **required**

**Constraints:** `const`=`1.0.0`

#### `scientific_role` — **required**

**Constraints:** `enum`=`["training","calibration","validation","holdout","benchmark","context"]`

#### `sha256` — **required**

**Constraints:** `$ref`=`#/$defs/sha256`

#### `spatial` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `crs`, `support`, `resolution`

##### Properties

###### `crs` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `resolution` — **required**

###### oneOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `value`, `unit`

###### Properties

###### `unit` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `value` — **required**

**Constraints:** `$ref`=`#/$defs/positiveNumber`

###### `support` — **required**

**Constraints:** `enum`=`["point","line","polygon","grid_cell","raster_cell","administrative_area","asset","event","other"]`

#### `storage_reference` — **required**

**Constraints:** type=`string`; `pattern`=`^external://(?!.*//)(?!.*(?:/\.\.?)(?:/|$))(?!.*\/$)[A-Za-z0-9][A-Za-z0-9._/-]*$`

#### `temporal` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `support`, `start`, `end`, `step_seconds`, `aggregation_window_seconds`

##### Properties

###### `aggregation_window_seconds` — **required**

**Constraints:** `$ref`=`#/$defs/positiveIntegerOrNull`

###### `end` — **required**

**Constraints:** type=`string | null`; `format`=`date-time`

###### `start` — **required**

**Constraints:** type=`string | null`; `format`=`date-time`

###### `step_seconds` — **required**

**Constraints:** `$ref`=`#/$defs/positiveIntegerOrNull`

###### `support` — **required**

**Constraints:** `enum`=`["static","instant_series","interval_series","event_series","climatology"]`

##### allOf

###### Branch 1

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `support`

###### Properties

###### `support` — **required**

**Constraints:** `const`=`static`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `aggregation_window_seconds`

**Constraints:** type=`null`

###### `end`

**Constraints:** type=`null`

###### `start`

**Constraints:** type=`null`

###### `step_seconds`

**Constraints:** type=`null`

###### else

**Constraints:** type=`object (implicit)`

###### Properties

###### `end`

**Constraints:** type=`string`; `format`=`date-time`

###### `start`

**Constraints:** type=`string`; `format`=`date-time`

### $defs

#### `identifier`

**Constraints:** type=`string`; `pattern`=`^[a-z0-9][a-z0-9._-]*$`

#### `nonBlankText`

**Constraints:** type=`string`; `pattern`=`\S`

#### `positiveIntegerOrNull`

##### oneOf

###### Branch 1

**Constraints:** type=`integer`; `minimum`=`1`

###### Branch 2

**Constraints:** type=`null`

#### `positiveNumber`

**Constraints:** type=`number`; `exclusiveMinimum`=`0`

#### `sha256`

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`
