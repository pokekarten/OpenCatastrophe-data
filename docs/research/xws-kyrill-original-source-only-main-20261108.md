<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# XWS Kyrill 2007: standalone original NetCDF source integrity gate

**2026-11-08, source-level research only.** This is a narrowly scoped, verifiable extraction of the **original-source receipt** subtask of [OpenCatastrophe-data Draft #1389](https://github.com/pokekarten/OpenCatastrophe-data/pull/1389). No original external NetCDF bytes, sensitive insurer data, geocoded risk assets, or generated model losses are stored in the repository or written to the production Neon database.

## What is tested

- `research_runners/xws_kyrill_original_netcdf_hazard_receipt_v0.py` allowlists four public issuer URLs, bounds downloads to 256 KB, checks NetCDF Classic magic, original **122,304-byte** length and pinned individual SHA-256, verifies CF/rotated-pole source axes, physical gust units, source grid and valid-value ranges. It rejects an unapproved redirect and never treats rotated lat/lon as WGS84.
- `research/observations/xws_kyrill_2007_original_netcdf_receipts_v0.toml` records source identity, attribution, original SHA receipts, 158×178 historical grid size and explicit admission blockers. The original files are **four views of one historical Kyrill storm** on **2007-01-18**, not four independent frequency samples or an annual stochastic event catalogue.
- `tests/test_xws_kyrill_original_netcdf_hazard_receipt_v0.py` exercises the allowlist, bounds, header/sha rejection and no-admission flags offline using fictional bytes.
- `.github/workflows/xws-kyrill-original-nc-hazard-receipt.yml` runs the pinned source routine in GitHub Actions with temporary download and log-only aggregate receipts. No source artifact upload, repository redistribution or production database writes.

## Reproduction

```sh
python -m unittest discover -s tests -p 'test_xws_kyrill_original_netcdf_hazard_receipt_v0.py' -v
python -m compileall -q research_runners/xws_kyrill_original_netcdf_hazard_receipt_v0.py
python scripts/check_all.py
```

Live workflow additionally installs its pinned NetCDF3 scientific reader and downloads the **unchanged original publisher products**. The original research Draft #1389 had an exact-head successful original-NetCDF receipt CI run [#42184064453](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42184064453); this extracted new PR must establish its **own** source-workflow and full-CI success before merge.

## Hard boundaries

Source-readable or CC BY publication does **not** constitute scientific calibration, real insurer exposure, authorized insurer-level TIV, building geolocation, original R+V/German OED acceptance, source asset-vulnerability mapping, treaty parameters or gross/net annual OEP/AEP. The XWS Kyrill data and the separate fictional 10k NRW policy/hazard overlay, conditional Schwierz loss and QS/XL trials in **#1389** remain separate experiments. They are **not** silently included in this limited source receipt integration. Source terms/attribution and any downstream derivatives require explicit separate review; a historical one-event footprint cannot identify annual occurrence frequency.
