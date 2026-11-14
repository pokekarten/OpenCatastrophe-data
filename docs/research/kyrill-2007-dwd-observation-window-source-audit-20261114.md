<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Kyrill 2007 original DWD station-window source audit

**Status:** live replay of original DWD observations and event-era station
metadata completed. This is source coverage evidence, not a model validation.

The XWS Kyrill source receipt identifies the event at 2007-01-18 15:00 UTC.
For a fixed context window, this audit reads the original DWD CDC hourly FX_911
archives from 2007-01-16 00:00 through 2007-01-19 23:00 UTC (96 hour labels) at
stations 02667 Köln/Bonn and 00603 Königswinter-Heiderhof. These long-record
stations were chosen from the previous Ciara source audit before reading the
Kyrill event-window gust values. DWD station-list, archive-index and archive
bytes are SHA-256 pinned in the
[`source manifest`](../../research/observations/kyrill_2007_dwd_station_hourly_source_v0.toml).

The original archive history uniquely covers geography, device and FX_911
parameter metadata over every hour in the window. Both stations have 96 valid
gust observations and all 96 have QN_8=3.

| Station | Historic position | Elevation | Sensor height AGL | 96h observed max FX_911 | Peak hour UTC |
|---|---|---:|---:|---:|---|
| 02667 Köln/Bonn | 50.8645 N, 7.1575 E | 90.91 m | 10 m | 36.0 m/s | 2007-01-18 19:00 |
| 00603 Königswinter-Heiderhof | 50.7350 N, 7.1931 E | 159 m | 12 m | 29.0 m/s | 2007-01-18 20:00 |

The second site's source-attested sensor was 12 m AGL in 2007; its February
2020 historical metadata records 10 m. Do not carry a fixed station height
backward across years. The two 2007 measurements are observations at point
stations and do not establish the gust everywhere in a grid cell or insured
loss footprint.

Replay the live official-source audit with:

```sh
python research_runners/kyrill_2007_dwd_station_hourly_source_v0.py \
  --live-original-dwd
```

The aggregate receipt omits all hourly rows. The original XWS Kyrill source
provides a separate 72-hour maximum 3-second gust footprint; no direct
station-to-XWS spatial or temporal pairing is claimed here. The Ciara 2020
ERA5 10fg reader currently covers a separate fixed date window, so no 2007
ERA5 comparison is included. Extending ERA5 to 2007 needs a source-pinned
time-range reader and historic station-to-grid mapping. This audit supplies
no frequency estimate, vulnerability curve, model correction, calibration,
insured loss, or annual EP metric.
