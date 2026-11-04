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


## Executed direct original-source and ecCodes results (2026-11-04)

The original-provenance proof [GitHub Actions run #41827143546](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41827143546) **succeeded** for all previously pinned files **and both new 2024 objects**. The GitHub-hosted Ubuntu runner independently downloaded directly from fixed NOAA public S3 HTTPS URLs, verified original **byte lengths / SHA-256 / GZIP CRC32 / GRIB2 product identity, grid and UTC**, with TLS trust, redirects and ambient proxies disabled. Therefore both 2024 SHA-256 values above are no longer merely intermediary-generated hashes. **No original NOAA binary source bytes were committed, uploaded as artifacts, or published as output.**

The independent [ecCodes 2.50.0 original-field run #41827143477](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41827143477) also **succeeded** with both new 2024 objects, validating grid geometry/parameter 28 versus 29 and reading the **four exact source grid cells around the report point**, not a whole raster output.

### Original independent time-window comparison for the separate 2024 storm

| Source and offset from original NWS report 00:43Z | NW (32.715 N, 262.894999 E) | NE (32.715 N, 262.904999 E) | SW (32.705 N, 262.894999 E) | SE (32.705 N, 262.904999 E) | Missing |
| --- | ---: | ---: | ---: | ---: | ---: |
| `MESH_00.50` instantaneous **00:42:43Z, −17s** | **11.8 mm** | **18.4 mm** | **16.2 mm** | **23.6 mm** | 0 of 4 |
| `MESH_Max_30min_00.50` rolling max **00:44:00Z, +60s** | **20.0 mm** | **28.5 mm** | **22.0 mm** | **24.2 mm** | 0 of 4 |
| **Separate NWS mPING E3.25-inch categorical hail report at 00:43Z** | colspan concept only | | | **82.55 mm estimated** | n/a |

**Interpretation:** Both the 2-minute and the rolling-30-minute source estimates at the rounded report location are substantially lower than the NWS preliminary reported **82.55 mm** category. Unlike the selected **2021 Keller** case, whose 30-minute four-neighbour maxima were **67.8–77.8 mm** against a separately reported **63.5 mm**, the selected **2024 Arlington** case's rolling maxima at the same four-neighbour protocol are only **20.0–28.5 mm** against a categorical **82.55 mm**. This **falsifies the unwarranted generalization** that one positive Keller 30-minute near-match establishes broad algorithm quality. It is **not** proof that the 2024 radar algorithm was physically wrong: a mPING category is not instrument-calibrated, its point coordinate can be rounded, storm motion and nearby spatial maxima can differ, and the 30-minute product's time support and QC require investigation.

The original NWS product contains a second same-minute hail report of **E1.75 inch** at **32.71 N, −97.11 W**, alongside **E3.25 inch** at **32.71 N, −97.10 W**. They must **not** be treated as two independently arriving catastrophic events. The NCEI later storm-events row identity `1186553` is a candidate based on secondary indexing; acquisition/validation of its exact original NOAA NCEI event CSV is still an open provenance gate.

### Guardrails and next scientific step

- **Independence is by historical physical storm**, not by hailstones, four radar cells, product timestamps, 30-minute windows, NWS/mPING or NCEI reports. There are now *two selected dated storm tests*, not a representative sampling framework, a validation dataset or an event-rate estimator.
- Missing MRMS codes `−1` (source missing) and `−3` (no coverage) are kept distinct from valid `0` and positive hail estimates in each source product. This case has **zero missing among the four selected cells**, not evidence of complete nationwide coverage.
- The future falsifiable experiment should compare **a small independently pinned bounded spatial neighbourhood and several clock windows**, plus independent NWS/NCEI location uncertainties, without inferring insured losses, damage cost, portfolio TIV or CAT model fitness.
- No automated production ingest, vendor-style event catalogue, ELT/YLT or risk-model admission follows from this experiment; those require event-clustering, population-level observational controls, NOAA algorithm-version evidence, source licensing and model validation.

**No third-party original pixels/files or mPING users' private records enter public GitHub; only fixed source references and selected bounded public-science verification results appear here.**
