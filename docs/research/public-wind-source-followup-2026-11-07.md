<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Public wind-source follow-up: acquired bytes, Oasis challenge and access boundary

Reviewed 2026-11-07. This is a bounded update to the existing public wind candidates, not a source admission. It uses a fictional exposure only and contains no personal, customer, claim, policyholder or insurer portfolio data. Provider bytes and local machine paths remain outside Git.

## CLIMK-WINDS v2

The public Zenodo record `https://zenodo.org/records/15305753` declares CC BY 4.0. This run acquired:

| NetCDF | Bytes | SHA-256 | Verification/use |
|---|---:|---|---|
| ERA5 | 6,792,278 | `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102` | Previously verified footprint source; reused as the same-event control. |
| CCLM_ERA5_EUR-11 | 13,898,709 | `4bd28d8bd4f2fd820ea7f844e243b1234a2e4c8fa81ea420ef558917729ba94` | Newly acquired, opened, coordinate arrays and gust units inspected; Kyrill identified by source name/date. |
| CCLM_ERA5_CEU-3 | 80,330,992 | `2a8cd17e582280fece757b233d08cb580787172322c7bfd98f9d224c757c7077` | Acquired; provider MD5 verified; 423x415 Germany-focused rotated grid, geographic coordinates/gust units inspected; Kyrill mapped for Oasis. |
| COSMO-REA6 | 83,807,744 | `e0cb9fc238fd326a65b2ae31d093499d39b4cd8d707ce1b99798ca5c6cb09843` | Acquired in temporary memory-backed storage; provider MD5 `1a2f1f454d5672c8d8f499f237dff744` verified; 824x848 grid, Kyrill date, gust units and missingness checked. Bytes remain outside Git. |

The four CLIMK products contain 50 source-selected winter storms each. Event rankings/selections remain source-specific. They do not supply a complete common event catalogue or complete unmasked hazard series.

## XWS Kyrill

The public repository made `Kyrill_rawFoot.nc` (SHA-256 `1d9d996210bd08668624f7a2e625501c851f7cd58f0cff15bd73bb5c3d39d9a0`) and `Kyrill_rawFootUncon.nc` (SHA-256 `bf18bd37b0fa441bd02a00860c0fa74474c77691efe316efd46bde0ca8b483f5`) available (122,304 bytes each). Provider method captions establish that `rawFoot` is raw and `rawFootUncon` is decontaminated/uncontaminated. The latter name must not be read as “unconstrained”. Both files were inspected for gust units, rotated-pole grid, missing markers and time; both encode the storm at 2007-01-18 15:00 UTC. At jointly valid points, the decontaminated field does not exceed raw, and is lower at 7,281 of 14,472 valid cells (maximum reduction 22.25 m/s). This verifies the filename interpretation and mask operation for the downloaded pair, not the universal accuracy of either field.

The XWS methodology describes maximum 3-second gust footprints over a 72-hour window, with a 1,000-km storm-track radius used to remove nearby events for the decontaminated field. This is not directly equivalent to the CLIMK daily maximum/98th-percentile-selected footprint.

## Native Oasis model challenge

One reviewed native Oasis 2.5.9 execution evaluated six representations of the **same Kyrill event** over the same 7,998 fictional German building-value interests. The fixed scenario uses a 1,000 EUR individual deductible, full-value limits, transferred CLIMADA PAA/MDD reference and source-specific nearest grid cells. All selected source gusts were finite and in the configured supported range. Nearest-grid distances were 8.535 km for CCLM EUR-11, 2.150 km for CCLM CEU-3, 4.289 km for COSMO-REA6 and 17.012 km for XWS; ERA5 retained the original mapping. One CEU-3 mapped point has source gust zero and remains a selected-footprint omission, not evidence of physical calm.

| Source | Expected footprint GUL EUR | Expected insured footprint contribution EUR |
|---|---:|---:|
| CLIMK ERA5 | 323,529.86 | 104,373.43 |
| CLIMK CCLM EUR-11 | 64,597.72 | 21,844.27 |
| CLIMK CCLM CEU-3 | 129,851.51 | 50,818.82 |
| CLIMK COSMO-REA6 | 81,900.45 | 21,099.80 |
| XWS raw | 5,499.96 | 5.81 |
| XWS decontaminated | 5,492.89 | 5.81 |

