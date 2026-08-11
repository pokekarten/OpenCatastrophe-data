<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/source-access-v1.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `source-access-v1.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:source-access:1.0.0

**Title:** OpenCatastrophe Source Access Contract v1

**Description:** Portable structural view of the fail-closed contract for an authoritative machine-access route. scripts/validate_source_access.py is the executable security authority for URL/IP/secret/path and cross-field constraints that JSON Schema cannot fully express. Connectivity never implies rights clearance, scientific approval or data admission.

**$comment:** The executable validator additionally rejects duplicate JSON keys, non-finite values, non-ASCII/IDNA-uncanonical host forms, local/private/legacy-numeric hosts, secret-bearing or signed query URLs, invalid UTF-8 or decoded path traversal/backslashes/URL smuggling, and enforces the fail-closed rights/probe/endpoint/implementation state machine below. Runtime network workers must still re-resolve and validate DNS/redirect targets before connection.

**Type:** object

**Additionalproperties:** `false`

## Required

- schema_version
- access_id
- source_ids
- provider
- interface_type
- status
- documentation_url
- service_root
- api_version
- access_scope
- authentication
- request_contract
- response_contract
- operational_constraints
- rights_and_policy
- probe_contract
- implementation_decision
- reviewed_at
- evidence_urls
- notes

## $defs

### Httpsurl

**Type:** string

**Pattern:** ^https://(?\!\[^/?\#\]\*@)(?\!localhost(?:\[:/\]\|$))(?\!127\\.)(?\!10\\.)(?\!192\\.168\\.)(?\!169\\.254\\.)\[\\x21-\\x7E\]+$

### Nullablehttpsurl

#### Anyof

##### Item 1

**$ref:** \#/$defs/httpsUrl

##### Item 2

**Type:** null


### Nonblank

**Type:** string

**Pattern:** \\S

## Properties

### Schema version

**Const:** 1.0.0

### Access id

**Type:** string

**Pattern:** ^\[a-z0-9\]+(?:\[.-\]\[a-z0-9\]+)\*$

### Source ids

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

#### Items

**Type:** string

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._-\]\*$

### Provider

**$ref:** \#/$defs/nonBlank

### Interface type

**Type:** string

#### Enum

- rest
- fdsn
- ogc_api
- stac
- wms
- wfs
- wcs
- arcgis_rest
- mqtt_http
- object_store
- http_file
- ftp_or_ftps
- provider_sdk
- web_portal
- other_documented_machine_interface

### Status

**Type:** string

#### Enum

- documented_only
- probe_ready
- verified_anonymous
- verified_authenticated
- blocked_registration
- blocked_credentials
- restricted_by_terms
- deprecated
- rejected

### Documentation url

**$ref:** \#/$defs/httpsUrl

### Service root

**$ref:** \#/$defs/nullableHttpsUrl

### Api version

#### Type

- string
- null

### Access scope

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

#### Items

**Type:** string

##### Enum

- metadata
- catalogue
- sample
- bulk
- realtime
- other

### Authentication

**Type:** object

**Additionalproperties:** `false`

#### Required

- mode
- credential_reference
- registration_url
- secret_in_repository

#### Properties

##### Mode

**Type:** string

###### Enum

- none
- api_key
- bearer_token
- basic
- oauth2
- provider_account
- signed_request
- other

##### Credential reference

###### Type

- string
- null

**Pattern:** ^\[A-Z\]\[A-Z0-9_\]\{2,127\}$

##### Registration url

**$ref:** \#/$defs/nullableHttpsUrl

##### Secret in repository

**Const:** `false`

#### Allof

##### Item 1

###### If

###### Properties

###### Mode

**Const:** none

###### Required

- mode

###### Then

###### Properties

###### Credential reference

**Type:** null

##### Item 2

###### If

###### Properties

###### Mode

###### Enum

- api_key
- bearer_token
- basic
- oauth2
- signed_request

###### Required

- mode

###### Then

###### Properties

###### Credential reference

**Type:** string

**Pattern:** ^\[A-Z\]\[A-Z0-9_\]\{2,127\}$


### Request contract

**Type:** object

**Additionalproperties:** `false`

#### Required

- allowed_operations
- path_templates
- parameter_rules

#### Properties

##### Allowed operations

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

###### Items

**Type:** string

**Pattern:** ^\[a-z\]\[a-z0-9_\]\*$

##### Path templates

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

###### Items

**Type:** string

**Pattern:** ^/(?\!/)(?\!.\*\\\\)(?\!.\*(?:^\|/)\\.\\.?/)(?\!.\*%2\[eEfF\]\|%5\[cC\]\|%3\[fF\]\|%23)(?\!.\*://)(?\!.\*\[?\#\])\[^\\s\]\*$

##### Parameter rules

**$ref:** \#/$defs/nonBlank

### Response contract

**Type:** object

**Additionalproperties:** `false`

#### Required

- expected_media_types
- format
- scientific_semantics

#### Properties

##### Expected media types

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

###### Items

**Type:** string

**Pattern:** ^\[A-Za-z0-9.+-\]+/\[A-Za-z0-9.+-\]+$

##### Format

**$ref:** \#/$defs/nonBlank

##### Scientific semantics

**$ref:** \#/$defs/nonBlank

### Operational constraints

**Type:** object

**Additionalproperties:** `false`

#### Required

- timeout_seconds
- max_probe_bytes
- max_sample_bytes
- retry_policy
- rate_limit_notes
- mutability_notes

#### Properties

##### Timeout seconds

**Type:** integer

**Minimum:** `1`

**Maximum:** `120`

##### Max probe bytes

**Type:** integer

**Minimum:** `1`

**Maximum:** `5242880`

##### Max sample bytes

**Type:** integer

**Minimum:** `1`

**Maximum:** `52428800`

##### Retry policy

**Type:** string

###### Enum

- none
- bounded_backoff

##### Rate limit notes

**$ref:** \#/$defs/nonBlank

##### Mutability notes

**$ref:** \#/$defs/nonBlank

### Rights and policy

**Type:** object

**Additionalproperties:** `false`

#### Required

- dataset_rights_status
- api_terms_status
- terms_url
- commercial_automation_status
- redistribution_status
- notes

#### Properties

##### Dataset rights status

**Type:** string

###### Enum

- verified
- not_reviewed
- conflicting
- restricted
- prohibited
- unknown

##### Api terms status

**Type:** string

###### Enum

- same_as_dataset
- separate_reviewed
- separate_unreviewed
- unknown

##### Terms url

**$ref:** \#/$defs/nullableHttpsUrl

##### Commercial automation status

**Type:** string

###### Enum

- allowed
- restricted
- prohibited
- unknown

##### Redistribution status

**Type:** string

###### Enum

- allowed
- restricted
- prohibited
- unknown

##### Notes

**$ref:** \#/$defs/nonBlank

#### Allof

##### Item 1

###### If

###### Properties

###### Api terms status

**Const:** separate_reviewed

###### Required

- api_terms_status

###### Then

###### Properties

###### Terms url

**$ref:** \#/$defs/httpsUrl

##### Item 2

###### If

###### Properties

###### Api terms status

**Const:** same_as_dataset

###### Required

- api_terms_status

###### Then

###### Properties

###### Terms url

**$ref:** \#/$defs/httpsUrl


### Probe contract

**Type:** object

**Additionalproperties:** `false`

#### Required

- mode
- operation
- requires_credentials
- expected_evidence

#### Properties

##### Mode

**Type:** string

###### Enum

- none
- metadata_get
- head
- catalogue_query
- provider_specific

##### Operation

###### Type

- string
- null

##### Requires credentials

**Type:** boolean

##### Expected evidence

**Type:** array

###### Items

**$ref:** \#/$defs/nonBlank

### Implementation decision

**Type:** string

#### Enum

- build_adapter_now
- document_only
- build_later
- do_not_automate

### Reviewed at

**Type:** string

**Format:** date

**Pattern:** ^\\d\{4\}-\\d\{2\}-\\d\{2\}$

### Evidence urls

**Type:** array

**Minitems:** `1`

**Uniqueitems:** `true`

#### Items

**$ref:** \#/$defs/httpsUrl

### Notes

**$ref:** \#/$defs/nonBlank

## Allof

### Item 1

#### If

##### Properties

###### Rights and policy

###### Properties

###### Dataset rights status

###### Not

**Const:** verified

###### Required

- dataset_rights_status

#### Then

##### Properties

###### Rights and policy

###### Properties

###### Commercial automation status

###### Not

**Const:** allowed

###### Redistribution status

###### Not

**Const:** allowed

###### Probe contract

###### Properties

###### Mode

**Const:** none

###### Operation

**Type:** null

###### Implementation decision

###### Enum

- document_only
- do_not_automate

### Item 2

#### If

##### Properties

###### Rights and policy

###### Properties

###### Api terms status

###### Enum

- separate_unreviewed
- unknown

###### Required

- api_terms_status

#### Then

##### Properties

###### Rights and policy

###### Properties

###### Commercial automation status

###### Not

**Const:** allowed

###### Probe contract

###### Properties

###### Mode

**Const:** none

###### Operation

**Type:** null

###### Implementation decision

###### Enum

- document_only
- do_not_automate

### Item 3

#### If

##### Properties

###### Rights and policy

###### Properties

###### Commercial automation status

###### Not

**Const:** allowed

###### Required

- commercial_automation_status

#### Then

##### Properties

###### Probe contract

###### Properties

###### Mode

**Const:** none

###### Operation

**Type:** null

###### Implementation decision

###### Enum

- document_only
- do_not_automate

### Item 4

#### If

##### Properties

###### Status

###### Enum

- documented_only
- blocked_registration
- blocked_credentials
- restricted_by_terms
- rejected
- deprecated

##### Required

- status

#### Then

##### Properties

###### Probe contract

###### Properties

###### Mode

**Const:** none

###### Operation

**Type:** null

###### Implementation decision

###### Enum

- document_only
- do_not_automate

### Item 5

#### If

##### Properties

###### Status

**Const:** probe_ready

##### Required

- status

#### Then

##### Properties

###### Probe contract

###### Properties

###### Mode

###### Not

**Const:** none

### Item 6

#### If

##### Properties

###### Status

**Const:** verified_anonymous

##### Required

- status

#### Then

##### Properties

###### Authentication

###### Properties

###### Mode

**Const:** none

###### Probe contract

###### Properties

###### Mode

###### Not

**Const:** none

###### Expected evidence

**Minitems:** `1`

### Item 7

#### If

##### Properties

###### Status

**Const:** verified_authenticated

##### Required

- status

#### Then

##### Properties

###### Authentication

###### Properties

###### Mode

###### Not

**Const:** none

###### Probe contract

###### Properties

###### Mode

###### Not

**Const:** none

###### Expected evidence

**Minitems:** `1`

### Item 8

#### If

##### Properties

###### Probe contract

###### Properties

###### Mode

###### Not

**Const:** none

###### Required

- mode

##### Required

- probe_contract

#### Then

##### Properties

###### Service root

**$ref:** \#/$defs/httpsUrl

###### Probe contract

###### Properties

###### Expected evidence

**Minitems:** `1`

### Item 9

#### If

##### Properties

###### Authentication

###### Properties

###### Mode

###### Not

**Const:** none

###### Required

- mode

###### Probe contract

###### Properties

###### Mode

###### Not

**Const:** none

###### Required

- mode

##### Required

- authentication
- probe_contract

#### Then

##### Properties

###### Authentication

###### Properties

###### Credential reference

**Type:** string

**Pattern:** ^\[A-Z\]\[A-Z0-9_\]\{2,127\}$

### Item 10

#### If

##### Properties

###### Interface type

**Const:** ftp_or_ftps

##### Required

- interface_type

#### Then

##### Properties

###### Probe contract

###### Properties

###### Mode

**Const:** none

###### Operation

**Type:** null

###### Implementation decision

###### Enum

- document_only
- build_later
- do_not_automate

### Item 11

#### If

##### Properties

###### Implementation decision

**Const:** build_adapter_now

##### Required

- implementation_decision

#### Then

##### Properties

###### Service root

**$ref:** \#/$defs/httpsUrl

###### Rights and policy

###### Properties

###### Dataset rights status

**Const:** verified

###### Api terms status

###### Enum

- same_as_dataset
- separate_reviewed

###### Commercial automation status

**Const:** allowed
