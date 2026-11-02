<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EIOPA original country-level annual premiums/claims research pilot (v0)

## Product and exact provider source

- Official EIOPA statistics page: https://www.eiopa.europa.eu/tools-and-data/insurance-statistics_en
- Publisher's actual CSV export, **Solo / Annual / Premiums, claims and expenses**:
  https://www.eiopa.europa.eu/assets/insurance-statistics/SA_Premiums_Claims_Expenses.csv
- Product: Solvency II quantitative reporting S.05.01 statistics, aggregated by reporting country, calendar year, business type and source row code.
- Current publisher describes history **2016–2025** (August 2026 annual release). A future revision may update historical years or the actual extraction date.
- This is **not company-level data**; the name of a reporting country is not the physical insured-risk location.
- Do not mix Solo with Group or Quarterly observations, treat cross-border premium location as insured-risk geography, or sum gross, net and ceded fields together.

### Observed real CSV column names

The publisher's live CSV begins with these eight headings:

1. `Reporting country`
2. `Reference period`
3. `Item`
4. `Business type`
5. `Item code`
6. `Value`
7. `Date of extraction (yyyymmdd)`
8. `Number of submissions (per reporting country, reference date and undertaking type)`

The `Value` column can contain **blank observations** and real `0` values, both of which must survive unmodified. Negative observations are possible in accountancy data. `Number of submissions` is not a policy or exposed-building count. Unit/currency/multiplier must **not** be assumed from raw decimal values: `value_unit_verified=false` until the exact EIOPA accompanying note confirms them.

The official site warns that historical data can be revised following resubmissions and that some releases are provisional. The source is a live CSV URL: use original SHA-256 **per retrieval**, period/extraction dates and versioned SQLite rows, not a fabricated fixed CSV checksum.

## Executable validation and isolated staging

```sh
python -m unittest tests.test_eiopa_solo_annual_pce_original_csv_pilot -v
python scripts/export_cat_source_registry_sqlite.py --out /tmp/opencat-research.sqlite
python scripts/eiopa_solo_annual_pce_original_csv_pilot.py --fetch \
  --out /tmp/opencat-research.sqlite --result /tmp/eiopa-research-profile.json
```

Alternatively pass `--csv /path/to/original-publisher.csv` for a source-byte-compatible offline preflight.

The workflow `.github/workflows/eiopa-solo-annual-original-csv.yml` performs original provider retrieval to GitHub runner temporary storage, strict CSV source preflight, dataset coverage checks and CAT-only SQLite staging. Neither the CSV nor the temporary database is committed or uploaded. A previous read-only content inspection confirmed the header and representative observations but a partial response was **not** considered proof of complete provider row counts.

The parser checks: exact original header and UTF-8; CSV column count, row cap and duplicate key; source year, item code and extraction date; valid bounded submission counts; finite decimal text, zero vs missing and negative values. All facts remain `model_admitted=0`, `unit_verified=0`, `rights_reviewed=0`. SQLite is stamped as a CAT research database and will reject an existing unrelated database.

### Unresolved admission and scientific gates

1. Confirm official EIOPA source reuse conditions, including persistent redistributable/corporate use; being on a public portal does not alone establish permission to use all rows in a commercial pipeline.
2. Independently inspect the accompanying Solo Annual statistical and QRT notes for amounts, unit currency and multiplier, line-of-business split, statistical aggregation and revisions; never silently convert to EUR or exposure TIV.
3. Distinguish observed annual *market-level* premiums, reinsurers' share and incurred claims from CAT event losses, individual insurer net retained portfolios or contract conditions.
4. Only after review, build a separately authorized import into the **existing** insurance-only Neon `insurance-risk-core`. Do not touch the Pokémon database `tcgp2p-core` or override any existing source ingestion restrictions.

This is a functional source-readiness and research staging step, **not** a new source admission or CAT underwriting model.
