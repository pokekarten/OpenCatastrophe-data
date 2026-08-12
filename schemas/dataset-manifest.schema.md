<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/dataset-manifest.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Dataset Admission Manifest

> This file is a deterministic human-readable projection of `schemas/dataset-manifest.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/dataset-manifest.schema.json`](dataset-manifest.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:dataset-manifest:1.0.0`  

**Authority note:** The canonical JSON Schema governs portable structure; repository Python validators may impose additional fail-closed semantic or security checks where documented.

## Contract structure

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `dataset_id`, `provider`, `product_name`, `canonical_source`, `retrieved_at`, `access_class`, `modelling_layer`, `intended_use`, `licensing`, `redistribution`, `privacy`, `review`

### Properties

#### `access_class` — **required**

**Constraints:** type=`string`; `enum`=`["open","registration_required","authenticated","restricted","unknown"]`

#### `canonical_source` — **required**

**Constraints:** type=`string`; `format`=`uri`; `pattern`=`^https://`

#### `dataset_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._-]*$`; `minLength`=`1`

#### `derived_artifact`

##### anyOf

###### Branch 1

**Constraints:** `$ref`=`#/$defs/artifact`

###### Branch 2

**Constraints:** type=`null`

#### `intended_use` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `licensing` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `status`, `terms_reference`, `terms_reviewed_at`, `commercial_use_status`

##### Properties

###### `attribution_requirements`

**Constraints:** type=`string | null`

###### `commercial_use_status` — **required**

**Constraints:** type=`string`; `enum`=`["allowed","restricted","prohibited","unknown"]`

###### `licence_name`

**Constraints:** type=`string | null`

###### `notes`

**Constraints:** type=`string | null`

###### `share_alike_or_derivative_requirements`

**Constraints:** type=`string | null`

###### `spdx_expression`

**Constraints:** type=`string | null`

###### `status` — **required**

**Constraints:** type=`string`; `enum`=`["verified","unverified","conflicting","unknown"]`

###### `terms_content_sha256`

**Constraints:** type=`string | null`; `pattern`=`^[a-f0-9]{64}$`

###### `terms_reference` — **required**

**Constraints:** type=`string`; `format`=`uri`; `pattern`=`^https://`

###### `terms_reviewed_at` — **required**

**Constraints:** type=`string`; `format`=`date-time`

###### `terms_version_or_date`

**Constraints:** type=`string | null`

#### `modelling_layer` — **required**

**Constraints:** type=`string`; `enum`=`["event_catalogue","hazard","exposure","vulnerability","observed_loss","engine","standard","other"]`

#### `privacy` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `personal_data_status`, `confidential_or_proprietary_status`

##### Properties

###### `confidential_or_proprietary_status` — **required**

**Constraints:** type=`string`; `enum`=`["none","contains","unknown"]`

###### `notes`

**Constraints:** type=`string | null`

###### `personal_data_status` — **required**

**Constraints:** type=`string`; `enum`=`["none","contains","unknown"]`

#### `product_name` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `provider` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `raw_artifact`

##### anyOf

###### Branch 1

**Constraints:** `$ref`=`#/$defs/artifact`

###### Branch 2

**Constraints:** type=`null`

#### `redistribution` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `status`, `scope`

##### Properties

###### `conditions`

**Constraints:** type=`string | null`

###### `scope` — **required**

**Constraints:** type=`string`; `enum`=`["raw","derived_only","metadata_only","none"]`

###### `status` — **required**

**Constraints:** type=`string`; `enum`=`["allowed","restricted","prohibited","unknown"]`

#### `retrieval_query_or_filters`

**Constraints:** type=`string | null`

#### `retrieved_at` — **required**

**Constraints:** type=`string`; `format`=`date-time`

#### `review` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `status`, `reviewed_at`, `reviewer`

##### Properties

###### `notes`

**Constraints:** type=`string | null`

###### `reviewed_at` — **required**

**Constraints:** type=`string | null`; `format`=`date-time`

###### `reviewer` — **required**

**Constraints:** type=`string | null`

###### `status` — **required**

**Constraints:** type=`string`; `enum`=`["pending","approved_metadata_only","approved_derived","approved_raw","rejected"]`

#### `schema_version` — **required**

**Constraints:** type=`string`; `const`=`1.0.0`

#### `spatial`

**Constraints:** type=`object | null`; `additionalProperties`=`false`

##### Properties

###### `crs`

**Constraints:** type=`string | null`

###### `extent`

**Constraints:** type=`string | null`

#### `temporal`

**Constraints:** type=`object | null`; `additionalProperties`=`false`

##### Properties

###### `extent`

**Constraints:** type=`string | null`

#### `transformation`

**Constraints:** type=`object | null`; `additionalProperties`=`false`

**Required here:** `code_reference`, `config_identity`

##### Properties

###### `code_reference` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `config_identity` — **required**

**Constraints:** type=`string`; `minLength`=`1`

#### `variables_and_units`

**Constraints:** type=`array`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `name`, `unit`

###### Properties

###### `description`

**Constraints:** type=`string | null`

###### `name` — **required**

**Constraints:** type=`string`; `minLength`=`1`

###### `unit` — **required**

**Constraints:** type=`string | null`

#### `version_or_release`

**Constraints:** type=`string | null`

### $defs

#### `artifact`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `byte_size`, `sha256`, `storage_reference`

##### Properties

###### `byte_size` — **required**

**Constraints:** type=`integer`; `minimum`=`0`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `storage_reference` — **required**

**Constraints:** type=`string`; `pattern`=`^external://(?!.*//)(?!.*(?:/\.{1,2})(?:/|$))(?!.*\/$)[A-Za-z0-9][A-Za-z0-9._/-]*$`
