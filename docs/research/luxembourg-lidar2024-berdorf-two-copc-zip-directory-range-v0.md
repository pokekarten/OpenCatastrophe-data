<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berdorf: real official 2024 classified LiDAR COPC/LAZ grouped ZIP directories

**Stage:** bounded original-source metadata inspection; no actual classified points and no CAT/insured model-input admission.

The official ACT LiDAR2024 tile index (merged #975) found four
500m tile polygons covering the fixed 100m Berdorf village study
site. They are grouped into two original public 2024 ZIP resources,
and the publisher metadata and actual original archive HEAD sizes and
SHA-1 metadata were independently verified in merged #987:

| Fixed group | Original resource ID | Whole original ZIP bytes (actual HTTP HEAD) | Publisher SHA1 *unverified against entire original file* |
| --- | --- | ---: | --- |
| Berdorf south, `Lidar2024_C030_R028` | `1e68ff5f-9182-42a4-8222-7496f3b689d7` | **1,701,393,927** | `45d154470b4a06f99f569b6294a2773bab504ec9` |
| Berdorf north, `Lidar2024_C030_R029` | `ff8e2bac-b1aa-441a-82a6-9af4221a1fab` | **1,736,263,124** | `773f6a2375e03d821149addcc5717903e54166f1` |

Public portal https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/ .

Prior city group research #991 proved the official provider supports exact HTTP
206 byte ranges to read the ZIP EOCD and central directory, finding nine
actual .laz members and one city tile reference in a 1.70GB original ZIP
while downloading only 66,106 ZIP metadata bytes.

## This exact two-original-source extension

`research_runners/luxembourg_lidar2024_berdorf_copc_zip_directory_range_v0.py`
uses the **same safety-reviewed ZIP parser and range reader as #991**,
with only the two exact original public Berdorf resource UUIDs,
publisher-advertised original whole file lengths and source SHA1 metadata.

For each group, it:

1. Fetches <=256KiB of original resource JSON and requires UUID, actual
   publisher filesize, published SHA1 and exactly derived original ZIP name.
2. Rechecks HTTPS original archive HEAD and exact published file length.
3. Requests exactly **65,557 bytes** of ZIP tail by strict HTTP 206.
4. Parses normal ZIP EOCD, then reads only the strictly bounded central
   directory <=256KiB by another HTTP 206. Abort if server sends full
   1.7GB HTTP 200, needs ZIP64/oversized metadata, uses unsafe/encrypted
   filenames or unexpectedly changes original byte counts.
5. Uses the original safe ZIP parser and looks for the **two predeclared
   village tile identifiers in each group**, each **exactly once**:
   south `92500_98500` and `93000_98500`, north `92500_99000`
   and `93000_99000`. It reports only counts, never the other
   member filenames, member byte offsets, LAZ contents or any
   point/building locations.
6. Performs no full-archive ZIP GET, no LAZ decompression and no
   actual class 2/5/6 point observation. The source-specific published
   SHA1 values are not cryptographically confirmed by HTTP metadata.

A bounded source workflow plus nine deterministic fake-network and
synthetic central-directory tests prove the class/source constraints
before the real original-server check. Live original source outputs are
to be recorded *after* the hosted workflow succeeds, not guessed.

## Why it improves CAT data quality

Merged #984 has 14 unique city/village independent-geometric-mask
comparisons in Berdorf with observed 2024 DSM-MNT pixels, but
the MNS data include trees and other non-roof surfaces. Knowing the
original COPC/LAZ group membership is a prerequisite for a future
**class 6 building versus class 5 high vegetation** observation
in an independently checked, bounded sample. These classifications
share ACT LiDAR upstream and **are not independent accuracy ground truth**.

No 2024 vertical datum certification, roof-class accuracy, individual
building survey, source redistribution rights or CAT model/exposure
approval is established by this ZIP directory study.

## Actual original official ZIP range results (2026-11-01)

Original source GitHub workflow [41323272332](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41323272332)
completed **successfully** with **9/9 fake-network/synthetic archive tests**
and both real official source ZIP HTTP 206 metadata reads.

| Verified source outcome (real original bytes) | Berdorf south `C030_R028` | Berdorf north `C030_R029` |
| --- | ---: | ---: |
| Publisher JSON/HEAD agreed original full archive bytes | **1,701,393,927** | **1,736,263,124** |
| Exact HTTP206 original ZIP tail acquired | **65,557 bytes** | **65,557 bytes** |
| Exact HTTP206 original central-directory acquired | **549 bytes** | **552 bytes** |
| Parsed original ZIP member count | **9** | **9** |
| Members ending in `.laz` | **9** | **9** |
| Members ending in `.copc.laz` | **0** | **0** |
| Expected published study tiles appearing **exactly once** | **2 of 2** | **2 of 2** |
| Original LAZ payload, LAS point count, class 2/5/6 contents acquired | **NONE** | **NONE** |

That means **18 real original LAZ file entries across the two official
Berdorf group ZIPs**, with all four predeclared fixed village tiles
accounted for exactly once. Original ZIP directory bytes downloaded
for Berdorf total only **132,215 bytes**, compared with the
**3,437,657,051-byte** combined full archives. HTTP range requests
remained bounded, and the source-metadata SHA1 values remain *publisher
reported, not archive-byte verified*. Each internal LAZ name was parsed
only transiently, never written into the source report. The file
suffix alone does **not** prove COPC compliance, class-6 building-point
coverage, vertical datum or roof/classifier accuracy. Those need actual
LAS public headers and later an independently quality-controlled
spatial point-class sample.

Combined with the **9 real city LAZ entries** from merged #991,
the **three original archives contain 27 LAZ entry names**, of
which the **five specific studied 500m tile entries** are all now
present in actual publisher ZIP central directories. These are
source-directory findings, not 27 independent buildings or 27
downloaded data files. No CAT exposure/model-input admission occurred.
