<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/polisa.cee18-insurer-market-compilation.20261109.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `polisa.cee18-insurer-market-compilation.20261109.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** polisa.cee18-insurer-market-compilation.20261109.documented

## Source ids

- polisa.cee18-insurer-market-compilation.20261109

**Provider:** Polisa independent public insurance market compilation

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://polisapro.com/data/README.txt>

**Service root:** <https://polisapro.com>

**Api version:** README snapshot 2026-11-09.d5ad62

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

- review_public_readme_only

### Path templates

- /data/README.txt

**Parameter rules:** Documentation-only publisher README path. README lists polisa-all-markets.csv and per-market exports, but landing page text in this review contradicts CSV availability. Do not construct dataset file requests, scrape insurer pages, enumerate endpoints, follow unreviewed export links or import provider rows. Before any executable contract, resolve current live export identity, exact file URL, source-level permissions, commercial automation rules and original response-size/hash bounds.

## Response contract

### Expected media types

- text/plain

**Format:** Polisa README text describes a proposed or available CSV version and detailed source caveats, not an authenticated CSV source or parsed insurer record.

**Scientific semantics:** Market-level named insurer and line-of-business premiums/claims/solvency statistics reconstructed from heterogeneous regulators, associations and insurer SFCRs. Account for entity-group rollups, currencies, conversion date, year, coverage and original-source lineage; not property location, actual insured TIV or model-ready CAT loss.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** Documentation-only; no live provider request, bulk download or automated enumeration is authorized by this contract.

**Mutability notes:** README names 2026-11-09.d5ad62; site displays another as-of date. Neither fixes a verified export file checksum nor consistent API schema; do not assume data availability from filenames.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** <https://polisapro.com/terms>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Polisa-generated ratios/shares are stated CC BY 4.0 but rights from original sources remain in force; restrictions include Serbia NBS for commercial use, other national associations and Estonia share-alike. Treat commercial use as unknown pending exact market/row/source check and resolve possible export-availability contradictions before automation.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://polisapro.com/data/README.txt>
- <https://polisapro.com/data>
- <https://polisapro.com/terms>
- <https://polisapro.com/methodology>

**Notes:** Documented-only readiness contract; zero supplier CSV bytes collected or uploaded. Exact source-level licences and mixed provenance preclude blanket commercial reuse and automatic insurer exposure calibration.
