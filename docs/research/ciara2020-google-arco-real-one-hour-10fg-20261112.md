<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Real Google-hosted original 10fg: one Ciara 2020 wind gust hour, one grid cell

**Research engineering, 12 November 2026.** Follow-on to the
[public original Google 10fg Zarr metadata proof](ciara2020-google-public-arco-10fg-original-metadata-20261112.md),
which successfully contacted Google Research's *anonymous* GCS
public ERA5 store from GitHub Actions twice. Exact four original
variable/coordinate Zarr metadata SHA-256s are frozen in the
2026-11-12 research observations TOML source register.

The objective here is **to read one real original, regridded ERA5
historical 10-metre wind-gust value**, not a toy normalized NetCDF
or guessed storm damages:

- Fixed UTC timestamp: **2020-02-09 12:00:00Z**, within Ciara/Sabine
  8–11 February 2020 storm window.
- One public ERA5 0.25-degree grid centre: **latitude 51.0,
  longitude 7.0**. Not a real R+V insured site, not the aggregate
  of all NRW, and NOT the 96h event-maximum gust.
- Exact original full variable
  10m_wind_gust_since_previous_post_processing
  (ECMWF 10fg, m/s) in the documented Google Research ARCO Zarr.
  Mean U10, V10 or any derived vector wind speed are not substitutes.
- Original metadata SHA, shape, 1323648-hour source axis and
  long/lat coordinate identities must match the separately
  archived live original-metadata receipts from GitHub #1506.
- Anonymous public read via pinned xarray + gcsfs + zarr stack
  in a **PR-branch-only one-off CI job**. The imported dependencies
  do NOT enter the permanent regular Python 3.11-3.14 validation
  matrix and there are no CDS account credentials.
- Validates the exact original UTC hour, lat/lon centre,
  original source variable/units, finite non-negative gust <=150 m/s
  and outputs a **scalar value** plus its float32 SHA (which is
  **not** the original compressed Zarr chunk SHA).
- It must refuse to call a missing original hour a success; no
  nearest-neighbor substitution in the **time** coordinate is allowed.
  The original 10fg Google distribution is regridded ERA5,
  not observed DWD station gust or a source-matched EIOPA claim.

## Independently verified original 2020 source result

The PR's public Google-hosted source test **actually succeeded** in
GitHub Actions run [#43307934303](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43307934303),
job **131496043770**. After independently comparing all four original
source Zarr metadata SHA-256 pins it loaded the public 2020-02-09
12:00 UTC original ERA5 10fg at the real atmospheric grid centre
51.0° N, 7.0° E: **20.320262908935547 m/s** (~73.15 km/h).

An exact observation-only historical provenance record is versioned at
research/observations/ciara2020_google_arco_one_real_hour_10fg_receipt_20261112.toml
with metadata-source link, timestamp, exact float32 scalar SHA-256
**12d34d73cece12a90220ddbbb5b092e388a6b1e0d9b0c9dcf5004a01a7c3119c**,
attribution and model-science nonadmission booleans. This SHA is of the
**one selected decoded float32 value**, NOT the original globally compressed
source Zarr chunk; the latter has not been independently archived.

## Data rights

Google Research publicly documents commercial and research usage of
its anonymously downloadable ARCO ERA5 under the **Copernicus Licence**
and required attribution, distinct from the Apache-2.0 software
licence. See
[Google Research source](https://github.com/google-research/arco-era5)
and the [Copernicus licence](https://cds.climate.copernicus.eu/api/v2/terms/static/licence-to-use-copernicus-products.pdf).

No action pretends to accept CDS portal terms for the operator.
The separate [manual account-owned CDS original source workflow](ciara2020-cds-original-manual-source-acquisition-20261112.md)
remains gated by the owner's separate licence acceptance and token.

## Test and interpretation boundaries

Run without network:

    python research_runners/ciara2020_google_arco_real_onehour_gust_v0.py --dry-run

One PR-specific GitHub CI job executes the original read after
four source SHA checks and original time/grid tests, with
versioned optional Python packages. Unit tests create invented
28.125 m/s gusts and adversarial shape/time/units/NaN changes;
those synthetic values are not evidence of actual Ciara 2020 winds.

Successful original **one grid cell / one hour** acquisition will
still not verify 96 original hours across 160 nodes, all original
compressed object SHAs, any observed insurer claims, German building
vulnerability, R+V real insured locations or 2020 contract data,
native Oasis/NextGen GUL/IL/RI, OEP/AEP, annual frequencies or SCR.
The [independently tested loss admission NO-GO](rva-germany-wind-loss-calibration-source-review-20261106.md)
is unaffected. The next executable step would be a bounded
96h original 10fg spatiotemporal replay with a complete source SHA
and 93-node site-support check; only then can a loss research
challenge be started.
