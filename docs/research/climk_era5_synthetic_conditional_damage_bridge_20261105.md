<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLIMK–WINDS ERA5 native point gust → synthetic physical damage: strict conditional pilot

**Research draft (2026-11-05). Not an insurer's real exposure or loss data; no CAT annual frequency, AAL, OEP, AEP, premium, insured recovery, regulatory capital, observed claims calibration or vendor-model validation.**

## Existing original source and proven research route

The **existing** OpenCatastrophe-data source route must be reused rather than duplicated:

1. `scripts/inspect_climk_winds_era5_v0.py` retrieves and verifies the original [CLIMK–WINDS v2 ERA5 NetCDF](https://zenodo.org/records/15305753), a **top-50 extreme-winter-storm selection for 1995–2015**, not a complete representative multi-year event catalogue. Verified provider bytes: size **6,792,278**, publisher MD5 `887ae3218793c599862f115876c145f9`, pinned SHA256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`. Existing repository execution receipt reports an authentic provider download and NetCDF header check, with 50 storms × 181 latitudes × 269 longitudes; see `docs/CLIMK_WINDS_ERA5_PROVIDER_PROBE.md` and [GitHub Actions source receipt](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41227457898). This PR does **not** re-download or rerun the original NetCDF.
2. `scripts/climk_era5_synthetic_native_sample_v0.py` independently samples one source-specific storm index at synthetic lon/lat points on the native grid, preserving source names/date annotations and the original unit `m s**-1`. No claimed mapping to the distinct C3S EWS physical storm event IDs.
3. **New** `scripts/climk_era5_synthetic_damage_preview_v0.py` takes that strict original JSON *shape* and separately authored synthetic assets and wind-gust damage curves. It computes exact-rational per-asset *conditional expected ground-up loss* without pretending to be original policy-insured gross, inward reinsurance or net retained loss.

The scientific paper [Flynn et al., *Earth System Science Data* 17, 4431–4453 (2025)](https://doi.org/10.5194/essd-17-4431-2025) confirms each of the four meteorological input sources selects its own top 50 extreme storms. The source dates and storm IDs **cannot** be assumed to match across source models. The publisher README states **CC BY 4.0**; attribution, third-party licenses and a source-specific publication review remain mandatory. An original sample's embedded SHA256 is only a declared source binding: **this new downstream adapter cannot prove the forwarded JSON gust values still equal the original NetCDF**. It explicitly exports `source_sample_gust_values_independently_reverified=false`.

## Explicit new input contracts

Three independently pinned JSON files are supplied to the new CLI:

- `--source-sample`: exactly the existing sampler's `oc-climk-era5-synthetic-native-point-sample-v0` JSON. It must cite the pinned source SHA, retain one original `storm-index:0..49`, the original gust-unit/measure, location IDs and all `scientifically_admitted=false`, `source_event_frequency_inferred=false`, and `damage_or_insured_loss_computed=false` flags. Bad types, mismatched IDs or omitted sites fail closed.
- `--synthetic-assets`: `{"schema_version":"oc-climk-era5-synthetic-asset-roster-v0","synthetic_only":true,"currency":"EUR","insurer_label":"ZURICH_RESEARCH_PROXY","rows":[{"asset_id":"invented-1","site_id":"site-1","taxonomy":"COM","replacement_cost_eur":10000000}]}`. These are **invented buildings** and an inspiration-only insurer label, not a Zurich property schedule. Every source sampled site must map to at least one synthetic asset; every asset must have an explicit reviewed source sample site.
- `--vlt`: `{"schema_version":"oc-climk-era5-synthetic-conditional-gust-vlt-v0","physical_intensity_measure":"MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT","normalized_unit":"mm/s","model_evidence":"USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION","curves":[{"taxonomy":"COM","gust_knots_mm_s":[0,15000,25000,35000,200000],"damage_ratio_bps":[0,0,100,2000,10000]}]}`. Monotone, physically bounded piecewise-linear *assumed* ratio, not a fitted claim curve. No extrapolation allowed.

CLI (run on real pinned point-sample JSON prepared **separately**):

```bash
python scripts/climk_era5_synthetic_damage_preview_v0.py \
  --source-sample /tmp/climk-synthetic-source-native-sites.json \
  --synthetic-assets /tmp/climk-synthetic-assets.json \
  --vlt /tmp/climk-assumed-wind-vlt.json \
  --out /tmp/climk-synthetic-conditional-damage-preview.json
python -m unittest discover -s tests -p test_climk_era5_synthetic_damage_preview_v0.py -v
```

### Exact physical-loss calculation

Gust in m/s is converted to **mm/s** with decimal half-up rounding. Damage ratio is interpolated *exactly* between user-supplied bps knots; per-asset conditional ground-up EUR is kept as exact rational numerator/denominator, without silently rounding cents, damaging source units or converting per-asset cost into a book-level TIV. With hypothetical gusts 20/30 m/s, per-asset cost EUR 10m, and the sample VLT above, loss ratios 50/1,050 bps give **EUR 50,000 / EUR 1,050,000**, or **EUR 1.1m** combined. **All these are invented test values.**

### Scientific and financial boundaries

- **Not the native C3S stochastic stage.** NextGen `research/c3s_wind_footprint_stage_v0.py` requires `MAX_3_SECOND_10M_GUST_OVER_72_HOURS` plus C3S-specific NetCDF/track/footprint semantics. CLIMK's `absolute_maxwindgusts` is published as its own storm footprint variable. This adapter **never relabels** CLIMK as C3S, nor treats C3S counts as CLIMK occurrence probabilities.
- **Not original-policy gross.** The existing NextGen `model_factory_portfolio_bridge_v0.py` applies limits/deductibles/shares to per-asset *sampled integer physical losses*; this adapter supplies only conditional rational means and **does not** generate `MUSE_SYNTHETIC_CAT_GROUND_UP_V0` or misrepresent original real hazard as `new_synthetic`.
- **Not EP.** The 50 preselected extremes are **not** 50 complete annual worlds, annual frequencies or a Poisson intensity. All reported `annual_AAL`, `annual_AEP`, `annual_OEP`, original insured gross, primary net, outside inward gross/net are explicitly `null`.
- **Not calibrated.** Actual empirical event-level impact observations, consistent buildings and taxonomy, spatial/temporal train/holdout and impact-function parameter bounds are needed before empirical vulnerability calibration. Even the source-aligned historical point gusts must be revalidated against original bytes at conversion time for an admitted physical loss stage.

## Local executed gates and next steps

- 2026-11-05: **13/13 local Python stdlib tests passed**, including a 2-asset exact hand-oracle, invalid source identity and event key, unsupported C3S gust substitution, duplicate assets, incomplete site mapping, nonmonotone VLT, unbounded gust, invalid JSON and CLI source-overwrite protection. Tests use **invented source-shaped JSON**, not original CLIMK event values.
- [ ] Cross-check a fresh exact-source sample **against the original NetCDF** at the same event index and 24 invented coordinates, produce separate raw+point+damage SHA evidence.
- [ ] Obtain independent event-level historical *observed impact* samples for a real test/holdout damage-function calibration; do not fit to a published insurer net AEL/PML directly.
- [ ] Build scientifically admitted annual physical-event frequency/occurrence law and correlation, then **sample** physical damage with validated dependency and explicit positive integer EUR handling.
- [ ] Run producer-admitted event/asset physical losses through NextGen **original insured → outward/inward Cat XL → external retro**, preserving all zero-event years and physical event identities, then Gross/Net AAL/AEP/OEP with independently rebuilt curve receipts.

No original/provider raw data, derived grid values, person information, actual insurer contracts or production database rows are committed in this research PR.
