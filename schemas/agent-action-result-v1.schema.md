<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/agent-action-result-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Agent Action Result v1

> This file is a deterministic human-readable projection of `schemas/agent-action-result-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/agent-action-result-v1.schema.json`](agent-action-result-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:agent-action-result:1.0.0`  

Portable closed result receipt for the owner-authorized trusted-main Agent Action Dispatch control plane. scripts/validate_agent_action_result.py is authoritative for exact Python scalar types, UTC ordering, acquisition-receipt identity and cross-field checks.

**Executable authority note:** request_validation records strict validation/dedup state. acquisition_receipt phase is shared by three closed network actions: measurement acquisition_receipt for Issue 162, dwd_metadata_receipt for Issue 211, and efehr_readme_receipt for Issue 298. All require external_bytes_persisted=false. The EFEHR README receipt proves bounded transport and immutable byte identity only; it does not establish scientific fitness, model-use eligibility or publication authorization.

## Contract structure

Portable closed result receipt for the owner-authorized trusted-main Agent Action Dispatch control plane. scripts/validate_agent_action_result.py is authoritative for exact Python scalar types, UTC ordering, acquisition-receipt identity and cross-field checks.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `semantic_request_id`, `repository`, `action`, `source_issue`, `source_comment_id`, `target_sha`, `dataset_id`, `execution_sha`, `run_id`, `run_attempt`, `started_at`, `finished_at`, `phase`, `status`, `external_bytes_persisted`, `evidence`, `duplicate_result_comment_id`, `failure_class`

### Properties

#### `action` — **required**

**Constraints:** `enum`=`["sample_audit","acquisition_receipt","dwd_metadata_receipt","efehr_readme_receipt"]`

#### `dataset_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9][A-Za-z0-9._:-]*$`; `minLength`=`1`; `maxLength`=`160`

#### `duplicate_result_comment_id` — **required**

**Constraints:** type=`integer | null`; `minimum`=`1`

#### `evidence` — **required**

##### oneOf

###### Branch 1

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`

###### Properties

###### `ledger_scan_complete` — **required**

**Constraints:** type=`boolean`

###### `prior_result_reused` — **required**

**Constraints:** type=`boolean`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 2

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `acquisition_receipt`

###### Properties

###### `acquisition_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/acquisitionReceipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 3

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `dwd_metadata_receipt`

###### Properties

###### `dwd_metadata_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/dwdMetadataReceipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 4

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_readme_receipt`

###### Properties

###### `efehr_readme_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrReadmeReceipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

#### `execution_sha` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

#### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

#### `failure_class` — **required**

**Constraints:** type=`string | null`; `enum`=`[null,"duplicate_request","ledger_incomplete","acquisition_failed"]`

#### `finished_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

#### `phase` — **required**

**Constraints:** `enum`=`["request_validation","acquisition_receipt"]`

#### `repository` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$`

#### `run_attempt` — **required**

**Constraints:** type=`integer`; `minimum`=`1`

#### `run_id` — **required**

**Constraints:** type=`integer`; `minimum`=`1`

#### `schema_version` — **required**

**Constraints:** `const`=`oc-action-result-v1`

#### `semantic_request_id` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

#### `source_comment_id` — **required**

**Constraints:** type=`integer`; `minimum`=`1`

#### `source_issue` — **required**

**Constraints:** type=`integer`; `minimum`=`1`

#### `started_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

#### `status` — **required**

**Constraints:** `enum`=`["pass","duplicate","blocked"]`

#### `target_sha` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

### $defs

#### `acquisitionReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `dataset_id`, `source_issue`, `requested_url`, `final_url`, `filename`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `last_modified`, `etag`, `archive_member_count`, `archive_uncompressed_bytes`, `product_member`, `product_station_id`, `product_begin_date`, `product_end_date`, `product_row_count`, `product_structure_validated`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `archive_member_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`32`

###### `archive_uncompressed_bytes` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`104857600`

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`52428800`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `filename` — **required**

**Constraints:** `const`=`10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip`

###### `final_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip`

###### `last_modified` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `product_begin_date` — **required**

**Constraints:** `const`=`20100101`

###### `product_end_date` — **required**

**Constraints:** `const`=`20110331`

###### `product_member` — **required**

**Constraints:** type=`string`; `pattern`=`\.[Tt][Xx][Tt]$`; `minLength`=`1`; `maxLength`=`512`

###### `product_row_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1000000`

###### `product_station_id` — **required**

**Constraints:** `const`=`00003`

###### `product_structure_validated` — **required**

**Constraints:** `const`=`true`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `requested_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-acquisition-receipt-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`162`

#### `dwdMetadataReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `dataset_id`, `source_issue`, `requested_url`, `final_url`, `filename`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `last_modified`, `etag`, `archive_member_count`, `archive_uncompressed_bytes`, `station_id`, `required_metadata_families`, `metadata_members`, `temporal_coverage_status`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `archive_member_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`128`

###### `archive_uncompressed_bytes` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`20971520`

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`5242880`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `filename` — **required**

**Constraints:** `const`=`Meta_Daten_zehn_min_fx_00003.zip`

###### `final_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/meta_data/Meta_Daten_zehn_min_fx_00003.zip`

###### `last_modified` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `metadata_members` — **required**

**Constraints:** type=`array`; `minItems`=`3`; `maxItems`=`128`

###### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `path`, `family`

###### Properties

###### `family` — **required**

**Constraints:** `enum`=`["equipment","geography","parameter"]`

###### `path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `requested_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/meta_data/Meta_Daten_zehn_min_fx_00003.zip`

