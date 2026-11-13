<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara/Sabine 2020 – actual 96-hour Google public ARCO ERA5 10fg NRW weather

**13 November 2026.** This challenge builds on the verified
[original four-Zarr-metadata source SHA receipts](ciara2020-google-public-arco-10fg-original-metadata-20261112.md)
and the [independently reproduced original one-hour Ciara wind gust](ciara2020-google-arco-real-one-hour-10fg-20261112.md)
from public Google Research ARCO ERA5.

## Purpose and exact limits

The source is a public, anonymous Google Research ARCO ERA5
0.25-degree regridded meteorological Zarr:
 gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3.
The 10m 3-second gust is the original variable
10m_wind_gust_since_previous_post_processing (10fg), not a 10m
vector-mean wind, not any weather station observation and **not
a financial or insurance loss**.

Date is exactly **2020-02-08 00Z through 2020-02-11 23Z**,
**96 consecutive UTC hourly frames**, over the **10 × 16
0.25-degree NRW rectangle** [N,W,S,E] = [52.50,5.75,50.25,9.50].
Only 160 public atmospheric nodes, not 10k residential source
polygons and not any personally identifiable/insured geocodes.

The source-pinned Google original metadata SHA-256 for all four
Zarr variable/coordinate objects is re-fetched before data reading.
The independently previously accepted
**2020-02-09 12Z, 51.0N, 7.0E original observed-source gust**
of 20.320262908935547 m/s must also match its exact float32 SHA
12d34d73cece12a90220ddbbb5b092e388a6b1e0d9b0c9dcf5004a01a7c3119c
in the complete 96h grid; if not, the original-source replay
is rejected rather than silently changing the historical evidence.

The reader checks exact timestamp uniqueness and sequence,
geographical coordinate support, variable identity and units,
finite/nonnegative gust <=150m/s and consistent 96-frame coverage.
It extracts *one global source hour chunk at a time*, reducing
in-memory retention of the global original dataset. The provider
original Zarr is physically time-chunked in 1×721×1440 blocks;
the reader needs approximately **96 source hour chunks** and has
no retained original provider compressed blob archive.

It hashes the **row-major, 96 × 10 × 16 decoded original float32
values** in little-endian order; this is NOT the original compressed
Google Cloud Storage chunk SHA. Only **aggregate hazard** is reported:
min/mean/max of the 160 grid-cell event-maximum hourly gusts and
counts exceeding 25/30/35/40m/s. A scalar value or annual
storm-frequency model is not derived from these four days.

## Restricted output and reproducibility

Dry run, no network:

    python research_runners/ciara2020_google_arco_real_96h_nrw_area_v0.py --dry-run

Actual public original source (requires reviewed optional
requirements-google-arco-2020-original-smoke.txt dependencies):

    python research_runners/ciara2020_google_arco_real_96h_nrw_area_v0.py --live-96h

One dedicated **PR-branch scoped** read-only CI job tests the
full original online read, separate from the ordinary Python
3.11–3.14 offline suite. It has no Google or CDS credentials
and does not upload original Google weather array chunks
or original HU2022 building coordinates to GitHub.
The CLI prints **only a JSON source- and aggregate-hazard receipt**.

## Data rights and scientific NO-GO

The Google-hosted dataset is distributed under the **Copernicus
Licence**, with attribution to **Copernicus Climate Change Service
(C3S)** and Google Research ARCO-ERA5; its code repository's
Apache-2.0 licence does NOT replace the ERA5 data licence.
[Google Research ARCO dataset README](https://github.com/google-research/arco-era5)
states commercial and research reuse under Copernicus terms.
No private CDS portal credential or hidden dataset-terms acceptance
is exercised by public GCS reading.

The 2022 NRW public physical building candidate dataset and the
10k **fictional** building insurance policies were not joined
in this initial full-rectangle test. A subsequent source-bound
10k site-to-93-cell join can use the already merged
[original HU2022-derived 10k exact-source ZIP gate](ciara2020-nrw-10k-era5-10fg-area-request-20261112.md),
if its original source ZIP is present and its SHA matches.
Do not report 2020 real R+V losses from 2022 public source
geometry or from fictional insurance policy values.

A successful 96h meteorological grid receipt is **not yet**
verified original compressed Zarr chunk byte SHA provenance,
historically accurate individual building 1990 Daria wind,
event-matched EIOPA insurer claims or country/treaty denominators,
German material/roof vulnerability calibration, native Oasis/NextGen
GUL/IL/RI, annual OEP/AEP, or SCR.
The [source/rights/scientific model no-go](rva-germany-wind-loss-calibration-source-review-20261106.md)
remains active.

**Online source values remain unconfirmed until the exact-HEAD
CI live research job succeeds.** Do not merge based only on
synthetic tests or earlier one-hour source smoke.
