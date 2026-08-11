<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ioc.vliz.slsmf.registered-api.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ioc.vliz.slsmf.registered-api.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Access id:** ioc.vliz.slsmf.registered-api.documented

## Source ids

- ioc.vliz.slsmf

**Provider:** Intergovernmental Oceanographic Commission of UNESCO / Flanders Marine Institute (VLIZ)

**Interface type:** rest

**Status:** restricted_by_terms

**Documentation url:** <https://api.ioc-sealevelmonitoring.org/v2/doc>

**Service root:** <https://api.ioc-sealevelmonitoring.org>

**Api version:** v2

## Access scope

- metadata
- catalogue
- realtime

## Authentication

**Mode:** api_key

**Credential reference:** IOC_SLSMF_API_KEY

**Registration url:** <https://ioc-sealevelmonitoring.org/api.php>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_v2_api_documentation

### Path templates

- /v2/doc

**Parameter rules:** Documentation-only contract. The provider states that API v2 requires an API key: users register for an SLSMF account and request membership in the 'Access gauges API (gauges_API)' group. IOC_SLSMF_API_KEY is only a symbolic future secret reference; no key is stored or requested by this repository. No automated station/data request is authorized here, and callers may not supply arbitrary hosts, paths, headers or query parameters.

## Response contract

### Expected media types

- application/json
- text/html

**Format:** IOC/VLIZ SLSMF API v2 documentation (OAS 3.0) and, only after a later rights review, explicitly bounded v2 station/sensor responses.

**Scientific semantics:** The live station API exposes heterogeneous real-time sea-level feeds; the v2 research endpoint is separately quality-controlled and has distinct semantics. Station operator, sensor, datum, sampling, gaps, quality-control flags and feed lineage must be preserved; overlapping DART/SLSMF feeds must not automatically be counted as independent evidence.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `524288`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** No automated provider API probing is authorized by this documentation-only restricted contract. Exact v2 provider limits and credential handling must be reviewed before any future probe.

**Mutability notes:** API v2 is the provider's latest documented version and has recorded breaking changes. Station availability, sensors, sampling and feeds can change; any future accepted response requires retrieval time, endpoint version and source/feed lineage.

## Rights and policy

**Dataset rights status:** restricted

**Api terms status:** separate_unreviewed

**Terms url:** <https://www.ioc-sealevelmonitoring.org/disclaimer.php>

**Commercial automation status:** prohibited

**Redistribution status:** unknown

**Notes:** The SLSMF web-service Data Policy states that data/products available through the website may not be used commercially and directs commercial users to the relevant data originators. The v2 OpenAPI page identifies its API description as CC-BY 4.0, but that documentation metadata is not treated as a commercial-use licence for the underlying station data or as clearance of API-specific terms.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** do_not_automate

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://api.ioc-sealevelmonitoring.org/>
- <https://api.ioc-sealevelmonitoring.org/v2/doc>
- <https://ioc-sealevelmonitoring.org/api.php>
- <https://www.ioc-sealevelmonitoring.org/disclaimer.php>

**Notes:** Current provider evidence binds this documentation-only record to API v2 and its API-key/account/group flow while preserving the stricter legal boundary. No API key is committed or used, and the contract remains restricted_by_terms / do_not_automate until commercial/API-specific terms are explicitly cleared for the intended insurance context.
