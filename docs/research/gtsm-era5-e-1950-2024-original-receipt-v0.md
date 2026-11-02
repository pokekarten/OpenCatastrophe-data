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

## Original native NetCDF structural evidence (2026-11-02 21:01:44 UTC)

Exact-head GitHub Actions GTSM run [41524452571](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41524452571) completed successfully after independent fixed SHA-256, size and provider-MD5 verification; the header was read with pinned `netCDF4` without sampling a single variable value. The original contains precisely **38,957** station entries, **8** return-period slots and **7** quantile slots. Those **38,957** entries are an original file dimension, not an independently verified count of all 44,734 GTSM simulation locations mentioned in the paper. Do not equate them.

Confirmed original variables and storage: `lon`/`lat` int32 with coordinate units `degrees_east`/`degrees_north`; `stations` uint16; `return_period` int64 with units `years`; `wl_quantiles` float32 on quantile×station with metres; `wl_extreme_bestfit`, `wl_extreme_5perc`, `wl_extreme_95perc` float64 on station×return_period with metres; and `eva_param_scale`, `eva_param_shape`, `eva_param_loc` float64 by station. The quantile and return period *values* have not been read and cannot yet be certified as specific numerical slots from NetCDF, even if the provider describes them.

**Important:** int32 longitude/latitude require exact native `scale_factor`, `add_offset`, missing-value metadata and spatial bounding checks before use in site joins. The next profile inventories coordinate packing *attributes only*. Coordinate unpacking, projection/datum compatibility and uncertainty calibration remain blocked. The field-level native axes/types/units gate is a source-vintage drift detector, not scientific admission. No storm events, spatial footprints or observations should be fabricated from these return-period vectors.

The paper describes a hydrodynamic-model coastal output point set, whereas these statistical results are an independently selected 38,957-row NetCDF station axis. Reconcile missing/excluded locations and dependence on prior GTSM/WRI Aqueduct coastal products before treating them as independent validations. Study: https://essd.copernicus.org/articles/18/5759/2026/ .

## Pinned native coordinate packing (2026-11-02 21:04 UTC)

The successful exact-head original-source run [41524827932](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41524827932) confirmed source MD5 and independent pinned SHA-256 again, plus **18** successful offline regression tests. The NetCDF native `lon` and `lat` variables are `int32`; both have the **metadata-only** packing attributes `scale_factor = 0.001`, no `add_offset`, and `_FillValue = -999`. These exact attributes are now fail-closed invariants in the next revision. The raw coordinate and return-period arrays remain unread in this research pass.

A downstream coordinate transform must mask the native fill code before applying the scale factor and independently check geographic ranges, indexing, axis units, coordinate duplicates, and any source/epoch mismatch; **no site-to-building join is authorized by this metadata receipt**. Also assess time-varying datum, coastal-model output-point semantics and 38,957-vs-44,734 coverage before defining coastal exposure.

## Execution evidence

The complete real-source receipt of 2026-11-02 is verified from exact-head runner logs (run #41507598794, job #125490753179); 12 synthetic boundary tests and Python 3.11–3.14 matrix passed. The following revision pins the independently observed SHA-256, reproduces the original native metadata from the GitHub run above, and adds a version-specific dimension/axis/unit/type gate. The next exact-head CI and header-inventory capture remain required before accepting the stricter gate. The earlier receipt did not inspect the NetCDF variables. No model admission, permission for commercial reuse, raw file retention or event generation is implied.
