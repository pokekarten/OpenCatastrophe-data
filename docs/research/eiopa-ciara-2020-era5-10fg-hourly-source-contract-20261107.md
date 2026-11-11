<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara/Sabine February 2020: ERA5 10fg original hourly wind preflight

**7 November 2026 — executable source request and offline negative
tests, NOT an actual downloaded original ERA5 or calibrated loss model.**

The independent EIOPA [Catastrophe Data Hub](https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en)
provides **2020 Ciara/Sabine** incurred insurer-reported windstorm
building losses at anonymized NUTS2 resolution. The Daria 1990 XWS
pilot is **a different storm** and has no usable observed EIOPA
same-event loss. The correct next computational step is obtaining
the **2020 Ciara/Sabine** gust footprint, not treating 1990 losses
as if they matched 2020 EIOPA insurer reports.

## Two ECMWF source variants, with correct units and times

1. [Copernicus ERA5 hourly single-levels main catalogue](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download),
   DOI **10.24381/cds.adbb2d47**. It has the original
   `10m_wind_gust_since_previous_post_processing` variable;
   ECMWF's official [ERA5 data documentation](https://confluence.ecmwf.int/pages/viewpage.action?pageId=216494709)
   confirms it is **10fg**, **GRIB paramId 49**, **m/s**, a
   *forecast-derived maximum since previous post-processing*,
   rather than 10 m vector mean wind or instantaneous U/V.
   The regular reanalysis CDS atmospheric grid is 0.25 degrees
   and historical data include February 2020.
2. [ERA5 hourly time-series catalogue](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=download),
   DOI **10.24381/1cf1ad76**, publication 2025-03-17.
   This newer *ARCO repackaged* dataset **explicitly lists
   10m wind gust since previous post-processing** as an available
   variable and can return a point or a bounded small region
   in **CSV or NetCDF**, hourly, 0.25-degree atmosphere cells.
   Its [official product guide](https://confluence.ecmwf.int/pages/viewpage.action?pageId=514296174)
   cautions that a user-selected coordinate is **rounded to
   the nearest 0.25-degree ERA5 gridpoint**. It is an appropriate
   lightweight **one-point technical bootstrap**, not a NUTS2
   event-loss footprint. Its source files are repackaged; they
   are not byte-identical to the main ERA5 archive.

**Important independent source QA:** In June 2026, ECMWF
[announced a one-hour temporal misalignment bug](https://forum.ecmwf.int/t/issue-affecting-some-parameters-from-the-era5-post-processed-daily-statistics-on-single-levels/15057)
in the separate **derived daily-statistics ERA5 dataset**, including
10fg. The fault concerns how the **00 UTC** post-processing
interval was associated with days/time zones. **We ban that
derived-daily source** from Ciara event joining. We do not assume
the bug exists in the original hourly parent or the ARCO
hourly time-series product; before any actual model we still
must verify 00 UTC interval interpretation and time limits
against source metadata and independent 10 m DWD station
gust observations. Do not mistake modelled wind for *observed
insurance claims*.

## Implemented and tested in OpenCatastrophe-data PR #1373

The immutable reference-only research contract is
`research/observations/eiopa_ciara2020_era5_10fg_hourly_point_contract_v0.toml`,
and its no-network code is
`research_runners/eiopa_ciara2020_era5_10fg_hourly_point_preflight_v0.py`.

Run the **source request preview only**, without CDS access:

```sh
python research_runners/eiopa_ciara2020_era5_10fg_hourly_point_preflight_v0.py --show-cds-request
```

It prints the official source request candidate:

```json
{
  "dataset": "reanalysis-era5-single-levels-timeseries",
  "request": {
    "variable": ["10m_wind_gust_since_previous_post_processing"],
    "date": ["2020-02-08", "2020-02-11"],
    "location": {"latitude": 51.0, "longitude": 7.0},
    "data_format": "csv"
  },
  "CDS_terms_acceptance_required_by_user": true,
  "request_executed": false,
  "data_obtained": false
}
```

The dates define a deliberately generous **96-hour candidate
event window** spanning 2020-02-08 00 UTC through 2020-02-11
23 UTC; it is not a scientifically established Ciara claim
period, and the **00 UTC since-previous-post-processing interval
may partly belong to the preceding calendar day**.
51.0° N, 7.0° E represents ONE illustrative point near Cologne,
not actual insured R+V locations, insurer policy values or
a German/NUTS2 wind/hail loss aggregation.

Actual original data access requires a CDS account and explicit
per-dataset acceptance of the [CDS API
terms](https://cds.climate.copernicus.eu/how-to-api).
**No credentials, licence acceptance or ERA5 actual bytes were
used or stored** in this PR. Never put the CDS personal access
token or `.cdsapirc` in GitHub files or logs.

A separate **offline future-input check** accepts only a
consciously *normalized* **UTF-8 CSV**, with exact fields
`time_utc,latitude,longitude,10m_wind_gust_since_previous_post_processing,units`.
This is **not claimed to be the raw original CDS CSV export
format**, which has not been inspected. It verifies exactly
96 sequential UTC hourly labels, constant point coordinates,
the correct 10fg rather than U/V wind components or a daily
mean, explicit m/s units, finite plausible values and source
CSV SHA-256. Its receipt remains **NOT SOURCE ATTESTED / NOT
LICENSE ACCEPTED / NOT OBSERVED CLAIMS**.

```sh
python research_runners/eiopa_ciara2020_era5_10fg_hourly_point_preflight_v0.py \
  --normalized-hourly-csv /tmp/normalized-local-ciara-10fg-96h.csv \
  --out-receipt /tmp/ciara-local-NOT-INSURER-LOSS-receipt.json
```

Eight synthetic negative test cases are in
`tests/test_eiopa_ciara2020_era5_10fg_hourly_point_preflight_v0.py`;
the cheap source-only Daria workflow now checks the source
metadata and executes them. No original ERA5 bytes or
EIOPA claims were included in tests.

## Scientific next steps before an EIOPA match

- **Source rights:** explicit CDS CC BY licence acceptance,
  record original downloaded netCDF/CSV SHA-256, original
  request parameters, dataset publication version, gridpoint
  rounding, original 10fg variable/units and license/attribution.
- **Physical hazard:** evaluate Germany and EIOPA's NUTS2
  spatial units using event-matched 2020 gust fields and a
  demonstrably matching meteorological track; a single point
  cannot produce spatial exposure-weighted insurance losses.
- **Observed insurer claims:** separate EIOPA incurred building
  loss from other claims; quantify 2020 insurer sample coverage,
  residential vs commercial cell suppression and 2020
  insured-value denominator. Do not infer company R&V or
  postcode exposures from anonymized NUTS2 totals.
- **Validation:** calibrate on independent observed claims
  only if data rights, hazard metric, claims values,
  insurance financial basis and training/holdout design
  are independently approved. Multiple storms and years,
  including quiet-year zeroes, are required before annual
  OEP/AEP or correlated event simulation can be admitted.

**Current result:** GO for source-specific, no-network
request preview and deterministic synthetic 96h hourly gust
QA. NO-GO for any existing original ERA5 Ciara wind
measurements, claims calibration, R&V insured risk sites,
annual windstorm event frequency or gross/net OEP/AEP.
