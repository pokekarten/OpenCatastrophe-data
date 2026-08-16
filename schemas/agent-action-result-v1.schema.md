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

**Executable authority note:** request_validation records strict validation/dedup state. acquisition_receipt phase is shared by closed network actions: measurement acquisition_receipt for Issue 162, dwd_metadata_receipt for Issue 211, efehr_readme_receipt for Issue 298, efehr_eshm20_tree_metadata for Issue 332, efehr_kosovo_exposure_receipt for Issue 328, efehr_eshm20_root_config_receipt for Issue 335, the two ESRM20 event-hazard Group1/Group2 receipt actions for Issue 346, efehr_kosovo_exposure_profile for Issue 351, and efehr_eshm20_gsim_resource_profile for Issue 376. All require external_bytes_persisted=false. EFEHR/ESRM20 receipts prove only their bounded transport, repository-metadata, or exact selected-file byte identity; they do not establish scientific fitness, dependency closure, model-use eligibility, completeness outside the selected scope or publication authorization. efehr_eshm20_root_dependency_profile for Issue 353 persists only verified first-order dependency metadata; dependency inventory, transitive closure, model use and publication remain unauthorized. efehr_eshm20_first_order_receipts for Issue 361 persists only exact byte receipts for the three \#353-selected first-order candidates; dependency inventory, semantics, closure, model use and publication remain unauthorized. efehr_eshm20_gsim_resource_profile persists only bounded structural _file/_table resource-reference metadata from the exact \#361-receipted GMM logic-tree bytes; dependency receipts, dependency closure, GSIM runtime validity, model use and publication remain unauthorized. efehr_kosovo_taxonomy_identity for Issue 363 persists only the exact pre-publication identity of the 86-value Kosovo residential TAXONOMY set; literal taxonomy values, provider bytes, normalization, mapping interpretation, vulnerability selection, publication and model use remain unauthorized. esrm20_exposure_vulnerability_mapping_receipt for Issue 340 persists only the exact selected mapping-file byte receipt; mapping-row interpretation, taxonomy-to-vulnerability resolution, vulnerability selection, provider-byte publication and model use remain unauthorized. efehr_eshm20_source_model_child_receipts for Issue 414 persists only the exact 51 frozen child byte receipts and bounded provenance; dependency expansion, transitive closure, model use and publication remain unauthorized.

## Contract structure

Portable closed result receipt for the owner-authorized trusted-main Agent Action Dispatch control plane. scripts/validate_agent_action_result.py is authoritative for exact Python scalar types, UTC ordering, acquisition-receipt identity and cross-field checks.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `semantic_request_id`, `repository`, `action`, `source_issue`, `source_comment_id`, `target_sha`, `dataset_id`, `execution_sha`, `run_id`, `run_attempt`, `started_at`, `finished_at`, `phase`, `status`, `external_bytes_persisted`, `evidence`, `duplicate_result_comment_id`, `failure_class`

### Properties

#### `action` — **required**

**Constraints:** `enum`=`["sample_audit","acquisition_receipt","dwd_metadata_receipt","efehr_readme_receipt","efehr_eshm20_tree_metadata","efehr_eshm20_root_config_receipt","efehr_kosovo_exposure_receipt","esrm20_event_hazard_group1_receipt","esrm20_event_hazard_group2_receipt","efehr_kosovo_exposure_profile","efehr_eshm20_root_dependency_profile","efehr_eshm20_first_order_receipts","efehr_eshm20_gsim_resource_profile","efehr_kosovo_taxonomy_identity","esrm20_exposure_vulnerability_mapping_receipt","esrm20_exposure_vulnerability_mapping_headers","efehr_eshm20_source_model_dependencies","efehr_eshm20_source_model_child_receipts"]`

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

###### Branch 5

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_eshm20_tree_metadata`

###### Properties

###### `efehr_eshm20_tree_metadata` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrEshm20TreeMetadata`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 6

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_kosovo_exposure_receipt`

###### Properties

###### `efehr_kosovo_exposure_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrKosovoExposureReceipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 7

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_kosovo_exposure_profile`

###### Properties

###### `efehr_kosovo_exposure_profile` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrKosovoExposureProfile`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 8

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_eshm20_root_config_receipt`

###### Properties

###### `efehr_eshm20_root_config_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrEshm20RootConfigReceipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 9

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `esrm20_event_hazard_group1_receipt`

###### Properties

###### `esrm20_event_hazard_group1_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/esrm20EventHazardGroup1Receipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 10

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `esrm20_event_hazard_group2_receipt`

###### Properties

###### `esrm20_event_hazard_group2_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/esrm20EventHazardGroup2Receipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 11

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_eshm20_root_dependency_profile`

###### Properties

###### `efehr_eshm20_root_dependency_profile` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrEshm20RootDependencyProfile`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 12

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_eshm20_first_order_receipts`

###### Properties

###### `efehr_eshm20_first_order_receipts` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrEshm20FirstOrderReceiptSet`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 13

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_eshm20_gsim_resource_profile`

###### Properties

###### `efehr_eshm20_gsim_resource_profile` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrEshm20GsimResourceProfile`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 14

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `esrm20_exposure_vulnerability_mapping_receipt`

###### Properties

###### `esrm20_exposure_vulnerability_mapping_receipt` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/esrm20ExposureVulnerabilityMappingReceipt`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 15

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `esrm20_exposure_vulnerability_mapping_headers`

###### Properties

###### `esrm20_exposure_vulnerability_mapping_headers` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/esrm20ExposureVulnerabilityMappingHeaders`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 16

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_kosovo_taxonomy_identity`

###### Properties

###### `efehr_kosovo_taxonomy_identity` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrKosovoTaxonomyIdentity`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 17

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_eshm20_source_model_dependencies`

###### Properties

###### `efehr_eshm20_source_model_dependencies` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrEshm20SourceModelDependencies`

