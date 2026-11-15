<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dlr.wsf.evolution.1985-2015.stac.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dlr.wsf.evolution.1985-2015.stac.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** dlr.wsf.evolution.1985-2015.stac

## Source ids

- dlr.wsf.evolution.1985-2015

**Provider:** German Aerospace Center (DLR) Earth Observation Center

**Interface type:** stac

**Status:** documented_only

**Documentation url:** <https://web.geoservice.dlr.de/web/datasets/wsf_evo>

**Service root:** <https://geoservice.dlr.de>

**Api version:** DLR EOC OGC STAC v1; exact WSF_Evolution Collection response schema not yet live-tested

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

- document_stac_collection_metadata

### Path templates

- /eoc/ogc/stac/v1/collections/WSF_Evolution

**Parameter rules:** Documentation-only T0: the official provider advertises the fixed WSF_Evolution STAC collection path with f=json output. No network operation is enabled by this contract. Before promoting to probe_ready, independently review the exact fixed GET, Content-Type, response size, provider terms, anonymous automation cadence, redirects and schema. A future trusted runner must construct one fixed HTTPS request with optional literal f=json only, no caller-supplied host, path, URL, headers, pagination, filters, retries, item links or downloadable raster URLs.

## Response contract

### Expected media types

- application/json

**Format:** Provider STAC 1.x Collection for WSF_Evolution (not a STAC Item or a raster file); require collection identity, CC-BY-4.0 product label, explicit DLR provenance and advertised historical extent. Exact response body and schema not yet validated on the trusted runner.

**Scientific semantics:** World Settlement Footprint Evolution is a DLR-derived Landsat-5/7 30 m yearly settlement-detection history 1985-2015, conditioned on WSF2015 settlement extent. The provider separately publishes an Input Data Consistency (IDC) score. Historical detection/settlement classifications are NOT construction years, property counts, current demolished/reconstructed buildings, replacement values or an insured exposure portfolio. Temporal observation support can vary; IDC coverage and independent source comparisons must precede any historical-exposure CAT model use.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** DLR EOC Geoservice AUP v1.1 requires considerate lawful usage and permits suspension/traffic monitoring; no exact automated request quota or specific cadence for this STAC product was established. No live probe, polling, crawler, item enumeration or raster acquisition is authorized under documented_only. A separately reviewed probe must be one small public metadata request without retry.

**Mutability notes:** Original WSF Evolution product released 2021-11-01, historical coverage 1985-2015; collection JSON and active service may change independently of scientific raster tiles. Freeze exact collection response byte hash/UTC and later freeze STAC Item, raster original SHA-256, tile CRS, nodata, units and IDC vintage separately.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://geoservice.dlr.de/resources/licenses/geoservice/EOC_Geoservice_AUP_v1.1.pdf>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** Official WSF Evolution 1985-2015 product page and DLR Collection advertise CC-BY-4.0 with required source attribution; the standard licence allows commercial reuse and derivatives within its terms. The EOC Geoservice AUP 1.1 dated 2023-09-01 governs service access, storage and processing, requires lawful/considerate usage and accepts additional product-specific conditions. The AUP does not establish an automation rate for this exact STAC service, so automated commercial access remains unknown and must not be promoted from the CC-BY product label. Source/sensor lineage, IDC coverage, third-party rights, exact raster redistributability and internal repository admission remain separate reviews. Only public T0 metadata/documentation is in scope, no unreviewed source bytes in Git.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://web.geoservice.dlr.de/web/datasets/wsf_evo>
- <https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution?f=html>
- <https://geoservice.dlr.de/web/terms>
- <https://geoservice.dlr.de/resources/licenses/geoservice/EOC_Geoservice_AUP_v1.1.pdf>

**Notes:** New narrowly scoped documentation contract and offline-only fail-closed STAC Collection parser. Official Collection landing page and licence were reviewed on 2026-11-15; no original application/json Collection body was acquired in this work claim. First causal next step: approve one reviewed anonymous metadata-only GET in the trusted runner if DLR service-automation conditions permit it; pin its original response and verify the parser, then separately select a very small scientific raster/IDC region. No model admission, Neon write, raw data mirroring or inference of true building construction years.
