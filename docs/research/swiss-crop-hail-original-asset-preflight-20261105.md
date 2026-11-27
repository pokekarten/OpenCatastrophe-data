<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Swiss crop-hail linked original-asset preflight (2026-11-05)

## Source scope

Primary peer-reviewed paper: https://doi.org/10.5194/nhess-24-2541-2024 (Portmann et al. 2024). The paper's "Code and data availability" section explicitly links all four version-specific Zenodo records.

All four Zenodo record pages display CC BY 4.0 licensing; independent review of upstream insurance-derived claims, MeteoSwiss and redistribution conditions is still needed before downstream model admission.

| Role | Published record and version | Source-listed original-file MD5 |
|---|---|---|
| 2021 crop exposure grids (1, 2, 4, 8 km) | https://zenodo.org/records/11064756 v1 | data-files.zip: 7db8df4c81ba5d1c1c7b8371cee53e15; metadata.csv: 05faf6e57f0b37130b3fc1c16190ed6c |
| Damage reports, per crop 10–12 events | https://zenodo.org/records/11064767 v1 | data-files.zip: c17119f9cd35f57ad49662a6f8ba1166; metadata.csv: 0260ae2047e3fc02aa7ad88cf7911dda |
| Radar hazard, 12 event dates | https://zenodo.org/records/11064781 v1 | MESHS HDF5: f18b4e27342a374b08ca4c0ec8f90b5c; POH HDF5: 3eee87725577ee3b74e0c33601dbfffa; metadata.csv: c4d4090b272eb9969a9045f93b2ce2c2 |
| Model/reproduction code | https://zenodo.org/records/12784190 version 1.0 | ZIP: 96f72406c1464824434e66c54998be0e |

Publisher radar event dates (YYYY-MM-DD): 2017-06-27, 2017-07-08, 2017-08-01, 2019-06-15, 2019-06-30, 2019-07-01, 2021-06-20, 2021-06-21, 2021-06-28, 2021-07-12, 2021-07-13, 2021-07-24.

**Evidence boundary:** MD5 values were checked on the original publisher record pages, not independently recomputed on original bytes. The original assets could not be downloaded in this isolated runtime. MD5 is a publisher-file identity aid and not a modern adversarial authenticity guarantee. No original SHA-256, HDF5 fields, data semantics, insurer losses, or frequency calibration have been independently verified. No external bytes are in Git.

## Offline operator verification

Acquire the exact released source file into an operator-owned directory *outside the Git checkout*, then run e.g.:

    python research_runners/swiss_crop_hail_asset_preflight_v0.py --asset radar_meshs_h5 --file /external/hail_MESHS_CH_12_events_2017_2021.h5

Other asset IDs: exposure_zip, exposure_metadata, damage_zip, damage_metadata, radar_poh_h5, radar_metadata, code_zip.

The script never downloads, unpacks, imports, executes third-party code, copies source data or writes to a database. On a true local match, it verifies source-listed MD5 and local basic format/container safety, computes SHA-256, and prints a JSON receipt with negative model-admission flags. It does **not** assert suitability for commercial insurance modelling.

Offline synthetics (Python 3.13): ten out of ten tests passed locally with

    python -m unittest -q tests.test_swiss_crop_hail_asset_preflight_v0

Full exact-branch repository validation and GitHub CI must be checked separately, not presumed green.

## Scientific and rights blockers

- The published research is a **yes/no crop-damage footprint classifier**, not damage-cost, TIV or treaty GUL/IL/RI loss estimation.
- Only 12 selected historical radar days, with 10–12 observed crop-specific dates. They are **not** a representative yearly event catalogue; do not infer annual AEP/OEP.
- Verify original-source rights and any provider conditions separately from CC BY on the Zenodo landing pages, particularly the insurer-derived gridded damage and MeteoSwiss-derived radar product.
- Confirm HDF5 field names, CRS, units, event timestamps, no-data support, exposure crop-area/field counts and consistent 1/2/4/8-km aggregation before spatial pairing.
- Do not interpret the four linked components as four independent observations/validation samples.
- For a future insurer CAT consumer, add calibrated insured crop values, financial terms, crop vulnerability and independently characterized event frequency/holdout.
