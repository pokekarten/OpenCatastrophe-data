<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/es.miteco.snczi.longitudinal-defence-works.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `es.miteco.snczi.longitudinal-defence-works.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** es.miteco.snczi.longitudinal-defence-works.2026

## Source ids

- es.miteco.snczi.longitudinal-defence-works.2026

**Provider:** Ministerio para la Transicion Ecologica y el Reto Demografico (MITECO), Spain

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.miteco.gob.es/es/cartografia-y-sig/ide/descargas/agua/iol.html>

**Service root:** <https://www.mapama.gob.es>

**Api version:** Inventario de Obras Longitudinales, MITECO download page dated 2022-06-24; version of current ZIP unknown

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

- download_fixed_iol_zip

### Path templates

- /app/descargas/descargafichero.aspx

**Parameter rules:** Official catalog advertises one original ZIP link at https://www.mapama.gob.es/app/descargas/descargafichero.aspx?f=iol.zip . The only candidate request is a read-only GET of that exact publisher URL with literal query f=iol.zip, no caller-selected host, path, query, filename, redirects, range-scan, retry, pagination or bulk enumeration. No live request is authorized by this documentation-only contract. Confirm the current canonical host, redirect policy, service terms, response media type, archive version and actual byte size before enabling a trusted-runner probe.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** Provider-described 5.63 MB compressed original Shapefile distribution, cartography in ETRS89, with accompanying documentation; no actual original bytes, ZIP member inventory, CRC, SHA-256 or feature schema verified.

**Scientific semantics:** Official Spanish flood defence and riverbank stabilization structures at declared map scale 1:25000; hydrological intercommunity catchments, not necessarily all regional basins. Official product page dates update 2022-06-24, not a current frozen feature vintage. Defence structures and bank-stabilization works must be distinguished; mere presence, type, height or administrative status does not prove a functioning hydraulic protection effect, overtopping probability, return period or building insured loss. Validate feature type, unit, geometry, CRS EPSG and time semantics on original bytes before any flood CAT model calibration.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `131072`

**Max sample bytes:** `8388608`

**Retry policy:** none

**Rate limit notes:** The provider download page permits free reuse with attribution, but separate automated HTTP access limits, request cadence and redirect policy were not independently established. No execution or repeat fetch is authorized. Future one-object acquisition requires reviewed provider terms, bounded trusted runner, no arbitrary requests and strict content/ZIP limits.

**Mutability notes:** The ZIP URL is not immutable and links through a legacy mapama domain. The website says last update 2022-06-24 but does not pin a digest, internal archive revision or release identifier. Preserve original GET URL, final URL/redirect trail, UTC, bytes, SHA-256, ZIP CRC/member listing, CRS and per-feature version after a rights-cleared original download; do not reuse an earlier digest for a changed file.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** MITECO official product page explicitly states free reuse with attribution to the Ministry (copyright attribution); the Spanish government open-data catalogue separately marks the dataset CC BY 4.0. This is promising product rights evidence, not a completed provider-service contractual review. Verify exact ZIP scope, attribution, commercial internal modelling, derivatives and publication against the currently distributed asset and service access conditions. No source-data approval, automated retrieval authorization, public raw redistribution or model admission is claimed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.miteco.gob.es/es/cartografia-y-sig/ide/descargas/agua/iol.html>
- <https://datos.gob.es/es/catalogo/e0dat0002-inventario-de-obras-longitudinales>
- <https://www.miteco.gob.es/es/agua/temas/gestion-de-los-riesgos-de-inundacion/planes-gestion-riesgos-inundacion/acceso-inventario-obras-de-proteccion-frente-a-inundaciones.html>
- <https://catalogo.datosabiertos.miteco.gob.es/catalogo/dataset/9c79a721-81f4-4a68-981b-4b636992b1ba>

**Notes:** T0 documentation-only source-access specification. Candidate already exists in landscape/sources-nl-es-flood-defence-20261114.json; this file is its machine-access contract, not a new source registry. No T1-T4 provider request, bytes, SHA-256, Neon storage or scientific approval. Next causal step: independently settle ZIP-specific data and HTTP-service terms, pin its current exact original identity, then implement a bounded trusted-main one-shot ZIP-header or archive sample check with synthetic zip-bomb and HTML-error negative tests; do not interpret this contract as authorization to fetch.