###### `ledger_scan_complete` — **required**

**Constraints:** `const`=`true`

###### `prior_result_reused` — **required**

**Constraints:** `const`=`false`

###### `request_validated` — **required**

**Constraints:** `const`=`true`

###### Branch 18

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `request_validated`, `ledger_scan_complete`, `prior_result_reused`, `efehr_eshm20_source_model_child_receipts`

###### Properties

###### `efehr_eshm20_source_model_child_receipts` — **required**

###### anyOf

###### Branch 1

**Constraints:** type=`null`

###### Branch 2

**Constraints:** `$ref`=`#/$defs/efehrEshm20SourceModelChildReceiptSet`

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

#### `efehrEshm20FirstOrderArtifactReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `requested_url`, `final_url`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `etag`, `external_bytes_persisted`, `publication_authorized`, `parent_result_comment_id`, `parent_section`, `parent_option`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`67108864`

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `final_url` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`1024`

###### `parent_option` — **required**

**Constraints:** `enum`=`["site_model_file","gsim_logic_tree_file","source_model_logic_tree_file"]`

###### `parent_result_comment_id` — **required**

**Constraints:** `const`=`5301726249`

###### `parent_section` — **required**

**Constraints:** `enum`=`["site_params","calculation"]`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `enum`=`["oq_computational/oq_configuration_eshm20_v12e_region_main/eshm20_site_model_v06d.csv","oq_computational/oq_configuration_eshm20_v12e_region_main/gmpe_complete_logic_tree_5br.xml","oq_computational/oq_configuration_eshm20_v12e_region_main/source_model_logic_tree_eshm20_model_v12e.xml"]`

###### `requested_url` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`1024`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-gitlab-artifact-receipt-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `efehrEshm20FirstOrderReceiptSet`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `control_issue`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `selection_request_comment_id`, `selection_result_comment_id`, `selection_run_id`, `selection_execution_sha`, `retrieved_at`, `receipts`, `dependency_inventory_authorized`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `control_issue` — **required**

**Constraints:** `const`=`361`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `dependency_inventory_authorized` — **required**

**Constraints:** `const`=`false`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `operation_id` — **required**

**Constraints:** `const`=`eshm20-first-order-dependencies-v12e-region-main-v1`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `receipts` — **required**

**Constraints:** type=`array`; `minItems`=`3`; `maxItems`=`3`

###### Array items

**Constraints:** `$ref`=`#/$defs/efehrEshm20FirstOrderArtifactReceipt`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-eshm20-first-order-receipt-set-v1`

###### `selection_execution_sha` — **required**

**Constraints:** `const`=`bd146a19fa4a1dc85b616288ec6d24946336a483`

###### `selection_request_comment_id` — **required**

**Constraints:** `const`=`5301725105`

###### `selection_result_comment_id` — **required**

**Constraints:** `const`=`5301726249`

###### `selection_run_id` — **required**

**Constraints:** `const`=`31878511737`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `efehrEshm20GsimResource`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `argument_key`, `relative_path`, `resolved_path`, `selected_prefix_inventory_member`, `comment_prefixed`, `origins`

##### Properties

###### `argument_key` — **required**

**Constraints:** type=`string`; `pattern`=`^[A-Za-z0-9_]+_(?:file|table)$`; `minLength`=`1`; `maxLength`=`128`

###### `comment_prefixed` — **required**

**Constraints:** type=`boolean`

###### `origins` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `maxItems`=`512`; `uniqueItems`=`true`

###### Array items

**Constraints:** `$ref`=`#/$defs/efehrEshm20GsimResourceOrigin`

###### `relative_path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `resolved_path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `selected_prefix_inventory_member` — **required**

**Constraints:** type=`boolean`

#### `efehrEshm20GsimResourceOrigin`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `branch_set_id`, `branch_id`

##### Properties

###### `branch_id` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `branch_set_id` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

#### `efehrEshm20GsimResourceProfile`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `source_issue`, `control_issue`, `dataset_id`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `byte_count`, `sha256`, `openquake_reference`, `inventory_receipt_comment_id`, `root_dependency_result_comment_id`, `root_dependency_section`, `root_dependency_option`, `first_order_receipt_request_comment_id`, `first_order_receipt_result_comment_id`, `first_order_receipt_run_id`, `first_order_receipt_execution_sha`, `first_order_receipt_retrieved_at`, `branch_set_count`, `branch_count`, `resource_reference_count`, `resources`, `dependency_inventory_authorized`, `dependency_receipt_authorized`, `external_bytes_persisted`, `publication_authorized`, `model_use_authorized`, `profiled_at`

##### Properties

###### `branch_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`512`

###### `branch_set_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`64`

###### `byte_count` — **required**

**Constraints:** `const`=`33760`

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `control_issue` — **required**

**Constraints:** `const`=`374`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `dependency_inventory_authorized` — **required**

**Constraints:** `const`=`false`

###### `dependency_receipt_authorized` — **required**

**Constraints:** `const`=`false`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `first_order_receipt_execution_sha` — **required**

**Constraints:** `const`=`ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1`

###### `first_order_receipt_request_comment_id` — **required**

**Constraints:** `const`=`5301857400`

###### `first_order_receipt_result_comment_id` — **required**

**Constraints:** `const`=`5301858821`

###### `first_order_receipt_retrieved_at` — **required**

**Constraints:** `const`=`2026-08-15T10:40:16Z`

###### `first_order_receipt_run_id` — **required**

**Constraints:** `const`=`31880089623`

###### `inventory_receipt_comment_id` — **required**

**Constraints:** `const`=`5290449064`

###### `model_use_authorized` — **required**

**Constraints:** `const`=`false`

###### `openquake_reference` — **required**

