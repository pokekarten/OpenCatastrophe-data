<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/fao.cropgrids.2020.figshare-v9.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `fao.cropgrids.2020.figshare-v9.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** fao.cropgrids.2020.figshare-v9

## Source ids

- fao.cropgrids.2020.global

**Provider:** CROPGRIDS research consortium (Tang et al.) via Figshare; distinct from the later FAO/CGIAR COG derivatives

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://figshare.com/articles/dataset/CROPGRIDS/22491997>

**Service root:** <https://api.figshare.com>

**Api version:** Figshare article 22491997 version 9 (2024-04-23); original CROPGRIDSv1.08 NetCDF distribution

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

- cropgrids_v9_article_metadata

### Path templates

- /v2/articles/22491997/versions/9

**Parameter rules:** Frozen Figshare article version 9 metadata route only. Earlier separate Neon research sample \#14 records 6 original article file identities, not original NetCDF pixels. This documented_only contract forbids execution, request parameters, free-form URLs, file-download URL following, archive streaming, pagination, automatic mirrors and metadata-to-asset escalation. Any future fixed bounded request requires legal/API re-review, a trusted source-specific runner and strict response identity, content type and SHA-256 verification.

## Response contract

### Expected media types

- application/json

**Format:** Original Figshare article version 9 JSON metadata, listing 6 files: CODES.zip; CROPGRIDS_Dataset_Distribution.pdf; CROPGRIDSv1.08_NC_maps.zip; CROPGRIDSv1.08_PNG_maps.zip; Table_CROPGRIDSv1.08_COU.xlsx; Tang_ETAL_2024_SDATA_CROPGRIDS.pdf. No original asset bytes were retrieved under this contract.

**Scientific semantics:** CROPGRIDSv1.08 maps modelled 2020 harvested area (harvarea, hectares) and physical crop area (croparea, hectares) of 173 crops on a WGS84 0.05-degree global grid, alongside source/quality flags. Repeated harvests can yield harvarea greater than croparea. The gridded estimates fuse earlier MRF, additional gridded sources, subnational reports and FAOSTAT 2020: they are not independent FAOSTAT total validation, field boundaries, insured area, TIV or agricultural CAT losses. The original Figshare v9 six-file release must not be conflated with the later FAO/CGIAR COG catalogue of 171 distinct file identities; inspect original per-crop NetCDF and the source quality flags before scientific use.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** No source-specific automated API request rate reviewed for this exact Figshare release. This documentation-only contract grants no new request. Avoid scheduled crawling or large downloads; original NetCDF zip is approximately 806.9 MB, exceeding the bounded metadata scope.

**Mutability notes:** Exact Figshare version 9 frozen; article version 9 was published 2024-04-23. Underlying CROPGRIDSv1.08 assets remain distinct from metadata. Research Neon sample \#14 was obtained 2026-11-11 and records original article metadata only, including six advertised file names and bytes, not independent asset hashes or per-NetCDF contents. Do not treat provider-side file metadata or original metadata SHA as a verified GIS asset SHA.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://figshare.com/articles/dataset/CROPGRIDS/22491997>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The original research data distribution note and linked Figshare record describe CC BY 4.0 for CROPGRIDS research release; this is a product/release claim, not independent verification of every bundled third-party input, its provenance or the distinct later CGIAR/FAO derivative. Figshare API/Data Access Policy and any version-9 asset-specific restrictions still require authoritative review. In particular, commercial insurer CAT modelling, automated service calls, retention, publication of raw/derived per-crop assets and share-alike/attribution obligations are not declared allowed by this contract. Until resolved, commercial automation and raw or derived redistribution are not approved.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://figshare.com/articles/dataset/CROPGRIDS/22491997>
- <https://doi.org/10.6084/m9.figshare.22491997.v9>
- <https://www.nature.com/articles/s41597-024-03247-7>
- <https://www.fao.org/agroinformatics/training-and-resources/data-sets/data-set-detail/cropgrids-data-on-harvested-and-crop-areas/en>

**Notes:** T0 research: exact original Figshare 22491997/v9 and CROPGRIDSv1.08 2020 variables, units and provenance identified. Prior private Neon sample \#14 is a public metadata research observation, not a new original crop raster download, verified per-crop content, licence or CAT model admission. T1-T4 not executed in this change. Next smallest step: verify precise Figshare API and version-9 per-asset rights and one allowed fixed metadata probe; then select a tiny version-pinned crop NetCDF sample outside public Git and check WGS84, nodata, harvested/crop-area units and original SHA.
