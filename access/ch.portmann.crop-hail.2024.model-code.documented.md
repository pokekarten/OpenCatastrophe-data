<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ch.portmann.crop-hail.2024.model-code.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ch.portmann.crop-hail.2024.model-code.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ch.portmann.crop-hail.2024.model-code.documented

## Source ids

- ch.portmann.crop-hail.2024.model-code

**Provider:** Portmann, Schmid and Villiger / Zenodo / CLIMADA-project

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://doi.org/10.5281/zenodo.12784190>

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

- /api/records/12784190/files/raphael-portmann/202403_crop_hail_damage_footprint-1.0.zip/content

**Parameter rules:** Exact published version and filename only. Historical data-file GET used download=1; code used exact API content path. Documentation-only; no new live request, scheduled fetch or bulk transfer authorized.

## Response contract

### Expected media types

- application/zip

**Format:** Python 3.9 study-specific model/reproduction code; dependency CLIMADA platform and public crop/radar/damage-grid research records

**Scientific semantics:** NHESS 10.5194/nhess-24-2541-2024 provides DOI 10.5281/zenodo.12784190 for the published study code, as well as links to the three separately identified data assets in this shard. CLIMADA's cited platform license is GPL-3.0; do not assume the same license applies to all study code or linked third-party datasets. This is a hail crop-damage footprint classification research model, not an Oasis-ready insured loss model: pin archive checksum, code/dependency versions, valid tests and scientific limits before use. Review actual per-file code licences and dependency compatibility, including CLIMADA GPL-3.0, separately from deposit CC BY label. Do not execute downloaded code without isolation and review; method reproduces binary crop footprints, not monetary losses.

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

**Notes:** Live Zenodo record API on 2026-11-25 reports access_right=open and license.id=cc-by-4.0; original file sizes match prior receipts. This deposit-level licence is not a blanket grant covering upstream third-party inputs, code dependencies, privacy or automation. Review actual per-file code licences and dependency compatibility, including CLIMADA GPL-3.0, separately from deposit CC BY label. Do not execute downloaded code without isolation and review; method reproduces binary crop footprints, not monetary losses.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5281/zenodo.12784190>
- <https://zenodo.org/api/records/12784190>
- <https://doi.org/10.5194/nhess-24-2541-2024>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42184430327>
- <https://github.com/pokekarten/OpenCatastrophe-data/blob/cb566576e27fa85bbc9c387224061aa9d97283b9/research/observations/swiss_crop_hail_zenodo_original_eight_file_receipts_v0.toml>

**Notes:** Historical original-byte evidence from PR \#1396, not newly downloaded this run: Code ZIP 2240460 bytes, MD5 96f72406c1464824434e66c54998be0e, SHA-256 e72954eca06346d1b67c6a4d7287f4c102e65e2b5871193a5224419cb21d15e2, 21 members. Historical code-only source run 42184430327 did not execute code. Original workflow and pinned branch receipt identify those prior observations; live metadata rechecked 2026-11-25. Do not relabel historic branch proof as main-origin acquisition. No external data bytes or private Neon information committed; non-admission.