**Constraints:** `const`=`gem/oq-engine@v3.14.0:openquake/hazardlib/gsim_lt.py::rel_paths/collect_files`

###### `profiled_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`oq_computational/oq_configuration_eshm20_v12e_region_main/gmpe_complete_logic_tree_5br.xml`

###### `resource_reference_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`256`

###### `resources` — **required**

**Constraints:** type=`array`; `minItems`=`0`; `maxItems`=`256`; `uniqueItems`=`true`

###### Array items

**Constraints:** `$ref`=`#/$defs/efehrEshm20GsimResource`

###### `root_dependency_option` — **required**

**Constraints:** `const`=`gsim_logic_tree_file`

###### `root_dependency_result_comment_id` — **required**

**Constraints:** `const`=`5301726249`

###### `root_dependency_section` — **required**

**Constraints:** `const`=`calculation`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-eshm20-gsim-resource-profile-v1`

###### `sha256` — **required**

**Constraints:** `const`=`e2c53f11174b8cd4de1f65af4dafc5af2e7a6848563e8a4c0ada44a54f22ff62`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `efehrEshm20RootConfigReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `requested_url`, `final_url`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `etag`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1048576`

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `final_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/197/repository/files/oq_computational%2Foq_configuration_eshm20_v12e_region_main%2Fconfig_eshm20_v12e_main_region.ini/raw?ref=fbd334de68f85d72669f73fc5a314a113db67317`

###### `operation_id` — **required**

**Constraints:** `const`=`eshm20-root-config-v12e-region-main-v1`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`oq_computational/oq_configuration_eshm20_v12e_region_main/config_eshm20_v12e_main_region.ini`

###### `requested_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/197/repository/files/oq_computational%2Foq_configuration_eshm20_v12e_region_main%2Fconfig_eshm20_v12e_main_region.ini/raw?ref=fbd334de68f85d72669f73fc5a314a113db67317`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-trusted-acquisition-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `efehrEshm20RootDependencyProfile`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `source_issue`, `dataset_id`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `byte_count`, `sha256`, `parser`, `inventory_receipt_comment_id`, `root_receipt_comment_id`, `root_receipt_run_id`, `root_receipt_execution_sha`, `dependencies`, `dependency_inventory_authorized`, `profiled_at`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** `const`=`2719`

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `dependencies` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `maxItems`=`128`

###### Array items

**Constraints:** `$ref`=`#/$defs/eshm20Dependency`

###### `dependency_inventory_authorized` — **required**

**Constraints:** `const`=`false`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `inventory_receipt_comment_id` — **required**

**Constraints:** `const`=`5290449064`

###### `parser` — **required**

**Constraints:** `const`=`scripts.openquake_config_dependencies.extract_openquake_config_references`

###### `profiled_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`oq_computational/oq_configuration_eshm20_v12e_region_main/config_eshm20_v12e_main_region.ini`

###### `root_receipt_comment_id` — **required**

**Constraints:** `const`=`5299422143`

###### `root_receipt_execution_sha` — **required**

**Constraints:** `const`=`0e28297e784e7cac590c068d66fde519c292abdb`

###### `root_receipt_run_id` — **required**

**Constraints:** `const`=`31853044582`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-eshm20-root-dependency-bridge-v1`

###### `sha256` — **required**

**Constraints:** `const`=`f1f4dabc48e1b8a478dbdb96b01c8f58cc68c98abd6f9004671c5fba9eb7e714`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `efehrEshm20SourceModelChildReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `repository_path`, `retrieved_at`, `byte_count`, `sha256`, `project_id`, `project_path`, `commit_sha`, `parent_result_comment_id`, `external_bytes_persisted`, `publication_authorized`, `model_use_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1048576`

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `model_use_authorized` — **required**

**Constraints:** `const`=`false`

###### `parent_result_comment_id` — **required**

**Constraints:** `const`=`5304432768`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

#### `efehrEshm20SourceModelChildReceiptSet`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `control_issue`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `parent_request_comment_id`, `parent_result_comment_id`, `parent_run_id`, `parent_execution_sha`, `parent_semantic_request_id`, `parent_source_tree_byte_count`, `parent_source_tree_sha256`, `child_count`, `child_paths_sha256`, `retrieved_at`, `receipts`, `dependency_inventory_authorized`, `dependency_receipt_authorized`, `external_bytes_persisted`, `publication_authorized`, `model_use_authorized`

##### Properties

###### `child_count` — **required**

**Constraints:** `const`=`51`

###### `child_paths_sha256` — **required**

**Constraints:** `const`=`2fcc885dc9fbbd8e9ee45b185dc9f2339af3654e9976ae5f07d4d097551944b7`

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `control_issue` — **required**

**Constraints:** `const`=`414`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `dependency_inventory_authorized` — **required**

**Constraints:** `const`=`false`

###### `dependency_receipt_authorized` — **required**

**Constraints:** `const`=`false`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `model_use_authorized` — **required**

**Constraints:** `const`=`false`

###### `operation_id` — **required**

**Constraints:** `const`=`eshm20-source-model-child-receipts-v12e-region-main-v1`

###### `parent_execution_sha` — **required**

**Constraints:** `const`=`dac7c9ae1c391006b8272f1342143d1ace678234`

###### `parent_request_comment_id` — **required**

**Constraints:** `const`=`5304431360`

###### `parent_result_comment_id` — **required**

**Constraints:** `const`=`5304432768`

###### `parent_run_id` — **required**

**Constraints:** `const`=`31910992436`

###### `parent_semantic_request_id` — **required**

**Constraints:** `const`=`e96030c55952bf9b4b2c6911368c52b9353bd161860923203d115f550824c27e`

###### `parent_source_tree_byte_count` — **required**

**Constraints:** `const`=`17579`

