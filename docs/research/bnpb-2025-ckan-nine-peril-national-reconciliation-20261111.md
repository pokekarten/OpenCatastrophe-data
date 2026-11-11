<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BNPB 2025: nine-peril DataStore national aggregate reconciliation

Evidence date: 2026-11-11. Provider: Indonesia BNPB / Satu Data Bencana.

Evidence class: official provider CKAN DataStore API contents returned via a read-only research retrieval intermediary, not original provider response bytes captured locally, not downloaded or SHA-256-pinned original XLSX, and not science, licensing or model admission.

Official package: https://data.bnpb.go.id/dataset/kompilasi-data-kejadian-dan-dampak-bencana-2025

- Province × peril damaged houses, resource ID 43b83e79-c8b6-4b9a-b2f0-d1cbd9cfa636: https://data.bnpb.go.id/api/3/action/datastore_search?resource_id=43b83e79-c8b6-4b9a-b2f0-d1cbd9cfa636&limit=80
- Peril × damage severity summary, resource ID 6e947c9c-2404-4c02-b743-34dc5320f399: https://data.bnpb.go.id/api/3/action/datastore_search?resource_id=6e947c9c-2404-4c02-b743-34dc5320f399&limit=80
- Official resource_show metadata returned both as XLSX, size 18,955 and 12,646 bytes respectively, with empty hash fields, but no original XLSX was fetched or hashed. The publisher pages display Open Data Commons Attribution License; exact asset and commercial/republication review remains open.

## Critical row-grain finding

The province response has **39 rows: 38 province observations plus a national INDONESIA aggregate**. The severity summary has **10 rows: nine peril observations plus a Total aggregate**. Counting these total rows as additional data would double-count reported damaged-house counts.

For **all nine** hazards, the following three values agree exactly in the exposed 2025 source:

    sum(38 province house-damage counts) = INDONESIA total = sum(heavy + medium + light house damage for that peril)

| Official BNPB peril | Reported damaged houses | Incidents |
|---|---:|---:|
| BANJIR (flood) | 243,774 | 2,009 |
| CUACA EKSTREM (extreme weather) | 24,554 | 958 |
| ERUPSI GUNUNG API (volcanic eruption) | 232 | 7 |
| GELOMBANG PASANG DAN ABRASI (coastal waves/abrasion) | 334 | 28 |
| GEMPABUMI (earthquake) | 3,710 | 28 |
| KEBAKARAN HUTAN DAN LAHAN (forest/land fire) | 24 | 1,329 |
| KEKERINGAN (drought) | 0 | 37 |
| TANAH LONGSOR (landslide) | 8,571 | 330 |
| TSUNAMI | 0 | 1 |
| **Total** | **281,199** | **4,727** |

The publisher severity grand total is **69,049 heavily damaged, 62,487 moderately damaged and 149,663 lightly damaged houses**, summing exactly to **281,199**. All 38 exposed province codes are unique, and the national total row has a null province code. Some source count cells are numeric-looking **text** (e.g. "0.0" for drought/tsunami); absence, missing, text, and numeric zero must never be conflated.

Counts are reported damaged houses, **not** unique physical building IDs, geolocated insured sites, TIV, insurer claims, monetary loss, annualised loss rates, or independent vulnerability evidence. Data are aggregated by peril and province and separately by peril and severity; a province × peril × severity intersection is **not established**. The reporting year 2025 may be affected by event overlap and reporting delays.

## Reproducible code and tests

- New offline runner: [research_runners/bnpb_2025_ckan_reconcile_v0.py](../../research_runners/bnpb_2025_ckan_reconcile_v0.py). Takes the two previously acquired CKAN JSON response files via --province-json and --summary-json, never makes network calls or exports source rows. Fails closed on truncation, missing perils, wrong resource IDs, duplicate province codes, negative/fractional/missing numbers and any mismatch among all national/detail/severity totals.
- Updated the existing offline original-XLSX preflight to exclude and reconcile INDONESIA and Total when encountered as worksheet rows, rather than mistakenly adding them to source observation counts. The original workbook has NOT been examined, so no assertion of its exact header structure is made.
- **Local tests:** 15 synthetic JSON response tests and 18 synthetic OOXML workbook tests passed. The 9/9 real-API reconciliation above was calculated separately from official publisher-exposed DataStore contents obtained via an intermediary; it was not a locally checksum-pinned run of the new Python script against original provider JSON bytes.

Example local commands, after acquiring original publisher API JSON into a permissioned local private directory:

    python -m research_runners.bnpb_2025_ckan_reconcile_v0 --province-json /secure/province.json --summary-json /secure/summary.json
    python -m unittest discover -s tests -p 'test_bnpb_2025_*v0.py' -v

No source XLSX/PDF/JSON data rows have been committed; no CAT or Neon database writes, commercial rights admission, external-data redistribution approval, or scientific model-input admission has taken place.

## Remaining causal gate

Freeze original two XLSX byte identities and original CKAN API receipts through a working approved provider route, compare their worksheet/tabular representation, review exact product rights, and only then stage a non-production CAT model benchmark with explicit 2025 time and peril/region support. Do not use the same 2025 records as both calibration and untouched holdout evidence.
