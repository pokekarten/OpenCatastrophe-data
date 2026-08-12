<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.ghsl.ghs-age.r2025a.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.ghsl.ghs-age.r2025a.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.ghsl.ghs-age.r2025a

## Source ids

- ec-jrc.ghsl.ghs-age.r2025a

**Provider:** European Commission Joint Research Centre / Global Human Settlement Layer

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://data.jrc.ec.europa.eu/dataset/d503bb56-9884-4e4d-bb8f-d86711d9f749>

**Service root:** <https://jeodpp.jrc.ec.europa.eu>

**Api version:** GHS-AGE R2025A / V1-0; DOI 10.2905/JRC.YCNTMNG

## Access scope

- metadata
- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- fetch_release_asset

### Path templates

- /ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/V1-0/GHS_AGE_1975052020_GLOBE_R2025A_54009_100_V1_0.zip
- /ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/V1-0/GHS_AGE_1975052020_GLOBE_R2025A_54009_1000_V1_0.zip
- /ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/V1-0/GHS_AGE_1980102020_GLOBE_R2025A_54009_100_V1_0.zip
- /ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/V1-0/GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0.zip

**Parameter rules:** Documentation-only static-file contract. Future execution may select only one of the four repository-allowlisted V1-0 paths above; callers must not supply a host, arbitrary path, filename, query string, redirect target or release substitution. The four paths distinguish 5-year (1975-2020) versus 10-year (1980-2020) temporal classes and 100 m versus 1000 m resolution. No directory crawl, wildcard expansion or silent upgrade to another GHSL release is authorized.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** ZIP-packaged GHS-AGE R2025A raster release assets. JRC describes the underlying data as TIFF rasters in World Mollweide Equal Area projection (ESRI:54009), with class codes representing dominant built-stock age epochs.

**Scientific semantics:** GHS-AGE R2025A is a derived global gridded estimate of the dominant age class of the 2020 built stock. For each grid cell, the age class represents the epoch in which 50% of the 2020 built-up surface was first exceeded, derived from GHS-BUILT-S R2023A multi-temporal built-up-surface estimates. The 5-year and 10-year products are distinct classifications and the 100 m and 1000 m products have different aggregation. This is an approximate built-stock-age proxy for exposure/vulnerability context, not a building-level construction year, cadastral record, damage observation, vulnerability function or loss measurement.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `26214400`

**Retry policy:** none

**Rate limit notes:** JRC documents anonymous/no-limitations dataset access, but this contract intentionally authorizes no network request yet. No repository-specific numeric service budget or separate automated-download policy was established. Future execution must remain a single allowlisted asset request with no crawl, retry loop or parallel bulk mirror.

**Mutability notes:** Scientific identity is pinned to GHS-AGE R2025A, DOI 10.2905/JRC.YCNTMNG, release directory V1-0 and the exact four filenames. The current directory listing dates the four ZIP assets 2025-06-26 and exposes copyright metadata updated later; delivery metadata can change without changing scientific identity. Any future acquisition must freeze requested/final URL, retrieval UTC, byte count and SHA-256 and verify archive/file inventory before use. The 100 m assets exceed this contract's current 25 MiB sample ceiling and therefore require a separately reviewed high-volume transfer decision if ever executed.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The JRC Data Catalogue identifies GHS-AGE R2025A as CC BY 4.0 with no access limitations, and the provider copyright notice states that EU copyright and/or sui-generis rights on the dataset are licensed under CC BY 4.0 with attribution and change indication. This verifies dataset reuse/redistribution rights but does not establish a distinct automated-service entitlement for the static JEODPP delivery host, so commercial automation remains unknown and execution stays disabled. Any committed sample or derived publication still requires exact asset provenance, attribution and repository review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://data.jrc.ec.europa.eu/dataset/d503bb56-9884-4e4d-bb8f-d86711d9f749>
- <https://doi.org/10.2905/JRC.YCNTMNG>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/V1-0/>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/copyright.txt>

**Notes:** Bounded source-access documentation for Issue \#258 / \#173. No provider request, external byte, parser, adapter, Agent Action, admission promotion or publication decision is introduced. The preferred later canary is the 1 km / 5-year V1-0 ZIP because it is approximately 20 MB and preserves the richer temporal classification while staying inside the current sample-byte ceiling; this remains only a future asset-review proposal.
