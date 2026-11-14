<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# JRC Global Surface Water v1.5 — source contract, no automated service admission (2026-11-13)

## Why this candidate was advanced

A cross-check of the 707 existing source records against the independent
insurance research database found that
`ec-jrc.global-surface-water.1984-2024` was the **only**
`commercial_reuse_verdict=allowed_verified` source record without any
`research.source_sample_v0` entry. The counts are a **2026-11-13
external research-database observation**, not a continuously synchronized
GitHub state or a claim of rights approval for every downstream use.

The earlier
[JRC v1.5 original-listing preflight](jrc-gsw-v15-original-listing-preflight-20261112.md)
already fixed the original CloudFerro candidate asset path and supplied an
**offline-only** original listing validator, but no version- and service-specific
source-access contract was bound to the canonical registry entry.

This change adds a reviewed product/transport *description*:
`access/ec-jrc.global-surface-water.1984-2024.json`.
It is deliberately **documented_only**, with **no active probe**, no
credential and no model admission. Its conservative data rights and unreviewed
service-automation state are distinct.

## Exact version and original-host scope

- Official publisher and licensing statement:
  [European Commission JRC Global Surface Water Data Access](https://global-surface-water.appspot.com/download).
- Current product: **V1.5 / 1984–2024**. V1.4 FTP distribution is
  deprecated, not a fallback or interchangeable science source.
- Original provider-hosted [CloudFerro file list](https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/).
- Selected one 10° x 10° aggregated Occurrence source identity:
  `download2024/Aggregated/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif`.
- Copyright/reuse: publisher permits use, including commercial use in
  principle, under Copernicus Programme conditions with article/dataset
  acknowledgement and map attribution `Source: EC JRC/Google`.
  The source-specific data-use grant must not be stretched into **unreviewed
  CloudFerro automated requests, unrestricted provider polling or unlimited
  file mirroring**. Exact service/API terms and byte persistence need separate
  review.

## New independent host-policy research (2026-11-14)

See [JRC GSW v1.5 — separate publisher and CloudFerro public host policy](jrc-gsw-v15-cloudferro-public-host-policy-20261114.md)
and the machine-readable
`research_runners/policies/jrc_gsw_v15_cloudferro_host_scope_v0.toml`.

CloudFerro's [published General Terms of Service](https://cloudferro.s3.waw3-1.cloudferro.com/wp-content/uploads/2024/05/general_terms_and_conditions.pdf)
**section V.11(a–b), page 10** require **customers** using an API to
avoid excessive/unnecessary load and follow technical specifications.
The JRC [publisher-provided Python v1.5 download script](https://global-surface-water.appspot.com/gsw/Download_Instructions.html)
does explicitly distribute individual 10-degree aggregated tiles from the
named CloudFerro WAW4-1 Swift path, but the host customer contract does
**not** define a numerical limit or independently authorize unattended
anonymous JRC HTTP GET/HEAD/Range requests.

Thus the **dataset reuse licence is established** but the **anonymous
service-automation entitlement remains unknown**. The source remains
`documented_only`; no original listing, raster, TIFF metadata or pixel
value was downloaded in this step. One additional live Neon research
rights row now records this exact CloudFerro **hosting**, separately
from the existing fourteen JRC dataset rights rows, with
`automated_api_access=unknown`,
`scientific_model_admission=false` and
`original_asset_admitted=false`. It is an audit of host conditions,
not an API success claim.

## Science and data-integrity gates

1. **Official correction dated 2026-11-10**: the publisher corrected
   out-of-bounds water **Occurrence >100%** pixels in original GeoTIFF and
   Earth Engine assets. A cached pre-correction TIFF is not acceptable even
   if the filename still matches; verify current original source bytes.
2. **Monthly Recurrence remains independently defective** for sparse
   observations; do not infer that the 2026-11-10 Occurrence fix repaired
   Recurrence.
3. **Landsat Collection 1 / Collection 2 seam**: V1.5 combines 1984–2021
   LC1 with 2022–2024 LC2, introducing geographical co-registration differences
   that can reach or exceed 30 m. Treat version/period mismatches as scientific
   change, not physical surface-water change.
4. **Not a flood event model**: water Occurrence is an observational frequency
   percentage over available valid satellite observations. It does not
   directly measure annual flood probability, inundation depth, current
   flood extents, insured exposure or losses.
5. Model-facing raster samples need exact CRS, nodata and class/scale
   semantics, native numerical pixels, source-byte provenance, relevant
   independent holdout and rights-scoped consumer role.

## Exact next engineering work

- Review CloudFerro HTTP service access/API terms, limits, user-agent,
  direct/redirect behaviour, and whether bounded Range requests are explicitly
  acceptable. No new endpoint requests are authorised in this PR.
- Obtain one original *full* UTF-8 file listing outside Git under an
  independently approved small request, pin byte count, SHA-256 and the
  **single exact** selected v1.5 path using
  `scripts/preflight_jrc_gsw_v15_listing_v0.py`.
- Separately approve one exact and safely bounded original TIFF request.
  It must prove corrected-version identity and never interpret a prefix
  checksum as the hash of a whole GeoTIFF.
- Add synthetic offline regression tests for file header, version mismatch,
  unit/NoData, known-bad occurrence and uncorrected recurrence; only then
  propose a frozen, rights-gated live probe. Store permitted sample
  **outside public Git**, with provenance and use-case review.
- Do not change the source to `probe_ready`, import a raster tile or
  set `model_input_approved=true` solely because the product licence permits
  commercial analysis.

## New purely offline original-TIFF and decoded Occurrence semantics gate (2026-11-14)

New code: `scripts/preflight_jrc_gsw_v15_occurrence_header_v0.py`.
New synthetic tests: `tests/test_preflight_jrc_gsw_v15_occurrence_header_v0.py`.

**No network provider request has been made by these components.** The CLI
requires an **externally and separately authorized exact 4096-byte source
prefix file**, and never tries to download it. It parses bounded, typed,
inline scalar tags in classic TIFF or BigTIFF first Image File Directories:
width/height, BitsPerSample, SamplesPerPixel, compression code, tile
dimensions and the presence (NOT the values) of GeoTIFF tags. Out-of-prefix
first-IFD data stays inconclusive. Oversized and duplicate directories,
invalid TIFF bytes and misleading source-byte lengths fail closed.

A separate pure function `validate_decoded_occurrence_values` checks up to
65,536 caller-supplied **decoded uint8 pixels**; it rejects 101–254 and
distinguishes **0 = observed not water** from **255 = NoData**. The
[FAO catalog for the 1984–2024 JRC Occurrence dataset](https://data.fao.org/catalog/iso/f1b1d45a-e360-44bd-95a9-d628c468a7f6)
pins source v1.5 metadata, `EPSG:4326`, `0.00025°` grid resolution,
8-bit Byte and NoData=255. Such semantic checks cannot be called on
compressed TIFF bytes. They are exercised only with synthetic windows
in this PR; **no original pixels are claimed**.

A 10-degree grid at the documented `0.00025°` resolution corresponds
to 40,000 by 40,000 nominal samples. This is a *candidate shape expectation*,
not an inferred original raster checksum/CRS or proof of the 2026-11-10
correction. The separate CloudFerro network contract remains `documented_only`;
the default official all-tile downloader is not invoked. Every emitted header
or decoded-pixel receipt explicitly sets original-source authenticity,
post-correction proof, full-file SHA and model admission to `false`.

One-shot **offline** usage only, after an independently authorized acquisition:

```sh
python -m unittest tests.test_preflight_jrc_gsw_v15_occurrence_header_v0 -v
python -m scripts.preflight_jrc_gsw_v15_occurrence_header_v0 \
  --offline-tiff-prefix-file /path/to/reviewed-exact-4096-byte-prefix
```

**Do not use** the [Source Cooperative JRC Monthly History mirror](https://source.coop/epoch/jrc-global-surface-water-monthly)
as if it were v1.5 **Aggregated Occurrence**: the mirror has
`monthlyhistory` (2017–2024, partial original period), a different
raster product and distinct pixel semantics. Likewise, the
[CloudFerro published S3 general-tier performance limit](https://docs.cloudferro.com/en/latest/cloud/Block-storage-and-object-storage-performance-limits-on-CloudFerro-Cloud.html)
is not evidence of a granted request rate for a **public anonymous
WAW4-1 Swift** object. Both remain research context, not a host approval.

## Checks included

```bash
python -m unittest tests.test_jrc_gsw_v15_source_access_contract_v0 -v
python -m unittest tests.test_preflight_jrc_gsw_v15_listing_v0 -v
python -m scripts.validate_source_access \
  access/ec-jrc.global-surface-water.1984-2024.json
```

The new negative tests deliberately reject automated probe activation
while service-automation rights remain unknown. No external provider
bytes are included.

## Research snapshot cautions

The separate `research.source_candidate_review_v0` snapshot can lag
behind the live `research.source_sample_v0` ledger (for example,
MeteoSwiss and NOAA NODD still appear as `not_collected` in that
candidate snapshot despite new metadata-only samples).
Research reporting must join **actual sample receipts** instead of
promoting a stale candidate status. The main repo has an all-707
offline rights/contract audit and a separate reviewed 18-probe
manual GitHub workflow; **neither was run against this provider** by
the current documentation change.
