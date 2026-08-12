<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/source-access-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Source Access Contract v1

> This file is a deterministic human-readable projection of `schemas/source-access-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/source-access-v1.schema.json`](source-access-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:source-access:1.0.0`  

Portable structural view of the fail-closed contract for an authoritative machine-access route. scripts/validate_source_access.py is the executable security authority for URL/IP/secret/path and cross-field constraints that JSON Schema cannot fully express. Connectivity never implies rights clearance, scientific approval or data admission.

**Executable authority note:** The executable validator additionally rejects duplicate JSON keys, non-finite values, non-ASCII/IDNA-uncanonical host forms, local/private/legacy-numeric hosts, secret-bearing or signed query URLs, invalid UTF-8 or decoded path traversal/backslashes/URL smuggling, and enforces the fail-closed rights/probe/endpoint/implementation state machine below. Runtime network workers must still re-resolve and validate DNS/redirect targets before connection.

## Contract structure

Portable structural view of the fail-closed contract for an authoritative machine-access route. scripts/validate_source_access.py is the executable security authority for URL/IP/secret/path and cross-field constraints that JSON Schema cannot fully express. Connectivity never implies rights clearance, scientific approval or data admission.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `access_id`, `source_ids`, `provider`, `interface_type`, `status`, `documentation_url`, `service_root`, `api_version`, `access_scope`, `authentication`, `request_contract`, `response_contract`, `operational_constraints`, `rights_and_policy`, `probe_contract`, `implementation_decision`, `reviewed_at`, `evidence_urls`, `notes`

### Properties

#### `access_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-z0-9]+(?:[.-][a-z0-9]+)*$`

#### `access_scope` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

##### Array items

**Constraints:** type=`string`; `enum`=`["metadata","catalogue","sample","bulk","realtime","other"]`

#### `api_version` — **required**

**Constraints:** type=`string | null`

#### `authentication` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `mode`, `credential_reference`, `registration_url`, `secret_in_repository`

##### Properties

###### `credential_reference` — **required**

**Constraints:** type=`string | null`; `pattern`=`^[A-Z][A-Z0-9_]{2,127}$`

###### `mode` — **required**

**Constraints:** type=`string`; `enum`=`["none","api_key","bearer_token","basic","oauth2","provider_account","signed_request","other"]`

###### `registration_url` — **required**

**Constraints:** `$ref`=`#/$defs/nullableHttpsUrl`

###### `secret_in_repository` — **required**

**Constraints:** `const`=`false`

##### allOf

###### Branch 1

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `mode`

###### Properties

###### `mode` — **required**

**Constraints:** `const`=`none`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `credential_reference`

**Constraints:** type=`null`

###### Branch 2

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `mode`

###### Properties

###### `mode` — **required**

**Constraints:** `enum`=`["api_key","bearer_token","basic","oauth2","signed_request"]`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `credential_reference`

**Constraints:** type=`string`; `pattern`=`^[A-Z][A-Z0-9_]{2,127}$`

#### `documentation_url` — **required**

**Constraints:** `$ref`=`#/$defs/httpsUrl`

#### `evidence_urls` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

##### Array items

**Constraints:** `$ref`=`#/$defs/httpsUrl`

#### `implementation_decision` — **required**

**Constraints:** type=`string`; `enum`=`["build_adapter_now","document_only","build_later","do_not_automate"]`

#### `interface_type` — **required**

**Constraints:** type=`string`; `enum`=`["rest","fdsn","ogc_api","stac","wms","wfs","wcs","arcgis_rest","mqtt_http","object_store","http_file","ftp_or_ftps","provider_sdk","web_portal","other_documented_machine_interface"]`

#### `notes` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

#### `operational_constraints` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `timeout_seconds`, `max_probe_bytes`, `max_sample_bytes`, `retry_policy`, `rate_limit_notes`, `mutability_notes`

##### Properties

###### `max_probe_bytes` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`5242880`

###### `max_sample_bytes` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`52428800`

###### `mutability_notes` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

###### `rate_limit_notes` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

###### `retry_policy` — **required**

**Constraints:** type=`string`; `enum`=`["none","bounded_backoff"]`

###### `timeout_seconds` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`120`

#### `probe_contract` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `mode`, `operation`, `requires_credentials`, `expected_evidence`

##### Properties

###### `expected_evidence` — **required**

**Constraints:** type=`array`

###### Array items

**Constraints:** `$ref`=`#/$defs/nonBlank`

