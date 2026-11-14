<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EIA-860 annual 2025 Owner workbook: native source schema and generator grain

**Owner worksheet schema research only; no individual owner/company names or site records are exported, no owner shares or insurer exposures inferred.**

## Why this is a better immediate research path than a guessed GEM crosswalk

The exact official EIA-860 annual 2025 ZIP original was independently acquired, hashed and **re-acquired against pinned SHA-256** in [PR #1291](https://github.com/pokekarten/OpenCatastrophe-data/pull/1291). All 15 Delaware EIA plant IDs found in the earlier EPA FRS live queries occur in the EIA annual Plant workbook with `State=DE`.

The [official EIA product description](https://www.eia.gov/electricity/data/eia860/) states that `4___OwnerYyyyy` records generator-level ownership **only for jointly owned generators or those wholly owned by an entity different from the reporting operator**. Generators not appearing in this special Owner schedule are generally owned by their operator under the survey instructions, but **their absence is not a machine-proven current owner identity** without crosschecking the corresponding generator roster, operator identity, status and reporting period. EIA ownership of generation equipment is **not** legal ownership of every building or environmental risk and does not establish corporate underwriting, insurable TIV, a specific reinsurer, or BI coverage.

[Catalyst Cooperative's PUDL generator ownership dictionary](https://docs.catalyst.coop/pudl/en/v2025.7.0/data_dictionaries/pudl_db.html) separately models original EIA generator IDs and owner-utility IDs as a multi-key relational table. Its `fraction_owned` is a **generator share**, never an insurer share. PUDL's specific annual vintage and licensing/provenance need their own review; we do not substitute its derived records for the independently pinned EIA original.

## Original file and currently bounded source checks

- Official original EIA ZIP URL: `https://www.eia.gov/electricity/data/eia860/xls/eia8602025.zip`.
- Exact pinned original ZIP SHA-256: `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba`.
- The original ZIP central directory includes `4___Owner_Y2025.xlsx`, compressed **501,586** and uncompressed **514,124** bytes. That does not yet attest the internal Owner sheet schema/row values.
- Use a read-only original-source ZIP audit, not the Sep-2026 GEM download form, to inspect the actual **generator-owner schedule's worksheets and expected header tokens**.

## Implemented first step

The [bounded owner-schema reader](../../research_runners/eia860_2025_original_owner_schema_v0.py) reuses the original-file check from [the EIA 2025 source proof](../../research_runners/eia860_annual_2025_original_zip_v0.py). It only inspects the *original* `4___Owner_Y2025.xlsx` and outputs source workbook SHA-256, workbook member length, worksheet **names**, number of sheets, and allowlisted potential header labels in the first 35 rows. The actual owner/source rows and arbitrary cell values are **never printed**, even when a source contains addresses, corporate names, or numeric shares.

It fails closed for missing/padded original source, corrupt ZIPs, unexpected sheet paths, null relationships and overlarge sheets. Its synthetic offline tests exercise the XLSX/ZIP graph and verify that the fake source owner's name never appears in output. One explicit source-specific CI job can read the pinned official EIA ZIP over HTTPS, keep all source bytes in memory and print this **schema-only** receipt.

```bash
python -m unittest tests.test_eia860_2025_original_owner_schema_v0 -v
python research_runners/eia860_2025_original_owner_schema_v0.py --live
```

## Acceptance and next step

1. Read the **successful public GitHub original-source job** before claiming the actual Owner sheet and column semantics. Synthetic tests are not a substitute for a real owner workbook read.
2. Once exact header fields and source hash are known, pin them and implement a read-only **generator-keyed** aggregation for the 15 EIA Delaware plants; preserve operator/owner distinction and conditional Schedule 4 coverage. Validate shares in percentage units (sum per generator ~100%) and report exceptions without inventing absent owners.
3. Only then consider translating true generation ownership into legal-entity identity and synthetic portfolio *priors*. Never infer actual insured buildings, building replacement costs, commercial source rights, reinsurer coverage or an inward/outward treaty from generator-equity observations.

Issue [#1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251) remains open pending verified GEM location/unit ID provenance and rights. This first source-original Owner step does not change any database or source admission gate.

## Real original Owner sheet fingerprint (2026-11-04)

The [public live GitHub original-source job](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41891296290) completed **successfully** and exercised all 7 synthetic metadata tests before fetching the exact EIA 2025 ZIP again against its pinned source SHA.

- Exact nested source member `4___Owner_Y2025.xlsx`: **514,124 bytes**, SHA-256 `f0600c57b24f065017983e50a8a6561c8aa563382bb8862ad216448ca32d9383`.
- Actual source worksheet: **`Ownership`**. Original source headers recognized by exact allowlist: **`Generator ID`, `Owner Name`, `Percent Owned`, `Plant Code`, `Plant Name`, `State`, `Utility ID`**.
- This matches the [official EIA generator-owner exception reporting description](https://www.eia.gov/electricity/data/eia860/). The source did not reveal ownership values or names in the GitHub logs.
- **Important semantic limit:** `Utility ID` is not automatically a legal entity LEI or insurance company, and `State` in the Owner schedule must not automatically be assumed to represent the physical site as opposed to an owner mailing address. The next audit uses **Plant Code and Generator ID only** for keying, not name/location matches.

The [second-stage bounded audit](../../research_runners/eia860_2025_owner_shares_cohort_v0.py) and its [synthetic tests](../../tests/test_eia860_2025_owner_shares_cohort_v0.py) now measure **EIA Owner Schedule 4 rows for the 15 EPA/EIA-confirmed Delaware plant IDs**, grouped by exact (plant, generator) keys. It checks whether the *reported* owner percentages sum to 100±0.05 percentage points, detects missing/bad source shares and repeated owner names, and prints only aggregate counts. **This is not a population census of every generator at the plant:** the Owner workbook intentionally omits operator-owned generators, so observed rows must not be extrapolated to 100% generator or company-wide ownership.

A fresh, exact-hash EIA source run and full GitHub CI are mandatory before writing **any actual observed ownership-share counts** into the evidence register. If a source group fails the share test, preserve the anomaly and continue research; never modify or impute original percentages to force a pass. No carrier, facility construction cost, BI downtime, hazard score, TIV or reinsurance treaty is inferred from this schema.

## Real generator-share cohort audit and Excel percentage-unit correction

The [official original-source CI run #41892331971](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41892331971) completed **successfully** after reading the same pinned annual 2025 EIA ZIP and `4___Owner_Y2025.xlsx`. It ran 7 original-schema synthetic tests and 10 source-ownership synthetic tests before the real source aggregation.

**Critical scientific correction:** The first live generator share audit incorrectly treated the underlying XLSX raw fractional cell contents as percentage points. The six in-cohort `Percent Owned` cells all used **original XLSX cell style 12 with built-in number format ID 10 = 0.00%**, and their numeric values were between 0 and 1. XLSX percent style means a raw `0.40` denotes **40 percentage points**, not 0.4%. The original-source runner was modified to multiply by 100 **only for native percent-formatted cells**. On an exact-original source, a cell missing/using an unreviewed format is quarantined rather than silently assigned a unit. The earlier 6/6 apparent under-100 totals were an **artifact of our pre-correction parsing**, not an EIA ownership gap.

### Verified source observation, 2026-11-04

| Metric | Original-owner proof |
| --- | ---: |
| Original source ZIP SHA-256 | `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba` |
| Inner Owner workbook SHA-256 | `f0600c57b24f065017983e50a8a6561c8aa563382bb8862ad216448ca32d9383` |
| Total Owner schedule rows with plant and generator fields, all U.S. | **5,680** |
| EIA 2025 Delaware cohort: EPA-confirmed plant codes | **15** |
| Delaware cohort plants with explicitly reported Schedule 4 ownership rows | **3** |
| Reported Schedule 4 generator rows / distinct generators, cohort | **6 / 6** |
| Generators with summed reported owner percentages equal to 100 ± 0.05 percentage points | **6 / 6** |
| Generators with sub-100 / supra-100 shares after correct Excel formatting | **0 / 0** |
| Source rows with unparseable percentages or missing owner names | **0 / 0** |
| Source duplicate owner-name entries for the same generator | **0** |

The six named source owner rows are **not** reproduced here. Their source-identifying values were only held in memory while computing aggregates. The total 5,680 source rows is the all-U.S. Owner *special reporting schedule*, **not** the total U.S. generator population, and 3/15 plants should not be read as 20% ownership coverage. Generators absent from this exception schedule may be wholly owned by their reported operator, but **do not impute a legal owner** until generator roster/plant operator and exact report-year semantics are independently confirmed.

The five upstream review boundaries remain unchanged: actual 2026 GEM unit/location match and rights (including TZ CC BY-NC), EIA Schedule 4 owner-code versus operator-code identity, GLEIF ownership/accounting consolidation, company-specific insured exposure/replacement TIV and business interruption, and independent treaty/loss model configuration.

The initial source anomaly is now resolved by **original Excel-format evidence** rather than changing the share data or loosening the test. Reproducibility remains conditioned on exact GitHub head CI after final documentation and status cleanup.
