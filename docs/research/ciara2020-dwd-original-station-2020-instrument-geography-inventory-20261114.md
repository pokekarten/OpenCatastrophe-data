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

The bounded metadata inventory first hashed the exact geography,
device and parameter members in each original SHA-pinned ZIP. The
follow-on attestation then parsed the publisher's schemas, selected
exactly one metadata period covering all four Ciara dates, and matched
those fields to the already accepted member SHA receipt. This session
also replayed that parser offline against all three acquired original
ZIPs; the event-period result matched the committed attestation values.
Raw hourly files and source ZIPs remain outside Git.

## Verified February 2020 source metadata

| Station | Historical site position | Site elevation | Sensor above ground | Instrument | Nearest ERA5 cell / distance |
|---|---:|---:|---:|---|---:|
| Köln/Bonn (02667) | 50.8645N, 7.1575E | 90.91 m | 10 m | Windsensor Classic 4.3303 (DWDSYN) | 50.75N, 7.25E / 14.295 km |
| Wuppertal (15200) | 51.2531N, 7.2157E | 327 m | 12 m | Ultrasonic Anemometer 2D | 51.25N, 7.25E / 2.412 km |
| Königswinter-Heiderhof (00603) | 50.7350N, 7.1931E | 159 m | 10 m | Windsensor Classic 4.3303 | 50.75N, 7.25E / 4.337 km |

The DWD parameter metadata for all three stations describes `FX_911`
as the highest wind gust in the previous hour, in m/s, with the hour
reference **in UTC**. For Königswinter-Heiderhof, the February 2020
position and 10 m instrument height were valid through 2020-09-30;
the currently listed position and 12 m instrument are effective from
2020-10-01. Using today's location for the February comparison would
therefore be wrong by roughly one kilometre.

The source establishes DWD's UTC hour labels and station metadata.
It does **not** establish that the DWD one-hour maximum and ERA5
`10m_wind_gust_since_previous_post_processing` use exactly identical
hour windows or equivalent exposure/height. The stations map to only
two independent ERA5 grid nodes, and the three event maxima remain
descriptive checks; no same-hour bias, RMSE, climate skill, or gust
height correction is admitted. No insurer loss or vulnerability
calibration is admitted.

Run no network:

    python -m unittest tests.test_ciara2020_dwd_original_2020_station_metadata_inventory_v0 -v
    python -m unittest tests.test_ciara2020_dwd_historical_feb2020_station_attestation_v0 -v
    python research_runners/ciara2020_dwd_original_2020_station_metadata_inventory_v0.py --dry-run

Run bounded official public DWD originals:

    python research_runners/ciara2020_dwd_original_2020_station_metadata_inventory_v0.py --live-original-metadata

Both DWD QN_8=3 (automatic source quality review, **not QN10**)
and the original independent three-stations / two-ERA5-grid-cell
count remain unchanged. The actual 2020 R&V insured locations and
claims, historical insured TIV, German vulnerability fit and native
Oasis/NextGen GUL/IL/RI/OEP/AEP/SCR are all **NOT ADMITTED**.
