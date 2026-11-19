<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara/Sabine 2020: one source-bounded ERA5 10fg grid area for 10k public NRW candidates

**Research receipt, 12 November 2026 — NOT acquired ERA5 meteorology, NOT licensed
insurer losses, NOT a German wind damage model.** Reproducible from the
official-HU2022-derived 10k **fictional insurer** OED archive, already verified in
original GitHub Actions [HU2022 run #42097472463](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42097472463).
The produced 10k archival ZIP SHA-256 is
`5b0055ce71314f7d7baf4f67008cd4abba3df28a4bce0690bbe9521a3cc35757`;
the original 901MB physical building source ZIP SHA-256 is
`10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da`.
The public 2022 HU candidate geocodes are not actual R+V insured positions.

## Independently calculated area / support

From exactly 10,000 unique public building polygon candidates in 53 NRW
Kreise, with 10,000 *fictional* account keys and fictional 2025-like building
TIV of EUR 4,826,029,500:

| Quantity | Source-derived value |
|---|---|
| Source WGS84 lat range | 50.3640454 to 52.4478738 |
| Source WGS84 lon range | 5.8978614 to 9.4096531 |
| Request area [N,W,S,E] | **[52.50, 5.75, 50.25, 9.50]** |
| Area dimensions | 2.25° tall × 3.75° wide (within CDS 5° × 5° maximum) |
| Atmospheric 0.25° nodes within rectangle | **160** (10 latitude × 16 longitude nodes) |
| Nodes nearest at least one fictional candidate | **93** |
| Occupancy signature SHA256 | `de10099a9b79febb1a254bc765dc477a47589cb1f49ba75415bfe6b9723c2ebd` |
| Maximum possible gridpoint × time cells | **15,360** (160 × 96 hourly times) |
| Meteorology actually retrieved or source-byte verified | **none** |

The digest is SHA256 of one ASCII line per **occupied** quarter-degree grid
node, ascending `lat_quarter_step:lon_quarter_step:site_count\n`.
It does **not** include site coordinates or reveal individual insurer risks.

## Reproduce without contacting CDS

```bash
python research_runners/ciara2020_nrw_10k_era5_area_request_v0.py \
  /path/to/verified-nrw-hu2022-original-derived-10k.zip \
  --receipt-json /tmp/ciara-2020-nrw-10k-era5-area-receipt.json
```

The code checks the exact previous archive SHA256, all three CSV hashes,
manifest provenance and science flags, source polygon residential-use class,
1:1 policy/candidate IDs, 53 counties, all original fictional TIV, WGS84
coordinate bounds and the derived 0.25° nearest grid cell coverage. Missing or
modified source bytes cannot be passed merely with a new self-signed manifest.
The stdout/JSON includes only source identity and aggregate request/coverage.
No extracted site coordinates, physical source ZIP or ERA5 original data are
written to git.

The **preview** uses dataset `reanalysis-era5-single-levels-timeseries`, DOI
`10.24381/1cf1ad76`, variable `10m_wind_gust_since_previous_post_processing`
(ECMWF `10fg`, paramId 49, unit **m/s**), date Feb 8–11 2020,
the bounded `area` selection above, and **NetCDF** output. It is a
proposed CDS API request; exact request syntax and returned NetCDF dimension
names must be checked using the live CDS download form *after* the human has
accepted the dataset's licence. No CDS API calls, automatic licence
acceptance or credentials are included.

Official Copernicus original sources:

- [ERA5 hourly time-series CDS catalogue](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=overview), including 0.25° weather grid and CC-BY dataset licence
- [ECMWF ARCO product guide](https://confluence.ecmwf.int/spaces/CKB/pages/505390919/ERA5+hourly+Analysis+Ready+Cloud+Optimised+ARCO+data+on+single+levels+from+1940+to+present+Product+User+Guide+PUG), including rounding, up-to-5° × 5° areas and file-format caveats
- [ERA5 atmospheric gust data documentation](https://confluence.ecmwf.int/pages/viewpage.action?pageId=235634460), 10fg and parameter ID 49
- [Official CDS API and manual licence acceptance instructions](https://cds.climate.copernicus.eu/how-to-api)

**Review required before a native model:** the NetCDF dataset will contain
2020 reanalysis meteorology, not observed insured R+V damage. Reconcile
event/time/height/metric, test spatial coverage and independent original
source hash, obtain insurer loss denominators and rights, and review a
German-material/roof vulnerability model against independent holdout claims.
This area preview is not a 2020 NUTS2 insured-loss average, 1990 XWS Daria,
annual storm rate, native Oasis GUL/IL/RI, OEP/AEP or SCR.
