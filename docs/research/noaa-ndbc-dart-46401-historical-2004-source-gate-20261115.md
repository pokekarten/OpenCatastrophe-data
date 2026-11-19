<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA NDBC DART station 46401, 18–22 January 2004 — fixed T0/T2 canary

Review date: 2026-11-15. Source ID `noaa.ndbc.dart`.
This review freezes **one historical original-provider request identity**, not an
authorized provider download, model/tsunami-event validation, or new data admission.

## Authoritative source identity and format

- Provider's [official station history](https://www.ndbc.noaa.gov/station_history.php?station=46401):
  **46401**, Southeast Adak, owned/maintained by the **National Data Buoy Center**;
  recorded DART historical years **2003, 2004, 2005**.
- Official [station page](https://www.ndbc.noaa.gov/station_page.php?station=46401):
  DART I deployment; station **disestablished on 23 July 2006**. A historical
  station that was operated in 2004 is not a *currently operational* buoy.
- Provider's [DART data-access specification](https://www.ndbc.noaa.gov/dart_data_access.shtml)
  documents the **exact** example:
  `GET https://www.ndbc.noaa.gov/dart_data.php?station=46401&start=2004-01-18&end=2004-01-22`.
  Both date endpoints are inclusive. Its prose inexplicably also refers to a
  January 4–10 example: **the explicit query and shown response headers are
  January 18–22**, and this gate refuses the conflicting prose dates.
- DART `T=1` = 15-minute observations; `T=2` = one-minute; `T=3` = 15-second.
  Source times are UTC in descending order. `HEIGHT` is *water-column height in
  metres*, derived from bottom pressure with the provider's constant conversion.
  This is **not** de-tided tsunami amplitude, an event footprint, return period,
  insured exposure or CAT loss. Deployment, QC and data gaps need independent
  source evidence before any scientific interpretation.

## What is implemented

The new offline-only
[`research_runners/ndbc_dart_46401_historical_identity_gate_v0.py`](../../research_runners/ndbc_dart_46401_historical_identity_gate_v0.py)
reuses the existing bounded NDBC original-format parser, fixing station and
request dates in code rather than allowing a caller to substitute another
station, period, provider host or dataset. It requires a separately obtained
local plain-text body and emits only a SHA-256, row counts, extrema, timestamp
summaries and explicit non-admission flags. Optionally, a *caller-supplied*
64-hex SHA-256 must match the local file, but **that match alone is not
independent original-provider provenance**.

The associated synthetic-only unit tests reject an altered station,
start/end date, out-of-window observation, changed units, untrusted checksum,
HTML/error body and symlink. They also confirm that a matching caller-provided
digest does not promote source/authenticity/rights/model approval.

Local test:

```bash
python -m unittest tests.test_ndbc_dart_original_preflight_v0 tests.test_ndbc_dart_46401_historical_identity_gate_v0 -v
```

A previously and separately authorized local copy (not bundled or provided by
this repository) may be checked with:

```bash
python -m research_runners.ndbc_dart_46401_historical_identity_gate_v0 \
  --file /private/approved-46401-2004-source-body.txt
```

## Gate results and what remains blocked

| Gate | Status | Boundary |
| --- | --- | --- |
| T0 station/owner/date/request identity | **Pinned** | Official historic NDBC source and request |
| T1 source service probe | **Not executed** | `access/noaa.ndbc.dart.json` remains `documented_only` |
| T2 synthetic parser/identity | **Executable tests** | Tested format, not authenticated original bytes |
| T3 original-provider response | **Not acquired** | No original byte count/SHA-256 receipt or deployment/QC lineage |
| T4 CAT-model input | **Blocked** | No rights clearance, scientific event or independent validation |

The source-access contract still has
`dataset_rights_status=not_reviewed`,
`api_terms_status=unknown`,
`commercial_automation_status=unknown`, and
`redistribution_status=unknown`. NDBC hosting and NDBC station ownership
do **not** establish the exact commercial, automated-use, storage or
redistribution permissions. NDBC TAO product notices must not be silently
generalized to this DART product, nor vice versa.

Next causal step: review the **exact station 46401 / January 2004 DART product**
and HTTP service conditions (including commercial modelling, provider-owned
rows, bounded retrieval, readback and persistence ceilings). Only if those
rights explicitly permit it, run one trusted bounded original GET, capture
original status/final URL/content type/byte count/SHA-256 in a private
authorized receipt, run this identity parser and perform independent data-QC
and deployment checks. No source data bytes enter public Git in this stage.