The engine's per-policy conditional losses were weighted with the same assumed PAA to obtain these contributions. Twelve aggregate gross/insured comparisons and 95,976 conditional policy comparisons passed at pre-existing tolerances; the ERA5 result matched its earlier control. Three geographic-mapping tests passed. All six are alternate representations of one historical storm, not independent frequency observations.

## Matched CLIMK roster follow-up

A separate raw-file roster audit found 28 storm names present in all four 50-storm CLIMK files, but only 19 with an exact storm-name **and** date match. Nine shared raw-file names have date disagreements and were excluded rather than joined by nearest date. Four separate native Oasis runs then evaluated those 19 exact matches on the same 7,998-interest fictional exposure. All runs had full key coverage; 152 aggregate and 1,215,696 conditional per-interest checks passed with zero failures. These remain selected conditional footprints under one transferred vulnerability, not four aligned annual catalogues. Source/date selection, masks, grids and gust definitions remain confounded.

The raw roster count differs from the paper's Table 2: Flynn et al. (2025, [doi:10.5194/essd-17-4431-2025](https://doi.org/10.5194/essd-17-4431-2025)) list 29 common storms and six source-date disagreements. The paper defines event dates as the midpoint of the 3-day window with largest LI3D magnitude and explains that events may be split or combined between datasets. Its Table 2 reports Gunter as 2015-01-10 in all four CLIMK products, but the acquired CEU-3 NetCDF at the [Zenodo v2 record](https://zenodo.org/records/15305753) contains `GUNTER` dated 2005-01-10. This source-content conflict is unresolved; no date was corrected or fuzzy-matched. The exact-match Oasis results are unaffected because GUNTER is excluded. The paper's supplement references a `Top50Storms_All_Summary.csv`; a direct public download location was not found in this check. Detailed raw roster, aggregate evidence and descriptive ranges are in the [OpenCatastrophe v14 report](https://github.com/pokekarten/OpenCatastrophe/blob/research/synthetic-oasis-portfolio-20261104/docs/wind_source_roster_v14.md) and its linked evidence JSON.

These outputs combine differences in model/source, grid, time window, wind definition, event mask and transferred vulnerability. They do not isolate resolution effects, choose a scientifically best source or estimate actual Kyrill insured damage. In particular, the low XWS payout is not evidence of low actual damage. The initial exploratory internal XWS labels were reversed; the reviewed run corrected the labels and was repeated. The earlier exploratory run is not counted as a separate source scenario.

## C3S access attempt

The [C3S windstorm reanalysis product](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis) exposes process metadata for full-domain/original and downscaled products with 72-hour maxima. Public process/catalogue/form/constraints/layout metadata were retrieved. An anonymous execution POST returned HTTP 401 requiring authentication. No wind fields were obtained; request acceptance and event identity were not demonstrated. The exploratory February 2014 request selected 14 February, whereas the current CLIMK event roster lists TINI-ULLA on 13 February. That mismatch must be reconciled before comparing events.

## Data boundary and reproducibility

No external arrays, source bytes, synthetic location rows, private data, credentials or local execution paths have been committed. The repository stores only this source follow-up and public provider references; hashes and exact numerical receipts are documented in the linked upstream OpenCatastrophe code/report. Source/candidate status remains non-admitted. CLIMK/XWS CC BY declarations and OpenCatastrophe's distribution/admission reviews remain separate decisions. Public availability and a successful engine run do not constitute scientific admission.

OpenCatastrophe-data's [CLIMK source landscape](../../landscape/sources-event-loss-benchmarks-2026.json) remains the canonical non-admission record. The [C3S manifest](../../manifests/copernicus.c3s.european-windstorm-reanalysis.v1.0.json) remains metadata-only; its addendum above records the observed access response. The next useful acquisition is a rights-cleared C3S full-domain event field after authenticated access and exact event/time verification, followed by comparison against the independent station observations. That would reduce a source-mask gap but would not itself calibrate vulnerability or annual frequency.
