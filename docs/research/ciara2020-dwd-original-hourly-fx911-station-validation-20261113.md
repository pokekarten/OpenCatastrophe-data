<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara/Sabine 2020: DWD original measured hourly FX_911 validation source

**13 November 2026.** Following the source-verified Google Research
ARCO ERA5 96-hour 10fg meteorological reanalysis for 160 NRW grid
nodes and the source-verified HU22 2022 10k fictional-TIV 93-cell
counterfactual in merged
[PR #1559](https://github.com/pokekarten/OpenCatastrophe-data/pull/1559),
this is an **independent observed-weather source** rather than a
new vulnerability or insurer-loss function.

## Official sources, variable and rights

- DWD CDC original historical hourly **extreme_wind** publisher directory:
  https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/historical/
- Official historical station listing:
  https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/historical/FX_Stundenwerte_Beschreibung_Stationen.txt
- Original data format / quality / provenance:
  https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/BESCHREIBUNG_obsgermany_climate_hourly_extreme_wind_de.pdf
  (DWD original format description v24.03, March 2024).
- Official dataset terms:
  https://opendata.dwd.de/climate_environment/CDC/Nutzungsbedingungen_German.txt
  **Creative Commons BY 4.0 (CC BY 4.0)**. DWD attribution,
  source/version and indication of changes required for reuse.
- DWD parameter `FX_911` = **maximum hourly measured wind gust**,
  unit **m/s**; `QN_8` = provider quality assessment;
  `MESS_DATUM` = publisher hourly reference timestamp
  `YYYYMMDDHH`; DWD missing marker `-999`.
  **Not** DWD `FF` ten-minute mean wind speed and **not** ERA5
  `10m_wind_gust_since_previous_post_processing` source data.
  The original physical instrument/time windows differ from ERA5's
  modelled gridded hourly postprocessing maxima.

## First independent source challenge

One small, **PR-branch-scoped**, read-only GitHub Actions job uses
the Python standard library only (no personal API token).
It downloads the publisher's current station listing and official
historical ZIP-directory index, filters stations with data spanning
February 8–11, 2020, and examines **at most the twelve closest geographically eligible
historical station archives** to original ERA5 grid centre (51N, 7E),
within 120km and the NRW 2020 study rectangle. It admits exactly the
**three nearest stations with >=48 valid original FX_911 hourly values
in the 96-hour Ciara window**, records rejected original archive
SHA/identity when data are too sparse, and fails closed if no three
qualify. A DWD archive covering 2020 by *filename* alone is not
proof of 2020 hourly observations.

For each of three stations the job obtains **one official historical
FX ZIP**, verifies the DWD original exact HTTPS host/path and ZIP
member boundaries, hashes **original unmodified ZIP bytes**, parses
only its original `produkt_*.txt` hourly measurements, rejects
duplicate times, station ID drift, mean wind substitution, bad gust
units, unbounded values and missing-value-as-zero substitution.
It reports the maximum **measured station gust** across the date
window, the publisher's timestamp of that maximum, observed/missing
hour counts and the distribution of `QN_8` quality codes.
It prints **only three aggregated station measurements and source
SHA-256 evidence**, not the raw historical long time series or
source ZIPs. The ZIPs are ephemeral in GitHub-runner memory.

Commands:

    python research_runners/ciara2020_dwd_hourly_fx_original_station_observations_v0.py --dry-run

    python research_runners/ciara2020_dwd_hourly_fx_original_station_observations_v0.py --live-dwd

## Actual DWD historical observed-source result

The **original** official DWD CDN/CDC hourly `FX_911` measured gust
archives were acquired in genuine GitHub CI run
[43499602678](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43499602678),
live job **132144371691**. Four source ZIP archives were examined;
one (station `03623`, ZIP SHA
`d2503e4f4c1ff3860d7b9d0f73bd382cb9f08f62068772695878db7bc1ad98f6`)
had insufficient valid 2020 hourly gusts and was **rejected**.
Three distinct original observed stations passed all 96 calendar
hours without `-999` missing values:

| 2020 observed DWD station | Original ID | 2020 96h observed peak (m/s) | DWD-reported peak-hour label | Original archive ZIP SHA-256 |
|---|---|---:|---|---|
| Köln/Bonn | `02667` | **26.4** | `2020021008` | `e88536b7eebb6c7f94de63de56b1af85a0981fdd769e727f45f6d7db7c93ae78` |
| Wuppertal | `15200` | **31.1** | `2020020922` | `748ffdbc8f6ebf04a014ebf3d8fdc177e9a903349cc5b36e19f4c425998bfaa0` |
| Königswinter-Heiderhof | `00603` | **25.5** | `2020021009` | `4a61a6394344bba05a06553794ac1a2d5edb4c4e3ac39ae1f26407e5f4e2f62b` |

All three accepted stations reported **96 original hours each, QN_8=3**
in all 96. DWD documents QN_8=3 as **automatic check/correction**,
not completed highest quality (QN=10). The station metadata
coordinates may reflect *current* location and cannot yet substitute
for historical 2020 instrument/geography metadata.
**Do not attribute an hourly UTC interpretation** to these
reference time labels before verifying station-specific documentation.

Publisher station-list original SHA:
`da71a04670608512719703cbfafa9367fbd8b21b74d2e2275a663c58f5775ed0`;
original archive index SHA:
`4299666e67be6bd7a2854a2bb291d7619f17f84122d306248485c6a0dbf5bcb0`.
All three unmodified **ZIP byte** SHA-256 digests and the genuine
peak/quality observations are frozen in
`research/observations/ciara2020_dwd_original_fx911_three_stations_receipt_20261113.toml`.
The live CLI rechecks its observed original archive identities,
the 96-hour QN3 series, missing markers, peak magnitudes and
three source references against the first independent live proof;
source/quality drift raises NO-GO instead of silently passing.

**This is independently observed station meteorology, NOT validation
of insured building damage**. A future observed-to-reanalysis
comparison needs exact 2020 station altitude/anemometer exposure,
timestamp alignment and nearest ERA5 cell matching, not a naive
comparison of maxima from different physical sites.

## Critical science and source-use gates

1. Official station listing reports **current** station coordinates.
   Historical 2020 station-site identity, changes in height and
   anemometer/instrument exposure need checking against the original
   ZIP's `Metadaten_Geographie`, `Metadaten_Geraete` and
   `Metadaten_Parameter` files before geographic/time harmonization.
2. No assertion that DWD `MESS_DATUM` matches the hourly timestamp
   convention of Google ARCO ERA5; this is a **date-window peak only**
   comparison candidate until original measurement end/start and UTC
   semantics are verified. No invented pointwise error/skill metrics.
3. Quality code `QN_8` is preserved as a distribution; missing
   `FX_911=-999` is missing, not zero; completeness below 48
   valid out of 96 requested source hours is rejected. A partially
   observed 96h period cannot prove the full event maximum.
   The first genuine live source challenge encountered just such an
   incomplete station and therefore correctly returned NO-GO;
   a bounded nearest-12 station search now handles this explicitly.
4. Station observations and ECMWF/C3S atmospheric **reanalysis** differ
   in height, exposure, spatial support, time semantics and gust
   measurement/postprocessing, so compare only with explicit matched
   methodological normalization and local site metadata.
5. **No meteorological source alone supports** a Germany wind
   building-vulnerability curve, actual R+V insured exposure/claims,
   loss ratio, GUL/IL/RI, event frequency, OEP/AEP or SCR. Previous
   2022 public HU candidates and 2025-like fictional policy values
   are NEVER presented as actual 2020 insured sites.
6. Station archive original 2020 source SHA must be logged with
   source URL and archive vintage; no publisher original wind ZIPs
   committed to public Git or automatically retained in NeonDB.
   Commercial usage of DWD CDC product is per **CC BY 4.0 with DWD
   attribution**, independent of Copernicus Licence governing the
   Google Research ERA5 reanalysis.
