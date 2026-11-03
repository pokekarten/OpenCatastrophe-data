<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WFP CHIRPS3-GEFS forecast issue-vintage and nonindependence research (2026-11-03)

Source-specific, **non-admission** research grounded in the original World Food Programme (WFP) Source Cooperative catalogue pages:

- https://source.coop/wfp/chirps-daily-forecast
- https://source.coop/wfp/chirps-dekad-forecast
- https://data.source.coop/wfp/chirps-dekad/README.md
- https://source.coop/wfp/chirps-dekad (separate mirror of original CHIRPS3 observations)
- https://www.chc.ucsb.edu/data/chirps3

## Specific product lineage and unsafe historical comparison

The WFP CHIRPS3-GEFS **daily forecast** is not the original CHIRPS3 rain-observation product. Its source forecast is NCEP GEFSv12, bias-corrected to CHIRPS3 climatology and downscaled to daily with NASA IMERG Late V07. This produces forecast precipitation, not observed inundation or insurer losses. Other CHIRPS3 daily rain products inherit ERA5/IMERG dependencies; forecast and observational products must not be assumed independent when used in calibration, training, holdouts or validations.

The WFP daily forecast README reports that each issue writes 16 daily files (issue day plus 15 days lead), overwriting previous forecasts for any overlapping valid date. For past dates the displayed asset refers to the forecast issued on that day (**lead 0**), not the forecast that had lead 1–15 days at a prior issue. Thus the current public archive does **not** establish a reproducible historical fixed-issue forecast skill dataset. This is an as-of or look-ahead contamination hazard; simply knowing valid date and its original file URL does not preserve issue time or forecast vintage.

The WFP **dekadal forecast** uses the same parent GEFS/CHIRPS lineage and should not be treated as another independent forecast ensemble. Its original issue-retention policy and exact assets require separate investigation. The different WFP `chirps-dekad` COG release represents a mirror/format conversion of CHIRPS v3 historical observed precipitation, **not** a third independent measurement source. WFP Source Cooperative says CC BY 4.0 and cites CHIRPS3 original DOI, but these statements are research inputs; there has been no OpenCatastrophe exact-asset rights, original-file, service-terms or scientific admission review.

## Executable fail-closed proof

`research_runners/wfp_chirps_gefs_issue_vintage_gate_v0.py` uses synthetic/offline **research claims only**, no automatic provider fetch. It checks the exact daily WFP product/version, issue date, valid date and 0–15 day lead arithmetic, rejects missing/changeable fields, duplicate JSON keys, invalid dates, non-finite values, wrong source/variant, invalid SHA-256 formatting or attempts to relabel the product as an observed event, insured loss or historical backtest. It never converts a user-supplied SHA into independently checked original bytes or a claimed preserved forecast issue.

Its fixed output makes all as-of, original-bytes, independent-observation, external-rights and model-admission claims explicitly **false** even for internally coherent synthetic claims. No real original forecast data, source receipt, COG, parquet, STAC output, model simulation or database row is created.

A synthetic only example (the all-`a` hash is illustrative and must not be read as an original-byte receipt):

```json
{
  "source_id": "wfp.hdc.chirps3-gefs-daily-forecast.v3",
  "product_version": "v3.0",
  "issue_date": "2026-09-05",
  "valid_date": "2026-09-20",
  "lead_days": 15,
  "asset_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "research_role": "prospective_forecast_context_only"
}
```

After saving an independently synthetic claim outside Git, run:

```bash
python research_runners/wfp_chirps_gefs_issue_vintage_gate_v0.py --claim-json /path/to/local/synthetic.json
python -m unittest tests.test_wfp_chirps_gefs_issue_vintage_gate_v0
python scripts/check_all.py
```

## Before real modelling

1. Confirm original product-specific WFP/CHC/Source Cooperative access and commercial/redistribution rights for exact versions and routes; record attribution and licence conditions independently of the parent dataset.
2. Determine whether any trusted original-issue forecast archive with immutable issue `issue_time_utc`, lead time, original source bytes and SHA-256 exists. Without it, no retrospective forecast-skill or as-of event analysis is possible from the rolling WFP mirror alone.
3. Only after a reviewed fixed product/vintage can a bounded original metadata probe and separate approved model-consumer contract be developed. Keep forecast, observed precipitation, physical flood hazard, economic loss and insured loss as distinct roles.
