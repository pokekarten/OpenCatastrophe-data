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

The pinned 2026-11-15 profile fails on an unexpected or reordered 42-column header, any mixed/stale row data_version, unexpected market/year, duplicate (market, year, insurer_id), an invalid LEI shape, missing/unsafe HTTPS source URL, invalid numeric values, missing/negative gross premium, or departure from the advertised 1,772 rows across 18 named markets. Missing optional amounts remain null/unknown, **never zero-filled**. It emits only local-byte SHA-256, byte size, row count, market count, number of missing property-premium values and **explicit false admission indicators**. It does not authenticate the publisher response merely by hashing a local file.

## Rights / financial semantics

Polisa states CC BY 4.0 for its *own* derived calculations and compilation, but source-attributed upstream rights remain product- and market-specific; see its [terms](https://polisapro.com/terms) and [methodology](https://polisapro.com/methodology). Estonia contains CC BY-SA 4.0 upstream statistics; Serbia NBS requires separate permission for commercial reuse; additional Hungarian, Slovenian, Bosnia and Herzegovina and other original-source restrictions may apply. No blanket commercial admission is inferred.

Amounts are EUR millions as compiled by Polisa; financial-year and source-specific definitions vary. Insurer/group name, LEI, line-of-business premium and market share are **not** individual insured properties, buildings, TIV, policy terms or a CAT event-loss table. Do not merge group and solo totals indiscriminately or interpret missing values as zeros.

**Next gate:** independently confirm *original provider* bytes (size, SHA-256, final URL, response timestamp and version), run this exact-file preflight, review row/source rights and map legal entity/branch/group against GLEIF/EIOPA before any private NeonDB staging or model input. Existing access contract remains documented-only; this tool does not change it.
