<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara 2020: DWD measured three stations vs two public ERA5 0.25° cells

**14 November 2026, original-source research, NOT insured loss calibration.**

This experiment is a bounded and reproducible comparison of **three
independent original DWD measured hourly storm gust series** over
Feb 8–11 2020 and **Google Research publicly distributed ARCO ERA5
reanalysis original hourly 10fg gust peaks** over the same four
calendar days. A station-to-grid-centre assignment does **not**
make these quantities identical, nor establish actual 2020 insured
buildings, observed insurer damage, a spatially correct station
instrument calibration, or native Oasis/NextGen catastrophe losses.

## Verified source inputs

- DWD CDC original `FX_911` measured hourly peak gust, m/s, under
  **CC BY 4.0** with attribution to Deutscher Wetterdienst:
  https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/historical/
- Source archive, station metadata and observed 96-hour maxima are
  independently pinned from the successful original live
  [PR #1564](https://github.com/pokekarten/OpenCatastrophe-data/pull/1564).
  Source receipt:
  `research/observations/ciara2020_dwd_original_fx911_three_stations_receipt_20261113.toml`
- Original ERA5 96h×160 NRW grid from public Google Research
  ARCO ERA5, variable `10m_wind_gust_since_previous_post_processing`,
  **Copernicus Licence** with C3S attribution:
  `gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3`
  The original accepted decoded 96×10×16 float32 matrix SHA-256 is
  `5fb7c41963a94f88ee3651b51bfa84cc2f4bf379e1ee6f4eb4a4fb597d37f932`
  and the original Google four variable/coordinate metadata SHAs
  are independently re-checked by the accepted #1556 reader.

The comparator reloads **all three original DWD measured ZIPs**
(and rejects the known sparse fourth archive), matches their
unmodified ZIP SHA-256 against the accepted 2020 DWD source receipt,
and refetches the **complete actual 96h Google ERA5 grid** with
the exact original source, 160-node support and source-verified
float32 matrix SHA. It uses the *public* 2020/2022 research-only
meteorological data and does not load any insurer portfolios.

## Three stations ≠ three ERA5 spatial observations

The current DWD station list is not the authority for historical
coordinates. The original SHA-pinned DWD ZIPs contain date-versioned
geography and instrument metadata, now parsed and matched to their
original member SHA receipts in
`research/observations/ciara2020_dwd_original_historical_station_metadata_attestation_20261114.toml`.
The deterministic nearest-grid-centre, no-ties, <=20km mapping using
the locations valid during February 2020 is:

| Original DWD station | February 2020 site position | Nearest Google ERA5 0.25° node |
|---|---|---|
| Köln/Bonn, ID 02667 | 50.8645N, 7.1575E | **50.75N, 7.25E** |
| Wuppertal, ID 15200 | 51.2531N, 7.2157E | **51.25N, 7.25E** |
| Königswinter-Heiderhof, ID 00603 | **50.7350N, 7.1931E** | **50.75N, 7.25E** |

**Köln/Bonn and Königswinter-Heiderhof map to the same ERA5 node.**
Therefore three measured stations offer only **two** geographically
distinct gridded original 2020 event-max data values, not three
independent ERA5 samples. We must NOT claim independent model
validation simply by counting three different DWD sensors.

The first original DWD source 2020 peaks were **26.4 m/s**
(Köln/Bonn), **31.1 m/s** (Wuppertal), and **25.5 m/s**
(Königswinter-Heiderhof), all 96 original reported hourly values
with original **QN_8 = 3 (automatic QC)**; none had original
highest QN_8 = 10. A fourth station (ID 03623) was excluded after
an original SHA-verified archive had insufficient original 2020
measurements. The original DWD metadata verifies the February 2020
coordinates, sensor type/heights (10 m, 12 m, 10 m), and that FX_911
hour labels are **in UTC** and describe the highest gust in the last
hour. Königswinter-Heiderhof moved to the current position and a 12 m
sensor on 2020-10-01, after Ciara. Exact aggregation-window equivalence
to ERA5 remains unverified.

## Actual original-source result: first genuine 2020 live run

The first actual public-source reload **succeeded** in
[GitHub run 43603655228](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43603655228),
job **132473533297**. All three independently measured DWD
2020 original archive SHA-256s, QN_8=3 for 96 hours, and the
four Google public original Zarr metadata/decoded 96h×160
ERA5 10fg source values matched their earlier live research
receipts, including the original decoded SHA
`5fb7c41963a94f88ee3651b51bfa84cc2f4bf379e1ee6f4eb4a4fb597d37f932`.

| DWD original observed station | Source 2020 96h measured peak | Nearest Google ERA5 2020 modelled grid 96h peak | *Descriptive only* ERA5 minus DWD |
|---|---:|---:|---:|
| Köln/Bonn (02667) | 26.4 m/s | **31.169416427612305 m/s**, 50.75N/7.25E | **+4.769416 m/s** |
| Wuppertal (15200) | 31.1 m/s | **32.13789749145508 m/s**, 51.25N/7.25E | **+1.037897 m/s** |
| Königswinter-Heiderhof (00603) | 25.5 m/s | **31.169416427612305 m/s**, 50.75N/7.25E | **+5.669416 m/s** |

Distances from the original DWD geography valid in February 2020 to
the nearest original Google ERA5 grid centres are respectively
**14.295 km, 2.412 km and 4.337 km**. Köln/Bonn and Königswinter
**reuse one original ERA5 cell**.

The independently first-observed values and SHA-provenance
are versioned at
`research/observations/ciara2020_dwd3_era5_two_cells_original_peak_comparison_20261114.toml`.
The live CLI rejects any further source replay with changed
measured gust, original ZIP SHA, ERA5 cell, descriptive
difference or unapproved science flag rather than silently
turning it into a new historic benchmark.

## Scientific quarantine and legal bounds

The actual site measurement, the nearby modelled **0.25° cell
peak** and a descriptive signed difference can be displayed,
but are not a station-vs-ERA5 **same-hour forecast error**,
RMSE, bias, climatology, validated spatial interpolation,
insured windstorm loss or building vulnerability fit.
Original 2020 historical DWD `Metadaten_Geographie`,
`Metadaten_Geraete` and parameter time-reference definitions have
now been reviewed. Differences in elevation, land roughness,
measurement and reanalysis sampling are further limitations. DWD's
parameter metadata says `in UTC`; exact one-hour interval equivalence
with ERA5 post-processing remains unverified.
An original 2020 atmospheric ERA5 value is not a German insurer's
loss observation. The original 2022 NRW HU building candidates
and their 2025-like insurance TIV are fictional counterfactual
exposure only, not actual R+V policies.

DWD data **CC BY 4.0** and ERA5 data **Copernicus Licence**
are distinct legal regimes. The Apache-2.0 program source
licence does not override either dataset's source conditions.

### Reproducibility

Offline only, no API calls:

    python -m unittest tests.test_ciara2020_dwd_original_to_era5_station_peak_comparison_v0 -v
    python research_runners/ciara2020_dwd_original_to_era5_station_peak_comparison_v0.py --dry-run

Read original three DWD archives and 96 original Google ERA5
hours (requires reviewed optional `requirements-google-arco-2020-original-smoke.txt`):

    python research_runners/ciara2020_dwd_original_to_era5_station_peak_comparison_v0.py --live-original-station-grid

Only a bounded **PR-branch scoped public GitHub Actions original source
check** runs this live on the candidate branch. Do not merge based
on fixture-only tests, and do not mark scientific model approval
without real observed German insurer damage/coverage denominators
and validated time/spatial harmonization.
