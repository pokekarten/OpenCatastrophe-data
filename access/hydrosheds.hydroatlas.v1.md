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

**Status:** documented_only

**Documentation url:** <https://www.hydrosheds.org/hydroatlas>

**Service root:** <https://api.figshare.com>

**Api version:** v2

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

- basin_river_v10_archive_metadata

### Path templates

- /v2/articles/9890531

**Parameter rules:** Static documentation contract only. The archival metadata identity is fixed to Figshare public article 9890531 for HydroATLAS version 1.0 (BasinATLAS and RiverATLAS). A future reviewed implementation may resolve only this fixed article and the exact listed BasinATLAS_Data_v10.gdb.zip metadata identity; callers must not supply a host, article ID, file name, path, headers, arbitrary query parameters or download URL. The Figshare API is secondary archival metadata infrastructure and must not be represented as a native HydroATLAS scientific query API.

## Response contract

### Expected media types

- application/json

**Format:** Figshare public article metadata JSON for the fixed HydroATLAS v1 archival record.

**Scientific semantics:** The fixed archive record identifies HydroATLAS version 1.0 and its BasinATLAS/RiverATLAS global release files. HydroATLAS is a value-added hydro-environmental attribute database on the HydroSHEDS framework, not an event observation or hazard time series. BasinATLAS, RiverATLAS and LakeATLAS are distinct products; local-catchment and total-upstream attributes are not interchangeable, and topology/resolution and network-threshold limitations must remain explicit in any later model-facing sample.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** No repository-specific numeric Figshare API rate-limit assumption is made. Figshare publicly documents API access and responsible-use guidance, but this contract remains documentation-only and authorizes no live probe. Any future metadata receipt must remain a single fixed-record lookup under the reviewed public API/access policy and current operational guidance.

**Mutability notes:** The scientific release is pinned to HydroATLAS version 1.0 and Figshare article 9890531. The public metadata service is an access route, not scientific byte identity. Any later acquired file must bind its exact provider file identity, retrieval UTC, byte count and SHA-256 before scientific or publication use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://info.figshare.com/user-guide/figshare-policies/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** HydroATLAS version 1.0 is licensed as a CC BY 4.0 collective database. Its technical documentation states that every released attribute column is under either CC BY 4.0 or ODbL 1.0 and that both permit reuse for any purpose including commercial use; the exact per-column licence, citation, attribution and any ODbL database/share-alike obligations must remain attached to selected data. Figshare's public Data Access Policy and API guidance allow unauthenticated retrieval of public metadata/files and API mining subject to the content licence. These verified rights are source/API ceilings, not repository execution or publication approval: this contract deliberately remains documented_only with no live probe, and any persisted sample still requires exact asset identity, selected-column licence mapping, provenance, required attribution/share-alike handling and repository review before bytes are committed or published.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://www.hydrosheds.org/hydroatlas>
- <https://www.hydrosheds.org/terms-of-use>
- <https://data.hydrosheds.org/file/technical-documentation/HydroATLAS_TechDoc_v10_1.pdf>
- <https://figshare.com/articles/dataset/HydroATLAS_version_1_0/9890531>
- <https://doi.org/10.6084/m9.figshare.9890531>
- <https://info.figshare.com/user-guide/figshare-policies/>
- <https://info.figshare.com/user-guide/how-to-use-the-figshare-api/>
- <https://docs.figshare.com/>

**Notes:** Static metadata/access boundary only. The primary scientific distribution remains the versioned HydroATLAS bulk-file release; Figshare REST is recorded solely as a secondary archival metadata/identity route. Verified source/API rights do not activate execution: no provider bytes, live request, adapter, action dispatch, admission promotion or publication decision is introduced. Do not substitute HydroBASINS/HydroRIVERS/HydroLAKES for HydroATLAS merely to obtain smaller files, and do not treat connectivity as catastrophe-model fitness.
