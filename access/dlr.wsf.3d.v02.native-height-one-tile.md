<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dlr.wsf.3d.v02.native-height-one-tile.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dlr.wsf.3d.v02.native-height-one-tile.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** dlr.wsf.3d.v02.native-height-one-tile

## Source ids

- dlr.wsf.3d.v02

**Provider:** German Aerospace Center (DLR), Earth Observation Center / EOC Geoservice

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://web.geoservice.dlr.de/web/datasets/wsf_3d>

**Service root:** <https://download.geoservice.dlr.de>

**Api version:** WSF 3D Version 02; original single one-degree tile e021_s24_e022_s25; BuildingHeight native GeoTIFF

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- document_fixed_wsf3d_v02_native_buildingheight_tile

### Path templates

- /WSF3D/files/tiles/e021_s24_e022_s25/WSF3D_V02_e021_s24_e022_s25_BuildingHeight.tif

**Parameter rules:** T0 documentation-only fixed original provider GeoTIFF file identity; official DLR index advertises one 1x1 degree e021_s24_e022_s25 BuildingHeight.tif at approximately 41.1 KiB. No new network GET, HEAD, HTTP Range, retries, WMS pseudo-pixel extraction, arbitrary tile/location, user-supplied URL, host, path, query, headers, redirect, full download or scheduled polling is authorised. A future T1/T3 needs a separately approved trusted-runner exact request and service-specific automation cadence, full received-byte hash, GeoTIFF CRS/units/NoData and provider-byte receipt.

## Response contract

### Expected media types

- image/tiff
- image/geotiff
- application/octet-stream

**Format:** Original LZW-compressed WSF3D V02 BuildingHeight GeoTIFF file, not rendered WMS PNG preview; exact TIFF layout, total original byte count, CRS, scale, nodata and native numeric values remain untested.

**Scientific semantics:** DLR WSF 3D v02 provides globally gridded average building height in metres at nominal 90 m resolution. The version-specific layer measures aggregated building height, not individual surveyed building storeys, insured replacement value, number of structures, flood vulnerability, observed storm damage or insurer losses. The small single southern-African tile is a future technical sample only, never a representative global or independent urban accuracy benchmark.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `4096`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** DLR EOC Geoservice AUP v1.1 governs the DLR Download Service. The source-specific CC BY 4.0 licence does not specify automated transfer cadence. AUP requires non-disruptive use and reserves enforcement, with no separately established numeric maximum or automated HTTP Range entitlement for this WSF3D V02 file. Thus network mode remains none until a responsible, explicitly reviewed exact single-file or bounded range acquisition is approved.

**Mutability notes:** Official provider file listing observed 2026-11-15 advertises exact WSF3D V02 1x1 degree tile and size approximately 41.1 KiB. This is a directory observation, not an original-body HTTP receipt. No source TIFF bytes, original SHA-256, tagged GeoTIFF coordinates, nodata, scale or producer digest were obtained or proven. A release path is not proof of byte immutability.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://geoservice.dlr.de/resources/licenses/geoservice/EOC_Geoservice_AUP_v1.1.pdf>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The official DLR WSF 3D v02 product page labels the product CC BY 4.0; commercial modelling and transformations may be permitted under that source licence with attribution. The separately reviewed DLR EOC Geoservice AUP v1.1 governs download.geoservice.dlr.de and requires lawful, considerate use, but this source has no approved service-specific automatic transfer budget. Redistribution_status records the CC BY source-rights ceiling only, not any OpenCatastrophe raw-publication/admission decision. Raw assets, third-party rights, exact release vintage, native raster values and insurer exposure/modeled loss rights require independent review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://web.geoservice.dlr.de/web/datasets/wsf_3d>
- <https://download.geoservice.dlr.de/WSF3D/files/tiles/e021_s24_e022_s25/>
- <https://geoservice.dlr.de/web/terms>
- <https://geoservice.dlr.de/resources/licenses/geoservice/EOC_Geoservice_AUP_v1.1.pdf>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** Source-scoped native-raster T0 contract only. Existing Neon research samples \#22-25 for dlr.wsf.3d.v02 are 32x32 WMS PNG previews, byte-identity reverified in the linked PR; their rendered colors may never be interpreted as the original height in metres. The fixed native download path is a new documented candidate, NOT a successful original GeoTIFF GET. No T1/T2/T3/T4, source bytes, numerical pixel values, science validation, Neon write, or CAT model admission occurs here. Next action: authorize one bounded original-native service request only after service automation policy review, then original SHA and provider-specific TIFF negative science tests.
