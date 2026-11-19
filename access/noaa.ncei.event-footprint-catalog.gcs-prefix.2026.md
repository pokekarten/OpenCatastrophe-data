<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.event-footprint-catalog.gcs-prefix.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.event-footprint-catalog.gcs-prefix.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.event-footprint-catalog.gcs-prefix.2026

## Source ids

- noaa.ncei.event-footprint-catalog.2026

**Provider:** NOAA National Centers for Environmental Information (NCEI); public files hosted on Google Cloud Storage

**Interface type:** object_store

**Status:** documented_only

**Documentation url:** <https://catalog.data.gov/dataset/event-footprint-catalog>

**Service root:** <https://storage.googleapis.com>

**Api version:** NOAA Event Footprint Catalog v1.0 (2026), GCS JSON API v1 objects.list documentation

## Access scope

- catalogue
- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- efc_gcs_prefix_metadata_list

### Path templates

- /storage/v1/b/noaa-ncei-ipg/o

**Parameter rules:** Official NOAA NCEI/DCAT distribution links exactly to gs://noaa-ncei-ipg/datasets/event-catalog/. Google documents GET /storage/v1/b/\{bucket\}/o and exact prefix/delimiter/maxResults listing semantics. A PROSPECTIVE one-page read would use the fixed encoded prefix datasets%2Fevent-catalog%2F, delimiter=%2F, maxResults=10; the public availability of storage.objects.list and any anonymous/service permission are NOT tested or assumed. This contract is documentation-only: no network call, bucket enumeration, arbitrary prefix, pagination, pageToken follow-up, object GET, file export, user-controlled URL or unreviewed query. Endpoint identity is fixed, not a claim that an open GCS listing exists.

## Response contract

### Expected media types

- application/json

**Format:** Prospective bounded Google Cloud Storage JSON API list response kind=storage\#objects, items/prefixes and optionally nextPageToken; no event GeoJSON data or original asset bytes.

**Scientific semantics:** NOAA EFC is a 2026 tornado/hail event-footprint product, not a global stochastic hazard catalog or loss model. NOAA states tornado footprints derive from NWS Damage Assessment Toolkit and Storm Events Database; hail polygons derive from MRMS gridded hail estimates. Annual tornado and daily hail GeoJSON source files are mutable; historic revisions are not archived. Metadata object-name discovery does not establish an event schema, intensity units, independent observational evidence or insurance losses. Some upstream events overlap with NOAA SED/DAT/MRMS already present in the registry, so no independent validation/holdout role is inferred.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** No public anonymous list permission, product-specific GCS quota or commercial automated catalogue rate is confirmed. Google JSON API documents a maxResults bound and object-list IAM requirements. This contract authorizes ZERO requests; later reviewed implementation must cap a single fixed read to ten catalogue entries and refuse 401/403, 429, redirect, HTML, unexpected prefix or any paging.

**Mutability notes:** NOAA reports daily EFC updates and no retained prior versions. The Google bucket/prefix is a provider-declared distribution locator, not a stable asset/version identifier. A future selected object needs exact object name+generation, size, retrieval UTC, full response SHA-256, upstream event vintage and per-object rights before a single original sample.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_unreviewed

**Terms url:** <https://docs.cloud.google.com/storage/docs/json_api/v1/objects/list>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Data.gov's NOAA/NCEI Event Footprint Catalog dataset metadata identifies public access and CC0-1.0 for the product, with a provider-specific citation including subset/access date. This is NOT an independent per-object rights or privacy review; DAT/SED/MRMS upstream lineage and possible event narratives require exact asset review. Google Cloud Storage JSON objects.list requires storage.objects.list permission and separate service rules; it is NOT established that the bucket allows anonymous listing, automated downloads or free GCS API calls. No service permission, commercial bulk crawl, raw publication or insurer CAT model use is inferred. Keep dataset rights evidence separate from the unreviewed machine-service and asset publication decisions.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://www.ncei.noaa.gov/products/event-footprint-catalog>
- <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncei%3AC01773>
- <https://catalog.data.gov/dataset/event-footprint-catalog>
- <https://console.cloud.google.com/storage/browser/noaa-ncei-ipg/datasets/event-catalog/>
- <https://docs.cloud.google.com/storage/docs/json_api/v1/objects/list>

**Notes:** T0 improvement over existing access/noaa.ncei.event-footprint-catalog.portal.json: NOAA's own catalog supplies the exact public-cloud distribution bucket/prefix, and the GCS provider documents a standardized metadata-list operation. The current public rights label does NOT verify that GCS storage.objects.list is accessible anonymously. No T1/T2/T3/T4 and no original event bytes; do not upgrade to probe_ready or CAT admission until a reviewed, fixed, one-shot source/permissions test and per-asset scope exist. The preceding portal contract remains unchanged.
