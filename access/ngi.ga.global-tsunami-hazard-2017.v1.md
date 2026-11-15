<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ngi.ga.global-tsunami-hazard-2017.v1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ngi.ga.global-tsunami-hazard-2017.v1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ngi.ga.global-tsunami-hazard-2017.v1

## Source ids

- ngi.ga.global-tsunami-hazard-2017.v1

**Provider:** Norwegian Geotechnical Institute (NGI) and Geoscience Australia; Zenodo hosted record

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/16964551>

**Service root:** <https://zenodo.org>

**Api version:** Zenodo record 16964551, v1 (published 2025-08-27); scientific PTHA model vintage 2017

## Access scope

- metadata
- sample
- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- read_fixed_record_metadata
- read_exact_publisher_readme
- download_exact_globalptha_original

### Path templates

- /api/records/16964551
- /records/16964551/files/README.txt
- /records/16964551/files/globalPTHA.txt

**Parameter rules:** Documentation-only paths for exactly Zenodo record 16964551 v1 and its two published filenames. The public file links use download=1; no caller-provided URL, host, path, record ID, filename, headers, search expression, pagination or other query values are permitted. Any future trusted probe must pin a single exact operation, explicitly validate redirects and DNS, refuse HTML/error bodies, enforce the stated original bytes and provider MD5, use a named User-Agent, and obtain a separate rights and execution review before it is enabled. No current network operation is authorized by this contract.

## Response contract

### Expected media types

- application/json
- text/plain
- application/octet-stream

**Format:** Zenodo JSON record metadata; publisher README.txt text; semicolon-delimited original globalPTHA.txt (publisher-listed approx. 7.3 MB, MD5 d8dd8ad55fe89bd56b455e392387a99e). The publisher hash is a metadata declaration, not a computed original-byte receipt.

**Scientific semantics:** Modelled 2017 global probabilistic earthquake-tsunami inundation/runup hazard, republished as Zenodo v1 in August 2025. rate_N is annual mean exceedance rate for height thresholds in centimetres; ariN is height in metres at a stated return period in years, not event IDs or event probabilities. Heights at 0.1 m and 20 m are censored boundaries; longitude may use 0-360 degrees; the README names ari500LZ while the displayed CSV header may use ari500ZL. This global screening/benchmark product is explicitly not recommended by its authors for local risk assessment, and is not an insured-loss or stochastic event catalogue.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `8192`

**Max sample bytes:** `12000000`

**Retry policy:** none

**Rate limit notes:** Zenodo public developer documentation lists guest global limits of 60 requests/minute and 2000/hour, HTTP 429 on throttling, and recommends an identifiable User-Agent. These provider-wide limits are ceilings, not a license to harvest; the proposed future fixed probe would perform at most one small metadata or README GET, not bulk crawling.

**Mutability notes:** Publisher record v1 is a fixed citation identity, but access headers and delivery links may change. Future original sample evidence must record UTC timestamp, exact URL/method and redirects, byte size, separately computed SHA-256, publisher-declared MD5 verification, media type, scientific parser result, and approved external storage identity. No original-byte hash or storage receipt was created in this review.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_reviewed

**Terms url:** <https://about.zenodo.org/terms/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The provider record and its actual README.txt state copyright NGI/Geoscience Australia 2017 and CC BY 3.0 AU, whose licence deed permits commercial reuse/adaptation with attribution, licence link and modification notice. Zenodo Terms of Use v1.3 separately restrict service/content access to non-military purposes and require compliance with the uploader licence; Zenodo enforces rate limits. The public record's separate Rights/License UI metadata was not independently matched to the README, and the source-specific repository rights/admission review is not complete. Do not infer blanket permission for commercial automated harvesting, original publication, local CAT underwriting use, military purposes or third-party content. No probe/sample/storage is enabled.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://zenodo.org/records/16964551>
- <https://zenodo.org/records/16964551/files/README.txt?download=1>
- <https://creativecommons.org/licenses/by/3.0/au/>
- <https://about.zenodo.org/terms/>
- <https://developers.zenodo.org/>

**Notes:** T0 documentary access and product-scope evidence only. Official record lists globalPTHA.txt (approx. 7.3 MB; MD5 d8dd8ad55fe89bd56b455e392387a99e) and README.txt (approx. 2.8 kB; MD5 f52a37706b789f343b970e51b0076980). Their publisher MD5 values were not recalculated and no source file was saved as original data. The existing research_runners/ngi_global_ptha_preflight_v0.py checks original input after separate acquisition and existing tests/test_ngi_global_ptha_preflight_v0.py uses synthetic fixtures. Complete exact product rights and API-automation review, a bounded reviewed downloader, actual original SHA-256/sample QA, independent benchmark validation, Neon storage and any model admission remain open.
