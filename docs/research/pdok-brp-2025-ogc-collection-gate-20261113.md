<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# RVO/PDOK BRP 2025 — bounded original OGC Collection metadata gate (2026-11-13)

This research candidate **is not admitted** as insured crop exposure, parcel TIV, a loss observation or original source bytes in Git/Neon. It is not a new manifest.

## Exact candidate and source version warning

Candidate ID: `nl.rvo.brp-gewaspercelen.2025`.

RVO/PDOK publishes declared Dutch crop parcels through an OGC Features collection `brpgewas`; the canonical metadata service is [the exact anonymous collection JSON endpoint](https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json). Its [official service directory](https://www.pdok.nl/ogc-apis/-/article/basisregistratie-gewaspercelen-brp-) and [original OpenAPI specification](https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/api?f=html&lang=en) establish route, collection name, OGC API Features protocol, free access and no authentication.

Official [PDOK 2025 final release announcement](https://www.pdok.nl/-/brp-gewaspercelen-2025-definitief) dates the final 2025 release to 17 March 2026. **The online OGC collection is the mutable current dataset, not an immutable 2025 archived file.** Live metadata identity never proves year/parcel-vintage retention. Freeze the original 2025 export, content digest, source timestamps and crop definitions separately before any 2025 historical model mapping.

## Provider terms and intended use

The specific API landing page labels the dataset **Public Domain Mark 1.0**; [PDOK service conditions](https://www.pdok.nl/veelgestelde-vragen-over-pdok-services) state anonymous/free API access, ordinary commercial/private use and no excessive or disruptive queries. The marker is not a contractual grant or guarantee about every upstream asset/2025 archived extract; dataset extraction publication/privacy/redistribution remain subject to metadata and exact scope review. The v1 access contract permits only *one user-initiated GET for Collection metadata*, with approved API/service fair use **not** being an entitlement for bulk parcels, scheduled crawling or unbounded requests.

## Real original-provider metadata observation versus strict runner

On 2026-11-13, an external read-only intermediary fetched the original JSON collection representation and returned `id=brpgewas`, `title=BRP Gewaspercelen`, `itemType=feature`, `storageCrs=EPSG:28992`, the CRS84 option, a self-link and collection bbox. This intermediary did not expose original verified transport HTTP status, Content-Length and raw body digest to the caller. **It is not the trusted direct repo runner receipt.** No feature body, coordinates, farmer identity, parcel geometry, or insurer exposure was downloaded by this research change.

The new `access/nl.rvo.brp-gewaspercelen.2025.ogc-collection.json` defines the exact manually executable one-GET contract. `scripts/probe_pdok_brp_2025_collection_v0.py --live` performs no request unless explicitly invoked on a trusted network environment. A valid run requires original HTTP 200, no redirects, content-type JSON, uncompressed original body under 128 KiB, immutable request fingerprint, original SHA-256/bytes, strict collection schema/CRS and timestamp. Only hashes and structural booleans are printed; no provider bodies are saved.

## Scientific limits and next manifest gates

RVO BRP reports land user *declared* crop/parcel geometry for 15 May, not actual vegetation or insurable agricultural sums insured. The national BRP data may underlie EuroCropsV2 for Netherlands; do not treat the two as independent spatial evidence.

Before any later asset-level or derived manifest, independently verify: 2025 exact archive/granule ID, terms for that vintage, provider URL and SHA-256 of actual original file, geometry validity and EPSG transform, crop codebook and calendar, crop/field selection, coverage/missingness, licence attribution/privacy and intended commercial CAT use. Scientific model admission and model validation are separate approvals.

No API probe of crop-item features, original bytes in Git, insurer TIV, claims or model readiness are claimed.
