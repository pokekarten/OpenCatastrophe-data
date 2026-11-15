<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/pbl.grip4.catalogue.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `pbl.grip4.catalogue.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** pbl.grip4.catalogue.documented

## Source ids

- pbl.grip4.global-roads

**Provider:** PBL Netherlands Environmental Assessment Agency / GLOBIO

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://dataportaal.pbl.nl/GRIP4>

**Service root:** <https://dataportaal.pbl.nl>

**Api version:** `null`

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

- inspect_provider_catalogue
- inspect_published_checksum_index

### Path templates

- /GRIP4

**Parameter rules:** Documentation-only, no executable requests authorized by OpenCatastrophe. The PBL page exposes named files including /data/GRIP4/GRIP4_density_total.zip (approximately 3.5 MB) and /data/GRIP4/GRIP4_Region7_vector_fgdb.zip (approximately 36.6 MB). These concrete paths are evidence references, not permitted download operations. No arbitrary URL, host, file name, headers, redirect destination, query parameters or range requests may be caller supplied. After exact rights review, a separate bounded artifact-specific contract may be proposed.

## Response contract

### Expected media types

- text/html

**Format:** Provider GRIP4 data download catalogue and independent published Zenodo checksum index only; no external ZIP bytes are authorized by this documentation contract.

**Scientific semantics:** GRIP4 is a historical harmonized global road network plus derived road-density rasters at 5 arcminutes, not current road operational status, detailed bridge asset values, insured road replacement costs, or a flood/wind vulnerability model. Preserve vector region, UNSDI transportation classification, original source-vintage and provenance, and avoid treating OSM-derived geometry as independent from OSM comparisons.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No automated query, HEAD, range download, ZIP fetch, checksum readback or data acquisition is authorized. The documentation was manually examined; no OpenCatastrophe network probe was executed.

**Mutability notes:** Provider HTML and file links can change without a version bump. Zenodo record 6420961 names GRIP4_density_total.zip with MD5 24d3ed5c079f7a898fbc4a5d68be337a; this MD5 belongs to that Zenodo artifact, not automatically the current PBL ZIP. Future acquisition must record exact redirect-free URL, UTC time, byte count, SHA-256, checksum match if appropriate, inner archive members and downstream dataset identity before relying on any bytes.

## Rights and policy

**Dataset rights status:** conflicting

**Api terms status:** unknown

**Terms url:** <https://dataportaal.pbl.nl/GRIP4>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Provider conflict verified 2026-11-02: PBL GRIP4 catalogue and primary Zenodo record 6420961 state CC0; GLOBIO provider Resources page states CC BY 4.0; data.overheid.nl dataset header states CC0 but download resource advertises SHAPE CC-BY 4.0. A third-party republishing GIS service cites ODbL. Do not inherit any presumed CC0 clearance across source variants or upstream OSM rights. Require exact distributor/version/file and source-specific rights review before automated commercial access or publication.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://dataportaal.pbl.nl/GRIP4>
- <https://www.globio.info/resources>
- <https://zenodo.org/records/6420961>
- <https://data.overheid.nl/en/dataset/global-roads-inventory-project--grip----pbl-2018>

**Notes:** T0 metadata-only access evidence. This is a deliberately nonexecutable contract for the GRIP4 catalogue while authoritative licensing is inconsistent; no download, live API probe, schema interpretation of original bytes, admission or Neon warehouse ingestion is claimed. First sample candidate after rights clearance: exact Zenodo GRIP4_density_total.zip (3.6 MB published) with published MD5 and independently computed SHA-256; compare against the PBL distribution without assuming byte identity, then separately inspect Region7 Oceania vector geometry and property definitions.
