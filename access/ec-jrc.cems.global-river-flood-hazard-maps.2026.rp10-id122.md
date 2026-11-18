<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.cems.global-river-flood-hazard-maps.2026.rp10-id122.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.cems.global-river-flood-hazard-maps.2026.rp10-id122.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.cems.global-river-flood-hazard-maps.2026.rp10-id122

## Source ids

- ec-jrc.cems.global-river-flood-hazard-maps.2026

**Provider:** European Commission Joint Research Centre / Copernicus Emergency Management Service / GloFAS

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://data.jrc.ec.europa.eu/dataset/jrc-floods-floodmapgl_rp50y-tif>

**Service root:** <https://jeodpp.jrc.ec.europa.eu>

**Api version:** CEMS-GLOFAS Global river flood hazard maps v2.1.2; RP10 tile ID122 N50_E10; JRC catalogue DOI 10.2905/JRC.VD32YWG

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

- fetch_rp10_depth
- fetch_rp10_depth_reclass
- fetch_permanent_water
- fetch_spurious_depth_areas

### Path templates

- /ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/RP10/ID122_N50_E10_RP10_depth.tif
- /ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/RP10/ID122_N50_E10_RP10_depth_reclass.tif
- /ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/Permanent_WaterBodies/ID122_N50_E10_permanent_water.tif
- /ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/Spurious_Depths/ID122_N50_E10_spurious_depth_areas.tif

**Parameter rules:** Documentation-only exact-asset contract. No HTTP request is authorized yet. Future execution may select only one of the four repository-controlled ID122/N50_E10 paths above at a time; callers must not supply return period, tile ID, latitude/longitude token, filename, directory, host, query string, header, redirect target, representation or release substitution. No directory crawl, tile-index expansion, wildcard, adjacent-tile fetch, other-return-period substitution or global mirror is authorized. A scientific use of the raw or categorized depth tile must preserve the companion permanent-water and spurious-depth identities in run provenance even when those companion files are not downloaded in the same request.

## Response contract

### Expected media types

- image/tiff
- application/octet-stream

**Format:** Four fixed GeoTIFF assets for global flood-hazard tile ID122 / N50_E10. The RP10 raw tile contains flood water depth in metres; the categorized RP10 tile encodes classes 1: &lt;1 m, 2: 1-&lt;3 m, 3: 3-&lt;10 m, 4: &gt;10 m and excludes the separate Permanent water class. Companion rasters identify permanent water bodies and RP10 spurious-depth areas.

**Scientific semantics:** CEMS Global river flood hazard maps v2.1.2 are modelled return-period inundation surfaces produced from LISFLOOD hydrological flows and LISFLOOD-FP inundation simulations on a WGS84 3-arc-second (~90 m) grid. RP10 is a modelled 1-in-10-year hazard scenario, not an observed event footprint, gauge measurement or annual probability assigned to an individual asset. The spurious-depth companion identifies areas where depths above 10 m are predicted in small channels below 3,000 km² for the RP10 scenario plus a 2 km buffer; provider documentation also warns that unrealistically high depths can result from hydraulic-model limitations, DEM sinks, tile-boundary effects and residual DEM issues. Permanent water must remain distinct from flood depth, and excluded/flagged companion semantics must not be silently converted into unqualified inundation truth. The JRC catalogue states that this dataset is not an official flood hazard map and local/national authoritative maps remain scientifically distinct.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `26214400`

**Retry policy:** none

**Rate limit notes:** JRC exposes the fixed flood-hazard directories anonymously. This documented-only contract authorizes no network request, retry loop, directory crawl, tile-index traversal or batch acquisition. No repository-specific numeric request budget or separate automated-download entitlement for the JEODPP host was established. The current provider index reports the raw ID122 RP10 depth tile at about 15 MiB, the reclassified tile at about 2.2 MiB, the permanent-water tile at about 810 KiB and the spurious-depth tile at about 185 KiB; each fits the current 25 MiB per-sample ceiling individually.

**Mutability notes:** Scientific identity is pinned to CEMS-GLOFAS Global river flood hazard maps dataset version 2.1.2, README update 2026-01-12, return period RP10, tile ID122 / N50_E10 and the exact four filenames. The v2.1.2 README itself records DOI/PID as NA, while the current JRC Data Catalogue cites the broader dataset as DOI 10.2905/JRC.VD32YWG / PID jrc-floods-floodmapgl_rp50y-tif; this contract preserves that distinction and does not invent a version-specific DOI. Any future acquisition must bind requested/final URL, retrieval UTC, byte count, SHA-256, GeoTIFF CRS/grid/nodata/dtype and companion-mask identities. Do not silently mix older v2.x tiles or substitute a later release. The current provider-hosted README (last-update field 2026-01-12; published directory listing modified 2026-10-21) declares ODbL 1.0 while the separately hosted 2026 copyright notice declares CC BY 4.0; resolving their applicability to exact April/2026 versioned original assets is a prerequisite for new data/sample storage or commercial CAT modelling.

## Rights and policy

**Dataset rights status:** conflicting

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** OFFICIAL TERMS CONFLICT, fail closed as of 2026-11-15: the v2.1.2 product README at https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/README.txt (A02) explicitly names Open Data Commons Open Database License v1.0 (ODbL 1.0); the current publisher JRC Data Catalogue also lists ODbL 1.0 as use conditions. In contrast, both the flood_hazard/copyright.txt and parent CEMS-GLOFAS/copyright.txt identify CC BY 4.0 for EU dataset/database rights. Those authoritative same-product notices are not reconciled to an exact asset, version or derived database scope. ODbL and CC BY 4.0 can carry materially different attribution/share-alike/database obligations, particularly for redistribution of a transformed commercial CAT dataset. Do not select whichever notice is more convenient or treat the earlier CC BY statement as overriding the product-specific ODbL; request publisher clarification and source-specific legal review. Dataset commercial rights, raw/derived redistribution, retention and share-alike obligations remain unresolved. Static documented-only route: no automated download, probe, persisted original bytes or model admission; independent API/service terms and request cadence remain unknown.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://data.jrc.ec.europa.eu/dataset/jrc-floods-floodmapgl_rp50y-tif>
- <https://doi.org/10.2905/JRC.VD32YWG>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/README.txt>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/CHANGELOG.txt>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/copyright.txt>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/RP10/>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/Permanent_WaterBodies/>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/Spurious_Depths/>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/copyright.txt>

**Notes:** Current T0 review 2026-11-15 found directly conflicting official source-level licence notices: v2.1.2 README and JRC catalogue say ODbL 1.0, while same service copyright files say CC BY 4.0. Previously recorded dataset-rights verification and permitted redistribution are withdrawn pending authoritative reconciliation and legal review. The exact ID122/N50_E10 RP10 raw/reclass/permanent-water/spurious-depth quartet remains an identity-only prospective hazard/QA pilot. No source-byte request, GeoTIFF, adapter execution, Neon import or scientific admission in this review. Do not assume any specific output database/share-alike treatment without legal resolution.
