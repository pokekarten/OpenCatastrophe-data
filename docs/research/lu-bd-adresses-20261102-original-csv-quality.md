<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT BD-Adresses original 2026-11-02 CSV: bounded quality and identity receipt

**Research-only, 2026-11-04.** Follow-on to the live official original-provider
[metadata receipt](lu-bd-adresses-20261102-live-metadata-receipt.md).
The publisher API verified the fixed original CSV resource ID
`5cadc5b8-6a7d-4283-87bc-f9e58dd771f7`, size **28,209,815 bytes**, published
MD5 **`946114c1a24b49471b580bc225e4cb25`** and dated download path
[`20261102-033122/addresses.csv`](https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/20261102-033122/addresses.csv).

## Exact original-asset test

The narrowly scoped GitHub Action
[`luxembourg-bd-adresses-20261102-original-csv.yml`](../../.github/workflows/luxembourg-bd-adresses-20261102-original-csv.yml)
downloads **only this official 28.2 MB CSV** into private runner temporary storage.
The reader
[`research_runners/luxembourg_bd_adresses_20261102_csv_original_v0.py`](../../research_runners/luxembourg_bd_adresses_20261102_csv_original_v0.py)
checks the exact original byte count and publisher MD5, independently hashes
the **actual downloaded file** with SHA-256, and reads rows with a bounded
standard-library UTF-8 CSV parser. It emits source header **names**, delimiter,
aggregate record count and, only when WGS84 latitude/longitude columns can
be unambiguously identified, counts of valid, missing, invalid and exactly
repeated coordinate pairs. No address value, source row, building ID, location,
private insured exposure, policy number or original raw data file is emitted
or committed. Original bytes are deleted on runner exit.

**Important:** source-publisher MD5 is not a signed authenticity guarantee.
An independently observed original-file SHA-256 establishes reproducibility
of downloaded bytes but is not evidence of licensing or source independence.
The workflow fails closed on any source byte drift, oversized inputs, malformed
CSV, ambiguous header, inconsistent row width or unexpected schema.

## Scientific boundary

ACT explicitly warns that address points are not real building entrances,
may derive from parcel/largest-building centroids, can be identical across
addresses, and are not complete. This CSV belongs to the **same ACT provider
family** as the independently validated GeoBase Buildings 2026 source;
it is not an independent ground-truth sample against ACT.

A valid coordinate point is not necessarily associated with a single
building. The exact-source original files can inform a bounded diagnostic
candidate linkage via the merged
[`point_footprint_linkage_diagnostic_v0.py`](../../scripts/point_footprint_linkage_diagnostic_v0.py)
only after a separately approved, explicit CRS/namespace/vintage/
spatial-quality contract; that diagnostic still does not confer insured
building identity, TIV, event hazard severity or model admission.

## Execution status

Source and tests prepared; **no exact original-CSV result should be claimed
until the dedicated workflow passes at the matching Git commit**.
If the original source schema differs from the presumed UTF-8 CSV reader,
do not weaken file hash/date/size checks: inspect the original publisher
format and adjust only the parser with new synthetic regression evidence.
