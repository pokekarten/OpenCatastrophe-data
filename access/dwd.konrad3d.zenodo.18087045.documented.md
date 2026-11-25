<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dwd.konrad3d.zenodo.18087045.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dwd.konrad3d.zenodo.18087045.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** dwd.konrad3d.zenodo.18087045.documented

## Source ids

- dwd.konrad3d.zenodo.18087045

**Provider:** Deutscher Wetterdienst

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/18087045>

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

- /records/18087045/files/KONRAD3D_201904.tar.bz2

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/x-bzip2

**Format:** Monthly tar.bz2 archives of XML snapshots; 5-minute analysis cadence in April 2019 sample

**Scientific semantics:** Distinct historical reprocessing archive, not the already documented operational endpoint dwd.konrad3d.operational. Zenodo API returned 88 files, 2219772181 bytes, license cc-by-4.0 on 2026-11-25. Bounded macOS download of https://zenodo.org/records/18087045/files/KONRAD3D_201904.tar.bz2?download=1 succeeded: 8792122 bytes, SHA-256 d573694526df63d2233bafa21176510c0336b23c30bb36c84f60155b76e188aa, MD5 14200f3dd87df73eec5c7a04ac56dc3c matches provider. Streaming tar scan without extraction: 8640 XML members, sum member bytes 209615753; v1.7 root and UTC reference times confirmed. File KONRAD3D_20190401T193500.xml includes cell identifier, geodetic centroid, polygons, echo top, reflectivity thresholds, VIL/VII, hail_flag, HYMEC hail/large-hail area and volume, ICON-EU CAPE/shear and lightning_rate (strokes/5min), lightning_density. Sentinel -1000000000 observed; preserve missingness and radar-sweep availability. Header grid DE4800_WGS84 250 m is underlying processing grid, not measured hail footprint resolution. Hail flag and HYMEC are radar-derived, not observed ground hail size; cell detection uses lightning, so not independent validation of lightning-only predictors without lineage-aware split/holdout. Archive was retrospectively processed in 2025; do not treat creation date as event date or forecast as observation. No raw bytes committed, no database ingestion; formal rights review and scientific admission remain open.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://about.zenodo.org/terms/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** DWD deposit API CC BY 4.0 and full April 2019 sample verified with provider MD5. Strong open-first priority. Review exact deposit and embedded third-party inputs; validate sentinel, units, track continuity and sample hail flags; admission must precede model training.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://zenodo.org/records/18087045>
- <https://about.zenodo.org/terms/>

**Notes:** Open-first qualification queue. DWD deposit API CC BY 4.0 and full April 2019 sample verified with provider MD5. Strong open-first priority. Review exact deposit and embedded third-party inputs; validate sentinel, units, track continuity and sample hail flags; admission must precede model training. Discovery/access only: no admission, no external bytes in Git, no model approval.
