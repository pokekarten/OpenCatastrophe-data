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

The new **branch-scoped live source metadata inventory** downloads
only these three original official DWD source archives. It validates
their exact original ZIP SHA against accepted #1564 TOML and inspects
at most three bounded source metadata text files per original archive.
For each, the one-off CI logs original member name, original member
SHA256, raw original byte count, line count and up to twelve short
lines, to establish the exact historical file structure.
It does not publish entire original FX hourly measurements or any
genuine insurer private site data.

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

Both DWD QN_8=3 (automatic source quality review, **not QN10**)
and the original independent three-stations / two-ERA5-grid-cell
count remain unchanged. The actual 2020 R&V insured locations and
claims, historical insured TIV, German vulnerability fit and native
Oasis/NextGen GUL/IL/RI/OEP/AEP/SCR are all **NOT ADMITTED**.