###### `parent_source_tree_sha256` — **required**

**Constraints:** `const`=`97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `receipts` — **required**

**Constraints:** type=`array`; `minItems`=`51`; `maxItems`=`51`

###### Array items

**Constraints:** `$ref`=`#/$defs/efehrEshm20SourceModelChildReceipt`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-eshm20-source-model-child-receipt-set-v1`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `efehrEshm20SourceModelDependencies`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `source_issue`, `control_issue`, `dataset_id`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `byte_count`, `sha256`, `parser`, `inventory_receipt_comment_id`, `root_dependency_result_comment_id`, `root_dependency_section`, `root_dependency_option`, `first_order_receipt_request_comment_id`, `first_order_receipt_run_id`, `first_order_receipt_execution_sha`, `dependencies`, `dependency_inventory_authorized`, `dependency_receipt_authorized`, `external_bytes_persisted`, `publication_authorized`, `model_use_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** `const`=`17579`

###### `commit_sha` — **required**

**Constraints:** `const`=`fbd334de68f85d72669f73fc5a314a113db67317`

###### `control_issue` — **required**

**Constraints:** `const`=`367`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `dependencies` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `maxItems`=`62`; `uniqueItems`=`true`

###### Array items

**Constraints:** `$ref`=`#/$defs/efehrEshm20SourceModelDependency`

###### `dependency_inventory_authorized` — **required**

**Constraints:** `const`=`false`

###### `dependency_receipt_authorized` — **required**

**Constraints:** `const`=`false`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `first_order_receipt_execution_sha` — **required**

**Constraints:** `const`=`ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1`

###### `first_order_receipt_request_comment_id` — **required**

**Constraints:** `const`=`5301857400`

###### `first_order_receipt_run_id` — **required**

**Constraints:** `const`=`31880089623`

###### `inventory_receipt_comment_id` — **required**

**Constraints:** `const`=`5290449064`

###### `model_use_authorized` — **required**

**Constraints:** `const`=`false`

###### `parser` — **required**

**Constraints:** `const`=`scripts.openquake_source_model_logic_tree_dependencies.extract_source_model_logic_tree_dependencies`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`oq_computational/oq_configuration_eshm20_v12e_region_main/source_model_logic_tree_eshm20_model_v12e.xml`

###### `root_dependency_option` — **required**

**Constraints:** `const`=`source_model_logic_tree_file`

###### `root_dependency_result_comment_id` — **required**

**Constraints:** `const`=`5301726249`

###### `root_dependency_section` — **required**

**Constraints:** `const`=`calculation`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-eshm20-source-model-dependency-profile-v2`

###### `sha256` — **required**

**Constraints:** `const`=`97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `efehrEshm20SourceModelDependency`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `resolved_path`, `origins`, `is_hdf5_companion`

##### Properties

###### `is_hdf5_companion` — **required**

**Constraints:** `const`=`false`

###### `origins` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `maxItems`=`512`; `uniqueItems`=`true`

###### Array items

**Constraints:** `$ref`=`#/$defs/efehrEshm20SourceModelOrigin`

###### `resolved_path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

#### `efehrEshm20SourceModelOrigin`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `uncertainty_type`, `branch_id`

##### Properties

###### `branch_id` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `uncertainty_type` — **required**

**Constraints:** `enum`=`["sourceModel","extendModel"]`

#### `efehrEshm20TreeMetadata`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `branch`, `resolved_commit_sha`, `tree_prefix`, `retrieved_at`, `tree_page_count`, `tree_entry_count`, `metadata_byte_count`, `entries`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `branch` — **required**

**Constraints:** `const`=`master`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.eshm20`

###### `entries` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `maxItems`=`2000`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `path`, `type`, `id`, `mode`

###### Properties

###### `id` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

###### `mode` — **required**

**Constraints:** type=`string`; `pattern`=`^[0-7]{6}$`

###### `path` — **required**

**Constraints:** type=`string`; `pattern`=`^oq_computational/oq_configuration_eshm20_v12e_region_main/.+`; `minLength`=`1`; `maxLength`=`1024`

###### `type` — **required**

**Constraints:** `enum`=`["blob","tree"]`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `metadata_byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`8388608`

###### `operation_id` — **required**

**Constraints:** `const`=`eshm20-master-tree-metadata-v1`

###### `project_id` — **required**

**Constraints:** `const`=`197`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/eshm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `resolved_commit_sha` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{40}$`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-eshm20-tree-metadata-v1`

###### `source_issue` — **required**

**Constraints:** `const`=`320`

###### `tree_entry_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`2000`

###### `tree_page_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`20`

###### `tree_prefix` — **required**

**Constraints:** `const`=`oq_computational/oq_configuration_eshm20_v12e_region_main/`

#### `efehrKosovoExposureProfile`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `source_issue`, `dataset_id`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `receipt_comment_id`, `receipt_execution_sha`, `byte_count`, `sha256`, `profiled_at`, `profile`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** `const`=`316789`

###### `commit_sha` — **required**

**Constraints:** `const`=`900433ada80fbb424c0976c34d72eeef97bab1af`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `profile` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `parser`, `record_count`, `header`, `columns`, `raw_rows_returned`, `external_bytes_persisted`, `publication_authorized`

###### Properties

###### `columns` — **required**

**Constraints:** type=`array`; `minItems`=`2`; `maxItems`=`128`

###### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `name`, `record_count`, `empty_count`, `nonempty_count`, `distinct_count`, `exact_value_set_sha256`, `decimal_summary`

###### Properties

###### `decimal_summary` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `all_nonempty_decimal`, `finite_decimal_count`, `leading_or_trailing_whitespace_count`

###### Properties

###### `all_nonempty_decimal` — **required**

**Constraints:** type=`boolean`

###### `finite_decimal_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`316789`