###### `required_metadata_families` — **required**

**Constraints:** `const`=`["equipment","geography","parameter"]`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-dwd-metadata-receipt-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`211`

###### `station_id` — **required**

**Constraints:** `const`=`00003`

###### `temporal_coverage_status` — **required**

**Constraints:** `const`=`unverified`

#### `efehrReadmeReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `release_tag`, `tag_api_url`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `requested_url`, `final_url`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `etag`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1048576`

###### `commit_sha` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `final_url` — **required**

**Constraints:** type=`string`; `pattern`=`^https://gitlab\.seismo\.ethz\.ch/api/v4/projects/186/repository/files/_exposure_models%2FReadMe_Exposure_Model_Format\.txt/raw\?ref=[a-f0-9]{40}$`

###### `operation_id` — **required**

**Constraints:** `const`=`esrm20-exposure-format-readme-v1`

###### `project_id` — **required**

**Constraints:** `const`=`186`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20_exposure`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `release_tag` — **required**

**Constraints:** `const`=`v1.0`

###### `repository_path` — **required**

**Constraints:** `const`=`_exposure_models/ReadMe_Exposure_Model_Format.txt`

###### `requested_url` — **required**

**Constraints:** type=`string`; `pattern`=`^https://gitlab\.seismo\.ethz\.ch/api/v4/projects/186/repository/files/_exposure_models%2FReadMe_Exposure_Model_Format\.txt/raw\?ref=[a-f0-9]{40}$`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-trusted-acquisition-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`282`

###### `tag_api_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/186/repository/tags/v1.0`

### allOf

#### Branch 1

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`

###### Properties

###### `phase` — **required**

**Constraints:** `const`=`request_validation`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

###### allOf

###### Branch 1

###### not

**Required here:** `acquisition_receipt`

###### Branch 2

###### not

**Required here:** `dwd_metadata_receipt`

###### Branch 3

###### not

**Required here:** `efehr_readme_receipt`

#### Branch 2

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `status`

###### Properties

###### `phase` — **required**

**Constraints:** `const`=`request_validation`

###### `status` — **required**

**Constraints:** `const`=`pass`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `duplicate_result_comment_id`

**Constraints:** type=`null`

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `ledger_scan_complete`

**Constraints:** `const`=`true`

###### `prior_result_reused`

**Constraints:** `const`=`false`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 3

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `status`

###### Properties

###### `status` — **required**

**Constraints:** `const`=`duplicate`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `duplicate_result_comment_id`

**Constraints:** type=`integer`; `minimum`=`1`

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `ledger_scan_complete`

**Constraints:** `const`=`true`

###### `prior_result_reused`

**Constraints:** `const`=`true`

###### `failure_class`

**Constraints:** `const`=`duplicate_request`

###### `phase`

**Constraints:** `const`=`request_validation`

#### Branch 4

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `status`

###### Properties

###### `phase` — **required**

**Constraints:** `const`=`request_validation`

###### `status` — **required**

**Constraints:** `const`=`blocked`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `duplicate_result_comment_id`

**Constraints:** type=`null`

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `ledger_scan_complete`

**Constraints:** `const`=`false`

###### `prior_result_reused`

**Constraints:** `const`=`false`

###### `failure_class`

**Constraints:** `const`=`ledger_incomplete`

#### Branch 5

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`

###### Properties

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `action`

**Constraints:** `enum`=`["acquisition_receipt","dwd_metadata_receipt","efehr_readme_receipt"]`

###### `duplicate_result_comment_id`

**Constraints:** type=`null`

#### Branch 6

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

###### `evidence`

**Required here:** `acquisition_receipt`

###### `source_issue`

**Constraints:** `const`=`162`

#### Branch 7

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`dwd_metadata_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

###### `evidence`

**Required here:** `dwd_metadata_receipt`

###### `source_issue`

**Constraints:** `const`=`211`

#### Branch 8

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_readme_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `evidence`

**Required here:** `efehr_readme_receipt`

###### `source_issue`

**Constraints:** `const`=`298`

#### Branch 9

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `status` — **required**

**Constraints:** `const`=`pass`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `acquisition_receipt`

**Constraints:** `$ref`=`#/$defs/acquisitionReceipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 10

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`dwd_metadata_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `status` — **required**

**Constraints:** `const`=`pass`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `dwd_metadata_receipt`

**Constraints:** `$ref`=`#/$defs/dwdMetadataReceipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 11

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_readme_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `status` — **required**

**Constraints:** `const`=`pass`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `efehr_readme_receipt`

**Constraints:** `$ref`=`#/$defs/efehrReadmeReceipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 12

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `status` — **required**

**Constraints:** `const`=`blocked`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `acquisition_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 13

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`dwd_metadata_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `status` — **required**

**Constraints:** `const`=`blocked`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `dwd_metadata_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 14

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_readme_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

###### `status` — **required**

**Constraints:** `const`=`blocked`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `evidence`

**Constraints:** type=`object (implicit)`

###### Properties

###### `efehr_readme_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`