###### `mode` — **required**

**Constraints:** type=`string`; `enum`=`["none","metadata_get","head","catalogue_query","provider_specific"]`

###### `operation` — **required**

**Constraints:** type=`string | null`

###### `requires_credentials` — **required**

**Constraints:** type=`boolean`

#### `provider` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

#### `request_contract` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `allowed_operations`, `path_templates`, `parameter_rules`

##### Properties

###### `allowed_operations` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `pattern`=`^[a-z][a-z0-9_]*$`

###### `parameter_rules` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

###### `path_templates` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `pattern`=`^/(?!/)(?!.*\\)(?!.*(?:^|/)\.\.?/)(?!.*%2[eEfF]|%5[cC]|%3[fF]|%23)(?!.*://)(?!.*[?#])[^\s]*$`

#### `response_contract` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `expected_media_types`, `format`, `scientific_semantics`

##### Properties

###### `expected_media_types` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+$`

###### `format` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

###### `scientific_semantics` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

#### `reviewed_at` — **required**

**Constraints:** type=`string`; `format`=`date`; `pattern`=`^\d{4}-\d{2}-\d{2}$`

#### `rights_and_policy` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `dataset_rights_status`, `api_terms_status`, `terms_url`, `commercial_automation_status`, `redistribution_status`, `notes`

##### Properties

###### `api_terms_status` — **required**

**Constraints:** type=`string`; `enum`=`["same_as_dataset","separate_reviewed","separate_unreviewed","unknown"]`

###### `commercial_automation_status` — **required**

**Constraints:** type=`string`; `enum`=`["allowed","restricted","prohibited","unknown"]`

###### `dataset_rights_status` — **required**

**Constraints:** type=`string`; `enum`=`["verified","not_reviewed","conflicting","restricted","prohibited","unknown"]`

###### `notes` — **required**

**Constraints:** `$ref`=`#/$defs/nonBlank`

###### `redistribution_status` — **required**

**Constraints:** type=`string`; `enum`=`["allowed","restricted","prohibited","unknown"]`

###### `terms_url` — **required**

**Constraints:** `$ref`=`#/$defs/nullableHttpsUrl`

##### allOf

###### Branch 1

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `api_terms_status`

###### Properties

###### `api_terms_status` — **required**

**Constraints:** `const`=`separate_reviewed`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `terms_url`

**Constraints:** `$ref`=`#/$defs/httpsUrl`

###### Branch 2

###### if

**Constraints:** type=`object (implicit)`

**Required here:** `api_terms_status`

###### Properties

###### `api_terms_status` — **required**

**Constraints:** `const`=`same_as_dataset`

###### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `terms_url`

**Constraints:** `$ref`=`#/$defs/httpsUrl`

#### `schema_version` — **required**

**Constraints:** `const`=`1.0.0`

#### `service_root` — **required**

**Constraints:** `$ref`=`#/$defs/nullableHttpsUrl`

#### `source_ids` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `uniqueItems`=`true`

##### Array items

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._-]*$`

#### `status` — **required**

**Constraints:** type=`string`; `enum`=`["documented_only","probe_ready","verified_anonymous","verified_authenticated","blocked_registration","blocked_credentials","restricted_by_terms","deprecated","rejected"]`

### $defs

#### `httpsUrl`

**Constraints:** type=`string`; `pattern`=`^https://(?![^/?#]*@)(?!localhost(?:[:/]|$))(?!127\.)(?!10\.)(?!192\.168\.)(?!169\.254\.)[\x21-\x7E]+$`

#### `nonBlank`

**Constraints:** type=`string`; `pattern`=`\S`

#### `nullableHttpsUrl`

##### anyOf

###### Branch 1

**Constraints:** `$ref`=`#/$defs/httpsUrl`

###### Branch 2

**Constraints:** type=`null`

### allOf

#### Branch 1

##### if

**Constraints:** type=`object (implicit)`

###### Properties

###### `rights_and_policy`

**Constraints:** type=`object (implicit)`

**Required here:** `dataset_rights_status`

###### Properties

###### `dataset_rights_status` — **required**

###### not

**Constraints:** `const`=`verified`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `implementation_decision`

**Constraints:** `enum`=`["document_only","do_not_automate"]`

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

**Constraints:** `const`=`none`

###### `operation`

**Constraints:** type=`null`

###### `rights_and_policy`

**Constraints:** type=`object (implicit)`

