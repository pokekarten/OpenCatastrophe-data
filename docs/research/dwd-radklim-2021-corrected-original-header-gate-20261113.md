<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# DWD RADKLIM RW2017.002 2021 corrected NetCDF4: byte-pinned offline header gate

**Research only (2026-11-13).** No external source-byte commit, no provider API request, no Neon write, no CAT model admission or insured loss claim.

## Official correction and distinct product identity

The original [DWD NetCDF warning](https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/readme.txt) explicitly states that **the original 2021 NetCDF files are incorrect and should not be used**. The original [RADKLIM RW v2017.002 DOI landing page](https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_RADKLIM_RW_V2017.002-de.html) warns that supplemented/corrected material is **not part of the original DOI-referenced dataset**. A DOI-only source identity is therefore insufficient.

The official [supplement directory](https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/supplement/) lists:

- RW2017.002_2021_netcdf_supplement.tar.gz — **820,143,312 bytes** in the public listing; no full archive is acquired here.
- Original research on 2026-11-12 measured exactly the first **2,048 compressed bytes**, SHA-256 **741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867**.
- That exact original source prefix decompressed far enough to reveal the TAR directory 2021/, the first TAR file 2021/RW_2017.002_202107.nc with **91,356,907** uncompressed bytes declared in its TAR header, and the 8-byte native HDF5/NetCDF4 signature.
- Previous metadata-only research samples #55 and #58 are in the private research DB. **Neither is a precipitation-value observation.** A prefix SHA must never be represented as the archive's or month's full-file checksum.

This PR makes the previously documented source-prefix claim independently reproducible and fail-closed as code.

## Bounded executable proof

The research_runners/dwd_radklim_2021_corrected_prefix_header_v0.py script accepts an **already acquired** exact 2,048-byte private original compressed range. It does not accept any URL for retrieval and makes no network requests.

1. Pin the corrected 2021 URL and original 2,048-byte response SHA-256; reject the known-bad original year directory and all other paths.
2. Check the gzip header and decompress **at most 1,032 bytes** (two TAR headers plus 8 signature bytes), even from a highly compressible response.
3. Validate two original TAR USTAR octal header checksums, declared sizes, exact 2021 directory and first month/member identity.
4. Verify the native HDF5/NetCDF4 signature. This does not parse HDF5 groups, CF metadata, CRS, time coordinates, precipitation units, nodata masks or rainfall values.
5. Print only source identity, original prefix SHA/size, declared first-member name/size and false admission/completeness flags. No raw source data, coordinates or insurance information are printed or saved by the tool.

Example from an already authorized private workspace with the **previously obtained** original range file:

    python research_runners/dwd_radklim_2021_corrected_prefix_header_v0.py --path /private/approved-original-2048-byte-prefix.bin

The path is illustrative and does not claim that this file currently exists in the present environment.

## Offline negative tests

    python -m unittest tests.test_dwd_radklim_2021_corrected_prefix_header_v0 -v
    python scripts/check_all.py

Tests generate invented TAR headers and synthetic NetCDF-like signature bytes, without original DWD source data. They challenge incorrect URL/year, tampered original checksum, malformed gzip, corrupt TAR checksum, wrong month/size, missing HDF5 signature and the difference between an invented structural fixture and frozen original provider SHA-256.


## VERIFIED trusted original-provider run on 2026-11-13

**This is no longer just a previously observed external-intermediary prefix.**
The exact isolated public **GitHub Actions branch-push job**
[run 43488656039, job 132103695178](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43488656039/job/132103695178)
executed the new source-specific code directly from the reviewed Git commit
`01ab7b83d1765fb6bbe590ad772880c65d5e43c9`:

- Provider request completed at **2026-11-13T19:04:19.824499Z**.
- **HTTP 206**, exact `Content-Range: bytes 0-2047/820143312`, **2,048 original compressed bytes**, no redirect, no second request/retry.
- Original range response SHA-256 **741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867** exactly matches the independently frozen earlier source-prefix evidence.
- Original gzip/TAR (two header checksums, version/year/month) and native NetCDF4/HDF5 first-member magic validated.
- Independently recorded request identity SHA-256 `76b410d2c64e3147bb6932df07c860455d04e097d1ec3fe179ea16a472cb28c3`, probe code SHA-256 `635be219e2faf2b2e680f5a3d0f8d0b32cb3f80ba19440f38c6bb68b9672bd71` and validator code SHA-256 `86cbdfaf7e764d29be08d0c3b01b110726b10c480bdb21dbda782bbf62674a4b`.
- **13 synthetic offline tests passed** on the same source job. The pull-request job [132103716840](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43488662558/job/132103716840) independently verified the offline tests and **skipped the live step**, as designed.
- The temporary branch-push trigger was subsequently **removed**. In the final workflow, PR checks remain offline; additional provider requests require explicit manual `workflow_dispatch` and the `--live` argument. No automated repeated download exists.

The live proof uses the **strict original-source GitHub runner** and is materially stronger than the prior external-intermediary metadata receipts #55/#58. However, it is **only a 2,048-byte compressed prefix** of an 820,143,312-byte archive; it does **not** verify actual precipitation, months, CRS or full original archive digest. This run stores source code/digests and public logs, not the provider response bytes.

### Private-Neon evidence contract limitation

The separate research DB's `research.source_api_smoke_receipt_v0` currently has a hard `CHECK (NOT strict_repository_runner_executed)` constraint. Thus the new **true** GitHub trusted-runner proof **cannot truthfully be inserted with that flag set** without an independently reviewed schema change. We deliberately **did not bypass the constraint**, insert a false classification, or write provider data to Neon. GitHub's original run/job and the pinned digest/code commit are the auditable evidence until an append-only trusted-origin receipt schema is approved.

## Remaining source-data and science gates

- Carry out one independently authorized, fixed, 2,048-byte original Range GET in a trusted runner and verify the response SHA-256. **This PR does not execute it.**
- Acquire and pin the **entire corrected monthly NetCDF member**, independently verify its full SHA-256 and NetCDF4/CF schema, DWD projection, timestamps, rainfall units and missingness. Check every actual original monthly TAR member for whole-year completeness rather than assuming the first one is January.
- Validate radar artefacts, gauge adjustment, measurement uncertainty and independent rain-gauge holdouts before CAT hazard, occurrence rates, vulnerability or insurance-loss applications.

**Licensing:** Separate prior research records DWD CDC OpenData under CC BY 4.0. This does not authorize arbitrary crawling and does not establish scientific model fitness; no original source bytes are redistributable by this PR.
