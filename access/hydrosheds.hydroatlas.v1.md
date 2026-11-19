<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/hydrosheds.hydroatlas.v1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `hydrosheds.hydroatlas.v1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** hydrosheds.hydroatlas.v1

## Source ids

- hydrosheds.hydroatlas.v1

**Provider:** HydroSHEDS / HydroATLAS

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://www.hydrosheds.org/hydroatlas>

**Service root:** <https://api.figshare.com>

**Api version:** v2

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- basin_river_v10_archive_metadata

### Path templates

- /v2/articles/9890531

**Parameter rules:** One and only one explicitly manually dispatched anonymous HTTPS GET to https://api.figshare.com/v2/articles/9890531. No user-selected URL, headers, article version, file name, download URL, redirects, retries, pagination or asset retrieval. Parse only original public Figshare v2 article metadata and require exactly 7 reviewed v1 file identities (4 ZIP GIS archives, 3 PDFs) with provider-published sizes and supplied/computed MD5 metadata. Returned download URLs are not followed.

## Response contract

### Expected media types

- application/json

**Format:** Figshare public article 9890531, version 1, HydroATLAS version 1.0, CC BY 4.0 aggregate licence; seven exact original provider declared file IDs, sizes and MD5 values (4 GIS ZIP, 3 PDF). Original asset byte identity and per-column CC BY/ODbL licensing remain unverified.

**Scientific semantics:** The fixed archive record identifies HydroATLAS version 1.0 and its BasinATLAS/RiverATLAS global release files. HydroATLAS is a value-added hydro-environmental attribute database on the HydroSHEDS framework, not an event observation or hazard time series. BasinATLAS, RiverATLAS and LakeATLAS are distinct products; local-catchment and total-upstream attributes are not interchangeable, and topology/resolution and network-threshold limitations must remain explicit in any later model-facing sample.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** Figshare API recommends no more than one request per second; this contract is much narrower: exactly one manually triggered read-only public metadata GET, no retry, no scheduled live polling and 128 KiB/30s caps. Do not request any of the 12 GB of linked GIS/PDF data.

**Mutability notes:** The scientific release is pinned to HydroATLAS version 1.0 and Figshare article 9890531. The public metadata service is an access route, not scientific byte identity. Any later acquired file must bind its exact provider file identity, retrieval UTC, byte count and SHA-256 before scientific or publication use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://info.figshare.com/user-guide/figshare-policies/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** HydroATLAS version 1.0 is licensed as a CC BY 4.0 collective database. Its technical documentation states that every released attribute column is under either CC BY 4.0 or ODbL 1.0 and that both permit reuse for any purpose including commercial use; the exact per-column licence, citation, attribution and any ODbL database/share-alike obligations must remain attached to selected data. Figshare's public Data Access Policy and API guidance allow unauthenticated retrieval of public metadata/files and API mining subject to the content licence. These verified rights are source/API ceilings, not repository execution or publication approval: this contract deliberately remains documented_only with no live probe, and any persisted sample still requires exact asset identity, selected-column licence mapping, provenance, required attribution/share-alike handling and repository review before bytes are committed or published. This reviewed metadata-only execution does not broaden the collective CC BY 4.0 licence to per-column CC BY/ODbL obligations, guarantee original archive SHA-256, or authorize mirroring underlying content. Download links and provider-supplied MD5 values are references, not independently verified original files.

## Probe contract

**Mode:** metadata_get

**Operation:** basin_river_v10_archive_metadata

**Requires credentials:** `false`

### Expected evidence

- One exact public original Figshare API GET HTTP 200 JSON from article 9890531, version 1, no redirect and at most 131072 bytes
- HydroATLAS v1.0 source identity, CC BY 4.0 publication licence and public metadata status
- Exactly 7 original file metadata identities with approved IDs, sizes and provider supplied/computed MD5 equality: 4 GIS ZIPs and 3 PDFs
- Original metadata response bytes/SHA-256, exact request SHA-256, UTC retrieval time and trusted runner/contract SHA-256
- No original GIS/PDF source assets downloaded, no file bytes persisted, no per-column licence promotion, no CAT model admissions

**Implementation decision:** build_later

**Reviewed at:** 2026-11-12

## Evidence urls

- <https://www.hydrosheds.org/hydroatlas>
- <https://www.hydrosheds.org/terms-of-use>
- <https://data.hydrosheds.org/file/technical-documentation/HydroATLAS_TechDoc_v10_1.pdf>
- <https://figshare.com/articles/dataset/HydroATLAS_version_1_0/9890531>
- <https://doi.org/10.6084/m9.figshare.9890531>
- <https://info.figshare.com/user-guide/figshare-policies/>
- <https://info.figshare.com/user-guide/how-to-use-the-figshare-api/>
- <https://docs.figshare.com/>

**Notes:** Review and implement exactly one bounded public Figshare article-v1 metadata probe, not an original GIS asset download. BasinATLAS and RiverATLAS files total 11+ GB; provider MD5 declarations are metadata, not independently computed original-asset hashes. Any future sample must separately review article version/asset rights, per-column CC BY 4.0 or ODbL 1.0 attribution/share-alike and geographic/attribute semantics before modelling. No automatic provider poll, private storage write or CAT model admission.
