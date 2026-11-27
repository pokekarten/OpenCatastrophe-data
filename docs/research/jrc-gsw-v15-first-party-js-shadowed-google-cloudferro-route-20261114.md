<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# JRC GSW 1.5: publisher's actual JS chooses CloudFerro, not older Google v1.5 URL (14 November 2026)

## First-party original source-code discovery

Read the current **European Commission JRC official public [data download page](https://global-surface-water.appspot.com/download)**, not an inferred GIS tile-service URL. Its inline JavaScript for tile clicks has **three sequential variable declarations** in one script block **before** `function set_paths(x,y)`. This is a re-assignment to one JavaScript variable, not a list of active endpoints:

```js
var BASE_URL = 'https://storage.googleapis.com/global-surface-water/downloads2021/';
var BASE_URL = 'https://storage.googleapis.com/water-world/download2024/VER1-5/';
var BASE_URL = 'https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/';
var FILES = ['occurrence/occurrence', 'change/change', 'seasonality/seasonality', 'recurrence/recurrence', 'transitions/transitions', 'extent/extent'];
// set_paths(x,y) constructs tile links using [BASE_URL, FILES[i], ...].
```

**Effective publisher tile-click base: the third and final CloudFerro URL.** The Google `water-world/download2024/VER1-5/` URL is **actually present in first-party publisher code**, so it is a first-party **candidate historic/alternate distribution address**, not just a third-party conjecture. However **it is overwritten** before links are formed and is *not* the JRC site's currently selected output. This matters especially after the publisher's **10 November 2026** Occurrence fix. An unchanged Google object at that candidate address could be **pre-fix** or unavailable; even an HTTP 200/TIFF magic cannot prove the date/corrected pixel identity. Do not treat this alternate as equivalent to the official currently selected post-correction CloudFerro tile, or promote its unknown status to `probe_ready`.

Exact fixed 10E_50N example under one source product:

- **Official page current tile-click destination (not fetched here):**
  `https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif`
- **Overwritten first-party Google v1.5 code candidate (not fetched here):**
  `https://storage.googleapis.com/water-world/download2024/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif`
- **Previous version v1.4** is a different, deprecated `downloads2021` release, not a substitute.

This finding is grounded in the publisher's original HTML **script source**. Third-party data-catalog examples independently cite the Google URL, but do not establish its correction vintage. The publisher itself explicitly directs clickable 10-degree tile downloads from CloudFerro.

## Separate host rights and scientific verification

- **Dataset:** Publisher's [Copernicus data licence](https://global-surface-water.appspot.com/download) allows attributed source-product reuse; include **Source: EC JRC/Google**. The corrected 2026-11-10 release notice applies to v1.5 Occurrence GeoTIFF **and** Earth Engine; it does **not** certify every unseen Google alternative file.
- **CloudFerro host:** [public container guidance](https://docs.cloudferro.com/en/latest/s3/How-to-use-Object-Storage-on-CloudFerro-Cloud.html) says anyone with a public object link can download it. The [CloudFerro general customer terms](https://cloudferro.s3.waw3-1.cloudferro.com/wp-content/uploads/2024/05/general_terms_and_conditions.pdf) instruct contracted customers to avoid abusive API traffic. **Neither separately establishes an anonymous, repeated Swift/Range GET quota for a commercial third-party source collector.** We therefore retain original source contract `documented_only`, `api_terms_status=separate_unreviewed` and zero approved CloudFerro original TIFF requests.
- **Google Cloud Storage host:** [official Google public object documentation](https://docs.cloud.google.com/storage/docs/access-public-data) confirms anonymous GET of an **actually public** GCS object at `storage.googleapis.com/<bucket>/<key>` without a Google account. It does not certify that this *particular* `water-world/download2024` v1.5 TIFF object currently exists, remains public or contains the November-corrected JRC source asset. The alternative remains **review-only**, with no authorized new GET and no downloaded TIFF in this PR.
- **Google Earth Engine:** The [JRC-listed v1.5 Occurrence asset](https://global-surface-water.appspot.com/download) is `projects/global-surface-water/assets/GSW1_5/Occurrence`. Authenticated commercial Earth Engine access has separate account/subscription/IAM rules; that route is already fail-closed in `research_runners/policies/jrc_gsw_v15_earth_engine_access_v0.toml`.
- **Map imagery:** JRC expressly says the Google 2024 WMTS visual map is RGB and **not suitable as numeric analysis raster**. Do not equate an anonymous Google WMTS/PNG GET with a native numeric TIFF or flood model data.

## New reproducible, source-specific code check

New `scripts/preflight_jrc_gsw_v15_publisher_js_routes_v0.py` has a pure **offline** `inspect_inline_tile_routes(raw: bytes)` function:
- accepts only strict bounded public HTML bytes;
- isolates exactly one inline JavaScript block containing `function set_paths`, checks **all three original assignments in order**, that the last one precedes link construction, exact `occurrence` product, and current `[BASE_URL, FILES[i], ...]` link logic;
- blocks an extra assignment, changed base URL, changed order, missing product, invalid bytes, absent script, alternate product or unexpected code shape;
- returns **only source-route metadata**, the effective CloudFerro and overwritten Google URLs and explicit **false flags** for all TIFF retrieval, correction/date identity, scientific numeric validation, automated host permission and CAT model admission.

The already reviewed exact **single original JRC publisher HTML GET**, `research_runners/jrc_gsw_v15_publisher_page_one_shot_v0.py`, now performs this strict source-code inspection **alongside** its original HTML body SHA/byte length, publisher rights and 2026-11-10 correction notice checks. The additional **offline synthetic tests** in `tests/test_preflight_jrc_gsw_v15_publisher_js_routes_v0.py` and modified `tests/test_jrc_gsw_v15_publisher_page_one_shot_v0.py` protect the detected JavaScript shadowing/source drift.

A GitHub Actions read of the **public JRC publisher HTML page only** can independently verify this source-code shape, with its exact bytes SHA/time, without accessing either CloudFerro or Google original TIFF. Only one explicit original publisher GET is acceptable; no cron, job repetition, arbitrary URLs, raw provider HTML saved or original remote raster bytes. A publisher HTML receipt is **not** a native GeoTIFF sample. An independent direct original file request will require a later per-host/version permissions and science review.

## CAT science gate

JRC occurrence is the percentage of valid Landsat surface-water detections, not a flood exceedance annual probability, water depth, return period, loss exceedance curve, building exposure, insured value or insurer portfolio TIV. V1.5 blends Landsat Collection 1 (pre-2022) with Collection 2 (2022–2024). Monthly Recurrence is separately identified as affected by a sparse-observation issue. A TIFF URL or public dataset licence does **not** imply scientific hazard or insurance pricing admission. All JRC samples remain research-only; no commercial loss-model certification.

## Actual original JRC publisher HTML validation, GitHub and Neon

After the offline first-party JS parser and negative tests were created, the source-specific same-repository GitHub Actions provider job **132480916985** in [CI run 43606072894](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43606072894) **succeeded**, performing exactly one anonymous public **JRC publisher HTML GET** (not a CloudFerro/Google TIFF request). Receipt UTC: **2026-11-14T14:40:35.787403+00:00**, exact original publisher response **HTTP 200**, **85,581 bytes**, complete original HTML SHA-256:

\`510b4bc273c743b8789afb3ffa57db31077e1f2ac617aca4869870c123995a08\`

The job's **19 synthetic/negative tests** passed before network. It confirmed the current original first-party three-assignment JS order. The original page bytes hash and size match prior original JRC publisher-only GitHub sample **#129** from earlier the same day. The full HTML body was not persisted; only exact full-body SHA/time and typed derived JavaScript route metadata were logged. It did **not** fetch the Swift original catalogue, a CloudFerro GeoTIFF, Google GCS original GeoTIFF, any TIFF header or native pixels.

A separate append-only private **Neon research-only metadata sample #130** now records the direct source job, original HTML SHA/size, linked previous page sample #129, all three source-defined URLs in their original order and the legal/science denial flags. Read-only independent Neon checks: **two page metadata samples, two canonical JSONB SHA-256 valid, one identical original page URL, one identical original full-body SHA, exactly one independently documented new inline JS route proof**; zero source assets/tiles admitted and zero CAT model approval.

**Seven additional use-case rights decisions** for the **overwritten Google \`water-world\` v1.5 Occurrence candidate** have been added with the source-controlled idempotent query \`research_runners/sql/jrc_gsw_v15_shadowed_google_gcs_rights_gate_v0.sql\` and private research metadata/official publisher-rights preconditions. They are **product/host-specific**, separate from existing CloudFerro and dataset decisions:

| Google shadowed object use case | Verdict |
| --- | --- |
| Automated API access | **unknown** |
| Commercial CAT modelling of this particular unverified object | **unknown** (underlying JRC dataset reuse licence remains allowed separately) |
| External raw redistribution | **unknown** |
| Internal Neon metadata | **allowed**, derived public route metadata only |
| Internal native source sample | **unknown**, no original TIFF permission |
| Internal research | **conditional**, metadata-only until object vintage/transport review |
| Published derived results | **conditional**, attributed metadata only |

All seven records set \`scientific_model_admission=false\` and \`original_asset_admitted=false\`. The actual original raster source remains **blocked**. The source product is useful for spatial water-observation context, but a metadata HTML receipt cannot be substituted for corrected 2026-11-10 numeric occurrence TIFF or insured flood risk modelling.

### Source-specific next proof

The current official publisher tile-click endpoint is CloudFerro. Its anonymous one-shot and continuing Swift/Range request conditions are not yet documented with a scoped approval. The Google GCS candidate is a *publisher-code-overwritten route*; despite Google's general public-object GET policy, it remains unverified for exact object availability, original whole-body SHA, November-corrected version and scientific raster consistency. Only after one delivery route has a source-specific host approval and exact corrected object identity should a **single fixed, bounded header/raster-window** acquisition be considered. Do not grant 360-tile bulk downloading or silently upgrade research \`model_input_approved\` flags.
