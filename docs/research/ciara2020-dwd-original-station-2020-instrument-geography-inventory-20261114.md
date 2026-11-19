<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara 2020 DWD: genuine historical geography / device / FX parameter metadata

Following the genuine original 2020 wind peak comparison
[PR #1570](https://github.com/pokekarten/OpenCatastrophe-data/pull/1570)
and independent 2020 DWD original historical FX_911 archives
[PR #1564](https://github.com/pokekarten/OpenCatastrophe-data/pull/1564),
the primary unresolved scientific question is **DWD 2020 station
position, anemometer sensor type/height and exact hourly reference
time support**. Comparing event-maximum measured station gust
to gridded modelled ERA5 gust *does not* resolve these.

The **official DWD CDC hourly extreme wind product format**
[version v24.03](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/BESCHREIBUNG_obsgermany_climate_hourly_extreme_wind_de.pdf)
says the `FX_Stundenwerte_Beschreibung_Stationen.txt`
station coordinates represent the **current** positions. The original
station ZIPs contain `Metadaten_Geographie*` (history of geographical
coordinates/elevation), `Metadaten_Geraete*` (instrument, height,
measurement procedures), and `Metadaten_Parameter*` (units,
measurement time conventions, dates), plus hourly `produkt_*.txt`.

The DWD source uses **CC BY 4.0** with DWD attribution, not the
**Copernicus Licence** governing Google Research ARCO ERA5.
The already SHA-proven three original DWD FX station ZIPs are:

- 02667, Köln/Bonn, original ZIP SHA
  `e88536b7eebb6c7f94de63de56b1af85a0981fdd769e727f45f6d7db7c93ae78`
- 15200, Wuppertal, original ZIP SHA
  `748ffdbc8f6ebf04a014ebf3d8fdc177e9a903349cc5b36e19f4c425998bfaa0`
- 00603, Königswinter-Heiderhof, original ZIP SHA
  `4a61a6394344bba05a06553794ac1a2d5edb4c4e3ac39ae1f26407e5f4e2f62b`

## Historical metadata from genuine first live ZIP inspection

The actual official DWD source metadata inventory **succeeded**
in GitHub run [43605892890](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43605892890),
live job **132480458101**. Exactly three unmodified DWD hourly-FX
source ZIPs passed their previously accepted original archive SHA-256.
The source original subfiles `Metadaten_Geographie_*`,
`Metadaten_Geraete_Maxwind_*` and
`Metadaten_Parameter_fx_stunde_*` exist for all three, with
**nine original separate member SHA-256s** now pinned in
`research/observations/ciara2020_dwd_original_historical_station_metadata_attestation_20261114.toml`.

The actual publisher **February 8–11, 2020** metadata rows are:

| Station | Actual source 2020 latitude/longitude | DWD station altitude | FX sensor above ground | Original instrument valid across all four days |
|---|---|---:|---:|---|
| Köln/Bonn 02667 | 50.8645N, 7.1575E | 90.91m | **10m** | Windsensor Classic 4.3303 (DWDSYN), 2018-01-22–2026-04-19 |
| Wuppertal 15200 | 51.2531N, 7.2157E | **327m** | **12m** | Ultrasonic Anemometer 2D, 2013-06-01–2020-11-04 |
| Königswinter-Heiderhof 00603 | **50.7350N, 7.1931E** | **159m** | **10m** | Windsensor Classic 4.3303, 2019-10-02–2020-09-30 |

**Critical correction**: Königswinter-Heiderhof was relocated on
**2020-10-01**, *after* the Ciara event, to the more recent
50.7293N / 7.2040E metadata position, with site elevation
147.17m and a new **12m** ultrasonic wind anemometer. The
comparison in merged #1570 used that *current* position, not the
historically correct 2020 site. Both sites still nearest-map to
Google ERA5 50.75N/7.25E but the historical site-to-ERA5
distance becomes **4.337km**, not the previous **3.972km**.
Other station-era5 distances remain 14.295km (Köln/Bonn) and
2.412km (Wuppertal).

The **original DWD parameter member** explicitly says
`FX_911` = *highest wind gust of the previous hour* with unit
`m/sec` and **`Zusatz-Info: in UTC`** for all three 2020
coverage intervals. This establishes the official DWD reference
time convention, while the exact equivalence of the original
DWD physical instrument rolling measurement period and ERA5
model post-processing remains **unverified**. It does not on its
own validate any 2020 wind-event damage observations.

The follow-on fail-closed parser
`research_runners/ciara2020_dwd_historical_feb2020_station_attestation_v0.py`
reads the actual original source ZIP files, checks full ZIP SHA
and all nine original metadata member SHA pins, enforces one
unambiguous geography/device/parameter source-valid row spanning
**2020-02-08 to 2020-02-11**, checks sensor height/geography/
parameter values against the observed frozen TOML attestation,
and refuses source drift.

The new **branch-scoped live source metadata inventory** downloads
only these three original official DWD source archives. It validates
their exact original ZIP SHA against accepted #1564 TOML and inspects
at most three bounded source metadata text files per original archive.
For each, the one-off CI logs original member name, original member
SHA256, raw original byte count, line count and up to twelve short
lines, to establish the exact historical file structure.
It does not publish entire original FX hourly measurements or any
genuine insurer private site data. The subsequent independent exact-SHA
attestation command validates the **actual February 2020** source
geography, sensor height/device and original DWD FX UTC field.

**This is discovery rather than historical matching**: source
metadata lines remain uninterpreted until the file structure is
observed. An independent follow-on test can then parse dates,
geography, device/measurement-height and timestamp standards for
the 2020 Ciara period, with fail-closed interval selection and
source provenance. No timewise DWD/ERA5 bias, RMSE, geography
calibration or vulnerability is currently approved.

Run no network:

    python -m unittest tests.test_ciara2020_dwd_original_2020_station_metadata_inventory_v0 -v
    python research_runners/ciara2020_dwd_original_2020_station_metadata_inventory_v0.py --dry-run

Run bounded official public DWD originals:

    python research_runners/ciara2020_dwd_original_2020_station_metadata_inventory_v0.py --live-original-metadata

    python -m unittest tests.test_ciara2020_dwd_historical_feb2020_station_attestation_v0 -v
    python research_runners/ciara2020_dwd_historical_feb2020_station_attestation_v0.py --live-feb2020-attestation

Both DWD QN_8=3 (automatic source quality review, **not QN10**)
and the original independent three-stations / two-ERA5-grid-cell
count remain unchanged. The actual 2020 R&V insured locations and
claims, historical insured TIV, German vulnerability fit and native
Oasis/NextGen GUL/IL/RI/OEP/AEP/SCR are all **NOT ADMITTED**.
