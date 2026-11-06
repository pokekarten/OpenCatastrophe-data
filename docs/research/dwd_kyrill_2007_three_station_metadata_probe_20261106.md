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
