<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/dwd-metadata-receipt-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe DWD Metadata Receipt v1

> This file is a deterministic human-readable projection of `schemas/dwd-metadata-receipt-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/dwd-metadata-receipt-v1.schema.json`](dwd-metadata-receipt-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:dwd-metadata-receipt:1.0.0`  

Portable closed evidence contract for one ephemeral acquisition of the frozen station-00003 DWD extreme-wind metadata ZIP. It proves byte identity, safe archive/member inventory and required provider-native metadata-family presence; it does not prove temporal validity coverage, scientific fitness, admission or publication authority.

**Authority note:** The canonical JSON Schema governs portable structure; repository Python validators may impose additional fail-closed semantic or security checks where documented.

## Contract structure

Portable closed evidence contract for one ephemeral acquisition of the frozen station-00003 DWD extreme-wind metadata ZIP. It proves byte identity, safe archive/member inventory and required provider-native metadata-family presence; it does not prove temporal validity coverage, scientific fitness, admission or publication authority.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `dataset_id`, `source_issue`, `requested_url`, `final_url`, `filename`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `last_modified`, `etag`, `archive_member_count`, `archive_uncompressed_bytes`, `station_id`, `required_metadata_families`, `metadata_members`, `temporal_coverage_status`, `external_bytes_persisted`, `publication_authorized`

### Properties

#### `archive_member_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`128`

#### `archive_uncompressed_bytes` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`20971520`

#### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`5242880`

#### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

#### `dataset_id` — **required**

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

#### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

#### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

#### `filename` — **required**

**Constraints:** `const`=`Meta_Daten_zehn_min_fx_00003.zip`

#### `final_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/meta_data/Meta_Daten_zehn_min_fx_00003.zip`

#### `last_modified` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

#### `metadata_members` — **required**

**Constraints:** type=`array`; `minItems`=`3`; `maxItems`=`128`

##### Array items

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `path`, `family`

###### Properties

###### `family` — **required**

**Constraints:** `enum`=`["equipment","geography","parameter"]`

###### `path` — **required**

**Constraints:** type=`string`; `minLength`=`1`; `maxLength`=`512`

#### `publication_authorized` — **required**

**Constraints:** `const`=`false`

#### `requested_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/meta_data/Meta_Daten_zehn_min_fx_00003.zip`

#### `required_metadata_families` — **required**

**Constraints:** type=`array`; `const`=`["equipment","geography","parameter"]`

#### `retrieved_at` — **required**

**Constraints:** type=`string`; `pattern`=`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

#### `schema_version` — **required**

**Constraints:** `const`=`oc-dwd-metadata-receipt-v1`

#### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

#### `source_issue` — **required**

**Constraints:** `const`=`211`

#### `station_id` — **required**

**Constraints:** `const`=`00003`

#### `temporal_coverage_status` — **required**

**Constraints:** `const`=`unverified`