###### Properties

###### `commercial_automation_status`

###### not

**Constraints:** `const`=`allowed`

###### `redistribution_status`

###### not

**Constraints:** `const`=`allowed`

#### Branch 2

##### if

**Constraints:** type=`object (implicit)`

###### Properties

###### `rights_and_policy`

**Constraints:** type=`object (implicit)`

**Required here:** `api_terms_status`

###### Properties

###### `api_terms_status` — **required**

**Constraints:** `enum`=`["separate_unreviewed","unknown"]`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `implementation_decision`

**Constraints:** `enum`=`["document_only","do_not_automate"]`

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

**Constraints:** `const`=`none`

###### `operation`

**Constraints:** type=`null`

###### `rights_and_policy`

**Constraints:** type=`object (implicit)`

###### Properties

###### `commercial_automation_status`

###### not

**Constraints:** `const`=`allowed`

#### Branch 3

##### if

**Constraints:** type=`object (implicit)`

###### Properties

###### `rights_and_policy`

**Constraints:** type=`object (implicit)`

**Required here:** `commercial_automation_status`

###### Properties

###### `commercial_automation_status` — **required**

###### not

**Constraints:** `const`=`allowed`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `implementation_decision`

**Constraints:** `enum`=`["document_only","do_not_automate"]`

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

**Constraints:** `const`=`none`

###### `operation`

**Constraints:** type=`null`

#### Branch 4

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `enum`=`["documented_only","blocked_registration","blocked_credentials","restricted_by_terms","rejected","deprecated"]`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `implementation_decision`

**Constraints:** `enum`=`["document_only","do_not_automate"]`

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

**Constraints:** `const`=`none`

###### `operation`

**Constraints:** type=`null`

#### Branch 5

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`probe_ready`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

###### not

**Constraints:** `const`=`none`

#### Branch 6

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`verified_anonymous`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `authentication`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

**Constraints:** `const`=`none`

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `expected_evidence`

**Constraints:** `minItems`=`1`

###### `mode`

###### not

**Constraints:** `const`=`none`

#### Branch 7

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`verified_authenticated`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `authentication`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

###### not

**Constraints:** `const`=`none`

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `expected_evidence`

**Constraints:** `minItems`=`1`

###### `mode`

###### not

**Constraints:** `const`=`none`

#### Branch 8

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `probe_contract`

###### Properties

###### `probe_contract` — **required**

**Constraints:** type=`object (implicit)`

**Required here:** `mode`

###### Properties

###### `mode` — **required**

###### not

**Constraints:** `const`=`none`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `expected_evidence`

**Constraints:** `minItems`=`1`

###### `service_root`

**Constraints:** `$ref`=`#/$defs/httpsUrl`

#### Branch 9

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `authentication`, `probe_contract`

###### Properties

###### `authentication` — **required**

**Constraints:** type=`object (implicit)`

**Required here:** `mode`

###### Properties

###### `mode` — **required**

###### not

**Constraints:** `const`=`none`

###### `probe_contract` — **required**

**Constraints:** type=`object (implicit)`

**Required here:** `mode`

###### Properties

###### `mode` — **required**

###### not

**Constraints:** `const`=`none`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `authentication`

**Constraints:** type=`object (implicit)`

###### Properties

###### `credential_reference`

**Constraints:** type=`string`; `pattern`=`^[A-Z][A-Z0-9_]{2,127}$`

#### Branch 10

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `interface_type`

###### Properties

###### `interface_type` — **required**

**Constraints:** `const`=`ftp_or_ftps`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `implementation_decision`

**Constraints:** `enum`=`["document_only","build_later","do_not_automate"]`

###### `probe_contract`

**Constraints:** type=`object (implicit)`

###### Properties

###### `mode`

**Constraints:** `const`=`none`

###### `operation`

**Constraints:** type=`null`

#### Branch 11

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `implementation_decision`

###### Properties

###### `implementation_decision` — **required**

**Constraints:** `const`=`build_adapter_now`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `rights_and_policy`

**Constraints:** type=`object (implicit)`

###### Properties

###### `api_terms_status`

**Constraints:** `enum`=`["same_as_dataset","separate_reviewed"]`

###### `commercial_automation_status`

**Constraints:** `const`=`allowed`

###### `dataset_rights_status`

**Constraints:** `const`=`verified`

###### `service_root`

**Constraints:** `$ref`=`#/$defs/httpsUrl`
