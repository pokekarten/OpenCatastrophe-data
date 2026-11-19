<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara/Sabine 2020 – manual Copernicus ERA5 original-source acquisition

**Research protocol 12 November 2026: no original ERA5 provider data yet acquired.**
This is a separately governed acquisition path after our
[10k original-source-derived NRW ERA5 request plan](ciara2020-nrw-10k-era5-10fg-area-request-20261112.md)
and the [locally normalized NetCDF4 validation](ciara2020-nrw-era5-normalized-netcdf-hazard-audit-20261112.md).
Neither an API request preview nor a synthetic NetCDF4 test constitutes a
verified original Copernicus weather observation.

## Manual operator prerequisites

1. Log in with an individually authorized Copernicus CDS account, open the
   [ERA5 hourly single-level time-series catalogue](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries?tab=download).
   Personally **accept the Terms of Use on the official CDS site for that
   exact dataset**. A working API token does not independently prove terms
   acceptance.
2. Select the 10m gust since post-processing wind variable (10fg), date
   **2020-02-08 to 2020-02-11**, northwest corner [52.50, 5.75] and
   southeast [50.25, 9.50], NetCDF output. Click the official **Show API
   request code** option and independently compare its exact keys,
   date range representation, area shape and format with the repository
   preview. **If different, stop. Fix and re-review our request
   before the operator marks the API form as verified.**
3. Create the repository Actions secret **CDS_API_KEY** holding the personal
   CDS access token. Never put the value in commits, dispatch inputs,
   chat messages, code review, workflow logs or artifacts.
4. On the public repository default branch, select GitHub
   **Actions -> Ciara 2020 original ERA5 source one-shot (MANUAL TERMS +
   API FORM) -> Run workflow**. Choose both affirmative confirmation
   options only after steps 1-3. The default options NOT_ACCEPTED
   and NOT_VERIFIED skip the live job. It is never triggered on a PR or push.

Official requirements: [CDS API setup and license acceptance](https://cds.climate.copernicus.eu/how-to-api),
[ECMWF time-series / Zarr-to-NetCDF product guide](https://confluence.ecmwf.int/spaces/CKB/pages/505390919/ERA5+hourly+Analysis+Ready+Cloud+Optimised+ARCO+data+on+single+levels+from+1940+to+present+Product+User+Guide+PUG).
This service supports 0.25-degree hourly atmospheric data and <=5-by-5-degree
areas; however its NetCDF structures can change.

## Safe read-only dry run

    python research_runners/ciara2020_cds_original_source_one_shot_v0.py --dry-run

The dry-run prints fixed candidate request fields, canonical request SHA-256,
the original-NRW-derived-10k ZIP SHA and occupied-grid signature; it contains
no secrets, real weather observations or real insurer site information.
There are no API calls and no automatic dataset terms acceptance.

## Manual original source run

The explicit [workflow](../../.github/workflows/ciara2020-cds-original-source-manual.yml)
uses a pinned CDS client and NetCDF4 acquisition dependency. It runs
independent offline mock/adversarial tests **before** contacting the official
CDS service. With a valid secret and both real operator confirmations
it submits one fixed 96-hour / 160 grid-cell source request.

The source response is accepted only as a bounded original NetCDF or a
CRC-verified ZIP containing precisely one NetCDF. The first-level receipt
records SHA-256 of the exact downloaded response and (if zipped) the
contained file, byte sizes, NetCDF data model, actual original dimension
names/lengths and variable names/units. **It does not pretend the raw
provider file already matches our normalized 96x10x16 structure.**

Only the metadata receipt (7-day GitHub artifact) is uploaded. The
original provider file is deleted from ephemeral runner storage even
if validation fails. It is **NOT added to the public repository**.
For reproducible weather replays, a separately authorized operator
must securely preserve an unchanged original provider response
in private storage outside the public repository and link its
independently verified SHA-256, request and permissions; this workflow
does not invent a private storage destination or NeonDB connection.

A successful live receipt is **not** an independently provider-published
source hash, historical claims data, a calibrated vulnerability fit,
native Oasis/NextGen loss, annual OEP/AEP or production risk result.
The [German insured-wind-loss calibration rights gate](rva-germany-wind-loss-calibration-source-review-20261106.md)
continues to block these admissions. Daria 1990 winds, the 2022 public
building polygons and partial-market EIOPA Ciara 2020 insured aggregates
remain separate evidence, not directly interchangeable observations.

## Tests

Specialist NetCDF4 CI has four byte-based synthetic tests and four
additional pure offline source-consent and HTTP-protection tests.
The core repository Python 3.11–3.14 matrix does not retrieve any
original ERA5 weather data, expose API credentials or assert a
successful live-CDS API request.
