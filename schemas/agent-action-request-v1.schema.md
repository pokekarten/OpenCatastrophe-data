<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/agent-action-request-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Agent Action Request v1

> This file is a deterministic human-readable projection of `schemas/agent-action-request-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/agent-action-request-v1.schema.json`](agent-action-request-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:agent-action-request:1.0.0`  

Portable structural view of the closed request contract for a bounded trusted-main GitHub Actions evidence operation. scripts/validate_agent_action_request.py is authoritative for executable security policy that JSON Schema cannot fully express.

**Executable authority note:** Draft 2020-12 treats zero-fraction JSON numbers such as 1.0 as integers. The executable validator additionally requires the parsed issue value to have exact int type (rejecting bool and float), rejects duplicate keys and non-finite JSON, enforces the single-marker comment envelope, restricts acquisition_receipt to Issue 162 plus the frozen DWD dataset, restricts dwd_metadata_receipt to Issue 211 plus that same frozen DWD dataset, restricts efehr_readme_receipt to Issue 298 plus the frozen ESRM20 exposure dataset, restricts efehr_eshm20_tree_metadata to Issue 332 plus the frozen ESHM20 dataset, and restricts efehr_eshm20_root_config_receipt to Issue 335 plus the frozen ESHM20 dataset. No network action accepts a caller-supplied URL/path/header/provider/project/ref/prefix target.

## Contract structure

Portable structural view of the closed request contract for a bounded trusted-main GitHub Actions evidence operation. scripts/validate_agent_action_request.py is authoritative for executable security policy that JSON Schema cannot fully express.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `action`, `issue`, `target_sha`, `dataset_id`, `requester`

### Properties

#### `action` — **required**

**Constraints:** `enum`=`["sample_audit","acquisition_receipt","dwd_metadata_receipt","efehr_readme_receipt","efehr_eshm20_tree_metadata","efehr_eshm20_root_config_receipt"]`

#### `dataset_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._:-]*$`; `minLength`=`1`; `maxLength`=`160`

#### `issue` — **required**

**Constraints:** type=`integer`; `minimum`=`1`

#### `requester` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._:-]*$`; `minLength`=`1`; `maxLength`=`128`

#### `schema_version` — **required**

**Constraints:** `const`=`oc-action-request-v1`

#### `target_sha` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

### allOf

#### Branch 1

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

###### `issue`

**Constraints:** `const`=`162`

#### Branch 2

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`dwd_metadata_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

###### `issue`

**Constraints:** `const`=`211`

#### Branch 3

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_readme_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `issue`

**Constraints:** `const`=`298`

#### Branch 4

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_tree_metadata`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `issue`

**Constraints:** `const`=`332`

#### Branch 5

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_config_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `issue`

**Constraints:** `const`=`335`
