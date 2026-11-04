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

The exact native join **has now succeeded** on the original pinned EIA 2025 ZIP in [the live original-source research job #41904234652](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41904234652), following synthetic tests. It provides the source population and status-/key-cardinality counts below. All outputs remain aggregate, research-only, and explicitly refuse insurance portfolio/TIV model admission.

```bash
python -m unittest tests.test_eia860_2025_generator_utility_owner_join_v0 -v
python research_runners/eia860_2025_generator_utility_owner_join_v0.py --live
```

**Next scientific gate:** Report exact live-source generator counts by reporting scope and source utility match rates. To build a synthetic insurer portfolio, separate named EIA operator legal entities and generators into reproducible, licensed and dated research inputs with independent company/LEI and geographic risk-quality evidence. The mere existence of a generator is not proof of a building, a commercial insurance policy, a modeled event loss or an inward/outward reinsurance treaty.

## Verified original generator / reporting utility / Owner Schedule 4 pilot — 2026-11-04

A [successful direct original-EIA source run](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41904234652) re-acquired the fixed **23,622,347-byte** 2025 annual ZIP with original SHA `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba`, then independently verified the nested Generator, Utility and Owner workbook SHA-256 fingerprints from the earlier receipts. The source run passed the initial 10 schema tests and 12 generator-utility-owner tests. This is a **real provider source audit**, not a simulated portfolio.

| Exact 2025 EIA source perimeter | Actual unique counts in the 15 Delaware plants |
| --- | ---: |
| Independently EPA-FRS/EIA-2025-confirmed plant codes | **15** |
| Distinct generator keys `(Plant Code, Generator ID)` in annual three-sheet source | **35** |
| Operable tab: source code `OP` (operating in 2025 reporting scope) | **26** |
| Operable tab: source code `SB` (standby in 2025 reporting scope) | **4** |
| Proposed tab in this pilot | **0** |
| Retired and Canceled tab: source code `RE` | **5** |
| Generator keys appearing in multiple tabs or duplicated within one tab | **0** |
| Distinct `Utility ID` values on these 35 generator keys | **11** |
| Generator keys with a utility ID found in original 2025 EIA Utility workbook | **35/35** |
| Plant codes with more than one source reporting utility ID | **0** |
| Original nationwide Utility workbook distinct IDs (not company-group counts) | **6,946** |
| Explicit Owner Schedule 4 rows / distinct generator keys in pilot | **6 / 6** |
| Owner Schedule 4 generator keys matched to Generator source inventory | **6/6** |
| Owner Schedule 4 matched generator keys by source tab | **3 Operable, 0 Proposed, 3 Retired and Canceled** |
| Original workbook source rows lacking *both* official plant and generator ID (per status tab) | **1 each** |

The **three unkeyed source rows** from the three generator worksheets are separately reported and **not** counted as generators: they lack usable official plant and generator keys. Their free-text payloads were neither logged nor used as evidence of actual facilities. No malformed in-cohort generator keys, missing/unknown source statuses, duplicated generator keys, absent reporting utility IDs or unmatched Owner Schedule 4 generator keys occurred in the pilot.

### Scientific interpretation

- **35 source generator keys ≠ 35 insured buildings**; several may be equipment units at the same physical site and five have **retired** reporting status in the **2025** vintage. Even 26 code `OP` rows only show EIA reporting status, not a 2026 operating guarantee, insurance eligibility, policy, CAT loss or BI replacement value.
- EIA `Utility ID` is the source **reporting-utility identifier**. Exactly **11** such codes occur among the 35 generators, and no original plant in this cohort has multiple reporting utility IDs. These **11 are not 11 insurer groups** and not independently resolved ultimate beneficial ownership/LEIs.
- **Three of the six explicitly Owner-Schedule-reported generator keys occur in the retired reporting tab.** Do not count all six as currently operable insured assets. A generator **without** an Owner Schedule 4 row is **not ownerless**; a missing Schedule 4 row cannot be treated as proof of the current owner without an independently validated reporting-operator relation and the EIA survey instructions.
- The original source Utility workbook's `Utility Name`, address and other entity fields were not printed. This audit is the base for a **controlled legal-entity lineage and insurer portfolio prior** with independent company reports, GLEIF entities, commercial data permissions, spatial asset proof and treaty contracts still separate.

**Next verification:** (1) inspect the exact EIA `Ownership` status codebook and 2025 Utility→operator semantics, (2) check 11 utility IDs' corporate parent evidence against dated legal company sources, and (3) derive only evidence-labeled **synthetic** portfolio weights and capacity exposure, never assume all EIA power plants are insured by a named carrier or that nameplate MW is TIV.
