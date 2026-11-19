<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CBS StatLine 83673NED — three direct original-source 2025 GETs (2026-11-13)

## Reviewed source rights

Official CBS source: https://www.cbs.nl/nl-nl/cijfers/detail/83673NED
Official government data register: https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5 — **CC BY 4.0**.
Official CBS standard API: https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data — **up to 10,000 cells** per direct standard API request.

Scope is **pure newly permitted dwellings from at least EUR 50,000 total construction sum excluding VAT**, not existing insured property rebuilding cost. Period **2025VJ06** = July 2024–June 2025, source-native **Definitief**. A separate 2026VJ06 period remains preliminary, not falsely upgraded to final.

The three reviewed **fixed** HTTPS GETs all start with:
https://opendata.cbs.nl/ODataApi/OData/83673NED/

| Source suffix | Original size / full original-body SHA-256 (intermediary) | Neon research-only sample | Prior external API receipt |
| --- | --- | ---: | ---: |
| TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5 | 1457 B / 70731cf7be6e73813059c250db9f1f21ad4024f0fb7cba5075ad8af666d90a5e | 98 | 44 |
| TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5 | 1459 B / 7c9b9e307fd7fbf4ef8d5e9e26eaf3d9b9a991dd54a6b95c01409d22663c5908 | 99 | 45 |
| Perioden?$filter=Key%20eq%20%272025VJ06%27&$top=1 | 234 B / 626dac3ab357839e615bcf0260237651d4a3983a88a0f18f6c8e3bfc24272c4d | 97 | 43 |

These earlier body SHA-256 hashes are based on complete original returned public JSON bytes from an **external read-only intermediary**, NOT a trusted GitHub direct HTTP attestation. All three source-native full-body hashes and byte lengths must be reproduced by the new genuine direct-provider runner or it will **fail closed**.

## New execution controls

- Canonical source access contract: access/nl.cbs.new-housing-permit-2025v06-direct-three.83673ned.json and deterministic generated human-readable Markdown.
- Source-specific opt-in runner: scripts/probe_nl_cbs_83673ned_2025_original_three_v0.py with --live-three. It has exactly three immutable original CBS URLs, no arbitrary host, feed, pagination, credentials, proxy, redirects or retry.
- Within existing .github/workflows/ci.yml, exactly one **same-repository original research PR branch** is allowed to run the direct probe, after offline synthetic/negative regression. Other PRs and main pushes do not run this three-GET live job.
- Job uses pinned Python 3.12 and pinned GitHub Actions setup/checkout, contents:read, checkout credentials not persisted, maximum 5 minutes and **three direct GETs each at most 8192 original bytes / 25 seconds**.
- Original HTTPS **200**, exact final URL, application/json, identity response encoding, source-native regional codes containing two trailing spaces, tenure codes, 10 fixed official aggregate numeric values, and native 2025VJ06 definitive period status are required.
- CBS unit trap: original property GemiddeldeBouwkostenPerM_2 means **EUR per cubic metre**; original property GemiddeldeBouwkostenPerM_3 means **EUR per square metre**. Numeric source interpretation is pinned and tested.
- GitHub stdout/step summary receives **only typed public aggregate values, request URL, complete original SHA256/byte length and retrieval UTC**; no original JSON responses, private properties, coordinates, large provider file or insurer data retained.

A passing actual Actions job and its actual provider response receipt are the direct HTTP attestation, not a self-assertion made by the script. The runner explicitly emits remote_direct_runner_trusted=false; only external inspection of the actual GitHub run can establish its execution.

## Independent science and rights gates

This separate three-GET contract does **not** change the nine-request direct 2012/2026 CBS draft PR #1542, the ten-row 2026 research PR #1553, or the two-period research PR #1560. Repeated requests for one source table do **not** multiply the distinct source count.

CC BY 4.0 permits attributed commercial reuse of CBS official statistics; it is not a licence to infer personal property, insurer claims, policy-level TIV or actuarial reconstruction cost. A definitive rolling mean from new building permits is not a constant-quality building cost index for identical structures. Country NL01 overlaps the four regions and **must not be summed into them**.

No CAT insured-loss, synthetic portfolio valuation or scientific model admission is authorized by this direct test. The prior Neon samples and logs remain research-only and not direct-runner-verified unless an independent append-only GitHub runner receipt is actually recorded after the job passes.
