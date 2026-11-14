<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/fema.usa-structures.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `fema.usa-structures.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** fema.usa-structures

## Source ids

- fema.usa-structures

**Provider:** Federal Emergency Management Agency / ORNL / USGS, distributed as an Esri U.S. Federal Datasets ArcGIS public view

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://gis-fema.hub.arcgis.com/datasets/fedmaps::usa-structures/about>

**Service root:** <https://services2.arcgis.com/FiaPA4ga0iQKduv3>

**Api version:** ArcGIS public hosted FeatureServer VIEW; Esri item 0ec8512ad21e4bb987d7e848d14e7e24; layer id 0 (USA_Structures_A observed 2026-11-13)

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

- usa_structures_service_metadata

### Path templates

- /arcgis/rest/services/USA_Structures_View/FeatureServer

**Parameter rules:** Documentation-only metadata binding. Exact original Esri public-item GET https://www.arcgis.com/sharing/rest/content/items/0ec8512ad21e4bb987d7e848d14e7e24?f=json and corresponding fixed FeatureServer metadata GET (?f=pjson) were independently retrieved 2026-11-13 and matched item ID and service URL. THIS access contract does not grant execution, query, export or bulk data access. Do not use old services.arcgis.com/VhMjCzR3cIjEkh7L/USA_Structures: its separate Esri item a51353d9b1d14b2ea3dc2f2eefb220d3 advertises a regional local projection 3452, not the US-wide published view. The public national view uses EPSG:3857 and layer id 0. No user-supplied query, headers, paging, object IDs, polygon geometries, attribute queries or feature extraction; an executable metadata probe requires separate review.

## Response contract

### Expected media types

- application/json

**Format:** Two original metadata-only JSON documents (public Esri item identity + fixed national FeatureServer view metadata); item id 0ec8512ad21e4bb987d7e848d14e7e24, matching serviceItemId, national WKID 3857 extent, observed layer 0 USA_Structures_A. No features or source asset bytes.

**Scientific semantics:** The Esri U.S. Federal Datasets public view references FEMA/ORNL/USGS USA Structures greater than 450 sq ft and is not the same entity as the original FEMA catalog FEMA-0209 publication or the unrelated historical narrow regional service. The hub advertises a September 13 2026 data currency; ArcGIS public view/item are mutable and do not independently establish a fixed release archive, exact country coverage or valid structure count. Local initial extent is not national coverage, and the national fullExtent may include world-wrap regions. Modelled structures are NOT parcel, insured value, policy, reconstruction cost, ownership, surveyed footprint or claims truth. Occupancy, population, address and local quality limitations require per-field and per-vintage review; no CAT source/model admission.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** The public feature service advertises a maxRecordCount of 2000, which is a server page maximum and NOT a commercial extraction permission or a request budget. No numerical automated-access entitlement verified. Metadata observation only: two fixed original small JSON reads were performed independently; no feature query, export, follow-up URL or bulk download permitted by this contract.

**Mutability notes:** 2026-11-13 original REST metadata observations: public Esri item original body 9601 bytes SHA-256 90b735393979db65b83896bea85beee13b368cccc31a747e0a826c3807d4822d; corresponding national FeatureServer metadata original body 4164 bytes SHA-256 d755bc79c1e3c3b52eb8abc60130b87cbd94840ec899b14e227ebd5130049ba7. Former regional service original body 4815 bytes SHA-256 950a0bcf61dd665ac71a168ec473e1d588554e94d4ddea9aa05bf33bfb660100, item a51353d9b1d14b2ea3dc2f2eefb220d3. Hashes are of transient original response bytes, not of original building features, historic release assets or complete dataset. Mutable item and view must be independently revalidated before any future execution.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://www.arcgis.com/home/item.html?id=0ec8512ad21e4bb987d7e848d14e7e24>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** 2026-11-13 original Esri federal item metadata owned by Esri_US_Federal_Data is public and its per-item HTML licenseInfo explicitly states Creative Commons Attribution CC BY 4.0. Official FEMA hub references that precise published Esri item. This verifies the published item license label only; the original federal Data.gov FEMA-0209 catalogue separately lists U.S. government-works. No blanket licensing is inferred for constituent third-party attributes, address/population components, the historical wrong regional service, unlimited feature exports, bulk commercial API access, redistribution of complete raw building geometries, or downstream insurer CAT data. Separate service conditions, attribution/source-of-truth, redistribution and scientific review still required. Metadata-only observation/persistence is research-only; no model input admission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://gis-fema.hub.arcgis.com/datasets/fedmaps::usa-structures/about>
- <https://www.arcgis.com/sharing/rest/content/items/0ec8512ad21e4bb987d7e848d14e7e24?f=json>
- <https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/USA_Structures_View/FeatureServer?f=pjson>
- <https://services.arcgis.com/VhMjCzR3cIjEkh7L/arcgis/rest/services/USA_Structures/FeatureServer?f=pjson>
- <https://catalog.data.gov/dataset/usa-structures>
- <https://gis-fema.hub.arcgis.com/pages/usa-structures>

**Notes:** Research identity correction: on 2026-11-13 the previous services.arcgis.com/VhMjCzR3cIjEkh7L route was proven to be a DIFFERENT ArcGIS service item and regional projection. The authoritative FEMA Hub points to the Esri U.S. Federal Datasets public item 0ec8512ad21e4bb987d7e848d14e7e24 and its nationwide full-extent view at services2.arcgis.com/FiaPA4ga0iQKduv3. Both exact provider metadata original responses were read and SHA-256 fingerprinted without collecting feature data. Keep documented_only; view is mutable, API terms and feature-data rights/admission remain unresolved. See docs/research/fema-usa-structures-2026-original-item-service-identity-20261113.md.
