<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLIMK Kyrill 2007: source-native ERA5 grid at three **real DWD stations**

**Research-only.** This experiment is neither an independently validated wind-model residual nor observed building/insured loss, fitted vulnerability, annual storm frequency, AAL/AEP/OEP or regulatory capital.

## Scientific problem

The original CLIMK v2 ERA5 Kyrill one-event pilot sampled two **fictional city markers** (Berlin 13.4050/52.5200, Munich 11.5820/48.1351), each with twelve fictional insured buildings. Comparing those modelled gusts to historical **actual** DWD instruments at *different coordinates* is spatially mismatched. The DWD observations are a maximum 3-second gust within each preceding 10-minute interval, with the timestamp at its end; CLIMK stores a modelled maximum associated with an entire storm footprint. The two measures are not automatically identical. Nor is an ERA5 cell center equivalent to a specific meteorological station in a different terrain/exposure environment.

## Independent source fingerprints

The source NetCDF is CLIMK-WINDS v2 ERA5 storm index 0 (`KYRILL`), SHA-256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`. The three separately verified *DWD original metadata and original observed daily-gust receipts* are pinned by their exact Git blob SHA-1 values:

| Source | Source proof Git blob SHA-1 |
|---|---|
| DWD original historical three-station geography, instrument and valid-on-date source proof | `7e87179d21a217d7a9d6f14e998c484865d05321` |
| DWD Berlin-Tempelhof original FX_10 source proof | `20ac79115e60beb6a8124789cf02956992b39e86` |
| DWD two Munich original FX_10 source proof | `dace35c11ac5272797662ea2860bdb768e080462` |

Relevant historical source-validated DWD station coordinates and heights (longitude/latitude, not the synthetic city markers): Berlin-Tempelhof 00433 (13.4021°, 52.4675°, 10 m / QN1), Munich Airport 01262 (11.8078°, 48.3574°, 10 m / QN1), Munich City 03379 (11.5429°, 48.1632°, 29.28 m / QN3). Reported 18 January 2007 observed gust maxima were 33.5, 33.0 and 29.0 m/s, respectively. Quality flags originate from the **observation archives**; heights/coordinates/validity from **independent historical metadata ZIPs**.

**Essential distinction:** We must NOT pass real DWD station coordinates into the existing `oc-effis-synthetic-sites-v0` *synthetic-only* loader, because doing so mislabels public meteorological stations as fictional insurance locations. The new `scripts/dwd_climk_kyrill_station_grid_holdout_v0.py` therefore opens the original SHA-256-pinned CLIMK NetCDF directly and reuses the same strict monotonic native-grid nearest-center helper and physical-wind reader logic. It reads *three station coordinates* and *two separately labelled fictional reference markers*, checks the original published storm name/date and source hash, then produces three small aggregate station-to-grid results only. It explicitly reports whether the DWD station and fictional city marker resolve to the same native cell (never assumed in advance), and the distance of the station to the **actual model grid center**. The raw NetCDF and DWD gust observation rows are never committed or uploaded as artifacts.

## Reproducibility and acceptance

Synthetic fixture tests (do NOT claim original source bytes were used):

```sh
python -m unittest tests.test_dwd_climk_kyrill_station_grid_holdout_v0 -v
```

The additional `.github/workflows/dwd-climk-kyrill-2007-station-grid-holdout.yml` reads the unchanged pinned original CLIMK NetCDF through the existing provider acquisition, verifies original source-receipt Markdown Git blobs, and refuses any source-station quality/height mismatch. The output contains only original **station-location-specific native ERA5 cells**, their storm-wide modelled gusts, model center distance, historical DWD measured daily gust maximum and categorical science limits. **Only a successful run of this exact workflow on its checked-out commit proves actual re-sampling.**

Even after successful source sampling, the reported `observed minus model` value is **descriptive only**: different time operators, station exposure, instrument height and grid-center displacement remain. Do not fit a CLIMK bias or a damage curve; do not infer any annual frequency or AAL/AEP/OEP. Original building losses and insurer exposure remain absent.