###### `leading_or_trailing_whitespace_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`316789`

###### `distinct_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`316789`

###### `empty_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`316789`

###### `exact_value_set_sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `name` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`256`

###### `nonempty_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`316789`

###### `record_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`316789`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `header` — **required**

**Constraints:** type=`array`; `minItems`=`2`; `maxItems`=`128`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`256`

###### `parser` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `encoding`, `bom_present`, `delimiter`, `line_endings`

###### Properties

###### `bom_present` — **required**

**Constraints:** type=`boolean`

###### `delimiter` — **required**

**Constraints:** `const`=`,`

###### `encoding` — **required**

**Constraints:** `enum`=`["utf-8","utf-8-sig"]`

###### `line_endings` — **required**

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `crlf_count`, `lf_count`, `cr_count`

###### Properties

###### `cr_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`316789`

###### `crlf_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`316789`

###### `lf_count` — **required**

**Constraints:** type=`integer`; `minimum`=`0`; `maximum`=`316789`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `raw_rows_returned` — **required**

**Constraints:** `const`=`false`

###### `record_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`316789`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-esrm20-exposure-content-profile-v0`

###### `profiled_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `project_id` — **required**

**Constraints:** `const`=`186`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20_exposure`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `receipt_comment_id` — **required**

**Constraints:** `const`=`5300981864`

###### `receipt_execution_sha` — **required**

**Constraints:** `const`=`46d054930025553ad19d8b05fff9018dc2a49b5f`

###### `repository_path` — **required**

**Constraints:** `const`=`_exposure_models/Exposure_Model_Kosovo_Res.csv`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-esrm20-exposure-content-profile-v0`

###### `sha256` — **required**

**Constraints:** `const`=`4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea`

###### `source_issue` — **required**

**Constraints:** `const`=`282`

#### `efehrKosovoExposureReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `requested_url`, `final_url`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `etag`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`67108864`

###### `commit_sha` — **required**

**Constraints:** `const`=`900433ada80fbb424c0976c34d72eeef97bab1af`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `final_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/186/repository/files/_exposure_models%2FExposure_Model_Kosovo_Res.csv/raw?ref=900433ada80fbb424c0976c34d72eeef97bab1af`

###### `operation_id` — **required**

**Constraints:** `const`=`esrm20-kosovo-residential-exposure-v1`

###### `project_id` — **required**

**Constraints:** `const`=`186`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20_exposure`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`_exposure_models/Exposure_Model_Kosovo_Res.csv`

###### `requested_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/186/repository/files/_exposure_models%2FExposure_Model_Kosovo_Res.csv/raw?ref=900433ada80fbb424c0976c34d72eeef97bab1af`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-trusted-acquisition-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`282`

#### `efehrKosovoTaxonomyIdentity`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `control_issue`, `worker_identity`, `retrieved_at`, `source_issue`, `dataset_id`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `receipt_comment_id`, `receipt_execution_sha`, `source_byte_count`, `source_sha256`, `taxonomy_field`, `taxonomy_count`, `taxonomy_artifact_representation`, `taxonomy_artifact_byte_count`, `taxonomy_artifact_sha256`, `taxonomy_values_returned`, `normalization_applied`, `raw_rows_returned`, `external_bytes_persisted`, `derived_artifact_persisted`, `publication_authorized`

##### Properties

###### `commit_sha` — **required**

**Constraints:** `const`=`900433ada80fbb424c0976c34d72eeef97bab1af`

###### `control_issue` — **required**

**Constraints:** `const`=`363`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `derived_artifact_persisted` — **required**

**Constraints:** `const`=`false`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `normalization_applied` — **required**

**Constraints:** `const`=`false`

###### `operation_id` — **required**

**Constraints:** `const`=`esrm20-kosovo-residential-taxonomy-identity-v1`

###### `project_id` — **required**

**Constraints:** `const`=`186`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20_exposure`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `raw_rows_returned` — **required**

**Constraints:** `const`=`false`

###### `receipt_comment_id` — **required**

**Constraints:** `const`=`5300981864`

###### `receipt_execution_sha` — **required**

**Constraints:** `const`=`46d054930025553ad19d8b05fff9018dc2a49b5f`

###### `repository_path` — **required**

**Constraints:** `const`=`_exposure_models/Exposure_Model_Kosovo_Res.csv`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-esrm20-kosovo-taxonomy-artifact-identity-v1`

###### `source_byte_count` — **required**

**Constraints:** `const`=`316789`

###### `source_issue` — **required**

**Constraints:** `const`=`282`

###### `source_sha256` — **required**

**Constraints:** `const`=`4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea`

###### `taxonomy_artifact_byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`774`; `maximum`=`316789`

###### `taxonomy_artifact_representation` — **required**

**Constraints:** `const`=`oc-taxonomy-u64be-utf8-sorted-v1`

###### `taxonomy_artifact_sha256` — **required**

**Constraints:** `const`=`d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945`

###### `taxonomy_count` — **required**

**Constraints:** `const`=`86`

###### `taxonomy_field` — **required**

**Constraints:** `const`=`TAXONOMY`

###### `taxonomy_values_returned` — **required**

**Constraints:** `const`=`false`

###### `worker_identity` — **required**

**Constraints:** `const`=`scripts.extract_efehr_kosovo_taxonomy.extract_verified_kosovo_taxonomy`

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

#### `eshm20Dependency`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `section`, `option`, `raw_path`, `resolved_path`

##### Properties

###### `option` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `raw_path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `resolved_path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `section` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

#### `esrm20EventHazardGroup1Receipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `requested_url`, `final_url`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `etag`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1048576`

###### `commit_sha` — **required**

**Constraints:** `const`=`05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `final_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/Configuration_files%2Fconfig_event_hazard_Group1.ini/raw?ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `operation_id` — **required**

