<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara/Sabine 2020 – original-source-bound NRW portfolio vs normalized ERA5 NetCDF4

**Research engineering, 12 November 2026.** The accepted [NRW 10k source-bound request plan](ciara2020-nrw-10k-era5-10fg-area-request-20261112.md) requests an ERA5 hour-by-hour 10m gust area from the Copernicus Climate Data Store (CDS) for February 8–11 2020. This **code does not download provider weather files**, does not accept CDS terms, and does not claim any original supplier NetCDF has been inspected. This is a strictly separate **local normalization-and-receipt** interface for a future operator-provided NetCDF4 file. No model admission.

## Finite deterministic input envelope

- Four UTC calendar days beginning **2020-02-08 00:00**: 96 hourly time cells, monotonic integer sequence 0–95 under exact unit `hours since 2020-02-08 00:00:00`, `proleptic_gregorian`.
- NetCDF4/HDF5 only; exactly three dimensions and four variables: `time`, `latitude`, `longitude`, `i10fg`. Explicit metadata `i10fg.original_era5_variable = "10m_wind_gust_since_previous_post_processing"`, `units = "m/s"` or `"m s-1"`.
- 10 latitude nodes **52.50, 52.25, …, 50.25** and 16 longitude nodes **5.75, 6.00, …, 9.50**, 0.25° spacing, 160 grid nodes × 96 hours = 15,360 scalar gusts.
- Every wind cell must be finite, unmasked and in research-validation bound **0–150 m/s**; every coordinate and time cell must exactly match expected support. Missing values, daylight shifts, daily maxima, 10m U/V components, mismatched field names or units, shifted time units, extra dimensions, and symlinks are rejected.
- **Exact pinned original-source-derived fictitious OED ZIP** from 2022 public NRW building polygons (GitHub original full-source workflow run [#42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463)), 10,000 distinct *public building candidate* geocodes, 53 NRW Kreise, 93 occupied ERA5 grid cells, €4,826,029,500 **fictional original TIV**. The 10k ZIP's full byte SHA-256 and all source-derived CSV hashes are verified by the already merged input gate (PR #1494).
- Output is **one aggregate-only JSON** with local file byte SHA-256, finite/shape/time proof, 93 occupied source grid support digest, and fictional-TIV-in-wind-threshold summaries at 25/30/35/40 m/s. No physical polygons or fictional individual policies are written to the audit output.

## Run only on a reviewed, locally normalized NetCDF4

The exact structure of an original ERA5 *download* (NetCDF variable names, CF time encoding and archive container) has not yet been independently verified. Therefore the user/operator must **retain the original file and original SHA-256 separately** and explicitly normalize its verified, licensed hourly data into the documented strict `i10fg` structure. A direct raw-CDS parser must only be added after inspecting provider original bytes and documented transformation details; changing metadata is **not** proof of provider origin.

```bash
python -m pip install -r requirements-glofas-acquisition.txt
python research_runners/ciara2020_nrw_era5_normalized_netcdf_v0.py \
  /path/to/exact-archived-HU2022-derived-10k-OED.zip \
  /path/to/separately-reviewed-normalized-Ciara2020-10fg.nc \
  --receipt-json /tmp/ciara2020-nrw-netcdf-hazard-only-receipt.json
```

CI (no original-provider data, no credentials): pinned optional NetCDF4 dependency in the preexisting **GloFAS NetCDF4 acquisition** job runs the real synthetic NetCDF4 file writer/reader/adversarial tests:

```bash
python -m unittest tests.test_ciara2020_nrw_era5_normalized_netcdf_v0 -v
```

## Scientific and licensing NO-GO

The NetCDF normalized input **is not yet original CDS-source-attested**. Wind gusts from ERA5 reanalysis are meteorological hazard, **not actual insurer claims**. 2022 public building polygons are not individual R&V insured locations, and their 2025-like policy counts and TIV are fictional. The separate [German wind-loss source rights register](rva-germany-wind-loss-calibration-source-review-20261106.md) blocks actual native loss model admission. No independently matched EIOPA Ciara 2020 source claim denominator, roof/material/type fragility curve calibration, annual event-rate model, Oasis/NextGen GUL/IL/RI, OEP/AEP, capital rank or SCR is authorized by this NetCDF-only test.

Licence acceptance (Copernicus CDS CC BY) and original-data acquisition must be performed explicitly by an authorized human/account, with original file content/CRC and SHA-256, download URL/API parameters, timestamp, version and transformation provenance independently recorded. No CDS credentials, license-acceptance automation or third-party original source bytes are committed.
