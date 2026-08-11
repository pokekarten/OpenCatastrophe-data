<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: schemas/dataset-manifest.schema.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# JSON Schema: `dataset-manifest.schema.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**$schema:** <https://json-schema.org/draft/2020-12/schema>

**$id:** urn:opencatastrophe:schema:dataset-manifest:1.0.0

**Title:** OpenCatastrophe Dataset Admission Manifest

**Type:** object

**Additionalproperties:** `false`

## $defs

### Artifact

**Type:** object

**Additionalproperties:** `false`

#### Required

- byte_size
- sha256
- storage_reference

#### Properties

##### Byte size

**Type:** integer

**Minimum:** `0`

##### Sha256

**Type:** string

**Pattern:** ^\[a-f0-9\]\{64\}$

##### Storage reference

**Type:** string

**Pattern:** ^external://(?\!.\*//)(?\!.\*(?:/\\.\{1,2\})(?:/\|$))(?\!.\*\\/$)\[A-Za-z0-9\]\[A-Za-z0-9._/-\]\*$

## Required

- schema_version
- dataset_id
- provider
- product_name
- canonical_source
- retrieved_at
- access_class
- modelling_layer
- intended_use
- licensing
- redistribution
- privacy
- review

## Properties

### Schema version

**Type:** string

**Const:** 1.0.0

### Dataset id

**Type:** string

**Minlength:** `1`

**Pattern:** ^\[A-Za-z0-9\]\[A-Za-z0-9._-\]\*$

### Provider

**Type:** string

**Minlength:** `1`

### Product name

**Type:** string

**Minlength:** `1`

### Version or release

#### Type

- string
- null

### Canonical source

**Type:** string

**Format:** uri

### Retrieved at

**Type:** string

**Format:** date-time

### Retrieval query or filters

#### Type

- string
- null

### Access class

**Type:** string

#### Enum

- open
- registration_required
- authenticated
- restricted
- unknown

### Modelling layer

**Type:** string

#### Enum

- event_catalogue
- hazard
- exposure
- vulnerability
- observed_loss
- engine
- standard
- other

### Intended use

**Type:** string

**Minlength:** `1`

### Raw artifact

#### Anyof

##### Item 1

**$ref:** \#/$defs/artifact

##### Item 2

**Type:** null


### Derived artifact

#### Anyof

##### Item 1

**$ref:** \#/$defs/artifact

##### Item 2

**Type:** null


### Licensing

**Type:** object

**Additionalproperties:** `false`

#### Required

- status
- terms_reference
- terms_reviewed_at
- commercial_use_status

#### Properties

##### Status

**Type:** string

###### Enum

- verified
- unverified
- conflicting
- unknown

##### Spdx expression

###### Type

- string
- null

##### Licence name

###### Type

- string
- null

##### Terms reference

**Type:** string

**Format:** uri

##### Terms reviewed at

**Type:** string

**Format:** date-time

##### Terms version or date

###### Type

- string
- null

##### Terms content sha256

###### Type

- string
- null

**Pattern:** ^\[a-f0-9\]\{64\}$

##### Commercial use status

**Type:** string

###### Enum

- allowed
- restricted
- prohibited
- unknown

##### Attribution requirements

###### Type

- string
- null

##### Share alike or derivative requirements

###### Type

- string
- null

##### Notes

###### Type

- string
- null

### Redistribution

**Type:** object

**Additionalproperties:** `false`

#### Required

- status
- scope

#### Properties

##### Status

**Type:** string

###### Enum

- allowed
- restricted
- prohibited
- unknown

##### Scope

**Type:** string

###### Enum

- raw
- derived_only
- metadata_only
- none

##### Conditions

###### Type

- string
- null

### Privacy

**Type:** object

**Additionalproperties:** `false`

#### Required

- personal_data_status
- confidential_or_proprietary_status

#### Properties

##### Personal data status

**Type:** string

###### Enum

- none
- contains
- unknown

##### Confidential or proprietary status

**Type:** string

###### Enum

- none
- contains
- unknown

##### Notes

###### Type

- string
- null

### Spatial

#### Type

- object
- null

**Additionalproperties:** `false`

#### Properties

##### Crs

###### Type

- string
- null

##### Extent

###### Type

- string
- null

### Temporal

#### Type

- object
- null

**Additionalproperties:** `false`

#### Properties

##### Extent

###### Type

- string
- null

### Variables and units

**Type:** array

#### Items

**Type:** object

**Additionalproperties:** `false`

##### Required

- name
- unit

##### Properties

###### Name

**Type:** string

**Minlength:** `1`

###### Unit

###### Type

- string
- null

###### Description

###### Type

- string
- null

### Transformation

#### Type

- object
- null

**Additionalproperties:** `false`

#### Required

- code_reference
- config_identity

#### Properties

##### Code reference

**Type:** string

**Minlength:** `1`

##### Config identity

**Type:** string

**Minlength:** `1`

### Review

**Type:** object

**Additionalproperties:** `false`

#### Required

- status
- reviewed_at
- reviewer

#### Properties

##### Status

**Type:** string

###### Enum

- pending
- approved_metadata_only
- approved_derived
- approved_raw
- rejected

##### Reviewed at

###### Type

- string
- null

**Format:** date-time

##### Reviewer

###### Type

- string
- null

##### Notes

###### Type

- string
- null
