<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/acquisition-receipt-v1.schema.json
Renderer: scripts/schema_reference.py
Change the canonical JSON Schema and run `python scripts/schema_reference.py --write`.
-->

# OpenCatastrophe Acquisition Receipt v1

> This file is a deterministic human-readable projection of `schemas/acquisition-receipt-v1.schema.json`. The canonical JSON Schema remains authoritative; this view does not change validation, security, rights, admission or scientific semantics.

**Canonical schema:** [`schemas/acquisition-receipt-v1.schema.json`](acquisition-receipt-v1.schema.json)  
**JSON Schema dialect:** <https://json-schema.org/draft/2020-12/schema>  
**$id:** `urn:opencatastrophe:schema:acquisition-receipt:1.0.0`  

Strict metadata-only evidence for one bounded ephemeral source acquisition. This receipt is not publication authorization and does not persist provider bytes.

**Executable authority note:** product_member records the safe text member already selected and structurally validated by the trusted acquisition worker. scripts/validate_agent_action_result.py is authoritative for canonical relative POSIX path, dot-segment, backslash and control-character rejection; provider filename prefixes are not scientific identity.

## Contract structure

Strict metadata-only evidence for one bounded ephemeral source acquisition. This receipt is not publication authorization and does not persist provider bytes.

**Constraints:** type=`object`; `additionalProperties`=`false`

**Required here:** `schema_version`, `dataset_id`, `source_issue`, `requested_url`, `final_url`, `filename`, `retrieved_at`, `byte_count`, `sha256`, `content_type`, `last_modified`, `etag`, `archive_member_count`, `archive_uncompressed_bytes`, `product_member`, `product_station_id`, `product_begin_date`, `product_end_date`, `product_row_count`, `product_structure_validated`, `external_bytes_persisted`, `publication_authorized`

### Properties

#### `archive_member_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`32`

#### `archive_uncompressed_bytes` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`104857600`

#### `byte_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`52428800`

#### `content_type` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

#### `dataset_id` — **required**

**Constraints:** `const`=`dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03`

#### `etag` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

#### `external_bytes_persisted` — **required**

**Constraints:** `const`=`false`

#### `filename` — **required**

**Constraints:** `const`=`10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip`

#### `final_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip`

#### `last_modified` — **required**

**Constraints:** type=`string | null`; `maxLength`=`512`

#### `product_begin_date` — **required**

**Constraints:** `const`=`20100101`

#### `product_end_date` — **required**

**Constraints:** `const`=`20110331`

#### `product_member` — **required**

**Constraints:** type=`string`; `pattern`=`\.[Tt][Xx][Tt]$`; `minLength`=`1`; `maxLength`=`512`

#### `product_row_count` — **required**

**Constraints:** type=`integer`; `minimum`=`1`; `maximum`=`1000000`

#### `product_station_id` — **required**

**Constraints:** `const`=`00003`

#### `product_structure_validated` — **required**

**Constraints:** `const`=`true`

#### `publication_authorized` — **required**

**Constraints:** `const`=`false`

#### `requested_url` — **required**

**Constraints:** `const`=`https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip`

#### `retrieved_at` — **required**

**Constraints:** type=`string`; `format`=`date-time`; `pattern`=`Z$`

#### `schema_version` — **required**

**Constraints:** `const`=`oc-acquisition-receipt-v1`

#### `sha256` — **required**

**Constraints:** type=`string`; `pattern`=`^[a-f0-9]{64}$`

#### `source_issue` — **required**

**Constraints:** `const`=`162`
