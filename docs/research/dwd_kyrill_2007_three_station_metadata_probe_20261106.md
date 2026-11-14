<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kyrill 2007: original DWD station geography and instrument metadata preflight

**Research-only, never science admission or calibration.** The three original historical DWD FX_10 gust archives were replayed in PR #1361 for stations 00433 (Berlin-Tempelhof), 01262 (Munich Airport), 03379 (Munich City). Their historical QN distributions are unequal: 00433/01262 are QN1, 03379 QN3 in the Jan 17–20, 2007 holdout. Source-specific station settings, location and measurement-height **valid on 2007-01-18** have not yet been proven, and no station is identical to the fictional CLIMK model marker.

## Primary DWD documentation and quality meanings

Official 10-minute extreme wind description: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/DESCRIPTION_obsgermany_climate_10min_extreme_wind_en.pdf

- QN=1 is **formal checking only**, QN=2 is individual criteria, and QN=3 is **automated checking and correction**. DWD warns that QN1 ten-minute values can have significant errors. A file living under `historical/` does **not** turn a QN1 observation into QN3.
- FX_10 is the 10-minute maximum gust of the **preceding interval**, with the time label at interval end, UTC after year 2000. It is not automatically the same temporal/statistical operator as the CLIMK event-wide ERA5 grid maximum.
- DWD describes `Meta_Daten_zehn_min_fx_<STATION>.zip` archives per station in `meta_data/` containing station geography, instruments, sensor height, parameters and station-name history: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/meta_data/

## Implemented original metadata-shape probe

The runnable `scripts/dwd_kyrill_2007_station_metadata_probe_v0.py` processes **three original station metadata ZIPs** (00433, 01262 and 03379). It bounds ZIP and expanded sizes, rejects path traversal, symlinks, duplicate or missing geography/device/parameter sources, reads CRC, records ZIP/member SHA-256 hashes, checks encoding, and emits **only short public metadata line previews**. It does **not** export raw wind observations or original ZIPs. Corresponding isolated adversarial tests cover malformed and manipulated archive cases. GitHub Actions workflow `.github/workflows/dwd-kyrill-2007-three-station-metadata-shapes.yml` downloads the three original files to an ephemeral temporary directory and removes them after the run.

This first, **schema-discovery** execution cannot prove a time-valid 2007 instrument or geographic observation point: archive content and relevant temporal interval fields must be inspected before building a strict valid-on-2007-01-18 join. Therefore `source_2007_instrument_validity_resolved`, `source_2007_station_geography_resolved` and `source_2007_sensor_height_resolved` stay **false**. QN1 stays QN1; all vulnerability calibration, spatial dependence fitting, annual event rates, AAL/AEP/OEP and SCR remain out of scope. Next step: use exact authentic metadata schema to implement a source-locked, conflict-aware 2007 temporal validity join and independently check against CLIMK model grid semantics.

## Original-source valid-on-2007 follow-up — successfully replayed

The initial schema probe confirmed the real provider layout: there are multiple instrument metadata files (.txt plus .html), not precisely one `Metadaten_Geraete` file per station. Therefore the first one-of-each assumption was correctly removed as a **discovery-only** classification check; incomplete or ambiguous shape remains explicitly not science-admitted.

The separate `scripts/dwd_kyrill_2007_station_validity_v0.py` now uses exactly three `*.txt` sources per station, including `Metadaten_Geographie`, `Metadaten_Geraete_Windgeschwindigkeit_Maxwind` and `Metadaten_Parameter` for **FX_10**, and requires one and only one interval covering the entire 2007-01-17 through 2007-01-20 window for each. All original ZIP SHA-256 hashes are frozen. Exact source geography, station altitude, instrument class and sensor height must match the independently reviewed DWD result, with a small bounded check of device-versus-geography rounding.

[Original provider source execution](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42246305755) proved three distinct historical locations and sensors; the later [strict source-evidence replay](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42246731206) completed **success**. The pinned machine-readable output, three archive SHA-256 values, individual member hashes and time validity intervals are retained in `docs/research/evidence/dwd-kyrill-2007-three-station-history-source-receipt-20261106.md`. A new workflow step checks the exact full JSON against this receipt each time original metadata bytes are fetched. Original ZIPs and raw gust observations remain outside Git.

Scientific interpretation: **Berlin-Tempelhof 10 m/QN1**, **Munich Airport 10 m/QN1**, **Munich City 29.28 m/QN3**. These QN flags originate from the **separate, earlier original FX_10 observation archives**, not the metadata ZIP; the latter establishes historical sensor/geography validity only. Geographic distance from our deliberately fictional CLIMK points is approximately 5.84/29.84/4.26 km respectively. Thus source history is verified, but a matched-grid wind-model performance estimate or adjustment for 29.28 m is not. No observed building loss, frequency, insurer expected loss or annual EP is implied.
