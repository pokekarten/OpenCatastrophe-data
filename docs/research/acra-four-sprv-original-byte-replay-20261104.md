<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Reproducing the four original ACRA UEN source-response fingerprints

**Non-admitted public source research.** The original source is the Singapore government's ACRA-published **Entities Registered with ACRA** dataset, resource ID `d_3f960c10fed6145404ca7b821f263b87`. It reported last update `2026-10-14T17:10:49+08:00` and coverage to `2026-10-11` at review time.

Original dataset metadata: https://api-production.data.gov.sg/v2/public/api/datasets/d_3f960c10fed6145404ca7b821f263b87/metadata

Query pattern, one exact entity at a time: `https://data.gov.sg/api/action/datastore_search?resource_id=d_3f960c10fed6145404ca7b821f263b87&filters=%7B%22entity_name%22%3A%22<URL-ENCODED-EXACT-NAME>%22%7D&limit=10`. The query was checked for `success=true`, exactly one `records` row, exact `entity_name` and `uen`, `issuance_agency_desc=ACRA`, `uen_status_desc=Registered`, `entity_type_desc=Local Company`. Original API responses were SHA-256 hashed over the response HTTP body bytes, not reserialized JSON. **No original provider bytes were committed.**

| Exact filter legal name | Original verified UEN | Original body SHA-256 | Observed bytes |
|---|---|---|---:|
| ASTRO RE PTE. LTD. | `202117654Z` | `30fe030a25c1ca8bc9ee5fa1445981b0d860f5e487a7860e0f1695e392ab04f7` | 1098 |
| MANATEE RE III PTE. LTD. | `201912999K` | `ab7a6f23aeae8fe139c4acd02f9b737adf9d88a06e8bb97600d12b5972452e89` | 1125 |
| NAKAMA RE PTE. LTD. | `202130681G` | `5823e606096a940bcf832eb427d135f05884b76d877e518be82263c09fd5cfa2` | 1101 |
| TOMONI RE PTE. LTD. | `202206915M` | `21816d16cf931eb584ffab76bec2af0e94717c772548dd50b0e48486b55be105` | 1101 |

A reproducibility challenge should obtain the original exact bytes in an isolated working directory and compute `sha256sum original-response.json` **before** parsing or normalizing JSON. A future monthly data.gov.sg version may legitimately change the JSON body, row IDs and even company status. A matching SHA-256 against a locally supplied pin is not independent source authentication, a guaranteed historical replay, licence review, or financial-model admission. If live bytes do not match a stored digest, report **source revision or unresolved drift**; never silently update a hash to force success.

The [original-source research note](singapore-sprv-acra-mas-public-reference-20261104.md) carries the crosswalk to MAS regulation and explicitly distinguishes Marsh/Aon managers from equity parents, cedants and real insurance portfolios. The `landscape/sources-singapore-ils-acra-mas-20261104.json` registered canonical shard preserves ACRA, MAS, Manatee FY2024 original filings, and BSX 2022/2026 note lifecycle as independent **not_admitted** source candidate types. The executable consumer and exact SHA-256 source references remain in private [NextGen PR #279](https://github.com/pokekarten/NextGen/pull/279).

**No original ACRA CSV/JSON bytes, investment security trade data, policy-level exposures or treaty wording are distributed by this note.**
