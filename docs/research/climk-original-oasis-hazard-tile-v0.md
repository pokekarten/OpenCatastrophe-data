<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Exact CLIMK–WINDS v2 ERA5 NetCDF → native Oasis hazard tile

**5 November 2026. Original provider-data scientific hazard tile study, no original data committed.**

## Why this branch and not invented WISC files

The [Copernicus C3S WISC synthetic event set](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-synthetic-events)
remains behind CDS login and licence acceptance, and its original
[Product User Guide](https://confluence.ecmwf.int/spaces/CKB/pages/255094970/Synthetic+Windstorm+Events+for+Europe+from+1986+to+2011+Product+User+Guide)
announces withdrawal in the future. Source acquisition and rights are
tracked separately in [issue #1391](https://github.com/pokekarten/OpenCatastrophe-data/issues/1391).
Do not fake WISC access or recast another source as WISC.

As an **independent observed/reanalysis source**, the
[CLIMK–WINDS v2 ERA5 NetCDF record](https://zenodo.org/records/15305753)
contains 50 **selected extreme** storms from winter 1995–2015 on an
181 × 269 grid. Zenodo publisher explicitly lists **CC BY 4.0** and
offers direct source file download without requiring CDS credentials.
The source is not a complete all-storm annual probability sample.

## Source pins from existing public code and earlier receipts

Pre-existing audited source:
[`scripts/inspect_climk_winds_era5_v0.py`](../../scripts/inspect_climk_winds_era5_v0.py).
Exact source constants are reused rather than copied into a second
independent executable source-truth:

- [Original Zenodo publisher source file](https://zenodo.org/api/records/15305753/files/ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc/content).
- Exact original file length: **6,792,278 bytes**.
- Publisher MD5: `887ae3218793c599862f115876c145f9`.
- Previously verified original SHA-256:
  `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.
- Mandatory source variables: `absolute_maxwindgusts` with
  `m s**-1`, `relative_maxwindgusts` (dimensionless),
  `Storm_Names`, `Storm_Dates`; native `storm_number × latitude × longitude`.
- Source labels and event indices are **source-specific**. Do not
  assert identity or rank matches to COSMO-REA6, CCLM, WISC or C3S EWS
  just because the label appears similar.

## Executable original-data study

[`research_runners/climk_era5_original_oasis_tile_v0.py`](../../research_runners/climk_era5_original_oasis_tile_v0.py)
uses the original byte verifier and restricted URL from the existing
inspector. It reads one zero-based storm index 0–49 and one grid tile
at most 10,000 cells. The default is storm index 0, native grid rows
90–91 and cols 130–132, selected for a *technical source tile* test,
NOT a claimed Germany region or observed insured properties.

The bounded output is exactly four research CSVs:

1. `events.csv`: one source-local event key `storm_index + 1`.
2. `footprint.csv`: native OasisLMF 2.5.8
   `event_id,areaperil_id,intensity_bin_id,probability` schema;
   one deterministic conditional wind bin per valid source grid cell.
3. `intensity_bin_dict.csv`: explicit m/s gust bins.
4. `areaperil_dict.csv`: stable original source row/column IDs and
   centroids, not a site geocoder or entire cell polygon.

Original masked/missing cells remain **unknown weather**, not zero.
Nonfinite or unsupported gusts block. All source and output
quantities are bounded, full source MD5/SHA/byte size are verified,
and each CSV receives a byte length/SHA-256. No external original
NetCDF, license-gated data or insurer assets are committed.

The isolated
[`climk-original-oasis-footprint-v0.yml`](../../.github/workflows/climk-original-oasis-footprint-v0.yml)
workflow runs synthetic negative tests, fetches the authentic publisher
asset to temporary memory, computes one hazard tile, then invokes
**native OasisLMF 2.5.8 `csvtobin footprint`** to prove a binary
`footprint.bin` and `footprint.idx` from real source-derived CSVs.
This is an independent original-source follow-on to synthetic-only
[WISC tile PR #1388](https://github.com/pokekarten/OpenCatastrophe-data/pull/1388).

## Run and limitations

```sh
python -m pip install "netCDF4==1.7.3" "oasislmf==2.5.8"

python -m unittest discover -s tests \
  -p 'test_climk_era5_original_oasis_tile_v0.py' -v

python research_runners/climk_era5_original_oasis_tile_v0.py \
  --fetch-original --storm-index 0 \
  --row-start 90 --col-start 130 --height 2 --width 3 \
  --out /tmp/climk-real-native-oasis-tile
```

A successful native footprint binary generation proves *source
identity → decoded ERA5 native hazard gust → intensity bins → Oasis
hazard binary*, but nothing more. The 50 storm samples are extreme
**selected** rather than complete annual exposures; no
`occurrence.csv`, `periods.csv`, annual probabilities, annual
zero-loss years, scientific wind vulnerability or insurer/RI
terms are created. The annual frequency/EP and real-carrier claims
remain explicitly **false** in the receipt.

**Final run status:** read the exact GitHub Actions workflow results;
do not interpret this document or the presence of a NetCDF URL as a
successful new original-download test.
