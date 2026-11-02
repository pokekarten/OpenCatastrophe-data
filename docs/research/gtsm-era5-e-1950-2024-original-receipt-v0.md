<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E v2 original statistical NetCDF research receipt (v0)

Source: https://zenodo.org/records/14671593; DOI 10.5281/zenodo.14671593; published 2025-02-25, v2.
Exact asset: `ds_GTSM-ERA5-E_1950-2024_stats.nc`, original HTTP content length **9,652,424 bytes**, publisher-listed **MD5 0f2b7071c6ec3585768be6cf427e6eab**.
Publisher metadata was independently verified by GitHub Actions exact-head run [41507598794](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41507598794), 2026-11-02 19:12:57 UTC: full 9,652,424 bytes, publisher-listed MD5 matched, NetCDF4/HDF5 signature confirmed. Independently observed source **SHA-256 `e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767`** is now an additional fixed reject-on-drift source gate. SHA-256 was independently computed, not published by the provider. No source bytes committed or persisted to Neon.

## Executable research step

For a separately lawfully acquired original file, use the offline check:

    python scripts/gtsm_era5_e_original_receipt_v0.py --original /path/to/ds_GTSM-ERA5-E_1950-2024_stats.nc
    python -m unittest tests.test_gtsm_era5_e_original_receipt_v0 -v

To verify exactly one public provider file on an internet-enabled runner, run:

    python scripts/gtsm_era5_e_original_receipt_v0.py --fetch --inspect-header

The fixed PR workflow `.github/workflows/gtsm-era5-e-original-receipt.yml` runs the offline tests followed by this exact one-file HTTPS download (only same-repository PRs). The fetch mode has no caller-selectable URL; refuses non-Zenodo redirects, unexpected size, HTTP failures and MD5 mismatch; only a metadata receipt reaches CI logs. Provider bytes are held only in an ephemeral temporary file during verification and deleted immediately. No source file or raw array is uploaded as an artifact.


The verifier performs local read-only streaming over the full regular non-symlink source file, checks exact published length and MD5, validates a recognizable HDF5/NetCDF signature, then **rejects any drift from the SHA-256 observed in successful original-source run 41507598794**. With `--inspect-header` it inventories dimensions, variable names, types, shape, units and short descriptive attributes without reading variable values; source-native science/vertical-datum validity is not inferred. Offline mode never fetches; online mode uses only an ephemeral temporary file and deletes it before returning. Neither mode retains provider bytes in the repository, derives losses, or publishes raw values. The production-facing CLI has no hash/size override; synthetic unit tests exercise the internal receipt function with independently invented fixtures.

## Scientific and licence barriers

- This particular Zenodo asset is descriptive statistics of modelled *still water levels*, not flood-inundation footprints, actual coastal building damage, tide-gauge measurements, insured values or stochastic CAT event losses.
- The accompanying 2026 study (https://essd.copernicus.org/articles/18/5759/2026/) identifies the statistics as detrended hourly total-water-level extreme values with 5%–95% confidence ranges and independent original time series in CDS DOI 10.24381/cds.a6d42d60. The full time series has separate identity, access and scope.
- Publication describes tidal/surge modelling and reference to 1986–2005 local mean sea level for the total-water-level series. The statistics are detrended. Do not attach these statistics to a local DEM, vertical datum or building altitude without an independent reference/geometry audit.
- The data's exact redistribution/commercial rights must be confirmed against current Zenodo rights metadata and any upstream CDS conditions. Public download is not an admission.
- A validated MD5, file signature and new SHA-256 **do not prove** NetCDF dimension names, value units, vertical datum, scientific fitness or source independence. These are separate next tests and no insurer/CAT input approval is implied.

## Execution evidence

The complete real-source receipt of 2026-11-02 is verified from exact-head runner logs (run #41507598794, job #125490753179); 12 synthetic boundary tests and Python 3.11–3.14 matrix passed. The follow-on revision pins independently observed SHA-256 and adds metadata-only NetCDF inspection and tests. Its own exact-head CI and real NetCDF header output must be checked separately before any variable-level assertions. The earlier receipt did not inspect the NetCDF variables. No model admission, permission for commercial reuse, raw file retention or event generation is implied.
