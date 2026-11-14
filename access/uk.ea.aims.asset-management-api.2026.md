<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/uk.ea.aims.asset-management-api.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `uk.ea.aims.asset-management-api.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** uk.ea.aims.asset-management-api.2026

## Source ids

- uk.ea.aims.asset-management-api.2026

**Provider:** UK Environment Agency — Asset Management API

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://environment.data.gov.uk/asset-management/doc/reference>

**Service root:** <https://environment.data.gov.uk>

**Api version:** Provider documentation describes API meta.version 0.1 (alpha); public operational service is mutable

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- document_list_assets
- document_list_maintenance_activities

### Path templates

- /asset-management/id/asset.json
- /asset-management/id/maintenance-activity.json

**Parameter rules:** T0 documentation only; no network authority is granted by this contract. Provider documents HTTP GET with JSON suffix, _limit and _offset and optional typed asset/maintenance filters. Future single-request anonymous canary must be independently reviewed and fixed to one path, _limit=1, _offset=0, without _view=full, arbitrary ids, filters, host, redirects, pagination, geometry, follow-on links, bulk queries, retries or credential injection. Do not inherit the separate ArcGIS Spatial Flood Defences FeatureServer authorization or PR \#1602 original-source results.

## Response contract

### Expected media types

- application/json

**Format:** EA Asset Management API JSON: object with meta publisher/licence/version and items array; per-item @id is source identity, not an independently resolved cross-dataset identifier.

**Scientific semantics:** AIMS asset descriptions and maintenance activities are heterogeneous operational records, not verified geometry, actual protection probability, breach history, insurer assets or insured losses. Planned or funded maintenance is not proof of completion, inspected condition or structural effectiveness; only some assets have maintenance schedules. Asset linkage to AIMS spatial FeatureServer must be independently proven with identifiers and geography. API summary is mutable and may be incomplete.

## Operational constraints

**Timeout seconds:** `15`

**Max probe bytes:** `8192`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** No rate-limit entitlement, automation cadence, retry-after policy or commercial API service assurance was established. Documentation lists _limit/_offset but does not grant unbounded harvesting; no live probe, sampling or automated ingestion is authorized by this documented-only contract.

**Mutability notes:** API documentation describes meta.version 0.1 and a forward-compatibility intent, not immutable snapshots. Any later original receipt must pin exact request, response UTC, response body SHA-256, byte count, content type, observed meta.version/licence and item identifiers, then independently validate as-of and maintenance-period fields.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://environment.data.gov.uk/asset-management/doc/about>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Official EA asset-management About page states content is under Open Government Licence v3.0 except where otherwise stated; the developer reference includes an OGL 3 link in example response metadata. This is authoritative evidence of a potential licence path, not an independent exact product/version and every-field rights review. Separate service automation/rate rules, third-party field exclusions, asset-level privacy, historical retention, commercial model-derived outputs and any redistribution remain unresolved. No raw or derived asset approval.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://environment.data.gov.uk/asset-management/doc/reference>
- <https://environment.data.gov.uk/asset-management/doc/about>
- <https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>

**Notes:** Scope is one exact existing main landscape candidate, not the separate AIMS spatial FeatureServer source. T0 documentary route confirmed. T1 direct origin response was not obtained in this work; T2 not applicable to documented anonymous route. T3 original sample/hash, T4 health, science review, Neon write/readback and repository admission are not verified. No credentials or external data bytes are included.
