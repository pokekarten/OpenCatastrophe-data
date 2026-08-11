<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/acquisition-receipt-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `acquisition-receipt-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:acquisition-receipt:1.0.0

**Title:** OpenCatastrophe Acquisition Receipt v1

**Description:** Strict metadata-only evidence for one bounded ephemeral source acquisition. This receipt is not publication authorization and does not persist provider bytes.

**Type:** object

**Additionalproperties:** `false`

## Required

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

## Properties

### Schema version

**Const:** oc-acquisition-receipt-v1

### Dataset id

**Const:** dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03

### Source issue

**Const:** `162`

### Requested url

**Const:** <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip>

### Final url

**Const:** <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip>

### Filename

**Const:** 10minutenwerte_extrema_wind_00003_20100101_20110331_hist.zip

### Retrieved at

**Type:** string

**Format:** date-time

**Pattern:** Z$

### Byte count

**Type:** integer

**Minimum:** `1`

**Maximum:** `52428800`

### Sha256

**Type:** string

**Pattern:** ^\[a-f0-9\]\{64\}$

### Content type

#### Type

- string
- null

**Maxlength:** `512`

### Last modified

#### Type

- string
- null

**Maxlength:** `512`

### Etag

#### Type

- string
- null

**Maxlength:** `512`

### Archive member count

**Type:** integer

**Minimum:** `1`

**Maximum:** `32`

### Archive uncompressed bytes

**Type:** integer

**Minimum:** `1`

**Maximum:** `104857600`

### Product member

**Type:** string

**Minlength:** `1`

**Maxlength:** `512`

**Pattern:** (^\|/)produkt_extrema_wind_\[^/\]+\\.txt$

### Product station id

**Const:** 00003

### Product begin date

**Const:** 20100101

### Product end date

**Const:** 20110331

### Product row count

**Type:** integer

**Minimum:** `1`

**Maximum:** `1000000`

### Product structure validated

**Const:** `true`

### External bytes persisted

**Const:** `false`

### Publication authorized

**Const:** `false`
