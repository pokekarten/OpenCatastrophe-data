<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original Kyrill one-cell Oasis hazard → 24 fictional building area-peril crosswalk

**5 November 2026.** This is a research-only *spatial* compatibility proof,
not a native model loss, annual insurance risk result or exposure catalogue.

## Precise provenance and why the bridge matters

The [CLIMK–WINDS v2 ERA5 original source](https://zenodo.org/records/15305753)
is a public CC BY 4.0, 6,792,278-byte NetCDF-4 archive of 50 **selected
extreme** European windstorms. The actual first original event is
**KYRILL** with original string label `20070118` and zero-based
source storm index 0. Its exact byte SHA-256 is pinned by the existing
provider inspector as
`92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.

Previous merged [original-source native Oasis footprint PR #1395](https://github.com/pokekarten/OpenCatastrophe-data/pull/1395)
proved that a different *2 × 3 sample tile* (rows 90–91, cols 130–132)
could be compiled by OasisLMF 2.5.8. However, those cell indices were
**not** the cells used for our fictional 24-building conditional-loss
preview in [separate draft PR #1361](https://github.com/pokekarten/OpenCatastrophe-data/pull/1361).

That research preview explicitly records **two fictional site markers
that map to the SAME original source grid cell**:
- `SYNTH_CLIMK_A` (longitude 5.958677287830914,
  latitude 52.41546239242131).
- `SYNTH_CLIMK_B` (longitude 6.02, latitude 52.47).

Both resolve to **native longitude-column index x=112,
latitude-row index y=78**. A single source cell, irrespective of
two input coordinates, has the same original local hazard gust.
The corresponding deterministic Oasis hazard
`areaperil_id = 78 * 269 + 112 + 1 = 21095`.
The original source comparison in the other PR states
**35.21054044063598 m/s**, but this *requires an independent original
NetCDF reread* and must never be accepted just because it appears in
this document. The new CI gate actually reads the provider original
and compares its direct `absolute_maxwindgusts[0,78,112]` against
two independently sampled original site records.

## Exact reproducible execution

[`research_runners/climk_kyrill_24_assets_native_peril_crosswalk_v0.py`](../../research_runners/climk_kyrill_24_assets_native_peril_crosswalk_v0.py)
uses the original independently pinned CLIMK source downloader and two
pre-existing, non-colliding pathways:

1. Original-grid `source_to_tile` of merged PR #1395 for **exactly one**
   physical cell, source storm 0, row 78 and col 112. This creates
   `events.csv`, `footprint.csv`,
   `intensity_bin_dict.csv`, `areaperil_dict.csv` using
   the observed `absolute_maxwindgusts` in m/s.
2. The original pinned native point sampler in
   [`scripts/climk_era5_synthetic_native_sample_v0.py`](../../scripts/climk_era5_synthetic_native_sample_v0.py)
   on the two declared **fictional** longitudes/latitudes.
3. An independent direct exact NetCDF `[event,row,col]` read to
   verify the two site samples and the source cell gust match **exactly**.
4. Map 24 invented EUR10m buildings (12 at each fictional marker)
   to the **same** Oasis area-peril ID and one conditional
   intensity bin. This does **not** allocate two independent storms
   or two independent exposures.
5. Native `oasislmf==2.5.8` `csvtobin footprint` accepts the
   original-source one-cell hazard as a model-ready hazard *component*.
   It does not build the remaining valid vulnerability, OED lookup,
   damage-bin or GUL/IL/RI financial and coverage files.

Only bounded research CSVs in the GitHub Actions temporary runner:
`fictional_asset_peril_crosswalk.csv`, four *one-cell* hazard CSVs,
`crosswalk_receipt.json`, and native `footprint.bin/idx`.
Do not commit provider NetCDF weather grids, customer portfolio data,
or derived site-level policy records. The two fictional site lat/lon
values and wind measurements are used only for rights-cleared
research validation.

## Scientific and financial hard stops

The receipt must retain:
`fictional_site_markers=2`,
`distinct_physical_hazard_cells=1`,
`fictional_asset_count=24`, `fictional_tiv_eur=240000000`,
`annual_oep_aep_authorized=false`,
`native_full_oasis_gul_il_ri_verified=false`,
`insurer_loss_and_vulnerability_calibrated=false`,
`real_insurer_locations_verified=false`.

No extrapolation to a carrier's holdings, independent storm-source
frequency, per-occurrence clustering, stochastic correlation,
annual AEP/OEP, insurable per-event loss, actual R+V/Zurich exposure,
treaty net or retro results. In particular:

- A source wind gust is **not** by itself a conditional damage
  distribution for a real structure.
- One gust intensity bin and a made-up USD/EUR building value are **not**
  a complete Oasis insured location record or its policy terms.
- The 24 invented buildings at two points **do not** create
  diversification across different weather hazards or events.
- CLIMK's selected 50 extreme storms do not produce a complete
  stochastic year universe; annual EP remains unauthorized.
- The exact conditional damage estimate in draft PR #1361 remains
  an **independent uncalibrated model preview**, not a validated
  native Oasis loss output. Same-cell mapping does not equate
  its damage formula with an independently validated Oasis
  vulnerability/financial simulation.

This PR changes no files from the separate draft wind-damage research
PR #1361. An eventual full model must explicitly check original
source-cell, wind unit, physical-vulnerability units, damage-bin
integration, location financial coverage and policy terms, before
a meaningful GUL/IL/RI run.
