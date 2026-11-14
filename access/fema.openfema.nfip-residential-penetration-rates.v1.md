<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/fema.openfema.nfip-residential-penetration-rates.v1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `fema.openfema.nfip-residential-penetration-rates.v1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** fema.openfema.nfip-residential-penetration-rates.v1

## Source ids

- fema.openfema.nfip-residential-penetration-rates.v1

**Provider:** Federal Emergency Management Agency (FEMA), National Flood Insurance Program / OpenFEMA

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://www.fema.gov/openfema-data-page/nfip-residential-penetration-rates-v1>

**Service root:** <https://www.fema.gov>

**Api version:** OpenFEMA NFIP Residential Penetration Rates v1; official catalogue last data refresh 2026-08-04

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- nfip_residential_penetration_rates_v1_documented_get

### Path templates

- /api/open/v1/NfipResidentialPenetrationRates

**Parameter rules:** Provider documents GET and OData-like $top, $skip, $filter and $select. Its current v1 endpoint is fixed; an earlier separate Neon research receipt \#41 records an exact GET with $top=2 on 2026-11-12, not a newly executed probe. This documentation-only contract does NOT permit a new network request, paging, unrestricted field selection, bulk acquisition or transmission of results. A future reviewed fixed read-only request must bind parameters, UTC timestamp, response size, content type, exact original-body SHA-256, release identity and 429 policy before activation. No user-supplied host, URL, headers or unbounded query.

## Response contract

### Expected media types

- application/json

**Format:** OpenFEMA v1 JSON records with a provider metadata object and NfipResidentialPenetrationRates records; no original response was fetched under this access contract.

**Scientific semantics:** US county/community-level estimated residential NFIP contracts-in-force divided by estimated residential structure stock from NSI 2022, with separate SFHA and all-area ratios. Official refresh 2026-08-04 and three-month update frequency are metadata, not a frozen data version. Private flood policies are excluded. Some rates exceed 100% owing to incomplete NSI building stock; do not clip or treat them as a valid probability. Provider row id may change on refresh, so use FIPS plus asOfDate and retrieval identity for subsequent joins. Not actual insured exposure, building TIV, observed flood hazard, damage or a loss model; NSI-linked evaluations are not an independent holdout.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Official OpenFEMA guidance states a general limit of 200 requests per 5 minutes per IP and no more than two concurrent requests, with HTTP 429 on exceedance. NFIP claims and policies have stricter limits, but this penetration-rates endpoint is a distinct product. No request authorized or executed by this documented_only contract; a future bounded probe needs separate review.

**Mutability notes:** Version 1 remains a mutable quarterly-updated dataset (official last refresh 2026-08-04 when reviewed 2026-11-14). The provider says row id is not stable between refreshes, and incomplete NSI 2022 denominators can yield over-100% penetration. Retain source/endpoint, asOfDate, FIPS, exact request and original response SHA and bytes before any comparable empirical claim.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_reviewed

**Terms url:** <https://www.fema.gov/about/openfema/terms-conditions>

**Commercial automation status:** restricted

**Redistribution status:** unknown

**Notes:** Official OpenFEMA Terms and Conditions last updated 2025-01-22 govern both API and file downloads. They state use is solely for statistical research or reporting; prohibit reidentification and individual eligibility decisions; require citation of exact version and access time and a no-FEMA-endorsement notice; reserve the right to request cessation and deletion. The 'secondary use' paragraph does not explicitly clear commercial CAT production, insurer underwriting, derived model redistribution or indefinite retention. Public US federal provenance is not blanket third-party dataset rights. Statistical research scope may be assessable after specific permission/rights review, but commercial insurer automation, raw/derived redistribution and production modelling remain unapproved. No new download and no personal/provider data published in Git.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.fema.gov/openfema-data-page/nfip-residential-penetration-rates-v1>
- <https://www.fema.gov/about/openfema/api>
- <https://www.fema.gov/about/openfema/terms-conditions>
- <https://www.fema.gov/about/openfema/developer-resources>

**Notes:** T0 official product, access route, rate limits, terms and scientific scope reviewed 2026-11-14; no new T1/T2/T3/T4 probe and no admission. Existing private insurance-risk-core Neon sample \#41 is a distinct 2026-11-12 two-row research observation with recorded original-response and normalized-sample hashes and model_input_approved=false. This access contract neither asserts that original bytes were re-fetched nor changes database storage authorization. Next action: independently resolve permitted commercial insurer CAT modelling, retention and redistributable outputs under these custom terms before allowing a bounded fixed request and independent science QA.
