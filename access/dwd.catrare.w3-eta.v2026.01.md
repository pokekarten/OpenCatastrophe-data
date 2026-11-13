<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dwd.catrare.w3-eta.v2026.01.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dwd.catrare.w3-eta.v2026.01.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** dwd.catrare.w3-eta.v2026.01

## Source ids

- dwd.catrare.w3-eta.v2026.01

**Provider:** Deutscher Wetterdienst (DWD) Climate Data Center

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_CatRaRE_W3_Eta_v2026.01-de.html>

**Service root:** <https://opendata.dwd.de/climate_environment/CDC/event_catalogues/germany/precipitation/CatRaRE_v2026.01/data>

**Api version:** CatRaRE W3 Eta v2026.01, DOI 10.5676/DWD/CatRaRE_W3_Eta_v2026.01, observation window 2001-01-01–2025-12-31

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- read_fixed_csv_prefix

### Path templates

- /CatRaRE_2001_2025_W3_Eta_v2026_01.csv

**Parameter rules:** ONE fixed original DWD HTTPS Range GET exactly https://opendata.dwd.de/climate_environment/CDC/event_catalogues/germany/precipitation/CatRaRE_v2026.01/data/CatRaRE_2001_2025_W3_Eta_v2026_01.csv Range: bytes=0-4095, no query/fragment, caller paths, version substitution, credentials, redirects, retries, pagination, other file downloads, CSV bulk or geometry acquisition. Expect HTTP 206 Content-Range bytes 0-4095/12410601, precisely 4096 original UTF-8 CSV bytes, semicolon-separated, 67 unique headers (CatVersion/KEY_FIELD/Event_ID first), three source-specific first event IDs. Review was scoped to ONE fixed variant and the original 2026.01 release. The W3 and T5 catalogues share the same RADKLIM-RW V2017.002 parent and cannot be treated as independent event frequencies.

## Response contract

### Expected media types

- application/octet-stream
- text/csv
- text/plain

**Format:** First 4096 original bytes of immutable W3 Eta v2026.01 semicolon-delimited 67-column event CSV, not a whole file or source geometry.

**Scientific semantics:** DWD CatRaRE W3 Eta uses extreme-rain radar-derived objects from 1 km RADKLIM-RW V2017.002, 11 accumulation durations and provider event-detection / Eta selection; catalogue events are not independent of RADKLIM or of the other W3/T5 threshold catalogue. The CSV does not include an observed damage footprint, insurance exposure, loss amount or spatial EventZones geometry. Preserve UTC, event duration, event IDs qualified by threshold and version; no model admission without whole-file hash, full event uniqueness/time/geometry and independent reference validation.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `4096`

**Max sample bytes:** `4096`

**Retry policy:** none

**Rate limit notes:** Original DWD CDC-OpenData Terms_of_use.pdf documents CC BY 4.0 for CDC data. One exact 4KiB anonymously retrieved partial response is a deliberately tiny request to public source under the same dataset download terms; no claim of unlimited API service volume, no full 12/17MB CSV, no WFS, and no bulk crawler. The workflow only runs approved fixed probes from trusted main push or manual dispatch; never PR live.

**Mutability notes:** Original 2026.01 DWD directory listed source CSV at exactly 12410601 bytes. Previous actual original 4KiB HTTP Range observation SHA-256 a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12 must match fresh direct run or source drift fails closed. This is NOT full CSV SHA-256. W3 official DOI landing-page CSV link historically pointed to older missing archive; prefer only explicitly frozen current /data/2026.01 asset; preserve release and byte range. A changed original archive must be separately reviewed before re-pinning.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** DWD official CDC-OpenData Terms_of_use.pdf (May 2024) explicitly applies CC BY 4.0 to CDC datasets, including commercial reuse and reproduction with attribution and change indication; original CatRaRE W3 DOI landing page pins the exact release. This review interprets the very small anonymous fixed-file Range GET as covered by CDC dataset access conditions, not a right to unlimited automated crawling, unrelated DWD interfaces or redistributing unreviewed original provider bytes through this repository. Publisher attribution: Deutscher Wetterdienst (DWD), CatRaRE W3 Eta v2026.01, 10.5676/DWD/CatRaRE_W3_Eta_v2026.01; changes declared when appropriate. Dataset licensing does not establish model scientific validity.

## Probe contract

**Mode:** provider_specific

**Operation:** read_fixed_csv_prefix

**Requires credentials:** `false`

### Expected evidence

- Exactly one original official DWD HTTPS GET at pinned W3/T5 path and Range: bytes=0-4095, 30-second timeout, HTTP 206 and Content-Range bytes 0-4095/12410601; no redirects/retries
- Exactly 4096 original uncompressed UTF-8 bytes, 67 semicolon CSV columns, CatVersion/KEY_FIELD/Event_ID source-version identity and first three complete rows
- Original unmodified 4KiB response SHA-256 equals historical a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12, retrieval UTC, request SHA, original-byte count and exact variant, with no provider raw bytes persisted
- No full CSV SHA-256, full event frequencies, source polygons, insured exposure, W3/T5 independence, CAT model input or source-byte storage approval implied

**Implementation decision:** build_later

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_CatRaRE_W3_Eta_v2026.01-de.html>
- <https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf>
- <https://opendata.dwd.de/climate_environment/CDC/event_catalogues/germany/precipitation/CatRaRE_v2026.01/data/>
- <https://www.dwd.de/copyright>

**Notes:** Version-scoped CatRaRE W3 source access contract backed by a historical exact 4096-byte direct-source receipt already recorded in the public landscape; new work adds enforceable in-repo rights/exact-route fail-closed policy. No source bytes or full archive have been acquired by this contract. The scientific and admission gates remain open; the fixed runner and existing workflow must pass synthetic PR tests before trusted main original-provider checks.
