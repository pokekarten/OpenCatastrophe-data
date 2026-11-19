<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA SWPC, GFZ Kp and JRC GSW: live source-triage reconciliation (14 November 2026)

## Why this matters

The research database distinguishes immutable GitHub original-source API receipts from the older independent external web-content smoke observations. The existing `research.source_api_smoke_receipt_v0` table **intentionally enforces** `CHECK (NOT strict_repository_runner_executed)`. A zero in that table's `strict_runner_receipts` column is **not** evidence that a later genuine direct GitHub public GET did not happen. Never modify its constraint or silently re-label intermediary calls as direct.

The reviewed two extra **independent original-provider direct-source GitHub jobs** below were inspected in their actual GitHub Actions logs and checked against two private canonical JSONB research-only metadata samples. No new source GET was required; no original raw response body, sensor series, insurer location, portfolio exposure or model values were saved.

## Two proven exact public original response operations

| Product / scientific context | Actual original GitHub execution | Full original response SHA-256 / bytes | Private research sample | Technical admission |
| --- | --- | --- | --- | --- |
| **NOAA SWPC** real-time solar wind magnetometer (`rtsw_mag_1m.json`), moving spacecraft/multi-source | [GitHub run 43489514680, job 132106651956](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489514680) on 2026-11-13 at 19:09:57 UTC | `bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159`, **1,719,377 bytes** | **#124** | HTTPS 200 + native RTSW 2026 source format only |
| **GFZ Helmholtz Centre** definitive planetary three-hour Kp for **1 January 2024**, 8 original native bins | [GitHub run 43491158483, job 132112397671](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43491158483) on 2026-11-13 at 19:19:54 UTC | `f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a`, **361 bytes** | **#126** | HTTPS 200 + exactly one definitive-day native format only |

The NOAA job passed **16** source-specific offline tests, and its public JSON returned `source`, `active`, `time_tag`, finite magnetic readings (and legitimate null gaps) under the source parser. The exact GitHub original receipt retained code/contract digests, public response size and SHA, but no original sensor observations. NOAA SWPC can switch the operational spacecraft, and the payload is an ongoing rolling product; **we cannot assert a constant satellite lineage or complete historic hazard time series** from this one response.

The GFZ job passed **18** offline tests and verified eight definitive three-hour Kp timestamps in a single **2024-01-01** response. The independent fixed-day original-response SHA is proved, but this is **not** verification of the entire historical 1932-present archive nor an independently calibrated geomagnetic infrastructure/insurance loss relationship.

Official attribution/rights and caution:
- [NOAA SWPC RTSW scientific context](https://www.swpc.noaa.gov/products/real-time-solar-wind); [NWS public-data disclaimer and appropriate-use/polling guidance](https://www.weather.gov/disclaimer). NOAA/NWS federal public-domain usage generally permits lawful reuse with non-endorsement and recognition of source, but some products may contain third-party components. Product-scoped private rights still record `automated_api_access=conditional`, `commercial_cat_modelling=unknown`, `external_raw_redistribution=unknown`; do not upgrade these based on HTTP success. A recurring NOAA collector requires a reviewed cadence and quality/spacecraft policy.
- [GFZ Kp official provider and licence](https://kp.gfz.de/en/about-kp). GFZ explicitly publishes its Kp data under **CC BY 4.0** with GFZ credit; however, private rights still record `automated_api_access=unknown` for repeated requests. Licence ≠ unlimited polling nor scientific loss-model admission.

## Verified private Neon gate and updated all-source queue

New read-only SQL:
`sql/research_noaa_swpc_gfz_kp_direct_original_github_receipts_v0.sql`

This emits exactly one status for each of these two source-specific technical provider responses. It pins the exact source URL, complete original response SHA256 and byte length, actual GitHub run/job/commit, original output-format evidence and canonical SHA256 of the separate private JSONB receipt. It requires a scoped `research.source_usage_rights_v0` decision allowing **internal Neon metadata**, rejects source-byte persistence, and always treats model input as false. Both real private records **#124 and #126 pass**, with no insurer model admissions or new provider HTTP traffic.

The 707-entry all-source read-only triage is extended to count these two additional actual GitHub original source receipts separately from intermediary API smokes. Values after private replay:
- `nl.cbs.new-build-input-cost-index.85728ned`: **4** fixed original direct URLs
- `nl.cbs.new-build-output-cost-index.85772ned`: **6** direct URLs
- `nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned`: **14** direct URLs
- `noaa.swpc.real-time-solar-wind`: **1** original direct URL
- `gfz.geomagnetic-kp`: **1** original direct URL

**26** original fixed technical response operations across **five distinct source IDs**, not 26 independently approved data providers or 26 insurer CAT models. NOAA's previously `inconclusive` intermediary smoke remains unaltered but is no longer presented as an unaddressed direct-runner source-format test. Its updated next action is source-registry snapshot reconciliation; rights and sensor scientific review stay open. GFZ's next action is independent scientific observation validation. The SQL counts direct metadata only and does not change either source's source registry rights verdict.

## JRC Global Surface Water: metadata exists, no native tile admitted

The authoritative [JRC Global Surface Water download page](https://global-surface-water.appspot.com/download) states **v1.5**, 1984–2024, Copernicus dataset reuse allowed with citation and **Source: EC JRC/Google** attribution. The publisher reports an **Occurrence-layer correction published 10 November 2026** (values erroneously exceeding 100%). The older **v1.4 FTP** is deprecated.

The private research database now has **metadata-only sample #129** from the official JRC publisher website. This is **not** the corrected original CloudFerro-hosted Occurrence GeoTIFF, nor a georeferenced native raster header or verified individual pixel. The source-specific [CloudFerro policy review PR #1533](https://github.com/pokekarten/OpenCatastrophe-data/pull/1533) records that the operator's generic customer terms do not clearly settle permission for **anonymous third-party JRC bulk/Range GET automation**; the product-specific `automated_api_access` verdict is **unknown**. No CloudFerro object/network request is newly executed here.

The queue now correctly prioritizes this specific case as:
`P1_resolve_CloudFerro_anonymous_transport_before_original_tile`.

**Next source-specific gate:** verify a clear public-anonymous service/Range GET policy or receive provider approval, then perform one approved version-pinned bounded **original JRC v1.5 corrected Occurrence** header/pixel test. That work must separately review Landsat-era sensor seams, raster NoData=255, per-pixel temporal occurrence vs actual river/coastal flood hazard and CAT model fit.

## Important scientific and legal limits

Original provider HTTP 200 and typed public observations are **technical checks**, not scientific model certification, no confirmation of globally geocoded insured buildings, no geophysical-storm-to-property-damage vulnerability function, and no financial losses. All private `research.source_sample_v0` entries remain `research_only=true`, `model_input_approved=false`, `source_byte_persistence_authorized=false`. The source-specific rights entries are a separate independently reviewable policy register.

Only two read-only SQL files, offline tests and this research note are changed. No source payload bytes, API credentials, GitHub Actions dispatch, permanent new Neon tables, schema permissions or model admission changes are authorized by this PR.
