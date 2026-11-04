<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MRMS MESH: a second independent dated hail case, Arlington 2024

**Status (before direct-source GitHub CI):** Research case candidate. This is a *different actual storm and year* from the Keller 2021 [original hail comparison](./noaa-mrms-keller-hail-ground-report-grid-20261104.md), with an original National Weather Service (NWS) **preliminary local storm report** and two fixed NOAA MRMS historical source objects. No rights, hazard, scientific calibration, property value, insured losses, event frequencies, or downstream CAT-model input approval is granted.

## Distinct original NWS hail report / time conversion

- Independent weather-service field report: [Preliminary Local Storm Report, NWS Fort Worth, `NWUS54 KFWD 280045`](https://mesonet.agron.iastate.edu/wx/afos/p.php?e=202405280045&pil=LSRFWD) (Iowa Environmental Mesonet's historical mirror of the **original NWS text product**). The product records **2024-05-27 7:43 PM CDT**, **2 NE Arlington**, **32.71°N, 97.10°W**, and `E3.25 Inch` hail from the **public mPING app**, with report remark `Baseball+ (3.25 in.)`. This is a **reported/estimated size category**, *not* a gauge- or instrument-measured hail diameter or a scientifically independent calibrated source.
- `19:43` **CDT (UTC−5) = 2024-05-28T00:43:00Z**. The later NCEI Storm Events catalogue uses a **fixed `CST-6`** label and a matching `18:43` wall-clock time to represent the same UTC instant, which must **not** be interpreted as an extra one-hour discrepancy.
- The plausible later NCEI Storm Events ID `1186553` is independently indexed by third-party descriptions of the matching event/report. Its **original published NCEI CSV row has not yet been independently byte-verified**. Keep that identity explicitly *candidate* until the provider's source row is checked. The NCEI episode includes nearby `1.75 in` and `3.25 in` reports at the same minute; these may be observations from the same evolving weather system, **not independent storm-frequency events**.
- **Observation:** `3.25 in × 25.4 mm/in = 82.55 mm`. This is only the separately *reported* magnitude, not an original NOAA MRMS radar value.

## Pin exact historical NOAA original source objects

NOAA original-provider public bucket: [MRMS Open Data](https://registry.opendata.aws/noaa-mrms-pds/) / `https://noaa-mrms-pds.s3.amazonaws.com`. A bounded **original S3 ListObjectsV2** search confirmed two objects and their sizes.

| Field | 2-minute instantaneous MESH | 30-minute rolling MESH maximum |
| --- | --- | --- |
| Exact selected product | `MESH_00.50` | `MESH_Max_30min_00.50` |
| Original source UTC | `2024-05-28T00:42:43Z` | `2024-05-28T00:44:00Z` |
| Offset from NWS report UTC | **−17 s** | **+60 s** |
| Exact key | `CONUS/MESH_00.50/20240528/MRMS_MESH_00.50_20240528-004243.grib2.gz` | `CONUS/MESH_Max_30min_00.50/20240528/MRMS_MESH_Max_30min_00.50_20240528-004400.grib2.gz` |
| S3-indexed bytes | **62,367** | **105,601** |
| SHA-256 over intermediary-delivered full compressed object (original direct authentication *pending*) | `7dcca72784d7715a43dca5353726aaf2cee4066d2728500d0f3d0bce3d86397f` | `ddef94cad19ff39621b74563631ae0c9cf205fdf71abaa48c4b6d7715b75a806` |
| GZIP footer declared decoded `ISIZE` (not full local inflate/CRC verification) | **99,627** bytes | **141,720** bytes |
| Research SHA acquisition method | Three HTTP Range bodies: 0–23999, 24000–47999, 48000–62366 | Five HTTP Range bodies: 0–23999, 24000–47999, 48000–71999, 72000–95999, 96000–105600 |

The read-only web intermediary supplied the complete bounded byte ranges and source gzip headers/embedded original basenames. The SHA-256 values above were computed over reconstructed compressed bytes using a self-tested SHA-256 implementation. **This intermediary is not an authenticated independent direct NOAA HTTPS receipt**; the new path-scoped GitHub Actions workflow must fetch both original source URLs directly, verify SHA-256 and GZIP CRC32, and check source GRIB2 metadata before trusting ecCodes values. Original source bytes do **not** go into Git or workflow artifacts.

## Reproducible research challenge and no-double-count rules

The same fixed-GRIB2 metadata verifier and independent ecCodes **2.50.0** four-nearest-cell reader used for the 2021 Keller case now select these two exact 2024 objects. For this report the input point is `32.71 N / −97.10`, likely between four 0.01-degree grid-cell centres; exact geometry, source reference UTC, parameter 209/3/28 versus 209/3/29 and value/missing/no-coverage status must be authenticated by the **new executed direct-source workflow**. Four source cell values are **not four independent observations**.

This study challenges whether the difference between a 2-minute instantaneous MESH estimate and a 30-minute rolling MESH maximum also matters in a **physically independent 2024 storm**. It does **not** confer statistical independence to storm reports within the same NWS episode, nor does it make event-year occurrence rates estimable from two selected positive-hail storms. The 2024 mPING source is an estimated/categorical report, not an instrument-ground-truth calibration; the 2021 report was a different NWS source and likewise selected, not a randomized holdout. A meaningful CAT hazard model would require controlled event-independent train/test splits, precision/recall/coverage, physically validated storm-event object clustering, scientific product-version lineage, exposure and vulnerability sources, and explicit source rights review.

**Remaining gates:** Direct 2024 source SHA/CRC/GRIB verification, independent ecCodes radar size values, historical NOAA MRMS algorithm/product-version review, NCEI original CSV event-row identity, uncertainties of mPING size and location, broader events and misses. Raw data, insured claims, synthetic portfolios and ELT/YLT are out of scope.
