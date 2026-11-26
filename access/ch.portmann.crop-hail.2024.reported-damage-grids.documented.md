<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ch.portmann.crop-hail.2024.reported-damage-grids.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ch.portmann.crop-hail.2024.reported-damage-grids.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ch.portmann.crop-hail.2024.reported-damage-grids.documented

## Source ids

- ch.portmann.crop-hail.2024.reported-damage-grids

**Provider:** Portmann, Schmid, Villiger, Bresch and Calanca / Zenodo / CLIMADA

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://doi.org/10.5281/zenodo.11064767>

**Service root:** <https://zenodo.org>

**Api version:** `null`

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

- inspect_documented_route

### Path templates

- /records/11064767/files/metadata.csv
- /records/11064767/files/data-files.zip

**Parameter rules:** Exact published version and filename only. Historical data-file GET used download=1; code used exact API content path. Documentation-only; no new live request, scheduled fetch or bulk transfer authorized.

## Response contract

### Expected media types

- text/csv
- application/zip

**Format:** Published gridded reported crop-damage information; original insurer reports are not automatically public and are not interchangeable with these research grids

**Scientific semantics:** The NHESS Portmann et al. 2024 article explicitly identifies Zenodo 11064767 as 'Reported hail damage for 12 hail events in Switzerland' and says gridded damage information is available. This is a candidate for footprint occurrence validation, not permission to distribute underlying insurer claims, loss amounts or identifiable records. Review the precise Zenodo license, anonymization/aggregation, per-event units and linkage to hazard and exposure before download, rehosting or use. The same insured source data were used to design/assess the published method, so no independent holdout is implied. Confirm insurer-derived gridded observations are within depositor authority and intended commercial-use scope; review anonymization, spatial granularity and disclosure. 10-12 selected days by crop. Do not infer monetary severity or annual frequency. Historical original replay found 550 positive event-grid entries without matched exposure position across three 2 km pairs. Preserve outside-support counts; no naive positional join.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `41943040`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Review current Zenodo service terms, aggregate transfer budget, exact file and acquisition scope before any replay.

**Mutability notes:** Version-specific record ID and publisher MD5; record exact observed size, SHA-256 and retrieval time separately for every asset. Do not replace original release with concept DOI or latest version.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://about.zenodo.org/terms/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Live Zenodo record API on 2026-11-25 reports access_right=open and license.id=cc-by-4.0; original file sizes match prior receipts. This deposit-level licence is not a blanket grant covering upstream third-party inputs, code dependencies, privacy or automation. Confirm insurer-derived gridded observations are within depositor authority and intended commercial-use scope; review anonymization, spatial granularity and disclosure. 10-12 selected days by crop. Do not infer monetary severity or annual frequency. Historical original replay found 550 positive event-grid entries without matched exposure position across three 2 km pairs. Preserve outside-support counts; no naive positional join.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5281/zenodo.11064767>
- <https://zenodo.org/api/records/11064767>
- <https://doi.org/10.5194/nhess-24-2541-2024>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42114240145>
- <https://github.com/pokekarten/OpenCatastrophe-data/blob/cb566576e27fa85bbc9c387224061aa9d97283b9/research/observations/swiss_crop_hail_zenodo_original_eight_file_receipts_v0.toml>

**Notes:** Historical original-byte evidence from PR \#1396, not newly downloaded this run: metadata.csv 2368 bytes, MD5 0260ae2047e3fc02aa7ad88cf7911dda, SHA-256 cc88233701f06f952d5881a762b690bd9e14d55c24995298a61fbf70ea7759a5; data-files.zip 2455518 bytes, MD5 c17119f9cd35f57ad49662a6f8ba1166, SHA-256 8db4322059791952c9f886f7eb798a5ee66c395c7f0921ca3d003c8f0b06b6bc, 24 HDF5 archive members. Original workflow and pinned branch receipt identify those prior observations; live metadata rechecked 2026-11-25. Do not relabel historic branch proof as main-origin acquisition. No external data bytes or private Neon information committed; non-admission.
