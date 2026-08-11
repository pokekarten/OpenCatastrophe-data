<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/agent-action-result-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `agent-action-result-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:agent-action-result:1.0.0

**Title:** OpenCatastrophe Agent Action Result v1

**Description:** Portable closed result receipt for the owner-authorized trusted-main Agent Action Dispatch control plane. scripts/validate_agent_action_result.py is authoritative for exact Python scalar types, UTC ordering, acquisition-receipt identity and cross-field checks.

**$comment:** request_validation records strict validation/dedup state. acquisition_receipt is allowed only for Issue 162 and the frozen DWD dataset, carries metadata-only evidence from the trusted repository-owned worker, and always requires external_bytes_persisted=false.

**Type:** object

**Additional properties:** `false`

## Required

- schema_version
- semantic_request_id
- repository
- action
- source_issue
- source_comment_id
- target_sha
- dataset_id
- execution_sha
- run_id
- run_attempt
- started_at
- finished_at
- phase
- status
- external_bytes_persisted
- evidence
- duplicate_result_comment_id
- failure_class

## Properties

### Schema version

**Const:** oc-action-result-v1

### Semantic request id

**Type:** string

**Pattern:** ^\[a-f0-9\]\{64\}$

### Repository

**Type:** string

**Pattern:** ^\[A-Za-z0-9-\]+/\[A-Za-z0-9._-\]+$

### Action

#### Enum

- sample_audit
- acquisition_receipt

### Source issue

**Type:** integer

**Minimum:** `1`

### Source comment id

**Type:** integer

**Minimum:** `1`

### Target sha

**Type:** string

**Pattern:** ^\[a-f0-9\]\{40\}$

### Dataset id

**Type:** string

**Min length:** `1`

**Max length:** `160`

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._:-\]\*$

### Execution sha

**Type:** string

**Pattern:** ^\[a-f0-9\]\{40\}$

### Run id

**Type:** integer

**Minimum:** `1`

### Run attempt

**Type:** integer

**Minimum:** `1`

### Started at

**Type:** string

**Pattern:** ^\\d\{4\}-\\d\{2\}-\\d\{2\}T\\d\{2\}:\\d\{2\}:\\d\{2\}Z$

### Finished at

**Type:** string

**Pattern:** ^\\d\{4\}-\\d\{2\}-\\d\{2\}T\\d\{2\}:\\d\{2\}:\\d\{2\}Z$

### Phase

#### Enum

- request_validation
- acquisition_receipt

### Status

#### Enum

- pass
- duplicate
- blocked

### External bytes persisted

**Const:** `false`

### Evidence

#### One of

##### Item 1

**Type:** object

**Additional properties:** `false`

###### Required

- request_validated
- ledger_scan_complete
- prior_result_reused

###### Properties

###### Request validated

**Const:** `true`

###### Ledger scan complete

**Type:** boolean

###### Prior result reused

**Type:** boolean

##### Item 2

**Type:** object

**Additional properties:** `false`

###### Required

- request_validated
- ledger_scan_complete
- prior_result_reused
- acquisition_receipt

###### Properties

###### Request validated

**Const:** `true`

###### Ledger scan complete

**Const:** `true`

###### Prior result reused

**Const:** `false`

###### Acquisition receipt

###### Any of

###### Item 1

**Type:** null

###### Item 2

**$ref:** \#/$defs/acquisitionReceipt



### Duplicate result comment id

#### Type

- integer
- null

**Minimum:** `1`

### Failure class

#### Type

- string
- null

#### Enum

- `null`
- duplicate_request
- ledger_incomplete
- acquisition_failed

## $defs

### Acquisition receipt

**Type:** object

**Additional properties:** `false`

#### Required

- schema_version
- dataset_id
- source_issue
- requested_url
- final_url
- filename
- retrieved_at
- byte_count
- sha256
- content_type
- last_modified
- etag
- archive_member_count
- archive_uncompressed_bytes
- product_member
- product_station_id
- product_begin_date
- product_end_date
- product_row_count
- product_structure_validated
- external_bytes_persisted
- publication_authorized

#### Properties

##### Schema version

**Const:** oc-acquisition-receipt-v1

##### Dataset id

**Const:** dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03

##### Source issue

**Const:** `162`

##### Requested url

**Const:** <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip>

##### Final url

**Const:** <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip>

##### Filename

**Const:** 10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip

##### Retrieved at

**Type:** string

**Pattern:** ^\\d\{4\}-\\d\{2\}-\\d\{2\}T\\d\{2\}:\\d\{2\}:\\d\{2\}Z$

##### Byte count

**Type:** integer

**Minimum:** `1`

**Maximum:** `52428800`

##### Sha256

**Type:** string

**Pattern:** ^\[a-f0-9\]\{64\}$

##### Content type

###### Type

- string
- null

**Max length:** `512`

##### Last modified

###### Type

- string
- null

**Max length:** `512`

##### Etag

###### Type

- string
- null

**Max length:** `512`

##### Archive member count

**Type:** integer

**Minimum:** `1`

**Maximum:** `32`

##### Archive uncompressed bytes

**Type:** integer

**Minimum:** `1`

**Maximum:** `104857600`

##### Product member

**Type:** string

**Min length:** `1`

**Max length:** `512`

**Pattern:** (^\|/)produkt_extrema_wind_\[^/\]+\\.txt$

##### Product station id

**Const:** 00003

##### Product begin date

**Const:** 20100101

##### Product end date

**Const:** 20110331

##### Product row count

**Type:** integer

**Minimum:** `1`

**Maximum:** `1000000`

##### Product structure validated

**Const:** `true`

##### External bytes persisted

**Const:** `false`

##### Publication authorized

**Const:** `false`

## All of

### Item 1

#### If

##### Properties

###### Phase

**Const:** request_validation

##### Required

- phase

#### Then

##### Properties

###### Evidence

###### Not

###### Required

- acquisition_receipt

### Item 2

#### If

##### Properties

###### Phase

**Const:** request_validation

###### Status

**Const:** pass

##### Required

- phase
- status

#### Then

##### Properties

###### Evidence

###### Properties

###### Ledger scan complete

**Const:** `true`

###### Prior result reused

**Const:** `false`

###### Duplicate result comment id

**Type:** null

###### Failure class

**Type:** null

### Item 3

#### If

##### Properties

###### Status

**Const:** duplicate

##### Required

- status

#### Then

##### Properties

###### Phase

**Const:** request_validation

###### Evidence

###### Properties

###### Ledger scan complete

**Const:** `true`

###### Prior result reused

**Const:** `true`

###### Duplicate result comment id

**Type:** integer

**Minimum:** `1`

###### Failure class

**Const:** duplicate_request

### Item 4

#### If

##### Properties

###### Phase

**Const:** request_validation

###### Status

**Const:** blocked

##### Required

- phase
- status

#### Then

##### Properties

###### Evidence

###### Properties

###### Ledger scan complete

**Const:** `false`

###### Prior result reused

**Const:** `false`

###### Duplicate result comment id

**Type:** null

###### Failure class

**Const:** ledger_incomplete

### Item 5

#### If

##### Properties

###### Phase

**Const:** acquisition_receipt

##### Required

- phase

#### Then

##### Properties

###### Action

**Const:** acquisition_receipt

###### Source issue

**Const:** `162`

###### Dataset id

**Const:** dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03

###### Duplicate result comment id

**Type:** null

###### Evidence

###### Required

- acquisition_receipt

### Item 6

#### If

##### Properties

###### Phase

**Const:** acquisition_receipt

###### Status

**Const:** pass

##### Required

- phase
- status

#### Then

##### Properties

###### Evidence

###### Required

- acquisition_receipt

###### Properties

###### Acquisition receipt

**$ref:** \#/$defs/acquisitionReceipt

###### Failure class

**Type:** null

### Item 7

#### If

##### Properties

###### Phase

**Const:** acquisition_receipt

###### Status

**Const:** blocked

##### Required

- phase
- status

#### Then

##### Properties

###### Evidence

###### Required

- acquisition_receipt

###### Properties

###### Acquisition receipt

**Type:** null

###### Failure class

**Const:** acquisition_failed
