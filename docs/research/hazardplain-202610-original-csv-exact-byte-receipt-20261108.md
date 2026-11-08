<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hazard Plain 2026-10: independently verified original CSV byte receipts

**Receipt observed:** 2026-11-08 22:16:51 UTC

**Verification:** [GitHub Actions original-file run 42529431183](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42529431183), job `128880119635`.

**Input:** exactly three public, release-pinned original CSV files under
`https://files.hazardplain.org/r/2026-10/bulk/national/`.

**Original publisher bulk manifest:** [manifest.json](https://files.hazardplain.org/r/2026-10/bulk/manifest.json), independently hashed at `e04a707ab5b96a71e81f6ac29a584f3cb43acb5ec88c5e9669e092b5076434b4`, 59,508 bytes. Release 2026-10; source data as of 2026-09-30, build timestamp 2026-10-17T19:57:41+00:00.

## Exact source-byte identity checks actually completed

The read-only research runner downloaded the original files from the allowlisted HTTPS host into bounded memory, recomputed each entire file's SHA-256, checked exact byte length and compared both against the pinned original manifest. It then parsed every CSV record and compared the original header columns and source row count to the manifest table declarations. **These are independently executed original-byte checks**, not merely repeated provider claims.

| Original file | Verified bytes | Verified data rows (excluding header) | Independently recomputed SHA-256 |
| --- | ---: | ---: | --- |
| `national/nri_county_hazard.csv` | 23,764,594 | 58,176 | `262d0dbc42dfc123408f28d3723bde49c6249c8f734adb2fafb720bb4f770eae` |
| `national/eal_outliers.csv` | 10,265,835 | 45,853 | `47c50202b0c6b57fd0c75624e51d3b7b87bb11ae2951ac7b4f5e299882525815` |
| `national/b2c_county.csv` | 352,674 | 3,232 | `4d891f4fce8b0f5ae1c4d6119be74b217e302e5cd8f17e3a6b8e43c2c0c7ffc5` |

**Total:** 34,383,103 bytes; 107,261 independently parsed data records across the three distinct tables (not unique counties, exposures or claims). The first table is county × one of 18 hazards; the second is a county/peril diagnostic subset; the third is county-level NFIP aggregate categories. Do not add their row counts to estimate a national building population.

**No external CSV bytes were committed or uploaded as CI artifacts.** Individual data row values are never emitted in logs. The live receipt emits only source-file identities, byte hashes, byte sizes, row counts, real header names and declared upstream lineage. The checker itself lives in `research_runners/hazardplain_202610_original_csv_receipt_v0.py`; its synthetic-only regression tests live in `tests/test_hazardplain_202610_original_csv_receipt_v0.py`. Its source-network step remains distinct from ordinary repository CI.

## Rights and scientific readiness remain separate

The [publisher Downloads page](https://hazardplain.org/downloads/) and [Methods page](https://hazardplain.org/methods/) say the derived text and tables are **CC BY 4.0 with attribution to Hazard Plain and release 2026-10**, and upstream OpenFEMA terms still apply. That website statement does **not** itself complete our dataset-specific commercial/use-of-upstream-data legal review.

Even after the original bytes have been verified, the rows are **not** an independent empirical loss validation sample. Modeled FEMA NRI expected annual losses and exposures share upstream data/model dependencies with other NRI-derived calibrations; NOAA Storm Events summaries reuse NOAA observations; NFIP repetitive-loss aggregates concern a selected insured flood population. Their use may be appropriate for diagnostics and hypothesis generation, but source lineage overlap, missingness, claims selection and FIPS/geography vintages must be examined before any model calibration.

**Status:** exact original source-byte identity verified; source rights review `not_reviewed`; scientific suitability `not_reviewed`; model admission `not_admitted`. No source-derived ELT, YLT, AEP/OEP, asset-level vulnerability, insurance portfolio or insurer claim estimate has been computed.

## Next bounded scientific checks

Review per-table **county FIPS vocabulary and geographic vintage**, missing and invalid numeric EAL/exposure values, 18-hazard mapping, extreme modeled EAL diagnostic flags, NFIP repeated-loss class overlap and source-specific suppression rules. Produce only aggregate descriptive receipts until legal and scientific roles are reviewed. No independent holdout claims unless its raw observations and dependency graph have been established separately.