**Constraints:** `const`=`esrm20-event-hazard-group1-config-v1`

###### `project_id` — **required**

**Constraints:** `const`=`269`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`Configuration_files/config_event_hazard_Group1.ini`

###### `requested_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/Configuration_files%2Fconfig_event_hazard_Group1.ini/raw?ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-trusted-acquisition-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `esrm20EventHazardGroup2Receipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `requested_url`, `final_url`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `etag`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1048576`

###### `commit_sha` — **required**

**Constraints:** `const`=`05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `final_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/Configuration_files%2Fconfig_event_hazard_Group2.ini/raw?ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `operation_id` — **required**

**Constraints:** `const`=`esrm20-event-hazard-group2-config-v1`

###### `project_id` — **required**

**Constraints:** `const`=`269`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`Configuration_files/config_event_hazard_Group2.ini`

###### `requested_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/Configuration_files%2Fconfig_event_hazard_Group2.ini/raw?ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-trusted-acquisition-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`281`

#### `esrm20ExposureVulnerabilityMappingHeaders`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `control_issue`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `receipt_comment_id`, `receipt_run_id`, `receipt_execution_sha`, `header_source_commit`, `header_path`, `header_function`, `header_git_blob_sha1`, `retrieved_at`, `disclosure`, `raw_bytes_returned`, `external_bytes_persisted`, `derived_bytes_persisted`, `publication_authorized`, `mapping_interpretation_authorized`, `taxonomy_join_authorized`, `vulnerability_selection_authorized`, `model_use_authorized`

##### Properties

###### `commit_sha` — **required**

**Constraints:** `const`=`05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `control_issue` — **required**

**Constraints:** `const`=`410`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `derived_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `disclosure` — **required**

**Constraints:** `$ref`=`#/$defs/esrm20ExposureVulnerabilityMappingHeadersDisclosure`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `header_function` — **required**

**Constraints:** `const`=`disclose_verified_mapping_headers`

###### `header_git_blob_sha1` — **required**

**Constraints:** `const`=`cd0aa5cb573dbd8db431ef27b6a762c0a1d54c7c`

###### `header_path` — **required**

**Constraints:** `const`=`scripts/profile_efehr_esrm20_mapping_headers.py`

###### `header_source_commit` — **required**

**Constraints:** `const`=`e54b1f7a6220bafc67da540a57ed6fc7f6534e28`

###### `mapping_interpretation_authorized` — **required**

**Constraints:** `const`=`false`

###### `model_use_authorized` — **required**

**Constraints:** `const`=`false`

###### `operation_id` — **required**

**Constraints:** `const`=`esrm20-exposure-vulnerability-mapping-header-disclosure-v1`

###### `project_id` — **required**

**Constraints:** `const`=`269`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `raw_bytes_returned` — **required**

**Constraints:** `const`=`false`

###### `receipt_comment_id` — **required**

**Constraints:** `const`=`5303466667`

###### `receipt_execution_sha` — **required**

**Constraints:** `const`=`9b1bb7127138247cf613dbf444d139c189c9b13a`

###### `receipt_run_id` — **required**

**Constraints:** `const`=`31899242278`

###### `repository_path` — **required**

**Constraints:** `const`=`Vulnerability/esrm20_exposure_vulnerability_mapping.csv`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-esrm20-mapping-header-acquisition-v1`

###### `source_issue` — **required**

**Constraints:** `const`=`283`

###### `taxonomy_join_authorized` — **required**

**Constraints:** `const`=`false`

###### `vulnerability_selection_authorized` — **required**

**Constraints:** `const`=`false`

#### `esrm20ExposureVulnerabilityMappingHeadersDisclosure`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `decision_issue`, `source_issue`, `profile_issue`, `dataset_id`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `receipt_comment_id`, `receipt_run_id`, `receipt_execution_sha`, `byte_count`, `sha256`, `column_count`, `ordered_header_sha256`, `headers`, `disclosure_scope`, `header_strings_returned`, `cell_values_returned`, `raw_rows_returned`, `normalization_applied`, `mapping_interpretation_authorized`, `taxonomy_join_authorized`, `vulnerability_selection_authorized`, `external_bytes_persisted`, `derived_bytes_persisted`, `publication_authorized`, `model_use_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** `const`=`83585`

###### `cell_values_returned` — **required**

**Constraints:** `const`=`false`

###### `column_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`256`

###### `commit_sha` — **required**

**Constraints:** `const`=`05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `decision_issue` — **required**

**Constraints:** `const`=`410`

###### `derived_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `disclosure_scope` — **required**

**Constraints:** `const`=`exact_header_strings_only`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `header_strings_returned` — **required**

**Constraints:** `const`=`true`

###### `headers` — **required**

**Constraints:** type=`array`; `minItems`=`1`; `maxItems`=`256`; `uniqueItems`=`true`

###### Array items

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

###### `mapping_interpretation_authorized` — **required**

**Constraints:** `const`=`false`

###### `model_use_authorized` — **required**

**Constraints:** `const`=`false`

###### `normalization_applied` — **required**

**Constraints:** `const`=`false`

###### `ordered_header_sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `profile_issue` — **required**

**Constraints:** `const`=`404`

###### `project_id` — **required**

**Constraints:** `const`=`269`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `raw_rows_returned` — **required**

**Constraints:** `const`=`false`

###### `receipt_comment_id` — **required**

**Constraints:** `const`=`5303466667`

###### `receipt_execution_sha` — **required**

**Constraints:** `const`=`9b1bb7127138247cf613dbf444d139c189c9b13a`

###### `receipt_run_id` — **required**

**Constraints:** `const`=`31899242278`

###### `repository_path` — **required**

