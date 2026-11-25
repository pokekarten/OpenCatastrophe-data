<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ch.portmann.crop-hail.2024.exposure-grid.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ch.portmann.crop-hail.2024.exposure-grid.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ch.portmann.crop-hail.2024.exposure-grid.documented

## Source ids

- ch.portmann.crop-hail.2024.exposure-grid

**Provider:** Portmann, Schmid, Villiger, Bresch and Calanca / Zenodo / CLIMADA

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://doi.org/10.5281/zenodo.11064756>

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

- /records/11064756/files/metadata.csv
- /records/11064756/files/data-files.zip

**Parameter rules:** Exact published version and filename only. Historical data-file GET used download=1; code used exact API content path. Documentation-only; no new live request, scheduled fetch or bulk transfer authorized.

## Response contract

### Expected media types

- text/csv
- application/zip

**Format:** Published gridded Swiss crop exposure for wheat, maize, barley, rapeseed and grapevine; exact files, grid geometry, units and land-use provenance to verify per asset

**Scientific semantics:** The peer-reviewed NHESS crop-hail paper 10.5194/nhess-24-2541-2024 explicitly cites Zenodo 11064756 for gridded crop exposure and explains crop-density dependence of hail damage-footprint skill. This source is linked to the same 12-event research as the damage and hazard datasets below: never count the linked assets as independent validation samples. No insurance TIV, insured parcel membership, carrier allocation or crop policy terms established. The exact Zenodo release/file license, hashes, spatial reference, time alignment and crop-code mapping must be checked before source admission. Review exact archive redistribution and upstream land-use rights, historical geography mismatch (2021 exposure versus 2017-2021 damage), crop code and n_fields support. No insurer TIV or membership.

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

**Notes:** Live Zenodo record API on 2026-11-25 reports access_right=open and license.id=cc-by-4.0; original file sizes match prior receipts. This deposit-level licence is not a blanket grant covering upstream third-party inputs, code dependencies, privacy or automation. Review exact archive redistribution and upstream land-use rights, historical geography mismatch (2021 exposure versus 2017-2021 damage), crop code and n_fields support. No insurer TIV or membership.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5281/zenodo.11064756>
- <https://zenodo.org/api/records/11064756>
- <https://doi.org/10.5194/nhess-24-2541-2024>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42114240145>
- <https://github.com/pokekarten/OpenCatastrophe-data/blob/cb566576e27fa85bbc9c387224061aa9d97283b9/research/observations/swiss_crop_hail_zenodo_original_eight_file_receipts_v0.toml>

**Notes:** Historical original-byte evidence from PR \#1396, not newly downloaded this run: metadata.csv 1720 bytes, MD5 05faf6e57f0b37130b3fc1c16190ed6c, SHA-256 45a9e2bccd7571ada9e3bbb77482dbadfa4868c704527164e544e18d4013b9db; data-files.zip 31930278 bytes, MD5 7db8df4c81ba5d1c1c7b8371cee53e15, SHA-256 347bde669b4077b5350d2260eba0e4bcd68977434cb3ad95b7e056c67d1f6326, 24 HDF5 archive members. Original workflow and pinned branch receipt identify those prior observations; live metadata rechecked 2026-11-25. Do not relabel historic branch proof as main-origin acquisition. No external data bytes or private Neon information committed; non-admission.
