<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# JRC GSW v1.5 — separate publisher permission from CloudFerro public HTTP service policy

**Reviewed 2026-11-14; research evidence only; no provider original bytes acquired.**

## Evidence table: do not conflate provider roles

| Provider/source | Verifiable official statement | What it does **not** demonstrate |
| --- | --- | --- |
| [European Commission JRC dataset access](https://global-surface-water.appspot.com/download) | Copernicus GSW datasets free of charge, without restrictions of dataset use, with citation and map attribution `Source: EC JRC/Google` | No exact **anonymous host** request quota, no assertion of corrected original image content, no CAT model suitability |
| [JRC published Python v1.5 download instructions](https://global-surface-water.appspot.com/gsw/Download_Instructions.html) | Official programmatic downloader intentionally retrieves files from the CloudFerro WAW4-1 **Swift** HTTPS endpoint, one 10°×10° GeoTIFF per tile; the unscoped aggregated run spans **360 tiles** | The existence of a downloader is NOT a blanket entitlement to HTTP crawling, arbitrary retried requests, public redistribution, or an assessed transfer budget for third-party automation |
| [CloudFerro General Terms of Service, section V.11(a–b), page 10](https://cloudferro.s3.waw3-1.cloudferro.com/wp-content/uploads/2024/05/general_terms_and_conditions.pdf) | For CloudFerro **customers using an API**, avoid excessive and unnecessary server load, and obey the technical service specifications | This is a **customer contract** and does not prove what contract, rate cap or non-customer automated-GET terms govern anonymous JRC tile readers; no numerical limit is stated |
| [CloudFerro public object storage guidance](https://docs.cloudferro.com/en/latest/s3/How-to-use-Object-Storage-on-CloudFerro-Cloud.html) | Owners may mark containers public and distribute public object links | It is not a licence to mirror any unrelated bucket or bypass a JRC-specific data-access condition |

## Exact product and science

The reviewed JRC **v1.5 / 1984–2024** `occurrence` tile is:

```
https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif
```

- Only this tile is contemplated for a *future* explicit one-shot review.
  **No GET, HEAD, HTTP Range, redirect, retries, multiprocessing, full
  listing, 360-tile default downloader or original TIFF persistence** is
  authorized by the current OpenCatastrophe source contract.
- The JRC publisher [download page](https://global-surface-water.appspot.com/download)
  dates a **2026-11-10** correction of individual `Occurrence >100%`
  values in GeoTIFF and Earth Engine. Filename and HTTP success alone cannot
  prove that original pixels are the **post-correction** bytes.
- Monthly Recurrence has a separately acknowledged low-value error under
  sparse observations; it has **not** been corrected by the Occurrence update.
- The 1984–2021 Landsat Collection 1 and 2022–2024 Collection 2 seam may
  shift pixel geolocation by **at least one 30 m pixel** in some locations.
- Occurrence is the percentage of **valid satellite observations detecting
  water**, NOT event flood exceedance, physical inundation depth, return
  period, annual insured flood probability or a CAT-loss estimate.

## Gate decision

```json
{
  "source_id": "ec-jrc.global-surface-water.1984-2024",
  "exact_product": "GSW v1.5 1984-2024 corrected 2026-11-10 Occurrence",
  "publisher_dataset_reuse": "allowed_with_attribution",
  "publisher_official_download_script": "verified",
  "cloudferro_customer_api_policy": "no_excessive_unnecessary_load",
  "cloudferro_public_anonymous_get_terms": "not_bound",
  "approved_public_host_rate_limit": null,
  "live_probe_approved": false,
  "original_listing_sample": "not_acquired",
  "original_tiff_sample": "not_acquired",
  "corrected_pixel_value_proof": false,
  "insurer_cat_model_input_approved": false,
  "next_gate": "verify anonymous service conditions, then review one exact bounded request"
}
```

**Decision:** retain `documented_only`, `probe_contract.mode=none`,
`commercial_automation_status=unknown`, `api_terms_status=separate_unreviewed`,
with `terms_url=null` in `access/ec-jrc.global-surface-water.1984-2024.json`.
The CloudFerro *customer* Terms URL is **background evidence**, **not** the
missing public anonymous-use service agreement. Do not set this source to
`probe_ready` based only on a customer contract and a downloadable publisher
script.

## Swift listing pagination is independent of source-asset identity

The official [OpenStack Swift pagination documentation](https://docs.openstack.org/swift/2026.2/api/pagination.html) says that a container-listing GET normally returns at most **10,000 object names**. Additional pages require a `marker` and additional network requests; this maximum is server-configurable. A single HTTP 200 response with the target pathname and a correct SHA-256 proves only **that page's original byte identity**, not an exhaustive original catalogue, a tile body or post-correction pixel values. Even fewer than 10,000 names do not establish exhaustive completeness without verified host-specific pagination behaviour.

The existing offline `scripts/preflight_jrc_gsw_v15_listing_v0.py` now preserves exact object keys without stripping whitespace and emits `listing_page_object_count`, `swift_default_page_limit_reached`, `listing_scope=single_supplied_original_swift_listing_page`, and explicitly `complete_original_catalogue_verified=false`. A 10,000-name synthetic regression protects against treating a default capped page as a full source register. No `marker` pagination, second HTTP request, all-tiles crawler or CloudFerro source GET has been approved or executed by this change. Exact target-path presence is a **discovery receipt**, not an exhaustive source census or license grant.

## Frozen original TIFF 4,096-byte one-shot runner (prepared, not authorized)

An implementation now exists at
`research_runners/jrc_gsw_v15_original_tiff_prefix_one_shot_v0.py`,
with synthetic no-network fixtures and tests in
`tests/test_jrc_gsw_v15_original_tiff_prefix_one_shot_v0.py`.
This is a **conditional executable acquisition path**, not a claim
that provider source bytes were obtained.

The exact JRC publisher [download script instructions](https://global-surface-water.appspot.com/gsw/Download_Instructions.html)
document automatic v1.5 **10° tile** delivery from the specific WAW4-1 Swift
host. That establishes an officially intended distribution mechanism
and the data-use permission, but still does not supply an independently
reviewed *anonymous rate cap or CloudFerro service contract* for this
insurance workflow. The immutable on-repository policy **continues** to
authorize **0 original-host requests and 0 original data bytes**.
The test harness cannot turn this into permission.

The runner requires **both** a separately reviewed host-policy approval
and a canonical schema-valid active access contract. The latter uses
source-access v1's actual `rights_and_policy.api_terms_status =
separate_reviewed` enum (NOT the impossible legacy
`reviewed_allowed` string), an authoritative HTTPS
`terms_url`, `status=probe_ready` and a fixed
`provider_specific` operation. The host policy must independently
review `public_anonymous_download_permission=reviewed_allowed`,
set an explicit positive rate cap, **exactly one** permitted request
and **exactly 4096** original response bytes, and explicitly approve
the live probe. All conditions are currently **false**.

Once independently authorized, this one-shot code permits only a
`GET` to the exact hardcoded original
`occurrence_10E_50N_v1_5_2024.tif`, with
`Range: bytes=0-4095` and `Accept-Encoding: identity`.
It disables redirects and proxies; does not retry, paginate, persist
source bytes, follow alternative hosts or accept a full HTTP200
download. It requires same-host HTTP206, exact
`Content-Range: bytes 0-4095/TOTAL` with
`TOTAL > 4096`, exactly `Content-Length: 4096`,
native TIFF/octet-stream media, no transport compression
and an in-memory read capped at **4097 bytes**. Even if a
server ignores Range, the runner never accepts the response and
does not read a full TIFF into memory. It produces a metadata-only
receipt including an **original-prefix-only** SHA-256,
a 4096-byte first-IFD TIFF shape preflight and explicit negative
whole-asset, corrected-pixel and CAT-model flags.

**Crucial:** successful HTTP206 proves neither the
post-2026-11-10 corrected original TIFF nor a full-file hash or
decoded numeric pixels. Authorization of this prefix probe is
**not** a licence to request more bytes. For a future *actual*
original read, the strictly reviewed contract/policy must be
updated together and undergo an independent decision before an
authorized GitHub job is run. Current automated CI is completely
synthetic and makes no CloudFerro request.

## Minimum next original-provider acquisition proof (only once authorized)

Before a one-shot JRC `GET`, record a version-specific approval of the
public Swift hosting conditions, user-agent/timeout/one-request allowance,
byte cap, cache/redirect policy and corrected publication identity. Execute
on reviewed original code in a GitHub Actions job with strict bounds:
one fixed HTTPS hostname, one exact tile/listing URL, no caller-selected
path, `Retry: 0`, disallow redirects, no retry-on-HTTP429/5xx, max read
length and temporary in-memory bytes only. Record original HTTP status,
source SHA-256 of **only the actually received bytes**, whether Range was
honored, retrieval UTC and version/correction evidence. A **prefix** hash
never becomes a whole-TIFF hash. A first-party successful request is an
operational receipt only, not evidence of corrected values or insurance
science validation.

Source usage licensing and CloudFerro network permissions are two
**independent** gates.
