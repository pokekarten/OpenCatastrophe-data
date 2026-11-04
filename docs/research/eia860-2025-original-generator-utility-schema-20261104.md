<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EIA-860 annual 2025: original generator roster + utility crosswalk proof

**Research only; no insurer, location-level insured exposure, insured TIV, GEM project identity or ownership allocation has been inferred.** Follow-up to completed [15/15 independent EPA–EIA plant IDs](eia860-annual-2025-original-plant-proof-20261104.md) and the [6/6 generator Owner Schedule 4 sums](eia860-2025-original-owner-schema-20261104.md).

## Primary source and original-file perimeter

The official [EIA Form 860 detailed data page](https://www.eia.gov/electricity/data/eia860/) documents the following separate worksheets and their interpretation:

- `3_1_Generator_Y2025.xlsx`: **Operable** includes generators that are operating, standby or temporarily out of service; **Proposed** includes planned units not in service; **Retired and Canceled** holds recent retired and canceled generators, **not** a complete historic registry of all retirements. These **must not** be merged as one set of operating and insurable generators.
- `1___Utility_Y2025.xlsx`: original reporting-year utility-level attributes. An EIA utility identifier does **not** by itself prove ultimate corporate ownership or an LEI.
- `4___Owner_Y2025.xlsx`: *only* an EIA Schedule 4 generator ownership exception roster. Its absence for a reported generator is a source-semantic signal to review the operator relationship, **not** a zero owner share and not a missing facility.

The **original EIA 2025 archive** is [fixed at this byte hash](eia860-annual-2025-original-plant-proof-20261104.md): `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba`, **23,622,347 bytes**, 13 ZIP members. The original source archive is freshly re-downloaded on a dedicated GitHub job, checked against that original SHA and parsed in memory. Neither source bytes nor utility/owner names are persisted.

## Implemented native-source sanity checks

[Python original source schema audit](../../research_runners/eia860_2025_generator_utility_schema_v0.py) and [synthetic negative tests](../../tests/test_eia860_2025_generator_utility_schema_v0.py) inspect the actual source's OOXML workbook sheet relationships, streaming only a small first-row header window and emitting **only allowlisted header tokens and source member SHA digests**. They require the exact three generator reporting tabs. They do not print any generator- or utility-level source records, identifiers or coordinates.

The [successful original EIA source job #41903149796](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41903149796) actually re-downloaded the original pinned full EIA archive and independently parsed both native XLSX files. It ran **10 synthetic tests** and emitted source metadata only:

| Original source workbook | Original workbook SHA-256 | Bytes | Actual native sheet(s) |
| --- | --- | ---: | --- |
| `3_1_Generator_Y2025.xlsx` | `931e1ed0be2c6706794c196f158f779b5c8a32d08c61d748a823dfc25a3201a8` | **11,223,392** | **Operable; Proposed; Retired and Canceled** |
| `1___Utility_Y2025.xlsx` | `aa82abf7ecab6d202d44952e7ada2586f8a053dead3956d3eaca756bc8232db9` | **553,829** | **Utility** |

The actual source Generator header row contains `Plant Code`, `Generator ID`, `Utility ID`, `Status`, `Nameplate Capacity (MW)`, `Ownership`, `Prime Mover`, `Energy Source 1`, and other allowlisted reporting attributes. The Utility sheet contains `Utility ID`, `Utility Name` and address-related fields; **only the identifiers and allowlisted column labels** are read by the research join, and no source names, raw ownership shares, addresses or coordinates are printed. These SHA-256 values identify the nested **original XLSX bytes**, not a private derivative.

```bash
python -m unittest tests.test_eia860_2025_generator_utility_schema_v0 -v
python research_runners/eia860_2025_generator_utility_schema_v0.py --live
```

## Next acceptance gates

1. Exact-original generator and utility member SHA-256, native `Plant Code`, `Generator ID`, reporting utility ID, capacity/status headers and sheet scope validation.
2. Exact key join (2025, plant, generator) from generator roster to the six explicit Owner Schedule 4 generator keys, **separately** for Operable, Proposed, Retired and Canceled. Do not count a generator in Proposed/Retired as physically operating or currently insured.
3. Determine which roster rows have explicit Schedule 4 owner shares and which need an operator-key confirmation, including duplicates, statuses, and **unresolved** rather than zero-owner treatment. The entire 15-plant cohort is not a population census of insurers.
4. Distinguish EIA reporting operator or utility code from a GEM project owner, ultimate legal beneficiary (GLEIF) and eventual insurer/reinsurer counterparty. All identity and licensing boundaries remain in [issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251).

No insurance database writes or model admission take place in this research.

## The actual key-conservation research adapter

The next [in-memory generator/utility/owner crosswalk](../../research_runners/eia860_2025_generator_utility_owner_join_v0.py) and [synthetic negative tests](../../tests/test_eia860_2025_generator_utility_owner_join_v0.py) use **four independently pinned original source components**: whole annual EIA ZIP, nested Generator XLSX, nested Utility XLSX and previously pinned Owner XLSX. They strictly preserve the **three source generator reporting scopes**. For each of the 15 confirmed Delaware plant IDs, the exact key `(Plant Code, Generator ID)` identifies reported generator keys in Operable vs Proposed vs Retired and Canceled, preventing cross-tab double counting. Any row appearing in more than one tab is marked for review rather than multiplied.

Each generator row's 2025 `Utility ID` is checked for presence in the original `1___Utility_Y2025.xlsx`, **not** treated as a legal beneficial-owner proof. Each of the six original generator keys with explicit Schedule 4 ownership is sought by exact (plant, generator) key across source reporting tabs; a missing Owner row **is not interpreted** as 0%, 100% operator-owned, or absent insurance coverage. EIA `Status` values are restricted to the official codebook (unknown or incomplete statuses cannot be logged as source text and require review). We preserve original status-scope distinctions and detect duplicates, source join misses, and missing utility-code evidence without printing raw source keys.

**No actual count of operable vs proposed vs retired generators, no matched owner schedule count, and no utility operator link is claimed until a live run of the new adapter succeeds on the exact original EIA source ZIP.** All outputs remain aggregate, research-only, and explicitly refuse insurance portfolio/TIV model admission.

```bash
python -m unittest tests.test_eia860_2025_generator_utility_owner_join_v0 -v
python research_runners/eia860_2025_generator_utility_owner_join_v0.py --live
```

**Next scientific gate:** Report exact live-source generator counts by reporting scope and source utility match rates. To build a synthetic insurer portfolio, separate named EIA operator legal entities and generators into reproducible, licensed and dated research inputs with independent company/LEI and geographic risk-quality evidence. The mere existence of a generator is not proof of a building, a commercial insurance policy, a modeled event loss or an inward/outward reinsurance treaty.