**Constraints:** `const`=`Vulnerability/esrm20_exposure_vulnerability_mapping.csv`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-esrm20-mapping-header-disclosure-v1`

###### `sha256` — **required**

**Constraints:** `const`=`94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c`

###### `source_issue` — **required**

**Constraints:** `const`=`283`

###### `taxonomy_join_authorized` — **required**

**Constraints:** `const`=`false`

###### `vulnerability_selection_authorized` — **required**

**Constraints:** `const`=`false`

#### `esrm20ExposureVulnerabilityMappingReceipt`

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `operation_id`, `source_issue`, `dataset_id`, `provider_host`, `project_id`, `project_path`, `commit_sha`, `repository_path`, `requested_url`, `final_url`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `etag`, `external_bytes_persisted`, `publication_authorized`

##### Properties

###### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1048576`

###### `commit_sha` — **required**

**Constraints:** `const`=`05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `dataset_id` — **required**

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

###### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

###### `final_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/Vulnerability%2Fesrm20_exposure_vulnerability_mapping.csv/raw?ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `operation_id` — **required**

**Constraints:** `const`=`esrm20-exposure-vulnerability-mapping-v1`

###### `project_id` — **required**

**Constraints:** `const`=`269`

###### `project_path` — **required**

**Constraints:** `const`=`efehr/esrm20`

###### `provider_host` — **required**

**Constraints:** `const`=`gitlab.seismo.ethz.ch`

###### `publication_authorized` — **required**

**Constraints:** `const`=`false`

###### `repository_path` — **required**

**Constraints:** `const`=`Vulnerability/esrm20_exposure_vulnerability_mapping.csv`

###### `requested_url` — **required**

**Constraints:** `const`=`https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/Vulnerability%2Fesrm20_exposure_vulnerability_mapping.csv/raw?ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783`

###### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

###### `schema_version` — **required**

**Constraints:** `const`=`oc-efehr-trusted-acquisition-v1`

###### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

###### `source_issue` — **required**

**Constraints:** `const`=`283`

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

###### Branch 4

###### not

**Required here:** `efehr_eshm20_tree_metadata`

###### Branch 5

###### not

**Required here:** `efehr_kosovo_exposure_receipt`

###### Branch 6

###### not

**Required here:** `efehr_kosovo_exposure_profile`

###### Branch 7

###### not

**Required here:** `efehr_eshm20_root_config_receipt`

###### Branch 8

###### not

**Required here:** `esrm20_event_hazard_group1_receipt`

###### Branch 9

###### not

**Required here:** `esrm20_event_hazard_group2_receipt`

###### Branch 10

###### not

**Required here:** `efehr_eshm20_root_dependency_profile`

###### Branch 11

###### not

**Required here:** `efehr_eshm20_first_order_receipts`

###### Branch 12

###### not

**Required here:** `efehr_eshm20_gsim_resource_profile`

###### Branch 13

###### not

**Required here:** `efehr_kosovo_taxonomy_identity`

###### Branch 14

###### not

**Required here:** `efehr_eshm20_source_model_dependencies`

###### Branch 15

###### not

**Required here:** `efehr_eshm20_source_model_child_receipts`

###### Branch 16

###### not

**Required here:** `esrm20_exposure_vulnerability_mapping_receipt`

###### Branch 17

###### not

**Required here:** `esrm20_exposure_vulnerability_mapping_headers`

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

**Constraints:** `enum`=`["acquisition_receipt","dwd_metadata_receipt","efehr_readme_receipt","efehr_eshm20_tree_metadata","efehr_eshm20_root_config_receipt","efehr_kosovo_exposure_receipt","esrm20_event_hazard_group1_receipt","esrm20_event_hazard_group2_receipt","efehr_kosovo_exposure_profile","efehr_eshm20_root_dependency_profile","efehr_eshm20_first_order_receipts","efehr_eshm20_gsim_resource_profile","efehr_kosovo_taxonomy_identity","esrm20_exposure_vulnerability_mapping_receipt","esrm20_exposure_vulnerability_mapping_headers","efehr_eshm20_source_model_dependencies","efehr_eshm20_source_model_child_receipts"]`

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

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_tree_metadata`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `evidence`

**Required here:** `efehr_eshm20_tree_metadata`

###### `source_issue`

**Constraints:** `const`=`332`

#### Branch 10

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `evidence`

**Required here:** `efehr_kosovo_exposure_receipt`

###### `source_issue`

**Constraints:** `const`=`328`

#### Branch 11

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_profile`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `evidence`

**Required here:** `efehr_kosovo_exposure_profile`

###### `source_issue`

**Constraints:** `const`=`351`

#### Branch 12

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_config_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `evidence`

**Required here:** `efehr_eshm20_root_config_receipt`

###### `source_issue`

**Constraints:** `const`=`335`

#### Branch 13

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group1_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `evidence`

**Required here:** `esrm20_event_hazard_group1_receipt`

###### `source_issue`

**Constraints:** `const`=`346`

#### Branch 14

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group2_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `evidence`

**Required here:** `esrm20_event_hazard_group2_receipt`

###### `source_issue`

**Constraints:** `const`=`346`

#### Branch 15

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_dependency_profile`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `evidence`

**Required here:** `efehr_eshm20_root_dependency_profile`

###### `source_issue`

**Constraints:** `const`=`353`

#### Branch 16

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_gsim_resource_profile`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `evidence`

**Required here:** `efehr_eshm20_gsim_resource_profile`

###### `source_issue`

**Constraints:** `const`=`376`

#### Branch 17

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_exposure_vulnerability_mapping_headers`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `evidence`

**Required here:** `esrm20_exposure_vulnerability_mapping_headers`

###### `source_issue`

**Constraints:** `const`=`410`

#### Branch 18

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

#### Branch 19

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

#### Branch 20

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

#### Branch 21

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_tree_metadata`

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

