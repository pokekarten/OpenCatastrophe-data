<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# RVO / PDOK BRP — public current OGC metadata versus final 2025 source rights

**Source:** `nl.rvo.brp-gewaspercelen.2025`. Research-review scope is the **current live** [PDOK OGC Features service](https://api.pdok.nl/rvo/gewaspercelen/ogc/v1?f=html&lang=en), one `GET /rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json`, with no feature queries. Provider labels the service **Public Domain Mark 1.0**, no authentication, no charge, and public OGC API metadata. Original [PDOK service terms](https://www.pdok.nl/veelgestelde-vragen-over-pdok-services) require the fair-use Producten en Diensten Catalogus; provider also says exact *dataset*-specific licensing is in Nationaal Georegister metadata.

This review **does not treat Public Domain Mark as an independently granted licence** and **does not authorize** bulk geometry acquisition, raw redistribution, individual farmer/crop TIV, full 2025 archive, claims, or scientific CAT exposure admission.

## Seven distinct use-case decisions

| Use case | Product-scoped verdict |
| --- | --- |
| Internal research | Allowed for public service metadata |
| Commercial CAT modelling | **Unknown** for exact historical 2025 parcel-level data; no model admission |
| Automated API access | Allowed for one bounded anonymous collection metadata GET only |
| Private Neon metadata | Allowed for digests/bytes/times/code and contract provenance |
| Private Neon source sample | Allowed for sanitized public collection metadata **only**, not original provider body or rows |
| External original-asset redistribution | **Unknown**, historical product-specific licence not reviewed |
| Publication of derived results | Conditional on accurate provenance, attribution, model science and actual dataset rights |

This product/version separation prevents a successful `brpgewas` live API metadata response from being represented as an immutable official 2025 parcel dataset. PDOK announced definitive 2025 on 2026-03-17; additional May 2026 provider update/correction means the original 2025 archive identity and SHA must be frozen separately.

The exact research SQL file `research_runners/sql/insurance_pdok_brp_metadata_rights_v0.sql` adds **only these seven source/product/use-case decisions** to the separate private Neon rights ledger, with both `scientific_model_admission=false` and `original_asset_admitted=false`, idempotently. It is not a data admission or licence to republish third-party bytes.
