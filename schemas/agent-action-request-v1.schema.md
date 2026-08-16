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

**Executable authority note:** Draft 2020-12 treats zero-fraction JSON numbers such as 1.0 as integers. The executable validator additionally requires the parsed issue value to have exact int type (rejecting bool and float), rejects duplicate keys and non-finite JSON, enforces the single-marker comment envelope, restricts acquisition_receipt to Issue 162 plus the frozen DWD dataset, restricts dwd_metadata_receipt to Issue 211 plus that same frozen DWD dataset, restricts efehr_readme_receipt to Issue 298 plus the frozen ESRM20 exposure dataset, restricts efehr_eshm20_tree_metadata to Issue 332 plus the frozen ESHM20 dataset, restricts efehr_kosovo_exposure_receipt to Issue 328 plus the frozen ESRM20 exposure dataset, restricts efehr_eshm20_root_config_receipt to Issue 335 plus the frozen ESHM20 dataset, and restricts esrm20_event_hazard_group1_receipt plus esrm20_event_hazard_group2_receipt to Issue 346 plus the frozen ESRM20 risk-input dataset, and restricts efehr_kosovo_exposure_profile to Issue 351 plus the frozen ESRM20 exposure dataset. No network action accepts a caller-supplied URL/path/header/provider/project/ref/commit/group/parser/content target. efehr_eshm20_root_dependency_profile is restricted to Issue 353 plus the frozen ESHM20 dataset. efehr_eshm20_first_order_receipts is restricted to Issue 361 plus the frozen three-file ESHM20 first-order set. efehr_eshm20_gsim_resource_profile is restricted to Issue 376 plus the frozen ESHM20 dataset and exposes no caller-controlled GMM/resource target. efehr_kosovo_taxonomy_identity is restricted to Issue 363 plus the frozen ESRM20 Kosovo exposure dataset and exposes no caller-controlled provider, representation, taxonomy, mapping, vulnerability, or publication selector. esrm20_exposure_vulnerability_mapping_receipt is restricted to Issue 340 plus the frozen ESRM20 risk-input dataset and exposes no caller-controlled provider, path, commit, mapping, vulnerability, parser, publication, or model-use selector. efehr_eshm20_source_model_child_receipts is restricted to Issue 414 plus the frozen ESHM20 dataset and the exact 51-child set returned by trusted-main \#397.

## Contract structure

Portable structural view of the closed request contract for a bounded trusted-main GitHub Actions evidence operation. scripts/validate_agent_action_request.py is authoritative for executable security policy that JSON Schema cannot fully express.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `action`, `issue`, `target_sha`, `dataset_id`, `requester`

### Properties

#### `action` — **required**

**Constraints:** `enum`=`["sample_audit","acquisition_receipt","dwd_metadata_receipt","efehr_readme_receipt","efehr_eshm20_tree_metadata","efehr_eshm20_root_config_receipt","efehr_kosovo_exposure_receipt","esrm20_event_hazard_group1_receipt","esrm20_event_hazard_group2_receipt","efehr_kosovo_exposure_profile","efehr_eshm20_root_dependency_profile","efehr_eshm20_first_order_receipts","efehr_eshm20_gsim_resource_profile","efehr_kosovo_taxonomy_identity","esrm20_exposure_vulnerability_mapping_receipt","efehr_eshm20_source_model_dependencies","efehr_eshm20_source_model_child_receipts"]`

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

#### Branch 6

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `issue`

**Constraints:** `const`=`328`

#### Branch 7

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_profile`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `issue`

**Constraints:** `const`=`351`

#### Branch 8

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_taxonomy_identity`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `issue`

**Constraints:** `const`=`363`

#### Branch 9

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group1_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `issue`

**Constraints:** `const`=`346`

#### Branch 10

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group2_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `issue`

**Constraints:** `const`=`346`

#### Branch 11

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_exposure_vulnerability_mapping_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `issue`

**Constraints:** `const`=`340`

#### Branch 12

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_dependency_profile`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `issue`

**Constraints:** `const`=`353`

#### Branch 13

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_first_order_receipts`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `issue`

**Constraints:** `const`=`361`

#### Branch 14

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_gsim_resource_profile`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `issue`

**Constraints:** `const`=`376`

#### Branch 15

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_dependencies`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `issue`

**Constraints:** `const`=`397`

#### Branch 16

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_child_receipts`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `issue`

**Constraints:** `const`=`414`
