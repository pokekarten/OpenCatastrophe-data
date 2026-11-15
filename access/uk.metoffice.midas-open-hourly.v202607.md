<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/uk.metoffice.midas-open-hourly.v202607.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `uk.metoffice.midas-open-hourly.v202607.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** uk.metoffice.midas-open-hourly.v202607

## Source ids

- uk.metoffice.midas-open-hourly.v202607

**Provider:** UK Met Office / Centre for Environmental Data Analysis (CEDA)

**Interface type:** web_portal

**Status:** blocked_registration

**Documentation url:** <https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/>

**Service root:** <https://catalogue.ceda.ac.uk>

**Api version:** MIDAS Open UK hourly v202607 published 2026-07-23, DOI 10.5285/d04207b551674c07801b7d4e6d883e50

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** provider_account

**Credential reference:** `null`

**Registration url:** <https://data.ceda.ac.uk/>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_midas_open_v202607_catalogue

### Path templates

- /uuid/d04207b551674c07801b7d4e6d883e50/

**Parameter rules:** Documentation-only, no automatic source request or caller-selected path, unbounded domain, secrets, crawler, bulk extraction or retries. Metadata path(s) are only candidate exact origins; actual provider GET requires independently reviewed provider machine-use terms, exact URL, byte cap, body hash and source-specific approved workflow.

## Response contract

### Expected media types

- text/html

**Format:** Official immutable DOI catalogue metadata only; original CEDA BADC-CSV station files require provider registration and specific file identity.

**Scientific semantics:** Hourly data span 1875-2025 and report wind speed/direction; that does not imply any gust-variable or wind averaging-period availability for event/station. Dataset excludes METAR messages and restricted MIDAS records; record site moves, QC, missingness and independent storm holdout.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Registration is required for dataset download. No password or authenticated GET was attempted; source access speed, session constraints and account authorization must be reviewed separately.

**Mutability notes:** Pin exact DOI release, file, station, timestamp and versioned changelog; archive includes replaced/removed station content.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** CEDA official record labels this exact MIDAS Open v202607 product UK Open Government Licence 3.0 and Permitted Use Any, with licence/citation/attribution duties; it excludes restricted MIDAS and METAR. This does not grant CEDA automated scraping or an accepted insurer risk model.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/>
- <https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>
- <https://data.ceda.ac.uk/>

**Notes:** No authorized CEDA registration session, original BADC-CSV station file, provider source SHA, model exposure or wind gust validation. Citable public catalogue only.
