<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# RVO/PDOK INSPIRE-harmonised Gewaspercelen vs BRP 2025 — exact collection-only gate

**Two different RVO/PDOK interfaces, not two statistically independent farmer/parcel datasets:**

1. Existing direct BRP current OGC Collection at `/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json` was **first-party verified on trusted main** (run [43489886311](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489886311), strict metadata receipt #1 in private Neon).
2. This PR registers a separate INSPIRE-harmonised Collection at `/rvo/gewaspercelen-geharmoniseerd/ogc/v1/collections/gewaspercelen?f=json` under a **second access_id to the same canonical `nl.rvo.brp-gewaspercelen.2025` candidate**. The INSPIRE API has a distinct source `storageCrs` EPSG:4258 vs the raw BRP Collection EPSG:28992. It advertises EPSG:28992 as one of several output CRS options. Its live Collection metadata is mutable and is NOT original year-2025 immutable asset proof.

**Source rights and exact scope:** the [official PDOK INSPIRE OGC service](https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&lang=en) labels the interface **Open data (publiek)**, free and no authentication. The [PDOK general fair-use / PDC](https://www.pdok.nl/how-to-faq) limits disruptive or unapproved automated activity. This contract permits **one exact bounded Collection JSON metadata GET after reviewed main merge**. "Commercial automation allowed" applies *only to this tiny public metadata canary*, NOT entire parcel feature requests, spatial bulk, recurring polling, reuse of precise farmer property geometry, independent versioned attribution rights, insurer TIV or redistribution. `redistribution_status=unknown` blocks raw public asset publication. There is no mass API use or source-byte persistence.

**2025 nominal year vs lifecycle:** PDOK published the [definitive 2025 BRP release on 17 March 2026](https://www.pdok.nl/-/brp-gewaspercelen-2025-definitief). [PDOK's original forum update](https://geoforum.nl/t/brp-gewaspercelen-2025-definitief/11417) documents a further corrected source file/service update on **15 May 2026** (whitespace in ~30 crop labels). Independently visible INSPIRE *feature pages* show `dataset=#DS_NL_BRP_GEWAS_2025_Definitief` but also `validfrom=2026-05-15`; these facts **are not from this Collection metadata GET**, and neither field proves an immutable 2025 ZIP/GeoPackage SHA. Historical 2025 reference, declared crop-year snapshot and feature lifecycle intervals must not be treated as interchangeable, nor presented as current crop insurance exposure. Native 2025 freeze remains blocked.

**Probe:** one fixed source URL, an original max-65,536-byte UTF-8 JSON object, HTTP 200, no redirect/retry/compression, only `gewaspercelen`/title/description, CRS84/EPSG:28992/EPSG:4258, storage CRS EPSG:4258, Netherlands bbox and exact one self link. Output is **only** UTC, original request+response+code+contract SHA-256, original size, fixed booleans; never original metadata JSON/feature body, geometry, farmer IDs, crop values, a historical source count, model admission or signed links.

**Next scientific step after independent direct provider canary:** locate a **version-fixed official 2025 national archive**, record exact underlying version correction and dataset licence, source SHA and bytes, spatial CRS, unique records/validfrom accuracy and duplicates with direct raw BRP. The INSPIRE feature pages are not an independent validation of the RVO parent.
