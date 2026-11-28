<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source-reproduced CLIMK-WINDS Kyrill synthetic conditional physical-loss evidence

**Research evidence only; no original NetCDF grids in Git; no actual insurer exposures, calibrated vulnerability, annual AEP/OEP or claims.** The selected source index 0 represents one historical extreme storm, not a representative independent annual loss sample.

- [Original source-native live run 42012362586](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42012362586) — all 20 tests PASS; original pinned Zenodo NetCDF source re-read with matching point gust observations.
- [Source-locked follow-up workflow](https://github.com/pokekarten/OpenCatastrophe-data/actions/workflows/climk-era5-synthetic-conditional-loss-live.yml) — parses exactly the single JSON code block below and independently compares current real source values.
- Exactly two fictional location markers **share the same native ERA5 grid cell**; the 24 buildings, replacement cost, VLT and per-event loss are user-authored research assumptions.
- The full exact rational EUR figure is kept below so precision cannot be lost by display rounding. AAL, AEP, OEP and insured original/reinsurance Gross/Net remain null.

This documentation contains one **machine-readable** locked JSON record, not a tracked `.json` or `.jsonl` data file. The repository explicitly prohibits unregistered canonical JSON projections and tracked JSONL data; neither policy is relaxed.

```json
{
  "schema_version": "oc-climk-era5-original-conditional-damage-run-evidence-v0",
  "recorded_utc": "2026-11-05",
  "status": "REPRODUCED_IN_PUBLIC_GITHUB_ACTIONS_NOT_CALIBRATED_NOT_ANNUAL_LOSS",
  "github_workflow_run_url": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42012362586",
  "github_workflow_run_id": 42012362586,
  "github_workflow_job_id": 127194292925,
  "executed_source_commit": "f4379d445775c48b553d798ed28aab7ee3c4b345",
  "workflow_conclusion": "success",
  "workflow_tests_passed": 20,
  "workflow_tests_failed": 0,
  "runtime": "CPython 3.14.9; pinned netCDF4 1.7.4",
  "source_publisher": "CLIMK-WINDS v2 ERA5 / Zenodo record 15305753",
  "source_url": "https://zenodo.org/records/15305753",
  "source_file": "ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc",
  "source_sha256": "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102",
  "source_size_bytes": 6792278,
  "source_storm_index_zero_based": 0,
  "source_storm_name": "KYRILL",
  "source_date_label_not_exact_utc": "20070118",
  "source_event_cross_model_matched": false,
  "two_synthetic_sites_coincident_native_grid_cell": true,
  "source_points": [
    {
      "synthetic_site_id": "SYNTH_CLIMK_A",
      "native_cell_x": 112,
      "native_cell_y": 78,
      "absolute_max_gust_m_s": 35.21054044063598
    },
    {
      "synthetic_site_id": "SYNTH_CLIMK_B",
      "native_cell_x": 112,
      "native_cell_y": 78,
      "absolute_max_gust_m_s": 35.21054044063598
    }
  ],
  "original_point_sampler_rerun_and_exactly_compared": true,
  "synthetic_asset_count": 24,
  "synthetic_asset_replacement_eur_per_asset": 10000000,
  "synthetic_replacement_cost_total_eur": 240000000,
  "synthetic_asset_roster_sha256": "765be95cce871af76a91c5eb71b511461db7993010b5b2814cca19b795e47c0f",
  "synthetic_vulnerability_sha256": "188adb2c270a5b86da42f6c4e3d59011d095a390c338ba3f1b0660c6c934394e",
  "vulnerability_basis": "user-authored uncalibrated monotone gust/damage bps knots; NO empirical fitted observed claims",
  "conditional_expected_physical_groundup_loss_eur_exact": {
    "numerator": 530700800,
    "denominator": 11
  },
  "conditional_expected_physical_groundup_loss_eur_display": 48245527.27272727,
  "annual_event_frequency": null,
  "annual_AAL": null,
  "annual_AEP": null,
  "annual_OEP": null,
  "insurer_original_gross": null,
  "insurer_retained_net": null,
  "external_re_inward_gross": null,
  "external_re_retained_net": null,
  "real_insurer_exposure_matched": false,
  "real_insurance_contracts_matched": false,
  "source_selected_extremes_not_frequency_representative": true,
  "no_original_netcdf_bytes_or_raw_grids_committed": true,
  "limitations": [
    "Source selected 50 most extreme winter storms; do not infer independent annual rates",
    "Both invented sites sample exactly the same native ERA5 grid cell; no spatial insurance diversification demonstrated",
    "Per-building cost, sites and vulnerability are synthetic and uncalibrated",
    "This is conditional expected physical ground-up loss, not sampled loss, insured gross, external re or net",
    "Kyrill source date label is not independently parsed or certified as UTC",
    "Scientific CLIMK gust measure not interchangeable with C3S EWS 72h 3-second gust",
    "Not validated against observed insurer claims or an independent reference vulnerability calibration"
  ]
}
```
