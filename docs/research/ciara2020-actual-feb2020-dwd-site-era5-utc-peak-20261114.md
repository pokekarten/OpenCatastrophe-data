<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara 2020: fix the DWD–ERA5 event-max comparison to actual February 2020 sites

**14 November 2026. Source-verified independent research; no insurer-model calibration.**

The first original measured three-DWD-station vs two actual 0.25° Google-ERA5 grid-cell 2020 Ciara event maximum comparison was merged as [PR #1570](https://github.com/pokekarten/OpenCatastrophe-data/pull/1570). It used DWD's *currently published* station locations, because historical metadata had not yet been read. **Do not overwrite its original-source receipt:** it still faithfully captures what that first methodological attempt measured.

Follow-up [PR #1571](https://github.com/pokekarten/OpenCatastrophe-data/pull/1571) independently acquired all three original historical DWD ZIPs, confirmed their original ZIP SHA-256 and **nine** geo/device/FX parameter metadata member SHA-256s, and established the exact **February 8–11, 2020** source-valid rows. This V1 comparison instead uses those February 2020 sites and instruments, and keeps PR #1570's source record immutable.

## The actual DWD source-valid 2020 stations

| DWD ID | 2020 station location | Terrain height | Wind sensor height above ground | Original source 2020 instrument | Nearest original ERA5 0.25° node |
|---|---|---:|---:|---|---|
| 02667 Köln/Bonn | 50.8645N, 7.1575E | 90.91 m | 10 m | Windsensor Classic 4.3303 (DWDSYN) | 50.75N, 7.25E; 14.295 km |
| 15200 Wuppertal | 51.2531N, 7.2157E | 327 m | **12 m** | Ultrasonic Anemometer 2D | 51.25N, 7.25E; 2.412 km |
| 00603 Königswinter-Heiderhof | **50.7350N, 7.1931E** | **159 m** | **10 m** | Windsensor Classic 4.3303 | **50.75N, 7.25E; 4.337 km** |

The original historical records prove that Königswinter-Heiderhof's 50.7293N, 7.2040E current position and newer **12 m** ultrasonic instrument took effect on **2020-10-01**, *after* Ciara 2020. The old comparison used the newer 3.972 km cell distance; the actual 2020 site is at **4.337 km** from the same nearby ERA5 cell. The weather grid cell and all source-verifiable gust magnitudes **do not change** when fixing this location.

The original DWD 2020 `Metadaten_Parameter_fx_stunde_*.txt` for all three stations explicitly defines `FX_911` as *hoechste Windspitze der letzten Stunde*, `m/sec`, `in UTC`. ECMWF's official [ERA5 data documentation](https://confluence.ecmwf.int/pages/viewpage.action?pageId=155343959) specifies that its **hourly high-resolution reanalysis** surface minimum/maximum fields record the maximum in the *hour ending at the validity time*; its 10-m gust is a maximum since previous post-processing. Therefore the DWD source reference labels and the ERA5 validity times have a **nominally compatible UTC hour-ending** definition. This still does **not** prove that the physical DWD anemometer sensor and gridded modelled 3-second gust use the same numerical sampling/measurement methods.

## Previous source-validated 2020 event peak magnitudes (unchanged)

| DWD 2020 observed gust maximum | Original DWD FX911 event maximum | Original ERA5 nearest 96h cell maximum | Descriptive peak difference ERA5 minus DWD |
|---|---:|---:|---:|
| Köln/Bonn 02667 | 26.4 m/s | 31.169416427612305 m/s | +4.769416 m/s |
| Wuppertal 15200 | 31.1 m/s | 32.13789749145508 m/s | +1.037897 m/s |
| Königswinter 00603 | 25.5 m/s | 31.169416427612305 m/s | +5.669416 m/s |

These are **three independently observed station maxima but only TWO independent model grid-cell maxima**. They do not necessarily occur in the *same hour*. Each DWD peak has its own source-attested UTC ending-hour label (and the preceding-hour interval can now be stated), but the corresponding ERA5 gust at that *same hour* is **not yet retrieved as a station-paired 96-hour series** by this comparison. Hence no same-hour bias, RMSE, measured skill, spatial interpolation quality, building damage or insurer loss is admitted.

## Real first-live historical-site source proof

The genuine public-source research job **succeeded** on
[GitHub run #43608886802](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43608886802),
job **132489320449**. It re-read original DWD FX911 measured 2020
station ZIPs and all nine historically valid original DWD source
geography/instrument/parameter SHA files, and the original 96h×160
Google Research ARCO ERA5 10fg source matrix. Every 2020 source
identity and peak magnitude reproduced without modification.
Original Kelvin/precipitation/mean wind was **not** substituted.

This actually replayed result is frozen in
`research/observations/ciara2020_dwd2020_historic_sites_to_two_era5_utc_peaks_v1.toml`.
The live runner performs a second fail-closed comparison to the exact
first real-source site, sensor, DWD source ZIP, original ERA5 peaks,
reported DWD previous-hour UTC interval and original source-science
NO-GO flags; a future provider refresh that changes evidence must
be explicitly reviewed rather than silently overwriting historical
facts. The original #1570 first-current-site comparison remains
unchanged for provenance.

## Code, legal status and scientific controls

- `research_runners/ciara2020_dwd_historic_sites_era5_utc_peak_v1.py` first repeats the originally accepted [#1570](https://github.com/pokekarten/OpenCatastrophe-data/pull/1570) source and peak receipt without modification, then checks the independently original-source historical 2020 station metadata from [#1571](https://github.com/pokekarten/OpenCatastrophe-data/pull/1571). It validates full DWD original archive identities, nine original historical geo/device/parameter member SHA-256s, 96h original Google ARCO source digest, **historical** station-to-cell distances, and nominal UTC hour-ending labels.
- Offline fixtures cover the accidental use of the October-2020 Königswinter relocation, false 12m sensor, tampered original SHA, unapproved wind-model calibration, hour-label out-of-window and geography cell ties.
- One branch-scoped CI job re-fetches the **actual original public DWD station ZIPs and full 96h Google original ERA5 10fg reanalysis**. No credentials or original/raw ZIPs are committed or uploaded.
- DWD CDC FX observations: **CC BY 4.0** with Deutscher Wetterdienst attribution. Original Google ARCO ERA5 reanalysis: **Copernicus Licence** with attribution to C3S and Google Research. Software code is separately Apache-2.0. Dataset rights do not follow from the software licence.
- The historical 2020 **real R&V insured site universe, covered 2020 exposures and observed claims, wind-vulnerability curve, original native Oasis/NextGen GUL/IL/RI, annual OEP/AEP/SCR remain NO-GO**. Public 2022 HU building candidates and fictional TIV are not actual insurer policies.

Offline dry run:

    python -m unittest tests.test_ciara2020_dwd_historic_sites_era5_utc_peak_v1 -v
    python research_runners/ciara2020_dwd_historic_sites_era5_utc_peak_v1.py --dry-run

Live genuine source repeat after installing reviewed original-Zarr reader requirements:

    python -m pip install -r requirements-google-arco-2020-original-smoke.txt
    python research_runners/ciara2020_dwd_historic_sites_era5_utc_peak_v1.py --live-historic-site-peaks

**Next scientifically meaningful experiment**: read exact original hourly DWD FX911 station series and the corresponding two **original** Google ERA5 cell gust hourly series with UTC hour pairing, filter QN_8 and incomplete hours, and analyze three-station dependence on two shared model cells. Preserve distinct sensor heights and terrain without claiming damage calibration.
