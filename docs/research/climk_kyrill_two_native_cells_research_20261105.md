<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original CLIMK Kyrill across two different ERA5 cells — physical spatial preflight

**Research / synthetic scenario only.** Companion to OpenCatastrophe-data PR #1361 and NextGen PR #280. The earlier original-source 24-asset conditional-loss proof used **two labels sampling the same native ERA5 cell (112,78)**. It is therefore not evidence of spatial wind-gust diversity or building damage dependence. This follow-up uses two geographically separated, **fictional site markers** near the Berlin and Munich city centers; their coordinates are **not actual insured building locations**.

- Source publisher: CLIMK-WINDS v2 ERA5, Zenodo https://zenodo.org/records/15305753.
- **Immutable original source SHA-256:** `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`; identical to the original earlier verified Kyrill source, not a different event/model.
- Original source index zero, publisher name `KYRILL`, publisher day label `20070118`, **not certified UTC event timestamp**.
- Invented site markers: `FICTIONAL_BERLIN` (13.4050 E, 52.5200 N), `FICTIONAL_MUNICH` (11.5820 E, 48.1351 N). Exactly twelve fictional commercial buildings per marker, EUR 10m invented replacement each, EUR 240m invented total. Site coordinates are only synthetic markers, not insured exposure.
- **Essential new physical acceptance:** two distinct *original nearest-neighbor native ERA5 cells*. If both markers collide into one cell, if a cell is masked, or if the field/time/source label changes, the run fails. The original native sampler produces exact source-specific `absolute_maxwindgusts` in m/s, not DWD station-measured instantaneous gust and not a C3S 72h maximum three-second gust.
- Same uncalibrated, manually constructed monotone piecewise-linear gust-to-damage curve for both markers, with original source points independently **resampled from the same exact original NetCDF** before conditional financial-damage preview. Per-asset exact rational EUR results must reconcile separately by marker and to the full conditional physical total. `annual_AAL`, `annual_AEP`, `annual_OEP`, insurer gross/net and any inferred annual rate stay `null`.
- Two distinct source wind cells **are not** 24 independent wind realizations and do not estimate real-building damage correlation. All twelve invented assets at one marker share a single source gust observation; event count is still one selected historical extreme storm, not one annually sampled year.
- Original bytes are downloaded to an ephemeral GitHub Actions worker, not added to Git or uploaded as an artifact. Source, data reuse and original site semantics remain research-limited.

## Reproduce and evidence boundary

Offline adversarial tests (faked source observations; no source access required):

```bash
python -m unittest tests.test_climk_kyrill_two_cell_spatial_preview_v0 -v
```

The new workflow `.github/workflows/climk-kyrill-two-native-cell-research.yml` additionally downloads original bytes, executes the **unchanged** pinned CLIMK sampler and existing conditional damage preview, verifies independent re-sampling, outputs only selected native cell coordinates/physical gusts and synthetic aggregate damage, and retains no original NetCDF. **Only a successful exact-HEAD GitHub Actions run may establish real original source proof.** Local mocked unit tests establish input/contract defenses, never actual Berlin/Munich gust readings. Do not assign numeric original gusts before that run.

Next steps are independent observed wind station holdouts with matched time/height/gust semantics, cross-country HANZE event source/observed-vs-modelled lineage review, and actual spatially distributed exposure calibration. The original HANZE country reports are not asset-level insured losses and must not be identified as independent observed per-building damage. No cross-provider storm ID or annual AAL/AEP/OEP is created by this work.
