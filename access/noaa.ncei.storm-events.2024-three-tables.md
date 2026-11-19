<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.storm-events.2024-three-tables.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.storm-events.2024-three-tables.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.storm-events.2024-three-tables

## Source ids

- noaa.ncei.storm-events

**Provider:** NOAA National Centers for Environmental Information / National Weather Service

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/access/storm-events-database/>

**Service root:** <https://www.ncei.noaa.gov>

**Api version:** Storm Events bulk CSV v1.0: three separate 2024 source tables, data year d2024 and generation c20260728; NOT current-year rolling files

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

- inspect_2024_three_table_index

### Path templates

- /pub/data/swdi/stormevents/csvfiles/
- /pub/data/swdi/stormevents/csvfiles/StormEvents_details-ftp_v1.0_d2024_c20260728.csv.gz
- /pub/data/swdi/stormevents/csvfiles/StormEvents_fatalities-ftp_v1.0_d2024_c20260728.csv.gz
- /pub/data/swdi/stormevents/csvfiles/StormEvents_locations-ftp_v1.0_d2024_c20260728.csv.gz

**Parameter rules:** DOCUMENTATION ONLY; no live request is authorized by this access contract. The frozen future 2024 original-file identities are exactly the details, fatalities and locations names listed here; directory index and file paths are provider-owned HTTPS discovery evidence, not an approved executable probe or licence. Do not accept caller-supplied year, creation date, table, host, query, headers, redirects, signed URLs, fallback filenames, bulk mirror, pagination or download. Future original retrieval must independently review dataset and service terms, fix exact per-file request/byte/time/decompression bounds, use the trusted default-branch execution plane and preserve each original compressed SHA-256. Never infer that a newer c-date or another d-year is the tested d2024/c20260728 snapshot.

## Response contract

### Expected media types

- text/html
- application/gzip
- application/octet-stream

**Format:** Official NCEI directory HTML with three exact gzip-compressed CSV files, each independently versioned details/fatalities/locations v1.0 d2024 c20260728. No original CSV bytes are acquired under this contract.

**Scientific semantics:** Storm Events details rows are reported EVENT_ID records, grouped by EPISODE_ID; fatalities and locations are one-to-many child tables keyed to EVENT_ID and MUST NOT be naively joined before summing parent damage or event counts. Dates use source-specific local timezone codes; reported geographic units can be counties, forecast zones or marine zones. Historical event-type coverage and event submission/reporting standards change over time; missing reports do not imply zero hazard. DAMAGE_PROPERTY and DAMAGE_CROPS are reported event estimates, NOT policyholder insured losses, gross/net claims or validated TIV. Already executed 2024 original-source relational audit in docs/research/executed-source-findings-20261103.md found 3 parent-level fatality-count contradictions and up to 72x naive child-join multiplication; these are blocking scientific review findings, not grounds for silently discarding or repairing source events. This documentation-only contract does NOT establish CAT event frequency, hail/wind intensity, physics, commercial use or model admission.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Provider advertises a public download directory and public Cloud Storage access for bulk usage, but service-specific automated polling/scraping quotas and commercial model-use permissions for this exact three-table release have not been reviewed. No request, retry, redirect, scheduled fetch or bulk download is permitted by this contract.

**Mutability notes:** 2026-11-15 original provider directory index displays three distinct 2024 c20260728 source filenames, with compressed sizes of 12693243 bytes (details), 13057 (fatalities) and 983723 (locations). These are index values, NOT newly downloaded content hashes. Previously observed original compressed SHA-256 digests (2026-11-03 historical audit, NOT freshly recomputed): details=2070b83eccab041b36360ab73645b9a249c3eefc5b92b5b3fc0cbba4d9fcc09c; fatalities=7113ce3232c98056867cf8d144df770e9e6b140cce40dff3ef46ff805ba17fdb; locations=8847a6336e1af94000f7ecfb4a80c06bf0d5c1ac122fe39da5b2e379dc62c1b4. The supporting acquisition report is docs/research/executed-source-findings-20261103.md. New acquisitions MUST independently reverify these complete-file compressed hashes and record exact retrieval UTC; a matching name/size cannot substitute for a byte hash. cYYYYMMDD denotes generation/revision; source archive may change and different table/year editions are not interchangeable. Current index date/size alone proves neither same bytes nor model fitness.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** <https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00510/html>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The public provider is a U.S. federal agency and the official site invites public bulk CSV downloads; public availability and federal origin do not independently clear service automation terms, reported third-party narratives/location or casualty information, protected personal attributes, commercial insurance-model use, source/derived publication or onward redistribution of exact release bytes. Keep all such permissions unknown until a source- and use-specific review. Fatalities data may contain individual attributes; do not commit original rows or private-person details. The earlier 2024 scientific audit is research evidence, not a dataset licence, trusted new API entitlement or model admission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://www.ncei.noaa.gov/access/storm-events-database/>
- <https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/>
- <https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/README>
- <https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00510/html>

**Notes:** SOURCE_ID=noaa.ncei.storm-events; exact 2024 d2024 c20260728 details/fatalities/locations release. Gate T0 source identity/format/index/known historic original-acquisition links only. Previously acquired externally by an earlier researcher; this run neither downloaded any of the 3 source files nor reverified SHA nor wrote to Neon. Existing research_runners/noaa_storm_events_relational_audit_v0.py remains the sole offline event/fatality/location consistency gate, and the existing source discovery landscape remains authoritative. Source rights, scientific admission, model input and future direct network probe are all blocked.
