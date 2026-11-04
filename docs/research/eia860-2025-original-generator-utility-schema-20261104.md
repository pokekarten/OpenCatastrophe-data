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

The nested Generator workbook is expected to be about **11.2 MB**, nested Utility workbook about **554 kB**, based on original ZIP central directory previously examined. Their **actual** SHA-256 values, worksheet names and recognized headers must be read from the new exact-original live CI job. Until then, no new real-source header, generator count or operator match is claimed.

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
