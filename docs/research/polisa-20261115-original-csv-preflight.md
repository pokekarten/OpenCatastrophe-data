<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Polisa CEE 2026-11-15 original CSV preflight (research-only)

On 2026-11-15 the provider's [download page](https://polisapro.com/data) advertised an all-markets CSV for 18 CEE markets with **1,772 insurer-year rows**, plus CSV/XLSX per country. This is a *publisher count*, not an independent complete CSV-byte receipt. Its [README](https://polisapro.com/data/README.txt) identifies exact **data version 2026-11-15.792a4a** and its [codebook](https://polisapro.com/data/polisa-codebook.csv) explains missing-value semantics. The original provider file listing and read-only search intermediary also expose a 42-column CSV header containing insurer_id, source, lei and annuity claims/expenses.

**Important observed version drift:** the search intermediary showed the all-markets export under 2026-11-15.792a4a while a separately fetched Poland CSV representation still identified 2026-11-09.d5ad62 with an older ratio schema. This is not a trusted original HTTP response; **do not claim the live Poland download is currently stale**. It is evidence for an explicit fail-closed per-file version/schema comparison before joining country files.

## Reproducible offline structural gate

A new [offline source preflight](../../scripts/polisa_csv_preflight_v0.py) requires a previously obtained, separately authorised original CSV stored outside public Git. It never fetches data, stores rows, makes database writes or exports provider data.

Example execution after exact source acquisition and permission review:

~~~sh
python -m scripts.polisa_csv_preflight_v0 --csv /private/polisa-all-markets.csv
python -m unittest tests.test_polisa_csv_preflight_v0 -v
~~~

The pinned 2026-11-15 profile fails on an unexpected or reordered 42-column header, any mixed/stale row data_version, unexpected market/year, duplicate (market, year, insurer_id), an invalid LEI shape **or MOD 97-10 check digit**, missing/non-HTTPS/non-public-IP source URL, invalid numeric values, missing/negative gross premium, or departure from the advertised 1,772 rows across 18 named markets. Missing optional amounts remain null/unknown, **never zero-filled**. It emits only local-byte SHA-256, byte size, aggregate counts, rights/identity review-priority flags and **explicit false admission indicators**. It does not authenticate the publisher response merely by hashing a local file.


**LEI validation scope:** The [GLEIF LEI CDF Q&A](https://www.gleif.org/en/lei-data/access-and-use-lei-data) describes the 20-character LEI structure and check digits by ISO 17442 / ISO 7064. This offline preflight checks uppercase ASCII shape, two trailing decimal check digits, and the MOD 97-10 remainder of one. Passing that arithmetic does **not** establish that a legal entity is registered, current, solvent, a member of the stated insurer group, or the rightful owner of the number. An exact-version GLEIF Level 1/Level 2 registry join remains a separate source-rights and identity review. Original report URLs remain provenance text; the script never connects to them. Literal non-public IP targets are rejected as provenance evidence.

## Aggregate source-rights and identity review coverage

The local preflight additionally reports `distinct_upstream_source_links`,
`lei_present_rows`, `lei_missing_rows`, and
`rows_requiring_original_source_rights_review`, without exposing source URLs,
insurer identities or amounts. It also emits
`priority_rights_review_rows_by_market` for six **triage flags only**:
Estonia (Statistics Estonia CC BY-SA), Serbia (NBS noncommercial / separate
commercial consent), Hungary (MABISZ), Slovenia (SZZ), Bosnia and Herzegovina
(AZOBiH/ANO FBiH/AZORS), and North Macedonia (MSE). These names and conditions
come from the Polisa [README](https://polisapro.com/data/README.txt) and
[terms](https://polisapro.com/terms), retrieved on 2026-11-15.

The six labels **do not determine rights of each individual row**:
some market records use different source documents; additional restrictive
IMF, APR, stock-exchange and other sources may occur in or outside those
markets. Every row, including all markets not named above, remains
`rows_requiring_original_source_rights_review`. Market flags prioritize
legal/source checking; they are **not** an allow-list, deny-list, or row-level
licence conclusion. The `lei_present_rows` count records an arithmetically
valid identifier only, while `gleif_original_identity_crosswalk_completed`
remains false until exact original GLEIF identity evidence is evaluated. All
commercial-use, model-admission, and Neon-import decisions remain blocked.

## Rights / financial semantics

Polisa states CC BY 4.0 for its *own* derived calculations and compilation, but source-attributed upstream rights remain product- and market-specific; see its [terms](https://polisapro.com/terms) and [methodology](https://polisapro.com/methodology). Estonia contains CC BY-SA 4.0 upstream statistics; Serbia NBS requires separate permission for commercial reuse; additional Hungarian, Slovenian, Bosnia and Herzegovina and other original-source restrictions may apply. No blanket commercial admission is inferred.

Amounts are EUR millions as compiled by Polisa; financial-year and source-specific definitions vary. Insurer/group name, LEI, line-of-business premium and market share are **not** individual insured properties, buildings, TIV, policy terms or a CAT event-loss table. Do not merge group and solo totals indiscriminately or interpret missing values as zeros.

**Next gate:** independently confirm *original provider* bytes (size, SHA-256, final URL, response timestamp and version), run this exact-file preflight, review row/source rights and map legal entity/branch/group against GLEIF/EIOPA before any private NeonDB staging or model input. Existing access contract remains documented-only; this tool does not change it.
