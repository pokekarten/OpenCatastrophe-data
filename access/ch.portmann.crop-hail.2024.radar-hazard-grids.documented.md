<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ch.portmann.crop-hail.2024.radar-hazard-grids.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ch.portmann.crop-hail.2024.radar-hazard-grids.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ch.portmann.crop-hail.2024.radar-hazard-grids.documented

## Source ids

- ch.portmann.crop-hail.2024.radar-hazard-grids

**Provider:** Portmann, Schmid, Villiger, Bresch and Calanca / Zenodo / MeteoSwiss research context

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://doi.org/10.5281/zenodo.11064781>

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

- /records/11064781/files/metadata.csv
- /records/11064781/files/hail_MESHS_CH_12_events_2017_2021.h5
- /records/11064781/files/hail_POH_CH_12_events_2017_2021.h5

**Parameter rules:** Exact published version and filename only. Historical data-file GET used download=1; code used exact API content path. Documentation-only; no new live request, scheduled fetch or bulk transfer authorized.

## Response contract

### Expected media types

- text/csv
- application/octet-stream

**Format:** Gridded radar Maximum Expected Severe Hail Size (MESHS) research event data; published method compares crop resolutions of 8 km and vineyard resolutions of 1 km

**Scientific semantics:** The NHESS article cites Zenodo 11064781 as 'Radar data for 12 hail events in Switzerland'. MESHS is an inferred radar hail-size indicator, not direct point-measured hailstone size, a building-damage vulnerability function, or a stochastic event frequency. Review upstream MeteoSwiss rights separately from the paper license and Zenodo record; verify NetCDF/other format, CRS, cell size, units, nodata and event-year identity. No OEP/AEP or insurer loss calibration is warranted by 12 selected historical events. Resolve MeteoSwiss upstream derivative rights for exact released grids. MESHS mm and POH percent are different radar proxies, not measured ground hail. Preserve coordinate and time keys; selected events not a climatology.

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

**Notes:** Live Zenodo record API on 2026-11-25 reports access_right=open and license.id=cc-by-4.0; original file sizes match prior receipts. This deposit-level licence is not a blanket grant covering upstream third-party inputs, code dependencies, privacy or automation. Resolve MeteoSwiss upstream derivative rights for exact released grids. MESHS mm and POH percent are different radar proxies, not measured ground hail. Preserve coordinate and time keys; selected events not a climatology.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5281/zenodo.11064781>
- <https://zenodo.org/api/records/11064781>
- <https://doi.org/10.5194/nhess-24-2541-2024>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42114240145>
- <https://github.com/pokekarten/OpenCatastrophe-data/blob/cb566576e27fa85bbc9c387224061aa9d97283b9/research/observations/swiss_crop_hail_zenodo_original_eight_file_receipts_v0.toml>

**Notes:** Historical original-byte evidence from PR \#1396, not newly downloaded this run: metadata.csv 227 bytes, MD5 c4d4090b272eb9969a9045f93b2ce2c2, SHA-256 682dc230bfaa3d416a07c04874ca6d0e8222eb9280e467b8228f72fc1c579474; MESHS HDF5 6205459 bytes, MD5 f18b4e27342a374b08ca4c0ec8f90b5c, SHA-256 4ec457cfad8019cfb50d1e03399f2a7c53063eb2d6bd0d26e007d8201786db5b; POH HDF5 8919115 bytes, MD5 3eee87725577ee3b74e0c33601dbfffa, SHA-256 f6773a9152e9954f271c7d0951e27403dd46b9142b4253a54b97f374171a0ae7. Prior source HDF5 structural replay found 12 events and 454400 radar grid positions each. Original workflow and pinned branch receipt identify those prior observations; live metadata rechecked 2026-11-25. Do not relabel historic branch proof as main-origin acquisition. No external data bytes or private Neon information committed; non-admission.
