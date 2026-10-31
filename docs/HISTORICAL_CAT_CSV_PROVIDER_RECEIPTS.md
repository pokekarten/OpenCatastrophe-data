<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Historical CAT source-byte receipts — 2026-10-31

Source: exact versioned Zenodo publisher CSV bytes, downloaded in byte ranges and reassembled in full. Metadata and hashes only; no provider records committed, and no scientific, legal, insurance-loss or asset-exposure model admission.

## Exact sources

HANZE version 3.0.2 beta (2026-10-30), 699910 CSV bytes, SHA-256 44dc1861cf620d9e64085dc66159488237ca45df760d64042d921cd8b807ba66. 2780 flood events, with 1173 observed economic-loss fields and 1607 missing fields. Unique event IDs, 40 unique country codes with event rows, event years 1871-2025, 1290 distinct non-empty affected-region code tokens. Provider documents overall scope 42 countries and 1870-2025; do not conflate publisher area and the observed rows. Aggregated economic loss is neither insured loss nor flooded polygon.

European residential exposure version 2025 (2025-12-05), 177679 CSV bytes, SHA-256 ce8cc1a1f83b9ee248cd6380597bc21be5a9e75a4e26d3fe1d102ff0ca25d0fa. 612 rows, 18 indicators and 34 codes (33 countries plus EU aggregate); 25 years 2000-2024 with 15300 numeric, nonnegative, present cells. The EU aggregate must not be added to the country totals. Mean per-area replacement costs are not insured TIVs or individual property appraisals.

## Reproduction

Internet-enabled machine, repository root:

    python scripts/verify_historical_cat_csv_provider_receipts.py --fetch --output /tmp/historical-cat-receipt-check.json

Offline, after acquiring exact file versions:

    python scripts/verify_historical_cat_csv_provider_receipts.py --hanze-csv /path/to/HANZE_events_v3_0_2b.csv --residential-csv /path/to/Residential_exposure_v2025.csv

Provider SHA-256, publisher MD5, byte size, exact CSV headers and all profile counts must match. No source data bytes are written in fetch mode, only an optional metadata report. Synthetic-only unit tests run without internet:

    python -m unittest tests.test_verify_historical_cat_csv_provider_receipts -v

The initial receipt was profiled from complete publisher byte-range retrievals and has now been independently reproduced by the Python --fetch verifier on public GitHub Actions (runs 41226668464 and 41226804269, both successful). This confirms exact source bytes and preflight profiles, NOT scientific model suitability or any downstream rights admission. Review actual provider licence and attribution separately. Never infer insurer claims, insurance portfolio ownership, per-building values, or hazard polygons from the two CSV families.

## Verified country/prior-year availability witness (research only)

The byte-exact public GitHub Actions check of the `HANZE v3.0.2 beta` and
`Residential exposure v2025` files in [run 41244147338](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41244147338)
completed successfully on 2026-10-31. The additional *presence-only* diagnostic
`research_runners/historical_country_year_availability_v0.py` reported:

- 2,780 published historical flood event rows, of which 1,735 occur outside the
  eligibility window for an available previous calendar year (2001–2025).
- 1,045 events eligible for the literal country/code and previous-year check,
  consisting of 970 event rows with a matching prior-year residential indicator
  and 75 without such a match. `970 + 75 + 1735 == 2780` is enforced.
- 33 distinct countries in matched event contexts and 399 distinct country/year
  context pairs across the output inventory.
- 576 matched event rows also have a *reported economic loss field*.
  This does not make these losses insured, and missing fields are never treated
  as a zero amount.
- All indicator families are kept at their documented country/year granularity.
  The EU aggregate is excluded; no event footprint, subnational insured TIV,
  ground-up claim or monetary aggregate is generated.

This is a **source availability** diagnostic, not scientific calibration or an
as-of-event portfolio reconstruction. The previous calendar-year rule prevents
obvious future-year leakage but does **not** prove that the annual indicator was
known or effective on the flood date. Source-country code matches are literal;
no semantic crosswalk, regional mapping, interpolation, synthetic policy
ownership, insurer concentration or deductible is inferred. Source data bytes
remain outside Git.
