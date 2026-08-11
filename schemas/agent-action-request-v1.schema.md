<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/agent-action-request-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `agent-action-request-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:agent-action-request:1.0.0

**Title:** OpenCatastrophe Agent Action Request v1

**Description:** Portable structural view of the closed request contract for a bounded trusted-main GitHub Actions evidence operation. scripts/validate_agent_action_request.py is authoritative for executable security policy that JSON Schema cannot fully express.

**$comment:** Draft 2020-12 treats zero-fraction JSON numbers such as 1.0 as integers. The executable validator additionally requires the parsed issue value to have exact int type (rejecting bool and float), rejects duplicate keys and non-finite JSON, enforces the single-marker comment envelope, and restricts acquisition_receipt to Issue 162 plus the frozen DWD dataset.

**Type:** object

**Additional properties:** `false`

## Required

- schema_version
- action
- issue
- target_sha
- dataset_id
- requester

## Properties

### Schema version

**Const:** oc-action-request-v1

### Action

#### Enum

- sample_audit
- acquisition_receipt

### Issue

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

### Requester

**Type:** string

**Min length:** `1`

**Max length:** `128`

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._:-\]\*$

## All of

### Item 1

#### If

##### Properties

###### Action

**Const:** acquisition_receipt

##### Required

- action

#### Then

##### Properties

###### Issue

**Const:** `162`

###### Dataset id

**Const:** dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03
