<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GTSM-ERA5-E v2 original statistical NetCDF research receipt (v0)

Source: https://zenodo.org/records/14671593; DOI 10.5281/zenodo.14671593; published 2025-02-25, v2.
Exact asset: `ds_GTSM-ERA5-E_1950-2024_stats.nc`, original HTTP content length **9,652,424 bytes**, publisher-listed **MD5 0f2b7071c6ec3585768be6cf427e6eab**.
Those are provider metadata, **not** evidence that repository authors downloaded the complete file or that the publisher signed a SHA-256.

## Executable research step

After a separately lawful, manually acquired original asset, run:

    python scripts/gtsm_era5_e_original_receipt_v0.py --original /path/to/ds_GTSM-ERA5-E_1950-2024_stats.nc
    python -m unittest tests.test_gtsm_era5_e_original_receipt_v0 -v

The verifier performs local read-only streaming over the full regular non-symlink source file, checks exact published length and MD5, validates a recognizable HDF5/NetCDF signature, then emits computed SHA-256 **as an observed receipt only**. It never fetches, persists source bytes, derives loss or publishes raw values. The production-facing CLI has no hash/size override; synthetic unit tests exercise the internal receipt function with independently invented fixtures.

## Scientific and licence barriers

- This particular Zenodo asset is descriptive statistics of modelled *still water levels*, not flood-inundation footprints, actual coastal building damage, tide-gauge measurements, insured values or stochastic CAT event losses.
- The accompanying 2026 study (https://essd.copernicus.org/articles/18/5759/2026/) identifies the statistics as detrended hourly total-water-level extreme values with 5%–95% confidence ranges and independent original time series in CDS DOI 10.24381/cds.a6d42d60. The full time series has separate identity, access and scope.
- Publication describes tidal/surge modelling and reference to 1986–2005 local mean sea level for the total-water-level series. The statistics are detrended. Do not attach these statistics to a local DEM, vertical datum or building altitude without an independent reference/geometry audit.
- The data's exact redistribution/commercial rights must be confirmed against current Zenodo rights metadata and any upstream CDS conditions. Public download is not an admission.
- A validated MD5, file signature and new SHA-256 **do not prove** NetCDF dimension names, value units, vertical datum, scientific fitness or source independence. These are separate next tests and no insurer/CAT input approval is implied.

## Execution evidence

Eight independently synthetic tests passed offline in the ChatGPT Linux environment on 2026-11-02. No real Zenodo bytes were acquired here because the execution environment's download connection was unavailable. Exact-head repository CI is the next check, and any original-data retrieval requires a separate reviewed, bounded acquisition action.
