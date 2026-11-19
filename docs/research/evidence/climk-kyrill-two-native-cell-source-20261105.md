<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLIMK Kyrill: source-native Berlin/Munich two-cell execution evidence

**Research-only original-byte evidence excerpt, not observed insurer loss or admitted scientific calibration.** The values below are transcribed from the original GitHub Actions runner output for the complete original SHA-pinned CLIMK–WINDS v2 ERA5 NetCDF. They are not freshly rerun by any NextGen consumer and must not be relabeled as independently source-verified solely by reading this Markdown.

- Provider: https://zenodo.org/records/15305753
- Original SHA-256: `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102` (provider bytes not redistributed)
- Original native runner: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42095141447
- Runner job: `127483087193`, completed **success**, exact OpenCatastrophe-data commit `d009c27c45bc42a6b7bba36b28923cb276c59da5`, 2026-11-05.
- Provider storm index 0, original label KYRILL, original date label `20070118`; this is **not an independently certified UTC occurrence time**.
- The two coordinates are invented site markers. Their distinct native wind cells and original m/s values are from the verified provider workflow. The associated EUR physical conditional means, vulnerability curve and 24 replacement costs are **user-authored synthetic assumptions**, NOT observed claims.
- One selected extreme historical storm cannot supply annual storm frequency. Both sites share the storm identity and are **not independent physical events**. The 12 buildings per location are not independent observations.
- No underlying original ERA5 grid, identifiable assets, or provider data are saved here.

The following single JSON block is a bounded cross-repository receipt, which must be checked by **exact Git blob SHA1** and strict field/type validation before use. It is an extract of the successful native workflow's declared report (not an independent second data-source authentication).

```json
{
  "schema_version": "OC_CLIMK_TWO_CELL_GITHUB_EXECUTION_EXCERPT_V0",
  "source_repository": "pokekarten/OpenCatastrophe-data",
  "source_commit_sha": "d009c27c45bc42a6b7bba36b28923cb276c59da5",
  "source_workflow_run_id": 42095141447,
  "source_workflow_job_id": 127483087193,
  "source_workflow_conclusion": "success",
  "source_sha256": "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102",
  "source_physical_event_key": "climk-winds:v2:ERA5:storm-index:0",
  "source_storm_name": "KYRILL",
  "source_storm_date_label_unverified_utc": "20070118",
  "original_source_bytes_verified_in_source_workflow": true,
  "original_source_bytes_reverified_in_nextgen": false,
  "number_of_distinct_native_ERA5_cells": 2,
  "invented_assets": 24,
  "invented_replacement_eur": 240000000,
  "per_site": [
    {
      "site_id": "FICTIONAL_BERLIN",
      "native_cell_x": 142,
      "native_cell_y": 78,
      "native_gust_mm_s": 31090,
      "invented_assets": 12,
      "conditional_expected_physical_loss_eur_exact": {"numerator": 15085200, "denominator": 1}
    },
    {
      "site_id": "FICTIONAL_MUNICH",
      "native_cell_x": 134,
      "native_cell_y": 95,
      "native_gust_mm_s": 33976,
      "invented_assets": 12,
      "conditional_expected_physical_loss_eur_exact": {"numerator": 21665280, "denominator": 1}
    }
  ],
  "conditional_expected_physical_loss_total_eur_exact": {"numerator": 36750480, "denominator": 1},
  "synthetic_roster_sha256": "833e85db5cec4b4ffa3d56d2fa016d6742eac28ca185ec762baa3dae6a70de17",
  "uncalibrated_vlt_sha256": "d7e4c163e434e9098ad77d7ea95d287592084cb3e5a7fa202bb9093d7282ea55",
  "source_event_frequency_inferred": false,
  "fitted_spatial_damage_dependence": false,
  "annual_AAL": null,
  "annual_AEP": null,
  "annual_OEP": null,
  "insurer_original_gross": null,
  "insurer_retained_net": null
}
```