###### `efehr_eshm20_tree_metadata`

**Constraints:** `$ref`=`#/$defs/efehrEshm20TreeMetadata`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 22

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_receipt`

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

###### `efehr_kosovo_exposure_receipt`

**Constraints:** `$ref`=`#/$defs/efehrKosovoExposureReceipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 23

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_profile`

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

###### `efehr_kosovo_exposure_profile`

**Constraints:** `$ref`=`#/$defs/efehrKosovoExposureProfile`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 24

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_config_receipt`

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

###### `efehr_eshm20_root_config_receipt`

**Constraints:** `$ref`=`#/$defs/efehrEshm20RootConfigReceipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 25

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group1_receipt`

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

###### `esrm20_event_hazard_group1_receipt`

**Constraints:** `$ref`=`#/$defs/esrm20EventHazardGroup1Receipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 26

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group2_receipt`

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

###### `esrm20_event_hazard_group2_receipt`

**Constraints:** `$ref`=`#/$defs/esrm20EventHazardGroup2Receipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 27

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_dependency_profile`

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

###### `efehr_eshm20_root_dependency_profile`

**Constraints:** `$ref`=`#/$defs/efehrEshm20RootDependencyProfile`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 28

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_gsim_resource_profile`

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

###### `efehr_eshm20_gsim_resource_profile`

**Constraints:** `$ref`=`#/$defs/efehrEshm20GsimResourceProfile`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 29

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_exposure_vulnerability_mapping_headers`

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

###### `esrm20_exposure_vulnerability_mapping_headers`

**Constraints:** `$ref`=`#/$defs/esrm20ExposureVulnerabilityMappingHeaders`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 30

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

#### Branch 31

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

#### Branch 32

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

#### Branch 33

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_tree_metadata`

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

###### `efehr_eshm20_tree_metadata`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 34

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_receipt`

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

###### `efehr_kosovo_exposure_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 35

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_exposure_profile`

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

###### `efehr_kosovo_exposure_profile`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 36

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_config_receipt`

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

###### `efehr_eshm20_root_config_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 37

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group1_receipt`

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

###### `esrm20_event_hazard_group1_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 38

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_root_dependency_profile`

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

###### `efehr_eshm20_root_dependency_profile`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 39

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_event_hazard_group2_receipt`

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

###### `esrm20_event_hazard_group2_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 40

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_first_order_receipts`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `evidence`

**Required here:** `efehr_eshm20_first_order_receipts`

###### `source_issue`

**Constraints:** `const`=`361`

#### Branch 41

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_first_order_receipts`

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

###### `efehr_eshm20_first_order_receipts`

**Constraints:** `$ref`=`#/$defs/efehrEshm20FirstOrderReceiptSet`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 42

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_first_order_receipts`

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

###### `efehr_eshm20_first_order_receipts`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 43

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_gsim_resource_profile`

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

###### `efehr_eshm20_gsim_resource_profile`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 44

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_exposure_vulnerability_mapping_receipt`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.risk-inputs.v1.0`

###### `evidence`

**Required here:** `esrm20_exposure_vulnerability_mapping_receipt`

###### `source_issue`

**Constraints:** `const`=`340`

#### Branch 45

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_exposure_vulnerability_mapping_receipt`

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

###### `esrm20_exposure_vulnerability_mapping_receipt`

**Constraints:** `$ref`=`#/$defs/esrm20ExposureVulnerabilityMappingReceipt`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 46

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_exposure_vulnerability_mapping_receipt`

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

###### `esrm20_exposure_vulnerability_mapping_receipt`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 47

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`esrm20_exposure_vulnerability_mapping_headers`

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

###### `esrm20_exposure_vulnerability_mapping_headers`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 48

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_taxonomy_identity`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.esrm20.european-exposure-model.v1.0`

###### `evidence`

**Required here:** `efehr_kosovo_taxonomy_identity`

###### `source_issue`

**Constraints:** `const`=`363`

#### Branch 49

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_taxonomy_identity`

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

###### `efehr_kosovo_taxonomy_identity`

**Constraints:** `$ref`=`#/$defs/efehrKosovoTaxonomyIdentity`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 50

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_kosovo_taxonomy_identity`

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

###### `efehr_kosovo_taxonomy_identity`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 51

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_dependencies`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `evidence`

**Required here:** `efehr_eshm20_source_model_dependencies`

###### `source_issue`

**Constraints:** `const`=`397`

#### Branch 52

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_dependencies`

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

###### `efehr_eshm20_source_model_dependencies`

**Constraints:** `$ref`=`#/$defs/efehrEshm20SourceModelDependencies`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 53

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_dependencies`

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

###### `efehr_eshm20_source_model_dependencies`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`

#### Branch 54

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_child_receipts`

###### `phase` — **required**

**Constraints:** `const`=`acquisition_receipt`

##### then

**Constraints:** type=`object (implicit)`

###### Properties

###### `dataset_id`

**Constraints:** `const`=`efehr.eshm20`

###### `evidence`

**Required here:** `efehr_eshm20_source_model_child_receipts`

###### `source_issue`

**Constraints:** `const`=`414`

#### Branch 55

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_child_receipts`

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

###### `efehr_eshm20_source_model_child_receipts`

**Constraints:** `$ref`=`#/$defs/efehrEshm20SourceModelChildReceiptSet`

###### `failure_class`

**Constraints:** type=`null`

#### Branch 56

##### if

**Constraints:** type=`object (implicit)`

**Required here:** `phase`, `action`, `status`

###### Properties

###### `action` — **required**

**Constraints:** `const`=`efehr_eshm20_source_model_child_receipts`

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

###### `efehr_eshm20_source_model_child_receipts`

**Constraints:** type=`null`

###### `failure_class`

**Constraints:** `const`=`acquisition_failed`
