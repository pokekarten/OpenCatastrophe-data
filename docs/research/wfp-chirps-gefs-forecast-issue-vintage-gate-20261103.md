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


## Second independent obstacle: original WFP STAC raster-band units

Original WFP STAC Collection metadata was reviewed via Exa's official-page fetch on 2026-11-03:

- Daily: https://api.earthobservation.vam.wfp.org/stac/collections/chirps_daily_forecast
- Dekadal: https://api.earthobservation.vam.wfp.org/stac/collections/chirps_dekad_forecast

Both collections advertise STAC version `1.0.0`, licence identifier `CC-BY-4.0`, a 60S–60N spatial bbox, time interval beginning `2001-01-01T00:00:00Z`, a COG `band` asset, `raster:bands[0].data_type=float32`, `nodata=-9999`, and **`raster:bands[0].unit="1"`**. That string does **not verify millimetres of precipitation**. No scaling, unit conversion, interpretation of a pixel as mm/day or mm/dekad, loss hazard, or forecast performance is legitimate until the exact provider asset and band semantics are independently checked. The provider also does not establish that every historical forecast issue is preserved.

`research_runners/wfp_chirps_gefs_stac_collection_preflight_v0.py` is a second offline fail-closed checker for one externally saved original provider STAC **collection metadata JSON** (not feature/item/asset downloads). It requires exact fixed collection ID, version, origin/self URL, geospatial/temporal metadata, COG band type, numeric fill, unit declaration, source role and strict original byte SHA-256. It emits negative claims for verified rainfall mm units, retained issue history, original COG acquisition, as-of evaluation and model admission. Tests under `tests/test_wfp_chirps_gefs_stac_collection_preflight_v0.py` use synthetic metadata and reject mutated science and structural fields. Passing a caller-supplied file hash cannot establish HTTP transport authenticity; no real original-byte hash has been recorded yet.

Only after an authorized exact original metadata response is independently saved **outside Git**, the read-only checker may be run as:

```bash
python research_runners/wfp_chirps_gefs_stac_collection_preflight_v0.py \
  --collection daily --original-json /path/outside/git/original-collection.json \
  --expected-sha256 <verified_original_bytes_sha256>
```

The example is a future operator procedure, not a claim that provider bytes were fetched, that commercial rights were resolved, or that original forecast item values were obtained. The output must remain non-admission until a separate scientific/rights review and exact asset provenance prove physical units, issue-vintage and forecast roles.


## Alternative historical source: original CHC CHIRPS3-GEFS archive

The **producer**, UC Santa Barbara Climate Hazards Center, separately documents CHIRPS3-GEFS forecast products and historic archives: https://www.chc.ucsb.edu/node/251 . The daily forecast archive directory is https://data.chc.ucsb.edu/products/CHIRPS-GEFS/v3/daily/global/ . Original directory metadata visibly advertises year folders 2001 through 2026, a `created/` folder and the v3 model family. This is an upstream potential access route distinct from the WFP rolling COG delivery of the same underlying forecast family, **not a statistically independent forecast model** and not an admitted dataset.

Crucial original publisher caveats (CHC product page):
- CHIRPS3-GEFS v3 historical products begin 2001 and are calibrated to CHIRPS v3; GEFSv12 is the forecast parent. A visible historical year directory is **not** proof of complete, exact original forecast issue coverage or true point-in-time operational availability for that year.
- The publisher expressly says **2020 is excluded from its historical data archive** due to a nine-month reforecast/operational gap. A directory named `2020/` may exist even though that exclusion applies. Do not treat a directory label as a verified full forecast time series; reconcile its contents and actual issue coverage before any coverage claims.
- Historical GEFSv12 *reforecasts* and later actual *operational* forecasts are different experiment types. Backtesting a post-2025 reprocessed historical reforecast cannot be labeled the real 2001-era forecast known at that time. Model training/calibration cuts must remain independent from simulated out-of-sample tests.
- Publisher source DOI https://doi.org/10.15780/G2PH2M and original CC BY 4.0 source statement are useful licence/science evidence, not a licence review for any one exact WFP asset or an OpenCatastrophe admission.

**Next executable causal step:** after dataset and API terms are reviewed, construct a tightly bounded metadata-only original-source listing for one documented historical year and product path; record original response SHA-256, requested URL, retrieval UTC, actual filename/issue-time semantics, and a reproducible `reforecast` versus `operational` designation. Only after that could a real issue/valid/lead mapping and physical raster-unit challenge start; neither this PR nor WFP's rolling archive allows a retrospective as-of claim by itself.
