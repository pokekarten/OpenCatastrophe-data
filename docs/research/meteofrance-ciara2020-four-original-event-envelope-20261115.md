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

**Execution:** `python -m unittest tests.test_meteofrance_ciara2020_four_original_window_v0 -v`. The first research canary is a path-scoped PR workflow with 4 independent source jobs. After successful original-event receipts, make the network workflow manual-only, record the actual results here and verify complete repository CI. No original source files or station rows are checked into Git.
