<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# NFIP v3 claims + policies: bounded aggregate-only source preflight

**Status:** implemented offline local-source validator, synthetic tests; **no live
FEMA v3 bytes verified by this change**, no new manifest, no API acquisition
entitlement, no provider records committed or published, and **not an admitted
CAT-model input**.

## Why this is a useful next source pair

The current non-admission landscape already records
`fema.openfema.nfip-redacted-claims.v3` and
`fema.openfema.nfip-redacted-policies.v3`. OpenFEMA exposes claims and policy
transactions for the **U.S. National Flood Insurance Program**, not the entire
U.S. commercial/private flood insurance market. The two source families can
inform independent **county-level** insurance research when exact provider
rights, version, response and completeness evidence is obtained.

The public API has moved away from older FimaNfip* v2 naming. The researched
successor candidate routes are:

- `https://www.fema.gov/api/open/v3/NfipClaims`
- `https://www.fema.gov/api/open/v3/NfipPolicies`
- Official machine-readable catalogue: `https://www.fema.gov/api/open/v1/OpenFemaDataSets`
- Official field registry: `https://www.fema.gov/api/open/v1/OpenFemaDataSetFields`

**Current routes are research pointers, not a verified live provider receipt
or a grant to automate**. Before acquiring records, query the official
OpenFEMA metadata/field catalogue for the *exact* product, version, latest
refresh, deprecation state, source field names and API/service terms; then
obtain separately reviewed bounded original responses and byte-level receipts.
Do not fall back silently to `FimaNfipClaims` or `FimaNfipPolicies`.

Authoritative semantics and privacy warnings:
- https://agents.floodsmart.gov/flood-maps-and-data/faqs-about-nfip-data
- https://www.fema.gov/about/openfema/terms-conditions
- https://catalog.data.gov/dataset/fima-nfip-redacted-claims-openfema
- https://catalog.data.gov/dataset/fima-nfip-redacted-policies-openfema

FEMA explicitly states that rounded/truncated coordinates are inappropriate
for location-level commercial CAT modelling, and that **no individual claim to
policy record join key exists**. A claim's loss year is **not** a payment date.
Policies are transaction/renewal records: a record is in force on the
as-of date only when `effective <= as_of < termination`. Historical
incompleteness (particularly pre-2009 policy history), geographic reporting
changes, sample coverage, currency, and programme boundaries must remain
visible. Aggregate comparisons do not establish coverage for the same home,
insurer, event, policy, or calibrated loss probability.

## What has been implemented

`research_runners/nfip_v3_aggregate_preflight_v0.py` is **offline-only**.
It reads exactly two previously acquired, rights-cleared **bounded API JSON
pages** (each at most 20 MB / 20,000 records). It requires independently
recorded exact SHA-256 for both original responses, the modern v3 envelopes,
unique source row IDs, five-digit county codes, valid dates, and finite
Decimal financial fields.

It reports separate:
1. claims transaction-record counts and reported paid building+contents
   amounts **by county and year of loss**;
2. active policy transaction-record counts and reported building coverage
   **by county at the chosen as-of date**.

A missing payment or coverage value makes that group's monetary sum **null**,
never zero or a silently partial sum. Groups with fewer than 10 source records
are withheld. Individual IDs and coordinates are not in the output. The
response includes exact source-byte SHA-256, byte size and sampled row counts,
but **not** the provider records themselves.

A single `$top` API page or bounded extract does not prove a complete
population. **Do not annualize, extrapolate, infer claims frequencies, divide
these mismatched groups into loss ratios, or allocate risks to buildings or
insurers**. This pilot deliberately does not automate source downloads,
join the two provider families at a person/property level, publish any input,
or generate an insured-event loss.

## Deterministic local use

Only after access, privacy and reuse conditions are explicitly cleared,
acquire the two exact original response byte streams outside Git. Record their
full SHA-256 values independently and run:

```bash
python research_runners/nfip_v3_aggregate_preflight_v0.py \
  --claims-json /private/original-claims-page.json \
  --claims-sha256 EXPECTED_64_HEX_SHA256 \
  --policies-json /private/original-policies-page.json \
  --policies-sha256 EXPECTED_64_HEX_SHA256 \
  --as-of 2024-06-01
python -m unittest tests.test_nfip_v3_aggregate_preflight_v0 -v
```

No input path is printed. Do not commit downloaded source JSON, model
portfolios, credentials, secret URLs, or results containing personal records.

## Advancement gates

1. Independently confirm `NfipClaims` / `NfipPolicies` v3 with the **official
   current** OpenFEMA dataset and field catalogues (including deprecation and
   exact data refresh dates), then review provider API terms and U.S.
   government/third-party data rights for the precise intended use.
2. Produce a trusted acquisition receipt for a **single bounded page** per
   product: fixed allowlisted request, UTC retrieval, exact bytes+SHA, response
   fields, content type and absence of secrets; run the offline parser on real
   source bytes in a controlled environment.
3. For larger authorised datasets, prove query/pagination coverage, revision
   consistency, transaction semantics, completeness and geographic aggregation
   before a national or longitudinal statistic is claimed.
4. For an actual CAT validation lane, add independently admitted hazard
   footprints and compatible region/time mappings. Treat NFIP insured loss
   programme experience separately from modelled structure inventory,
   vulnerability, private insurance and reinsurance treaties.

This source work does **not** alter existing canonical landscape records,
source-access admission status, manifests, privacy gates or external licences.
