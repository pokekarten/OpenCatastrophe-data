<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Google Research public ARCO ERA5: Ciara 2020 10fg source challenger

**Research 12 November 2026 – public original Zarr metadata discovery only.**
Separate channel alongside the
[CDS manual authenticated original-source one-shot](ciara2020-cds-original-manual-source-acquisition-20261112.md).
No CDS tokens, no CDS portal term-acceptance automation and no raw
meteorological chunk values in this PR.

## Source and rights

- [Google Research ARCO ERA5](https://github.com/google-research/arco-era5)
  publishes a public anonymous Google Cloud Storage bucket
  gcp-public-data-arco-era5 with historical ERA5 hourly atmospheric Zarr
  values. Its README lists the actual 10m 3s gust variable
  10m_wind_gust_since_previous_post_processing (short name 10fg,
  paramId 49, units m/s) in its single-level data.
- Dataset legal regime is **Copernicus Licence**, not the Apache-2.0
  software licence of the public Google Research *code*. Its original
  README explicitly allows research and commercial use under the
  Copernicus licence with attribution to Copernicus Climate Change
  Service (C3S) and notice of modified Copernicus information.
  [Original README](https://github.com/google-research/arco-era5);
  [underlying Copernicus licence](https://cds.climate.copernicus.eu/api/v2/terms/static/licence-to-use-copernicus-products.pdf).
  This public Google-hosted source is an independent authorized
  distribution; it does not pretend that CDS-authenticated access is
  allowed without the operator's individual CDS website acceptance.
- Our 10k HU2022 public NRW physical building candidates are
  **not R+V insured sites**. The 10k fictional accounts and 2025-like
  €4.826bn building values are not insurer observations. Event Ciara
  2020 is separate from Daria 1990 and EIOPA reported insurer claims
  require an independent same-event licensed denominator.

## Independent source-original metadata-only test

Original provider Zarr source root:

    gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3

The tested candidate sources are the four named variable/axis Zarr
metadata objects: 10fg original full name, time, latitude, longitude
(each filename .zarray). The code allowlists the exact public Google
Cloud Storage host/bucket/prefix, prohibits redirects, enforces <=2MB
source JSON per object, verifies Zarr v2 shapes/chunking and
wind-to-time/lat/lon dimension consistency, and records the SHA-256
of the **unmodified metadata bytes**. It never reads weather chunks.

    python research_runners/ciara2020_google_arco_public_10fg_metadata_v0.py --dry-run

The first CI PR includes a one-off branch-scoped, **read-only**
Google public Zarr metadata job, which runs all offline adversarial
tests before fetching exactly four public publisher metadata objects.
No credentials, no individual building locations, no original 96h
weather grids, no claim cells and no 10fg data values enter GitHub
source code or its published artifact.

## Validation needed after metadata acceptance

Successful original-source metadata checks prove that this Zarr
variable is published, at most. To obtain scientific 2020 source wind
hazard we still need a legally compliant bounded 96h original chunk
read, independent coordinate/time/units and all 160-node support
checks, source value-byte SHA provenance, and reviewed normalization
into our [96x10x16 NetCDF4 schema](ciara2020-nrw-era5-normalized-netcdf-hazard-audit-20261112.md).
Google's ARCO values are regridded and need an independent comparison
with the CDS-ARCO data; a metadata SHA is not the weather field.

No physical risk-to-loss curve, independent German 2020 insurer claims
denominator, native NextGen/Oasis GUL/IL/RI, OEP/AEP or SCR is admitted
by this source-only work. See
[German wind-loss calibration rights register](rva-germany-wind-loss-calibration-source-review-20261106.md).
