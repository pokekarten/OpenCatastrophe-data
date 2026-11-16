<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara/Sabine 2020: original French northern-station hourly evidence envelope

**Purpose (15 November 2026).** Start an event-specific physical observation QA gate for the four previously byte-hash-verified Météo-France regional original archives. Source original files have frozen resource UUID, URL, byte length, full SHA-256 and bounded parser in [the four original gust reports](meteofrance-four-north-original-gust-proof-20261115.md). No new provider identity is inferred.

## Predeclared window and physical question

We predeclare **2020-02-09 00:00 UTC inclusive to 2020-02-12 00:00 UTC exclusive** (72 fixed UTC hour labels), deliberately wider than the strongest winds in northern France. Météo-France historically describes storm Ciara on 9–11 February 2020: [Météo-France storm chronology](https://meteofrance.com/actualites/norberto-onze-tempetes-sur-la-france-depuis-debut-fevrier). This is an *hourly observation envelope*, not the event's objectively reconstructed hazard footprint or a claim that each hour is storm-induced.

One standalone runner `research_runners/meteofrance_ciara2020_four_original_window_v0.py` reads **one** exact original gzip in ephemeral CI memory at a time, after revalidating its official catalogue UUID/URL/declared bytes, SHA-256 against the previously verified byte receipt, original Météo-France dictionary and whole archive using the strict upstream scanner. A second bounded streaming pass extracts only the exact 72h window. It reports department-level aggregates for:
- event-window station-hour label count, number of station IDs and how many stations have all **72** original hour labels;
- accepted quality `QFXI3S=0/1` gusts, `QFXI3S=9` filtered, missing flags, transfer-derived vs not-transfer-derived counts;
- original-source verified global event-window maximum valid 3-second gust in **m/s** and binned per-station maxima, without disclosing station IDs, raw observations, coordinates or whole hourly series;
- missingness across full 72h observation support versus quality-approved gust support.

**Strong limitations:** Station/site historical relocation, instrument height/exposure, transfer reconstruction and source correction history are not attested. `STATUS_FXI3S=0` means not computed by the transfer function, **not** necessarily directly instrument-measured. Matching hour labels do **not** establish exact interval averaging equivalence to ERA5 10fg, CLIMK winds or the separate DWD FX_911 Ciara test. This is not a held-out bias, model-skill or storm loss study. Four departments are four sources within **one provider family**, not four physically independent event catalogue models. No source admission, annual event frequency, insurer losses, OEP, AEP or AAL is authorized.

**Execution:** `python -m unittest tests.test_meteofrance_ciara2020_four_original_window_v0 -v`. The initial path-scoped PR workflow executed four independent source jobs successfully on 2026-11-15. The original network workflow is now **manual-only**; source byte SHA-256 identifiers and aggregate evidence are recorded below and remain fail-closed on changes. Full repository CI is independently required. No original source files or station rows are checked into Git.

## Executed source-original Ciara 72h receipts (15 November 2026)

The four actual-provider original source jobs in [GitHub Actions run 43741227952](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43741227952) completed **successfully**, including the offline synthetic duplicate/invalid-calendar/integrity tests and full original SHA/CSV/QC validation. The fixed 72h event window is 2020-02-09 00:00 UTC inclusive to 2020-02-12 00:00 UTC exclusive, not a storm-attribution classifier.

| Department | Total source station-hour labels | Station IDs with any label | Station IDs with 72 labels | Station IDs with 72 accepted FXI3S | Accepted FXI3S rows | Derived via transfer | Source peak m/s (accepted) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 02 | 648 | 9 | 9 | 0 | 71 | 0 | 27.9 |
| 62 | 936 | 13 | 13 | 3 | 216 | 0 | 32.5 |
| 76 | 936 | 13 | 13 | 4 | 288 | 1 | 32.4 |
| 80 | 864 | 12 | 12 | 2 | 144 | 0 | 30.3 |
| **Total / maximum** | **3384** | **47** | **47** | **9** | **719** | **1** | **32.5** |

Source-original `QFXI3S` flags among the 3,384 station-hour rows: `1` accepted = 719, `9` source-filtered = 1,439, and missing = 1,226. This is why 47 complete **hourly station-label** series do not provide 47 complete **quality-approved FXI3S** series. There is one transfer-derived approved 3-second gust in this window. `STATUS_FXI3S=0` for the remaining 718 *does not prove instrumental direct measurement.*

Original asset provenance is identical to the pinned all-year original sources:

- Dept `02`: original gzip SHA-256 `4c093caad74f854612485504d6d21ba67c7879e4d005e6b51ca6d1acb2b017e3`; successful Ciara event QA job `132894624323`.
- Dept `62`: original gzip SHA-256 `12a33b7c67f703aad2bcc95c06d91b81cb8e2cba95738da7e9bbb7971a81db7f`; successful Ciara event QA job `132894624581`.
- Dept `76`: original gzip SHA-256 `406dbf752f042254bfade674f606c2035eeb2560d06314324c9bd4694936780d`; successful Ciara event QA job `132894624498`.
- Dept `80`: original gzip SHA-256 `1d46879bd4c3ba1180b881cfb28eacccc4e8a5405e783bdc09ab5dae5418124f`; successful Ciara event QA job `132894624511`.

This receipt **does not publish a station-hour dataset**. The single maximum is a descriptive, quality-flag-gated peak across the department's included sources. It is **not** matched to an ERA5/CLIMK grid, not guaranteed to originate from an independently documented 10m sensor, not guaranteed to be a provider's published Ciara peak under the same physical metric, and does not establish event frequency, observation-model bias or insured-loss/vulnerability calibration. The next causal step is station sheet instrument/siting attestation and exact original wind interval comparison, only then model-grid pairing with holdout protocol.
