<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/source-landscape-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Source Landscape v1

> This file is a deterministic human-readable projection of `schemas/source-landscape-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/source-landscape-v1.schema.json`](source-landscape-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:source-landscape:1.0.0`  

Portable structural profile for the public non-admission source-discovery registry.

**Executable authority note:** scripts/source_landscape_contract.py is the authoritative executable policy validator. It additionally enforces strict JSON parsing, real calendar dates, globally unique candidate IDs and public-URL safety constraints that are not fully represented by this portable structural schema. Passing this schema never implies rights review, scientific approval, admission or permission for model use.

## Contract structure

Portable structural profile for the public non-admission source-discovery registry.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `purpose`, `review_date`, `entries`

### Properties

#### `entries` — **required**

**Constraints:** type=`array`; `minItems`=`1`

##### Array items

**Constraints:** `$ref`=`#/$defs/entry`

#### `purpose` — **required**

**Constraints:** type=`string`; `pattern`=`Non-admission`

#### `review_date` — **required**

**Constraints:** type=`string`; `format`=`date`; `pattern`=`^\d{4}-\d{2}-\d{2}$`

#### `schema_version` — **required**

**Constraints:** `const`=`1.0.0`

### $defs

#### `entry`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `candidate_id`, `name`, `provider`, `categories`, `spatial_scope`, `temporal_scope`, `resolution_or_granularity`, `potential_roles`, `authoritative_url`, `access_class_hint`, `candidate_status`, `rights_review_status`, `scientific_review_status`, `admission_status`, `note`

##### Properties

###### `access_class_hint` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `admission_status` — **required**

**Constraints:** `const`=`not_admitted`

###### `authoritative_url` — **required**

**Constraints:** type=`string`; `pattern`=`^https://\S+$`

###### `candidate_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-z0-9]+(?:[.-][a-z0-9]+)*$`

###### `candidate_status` — **required**

**Constraints:** `const`=`evidence_checked`

###### `categories` — **required**

**Constraints:** type=`array`; `minItems`=`1`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `name` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `note` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `potential_roles` — **required**

**Constraints:** type=`array`; `minItems`=`1`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`

###### `provider` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `resolution_or_granularity` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `rights_review_status` — **required**

**Constraints:** `const`=`not_reviewed`

###### `scientific_review_status` — **required**

**Constraints:** `const`=`not_reviewed`

###### `spatial_scope` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

###### `temporal_scope` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlankText`

#### `nonBlankText`

**Constraints:** type=`string`; `pattern`=`\S`
