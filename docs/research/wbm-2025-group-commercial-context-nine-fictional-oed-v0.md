<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2025 group commercial metrics vs nine fictional Oasis exposure rows

**Research status 2026-11-05.** This is a **synthetic OED 5.0 interoperability exercise**, NOT a WBM insured portfolio, R+V insurance site roster, insurer premium, source-derived TIV or CAT result.

## Original corporate primary source, not a policy schedule

The WBM press statement [WBM setzt strategischen Wachstumskurs erfolgreich fort (3 June 2026)](https://www.wbm.de/presse/pressemitteilung/detail/wbm-setzt-strategischen-wachstumskurs-erfolgreich-fort/) presents these 2025 group/portfolio-level metrics:

| WBM-sourced corporate metric | 2025 group context | Can be used to value any of the September nine insured commercial objects? |
| --- | --- | --- |
| Managed commercial floor area | approximately **314,000 m²** | **No**. Aggregates broad WBM commercial portfolio |
| Average commercial rent | **EUR 15.62 per m²** (publication's average rent; do not infer policy rent) | **No**. Neither rent roll of nine sites nor BI limit |
| Commercial vacancy | **1.4%** | **No**. Not per-site insured occupancy or policy deductible |
| Commercial tenant turnover | **4.6%** | **No**. Not hazard frequency nor policy churn |
| Entire group property portfolio market value | approximately **EUR 5.9 billion** | **No**. Multi-use market value is not replacement-cost TIV |
| Group rental flats | approximately **35,000** | **No**. Do not infer residential insured policy sites |

WBM locates much of its commercial activity in the S-Bahn-ring area, Mitte and Friedrichshain-Kreuzberg, and also in Spandau. This broad geographic description is **not** nine source-geocoded commercial risk sites, and cannot be substituted for WBM policyholder building addresses.

**Important source-level separation:** September original [TED 668506-2026](https://ted.europa.eu/en/notice/668506-2026) reports a single procurement lot and *nine pure commercial objects*, and proves three official awarded company-contract edges with **50/40/10 percentage text in contract identifiers** (HDI, Helvetia, R+V). The prior April notice 286307-2026 uses a **different indexed BT-04 procedure UUID**, and its tender minimum percentages are not proved to govern September. Neither published notice, corporate press statement nor the [expired public RIB tender 205349 access](berlin-wbm-2026-rib-205349-document-access-and-request.md) supplies a policy schedule, all nine addresses or actual insured reinstatement value. See separately [BT-04 research](berlin-wbm-2026-ted-bt04-procedure-lineage.md).

The above original corporate numbers are typed as **`source_level=entire_WBM_group`** in [research observation](../../research/observations/wbm_2025_group_commercial_metrics_separate_from_nine_award_v0.toml). They are source-context metadata only. Do not multiply or divide 314,000 m², EUR 5.9 billion, 15.62 EUR/m² or 1.4% by nine, or use them to set Oasis per-risk TIV, BI or expected loss.

## Nine completely invented OED 5.0 locations — technical wiring only

[Standalone generator](../../research_runners/wbm_like_nine_fictional_oed_v0.py) uses the *number nine* from September TED and invents **everything else**. All nine fabricated coordinates lie on a regular 3 × 3 grid roughly covering Berlin (latitude 52.42/52.49/52.56 and longitude 13.25/13.35/13.45). They are test-grid points, **not** parcel coordinates or actually insured properties. Invented site identifiers `FICTITIOUS-SITE-01` to `FICTITIOUS-SITE-09` have EUR 4m, 6m, ... 20m (fictional total EUR 108m) **entirely synthetic** building-TIV field values; the amounts have no empirical valuation or WBM business basis.

We reuse the existing repository's [OED 5.0 CSV field names](../../research_runners/export_synthetic_oed_v0.py), fictitious `PortNumber` / `AccNumber` / `PolNumber`, country `DE`, EUR currency and deliberately hypothetical `WW2;OO1` covered-peril group. No contents/other/business-interruption values are invented beyond explicit testing zeros, and **no R+V, HDI, Helvetia or WBM name** is emitted as an insured account or policy. The fictional CSV does not represent the actual nine award objects or the 2027 WBM policy. The generator creates `location.csv`, `account.csv` and a `fictional-provenance.json` record in a **new, disposable directory**; it refuses to overwrite existing output. No actual insurer data or database rows are read or written.

The [16 no-network tests](../../tests/test_wbm_like_nine_fictional_oed_v0.py) cover the exact artificial grid, unique locations, OED 5.0 required headers, account/location linkage, deterministic CSV bytes, exact fictional TIV recipe and fail-closed blocking of real-insurer/company attribution, modified coordinates/amounts, altered policy, missing fictional metadata, nine-to-ten risk overclaim and unsafe overwrites. [Seven corporate-statistic source tests](../../tests/test_wbm_2025_group_commercial_context_v0.py) prove that the EUR 5.9bn corporate market value and 314,000 m² broad holdings **never feed** the fictional nine-site numbers.

### Reproduction

From the repository root:

```bash
python -m unittest discover -s tests -p 'test_wbm_like_nine_fictional_oed_v0.py' -v
python -m unittest discover -s tests -p 'test_wbm_2025_group_commercial_context_v0.py' -v
python -m research_runners.wbm_like_nine_fictional_oed_v0 /tmp/berlin-fictional-nine-oed-v0
```

The output directory must not exist. Generated CSVs are disposable; do **not** commit them to the project data warehouse or Neon insurer database.

The [official ODS Tools version-pinned validator](../../research_runners/validate_wbm_like_nine_fictional_ods_tools_v0.py) runs `ods-tools==5.0.8` and `OedExposure(location=..., account=..., check_oed=True)` on generated data in a temporary directory. It also challenges the official library with a missing mandatory `CountryCode` and requires rejection. Wired into [Synthetic Oasis OED 5.0 compatibility CI](../../.github/workflows/synthetic-oed-compat.yml). Official OED schema acceptance demonstrates **CSV format compatibility only**, not any ability to run a German-peril hazard model, issue Oasis model area-peril keys, calculate ground-up losses, gross/insured loss, insurer net loss, treaties, OEP, AEP or IP.

**Next substantive modelling gate:** choose a documented hazard/vulnerability model with Germany/Berlin area-peril mapping, geocode uncertainty and valid exposure classes; run independent, tagged *fictional* loss simulations and benchmark against known unit test oracles. Thereafter collect permitted, individually source-traceable insurance contract/site and replacement-cost evidence before any *real* WBM/R+V portfolio admission or gross/net claim. Avoid applying the September BT-150 company percent labels as actual insurance or RI treaty terms.
