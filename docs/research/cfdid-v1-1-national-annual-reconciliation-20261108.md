<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CFDID v1.1 original annual-coverage reconciliation — 2026-11-08

**Goal:** reproduce all five published 1994–2023 national coverage percentages using the exact **original publisher files** and the authors' **L1-only** arithmetic. This is a *partly internal governmental reporting coverage check*, **not** independent insured-loss model calibration.

## Frozen upstream bytes and license boundary

| Original release asset | Publisher metadata MD5 independently matched | Independently computed SHA-256 | Byte count |
| --- | --- | --- | ---: |
| CFDID v1.1 *China Flood Disaster Impact Database.csv* | \`d8e828d7484fb5876000d2efab1d44a0\` | \`b2cc978a317710b5379fdc42cff787800f1bbaee505c5ce7c70370f31669f2bf\` | 337,549 |
| CFDID v1.1 *Official national annual totals_1994-2023.xlsx* | \`c2b7ae971efa5c4f886d824424141ad4\` | \`3791b32cbb4d772f7b984ba7ff03f9f3c2a1d37af3ea61e7fa1bbc07f12f7db6\` | 11,294 |

Publisher: https://zenodo.org/records/22918521 (version 1.1); original metadata: https://zenodo.org/api/records/22918521. Paper: https://doi.org/10.5194/essd-18-8129-2026 (published 2026-11-05). File bytes were read into an isolated short-lived execution environment and not copied into the Git repository, persistent databases or model installations. The deposited *dataset* metadata claims CC BY 4.0; upstream Chinese yearbooks/government reports/EM-DAT have separate rights. **Original dataset use remains research-only / non-admitted** until license and scientific review.

The original annual workbook contains a single tab with headers and 30 annual rows (1994–2023); five benchmarks have explicit units. The direct-economic-loss benchmark column is **million CNY, 2023 constant prices**, distinct from the *nominal* loss column also present in the event file.

## Independently reproduced paper results

The original source comparison, executed with [\`research_runners/cfdid_annual_coverage_preflight_v0.py\`](../../research_runners/cfdid_annual_coverage_preflight_v0.py), exactly reproduces the published **rounded** percentages. Each numerator is the sum over L1 events only, grouped by start year; each denominator is the sum of the 30 official annual totals. All reported sums are treated as observed (blank remains *missing*, not zero).

| Published impact indicator | Original L1 numerator | Original official denominator | Reproduced percentage | Publisher percentage | Years with L1 total > official annual total |
| --- | ---: | ---: | ---: | ---: | --- |
| Deaths and missing persons, persons | 35,770 | 52,229 | **68.49%** | 68.49% | 2010 |
| Affected population, thousand persons | 2,998,832.850 | 4,150,946.000 | **72.24%** | 72.24% | 1997, 2004, 2007 |
| Affected cropland, thousand ha | 202,458.681 | 333,546.120 | **60.70%** | 60.70% | none |
| Collapsed dwellings, thousand rooms | 25,696.262 | 39,126.400 | **65.67%** | 65.67% | 1997 |
| Direct economic losses, million CNY in 2023 prices | 5,390,048.758 | 7,200,572.595334 | **74.86%** | 74.86% | none |

Numbers above are displayed at a practical precision only; the actual source workbook uses full Excel stored numeric values (often binary-float decimal expansions), and the Python runner reads them as \`Decimal\` strings without premature rounding. The percent is a **30-year ratio of sums**, not the simple arithmetic average of 30 individual annual coverage percentages. No annual percentage is clipped at 100%; over-100 anomaly years are tracked for source consistency research instead of assumed fraudulent records.

Original L1 event count: **1,391**. The separate hierarchy gate confirms **300 L2 and 25 L3** records excluded from these ratios. Original direct-loss valid L1 observations: **1,197** (remaining 194 are *not reported*, not verified zero). The original event-file source has **192 event records without specified start day**, which matters for day-resolution weather event linkage but not for annual grouping.

## Reproducible local execution

\`\`\`bash
python -m unittest discover -v -s tests -p 'test_cfdid_*preflight_v0.py'

python -m research_runners.cfdid_annual_coverage_preflight_v0 \
  --event-csv /private/local/CFDID_v1_1.csv \
  --official-xlsx /private/local/Official_national_totals_1994_2023.xlsx \
  --event-sha256 b2cc978a317710b5379fdc42cff787800f1bbaee505c5ce7c70370f31669f2bf \
  --official-sha256 3791b32cbb4d772f7b984ba7ff03f9f3c2a1d37af3ea61e7fa1bbc07f12f7db6
\`\`\`

The example paths represent caller-owned files outside Git. This source-specific gate checks source schema, original SHA-256 and publisher MD5, numeric units, yearly support, 30-year coverage, L1 nesting exclusions, and **all five** rounded paper values. The XLSX reader fails closed on formulas/stale caches, unknown populated columns, missing annual values, invalid or duplicate worksheet structure, nonpositive annual denominators and non-finite numeric amounts. No \`openpyxl\` or \`pandas\` production dependency.

**Execution 2026-11-08:** both source originals and the PR branch Python code/tests were retrieved afresh into one isolated temporary directory; **23/23** focused synthetic regression tests passed; full real-source annual-coverage CLI exited 0 and returned \`all_published_coverage_percentages_reproduced=true\`. This is a scoped live execution, **not** a full GitHub Actions run.

## Scientific independence and model-use gates

1. **Shared reporting source:** Both CFDID events and the published official annual benchmark totals originate from governmental reporting. Paper section 2.5 itself warns that this is **partly internal**, and not fully independent empirical loss validation.
2. **Partial coverage:** The reported 74.86% national direct-loss coverage over 1994–2023 does not authorize scaling all CFDID events by \`1 / 0.7486\`, inferring complete stochastic frequency, or creating unreported individual properties.
3. **Financial type:** These are direct national *societal* economic impacts, not observed insurer gross/net claims, insurance penetration, TIV, paid losses, frequency-severity independent event sets, Oasis OED, or EP curves.
4. **Mixed peril parentage:** The original database includes typhoon-associated floods and other subperils; matching to tropical cyclone catalogs requires unified hazard-parent identities and peril attribution to avoid counting cyclone/flood components twice.
5. **Granularity:** Provincial/date-level reports cannot establish street-level ground-truth building damage. Unknown event days and unspecified locations must stay missing.
6. **Further validation:** Only an independent original dataset (e.g., separately sourced satellite-detected flood extent, hydrological gauge observations, truly independent property surveys) can contribute external event validation. Cross-source duplicated reports/EM-DAT crosswalks are not independent observations.

**No source admission, policy relaxation, CI bypass, Neon write, insurance model calibration, or original-data redistribution was performed.**
