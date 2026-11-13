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


## Original first-party metadata evidence from GitHub main

After merging the reviewed source access contract [PR #1538](https://github.com/pokekarten/OpenCatastrophe-data/pull/1538) and the safe JSON receipt logging change [PR #1561](https://github.com/pokekarten/OpenCatastrophe-data/pull/1561), the **actual first-party trusted-main original provider GET** [Actions run #43489886311](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489886311), live job `132108208702`, succeeded on push head `526303e78974ed234610bf0a65fac4786512da13`.

The publicly retrievable job log contains these **original source receipt facts**:

| Strict original-source field | Verified value |
| --- | --- |
| Original HTTPS 200 Collection JSON | 3,730 bytes |
| Original response SHA-256 | `99a64145c7b198bbe2e2a78f248c24845e212210d482e805cb581d6aaa61ca79` |
| Original fixed request SHA-256 | `f50ae18fd344ff4c201dd3e1db6fd75f321bb302e4f84fda642d6a1750696eb2` |
| Exact reviewed access-contract SHA-256 | `7164465a21b3cfb7e0dae2b77e89e31fcfd034297a156c7781083e53717ad396` |
| Executed runner code SHA-256 | `be00542bed9b6b5a2e41773a32421b41aba0d5b3b8ade4ca8d293c133eb10d66` |
| Original retrieval UTC | `2026-11-13T19:12:32.658210+00:00` |
| Provider collection ID | `brpgewas` |
| Source CRS evidence | CRS84 and EPSG:28992 |
| Historical frozen 2025 dataset | **Not proven** |
| Raw response bodies or field/parcel geometry stored | **None** |
| CAT/exposure/model admission | **None** |

The runner enforces exact original URL, HTTPS HTTP 200, JSON MIME, no redirects/encoding, maximum 128KiB original response, source identity, self-link and Dutch geographic extent. GitHub job success plus the printed original digests is a **first-party API proof**, not proof of immutable original 2025 dataset bytes.

Two distinct private research evidence operations are specified:
- `research_runners/sql/insurance_strict_metadata_probe_receipt_v1_schema.sql` and `insurance_pdok_brp_strict_metadata_receipt_v1_seed.sql` for a new strict trusted-GitHub JSON metadata ledger. The older 206 Range and intermediary metadata ledgers remain intact.
- `research_runners/sql/insurance_pdok_brp_strict_metadata_sample_v1_seed.sql` for exactly one sanitized JSONB `public_metadata` summary, with provider original-body SHA and independent SHA of the private JSONB structure; no original provider payload bytes, crop features, insured values or personal information.

No licence, terms, production-model or scientific gate is promoted by these private provenance receipts. The research receipt and seven product-scoped rights decisions are separately verified by `research_runners/sql/insurance_pdok_brp_strict_metadata_receipt_v1_verify.sql`.
