<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/de.bkg.vg250.3112.2025.md5.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `de.bkg.vg250.3112.2025.md5.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** de.bkg.vg250.3112.2025.md5

## Source ids

- de.bkg.vg250.3112.2025

**Provider:** Bundesamt fuer Kartographie und Geodaesie (BKG)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html>

**Service root:** <https://daten.gdz.bkg.bund.de>

**Api version:** BKG VG250 31.12.2025 UTM32s GeoPackage Ebenen ZIP original published MD5 sidecar only

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- get_exact_vg250_2025_gpkg_md5_sidecar

### Path templates

- /produkte/vg/vg250_ebenen_1231/aktuell/vg250_12-31.utm32s.gpkg.ebenen.zip.md5

**Parameter rules:** Exactly one read-only fixed HTTPS GET for one public original publisher MD5 sidecar, no credentials, redirects, query, freeform host, path, provider version, operator-selected size, retries, arbitrary headers or unreviewed bulk ZIP retrieval. Refuse responses above 128 bytes. This small sidecar is not the full ZIP (about 67 MB) and /aktuell/ can be re-pointed by the provider. Any MD5 or filename drift blocks rather than silently accepts a new 2026 vintage.

## Response contract

### Expected media types

- text/plain
- application/octet-stream

**Format:** Single GNU md5sum-like ASCII record (publisher ZIP MD5 hex followed by exactly one prescribed ZIP basename), measured response approximately 69 bytes; no original ZIP, geometry or coordinate data.

**Scientific semantics:** Strict 2025 official product reference and published checksum sidecar only. An MD5 value copied from a publisher sidecar is a claim about the whole ZIP, not a verified whole-file SHA-256, GPKG SQLite integrity, 2025 temporal-vintage confirmation inside the archive, valid national boundaries, coastline-versus-land GF2/GF4 mapping or CAT input. Compare independently to immutable BKG 2022 source, Natural Earth v5.1.1 and geoBoundaries DEU ADM1 2021 without silently merging vintages.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `128`

**Max sample bytes:** `128`

**Retry policy:** none

**Rate limit notes:** Official BKG product page offers public no-auth direct download, under its DL-DE BY 2.0 terms. Limit probe to one fixed metadata file, at most once on trusted-main workflow merge or manual dispatch; no schedule, crawler, bulk ZIP request or entire WFS. An individual public GET is not global unmetered-API permission.

**Mutability notes:** Official product metadata shows stand 31.12.2025 updated 10 June 2026. Public /aktuell/ alias is mutable; the reviewed sidecar publishes ZIP MD5 e6b4cf28d4b83557b4d6e3236713dec0, which is only MD5, NOT the missing complete original 2025 ZIP SHA-256. Bind original sidecar response byte count + SHA-256/UTC; future mismatch requires fresh exact-version/license/source review.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://sgx.geodatenzentrum.de/web_public/gdz/lizenz/deu/nutzungsbedingungen_vg250.pdf>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Official BKG product page advertises anonymous direct downloads for everyone, with source-specific Datenlizenz Deutschland Namensnennung 2.0 allowing commercial data reuse with mandatory prominent BKG/year, licence link, source-data contributors and alteration notice. This permission is scoped here to one tiny public sidecar GET; no separate unauthenticated bulk-crawling, rate-limit exemption, raw Git publication or CAT scientific admission is inferred.

## Probe contract

**Mode:** provider_specific

**Operation:** get_exact_vg250_2025_gpkg_md5_sidecar

**Requires credentials:** `false`

### Expected evidence

- one fixed BKG HTTPS 200 response, no redirects or credentials
- strict at-most-128-byte original sidecar response, publisher checksum/filename identity
- original metadata body byte size and SHA-256; provider ZIP MD5 value separately labeled
- UTC observation; source path pinned to published /aktuell/ and drift refused
- no original ZIP download and no raw provider bytes persisted
- model_input_approved=false; independent border truth not established

**Implementation decision:** build_later

**Reviewed at:** 2026-11-16

## Evidence urls

- <https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html>
- <https://sgx.geodatenzentrum.de/web_public/gdz/lizenz/deu/nutzungsbedingungen_vg250.pdf>
- <https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/aktuell/>
- <https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/aktuell/vg250_12-31.utm32s.gpkg.ebenen.zip.md5>

**Notes:** T1 one tiny original publisher sidecar is a metadata-only gate; no full original ZIP SHA or area/geometry findings. Build an exact-version-pinned full ZIP offline GPKG national/admin and GF4 land / GF2 water integrity checker before original 2025 download or CAT use. The earlier 2022 VG250 archive has a separate SHA and differing reference date.
