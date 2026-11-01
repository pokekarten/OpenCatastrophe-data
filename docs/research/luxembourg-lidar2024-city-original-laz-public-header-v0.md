<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT LiDAR2024: one Luxembourg-city original LAZ header, without downloading the 1.7GB ZIP

**Date:** 2026-11-01. Research and original bytes verification only;
not an admitted CAT vulnerability, independent roof truth, site exposure
or actual producer LAS class count.

## Original publisher evidence before this PR

- Official ACT public classified 2024 point cloud product
  <https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/> lists **ground class 2, high vegetation class 5, building class 6**, classified by the *same* original survey family as the 2024 surface/terrain rasters.
- Original tile-index validated in merged #975: SHA1 from publisher matched and exact city tile `77000_75500` in archive group `Lidar2024_C020_R013`.
- Merged #987 verified direct original publisher resource `9bc4df35-4c5a-4d79-8a05-a2faadd6dab1`, original ZIP HTTP HEAD size **1,700,086,212 bytes** and publisher-reported ZIP SHA1 `f8650c5eee38d941921199a0c6e1f64b985c9b34`. The complete ZIP original hash remains **not byte-verified**.
- Merged #991 used only two exact original HTTP206 byte ranges and proved the real original ZIP contains **nine .laz members**; city study tile `77000_75500` appears **once**, central directory **549 bytes**, no COPC-marked filename. It did NOT read actual LAZ file bytes or prove COPC status.

## This PR: a strictly capped public LAS *header* probe

`research_runners/luxembourg_lidar2024_city_laz_header_range_v0.py`
repeats exact reviewed publisher JSON+HEAD, ZIP EOCD+central directory
checks, and selects exactly the one `77000_75500` LAZ member.
No URL, coordinate, source package or tile selection input is accepted.

- Reject encrypted, ZIP64 sentinel or pathological member entry.
- Inspect the 30-byte ZIP **local member header** and the original
  public basename/extra header bytes, using exact HTTP206 Range, and
  require identity with already-checked central-directory entry.
- If the LAZ member uses ZIP **DEFLATE** compression method 8, **stop**
  at the metadata report and do not claim LAS byte-header access.
  If ZIP method **STORED** 0, request LAS public **first 110 bytes**
  and precisely the remainder of declared public LAS header
  (`227, 235 or 375` total bytes). No source point data is read.
- Validate LAS 1.2/1.3/1.4 signature, header sizes, point format,
  point-data offset, published legacy/extended point counts and
  record lengths, and emit only the source **public header fields**,
  not coordinates or source point records.
- A point *format* with a classification field does **not**
  establish which class values (e.g. 5 or 6) actually occur.
- The initial original file identified **LAS 1.4, format 7 and four public
  Variable Length Records (VLRs)**. The source metadata preflight now also
  requests the exact VLR region between the **375-byte public LAS header**
  and declared **point data offset**, capped at 32KiB and HTTP206-verified.
  Its strict metadata parser checks the COPC specification's mandatory
  **first `copc` info VLR with record ID 1**, **160-byte payload**,
  zero reserved fields and root-hierarchy offset/size bounds inside
  the selected LAZ member. It does **not** fetch the hierarchy page,
  compressed point nodes, XYZ positions or class values.
  Specification: <https://copc.io/copc-specification-1.0.pdf>.
- `COPC` capability is **not** established by the `.laz` extension
  or by the LAS point format; it requires a real COPC info VLR and a
  verified hierarchy. The actual city first-VLR proof has succeeded
  and identified a **12,608-byte root hierarchy page** at local LAZ
  member offset **179,952,913**. A final, capped HTTP206 request checks
  that hierarchy page (exact **32 bytes per octree entry**), verifies
  source point chunk offset bounds, counts embedded/nested page references
  and records only an **aggregate level histogram**. It does **not**
  expose individual octree XYZ keys or fetch compressed point chunks.
  A root page does not necessarily contain the whole hierarchy.

The original-source GitHub workflow triggers one read-only acquisition,
without files or artifacts, and includes **29 synthetic format/safety tests**
for the original ZIP/LAS headers and COPC info VLR.
Strict HTTP206 and `Content-Range` validation abort before touching
a potentially huge HTTP200 body. No arbitrary source or network redirects.

## Verified original-source execution, 2026-11-01

**Original provider GitHub Actions run:**
<https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41322987189>.
All **29 synthetic header/ZIP/VLR/hierarchy tests passed**; exact
original provider HTTPS JSON, HEAD and bounded HTTP206 ranges successfully
read the one actual city `77000_75500` LAS public header, four VLRs and
one COPC root hierarchy page.

| Actual original declared metadata | Result |
| --- | ---: |
| Source ZIP total published bytes (HEAD verified; NOT full hash) | **1,700,086,212** |
| Selected single `.laz` member bytes, ZIP method 0 (stored) | **179,965,521** |
| LAS version / declared point format | **1.4 / 7** |
| Original LAS full public header read | **375 bytes** |
| Original public VLR section read | **1,412 bytes; 4 entries** |
| First `copc` info VLR 160 bytes, original hierarchy pointers checked | **Yes** |
| COPC root hierarchy byte offset *within selected LAZ* | **179,952,913** |
| COPC root hierarchy page size | **12,608 bytes** |
| COPC root hierarchy octree entries read | **394** |
| Nested hierarchy pages required by root | **0** |
| Hierarchy entries referencing compressed point chunks | **394** |
| Total points declared by all root entries | **10,205,549** |
| Original LAS header declared points | **10,205,549** |

Actual octree entry count by public hierarchy level:
**level 0: 1**, **level 1: 4**, **level 2: 16**,
**level 3: 89**, **level 4: 284**. The cross-check of root declared
chunk point-count sum **exactly equals the LAS header population**;
this is meaningful internal structural consistency, not proof of
correct individual point classifications.

**Important remaining evidence:**
- The source ZIP full SHA1 is publisher-reported, **not verified**
  against all 1.7GB original bytes. The selected LAZ compressed chunks
  are **not read**.
- LAS 1.4 and public COPC VLR/hierarchy metadata are verified for
  this **single fixed public city tile only**; other LAZ tile archives
  may differ.
- Actual `class=5` / `class=6` counts, vegetation/building accuracy,
  roof matches, vertical datum and independent survey validation
  remain **unmeasured**.
- The public root hierarchy describes 394 compressed point nodes.
  Their public octree keys, offsets and byte sizes were used only
  internally for metadata integrity and were **not exported** as
  feature-level geospatial or point records.

**Decision:** Move to a separate source-CRS-checked spatial octree
window preflight to determine how many compressed nodes a fixed
100m ROI intersects, without point transfer. Only then consider a
strictly size-bounded, rights-cleared classification diagnostic.

## Scientific gate

Only after confirming exact original LAS/COPC header and identifying
supported VLR hierarchy and LAZ compression can a separately reviewed,
bounded 100m point-level experiment read original **classification values**.
The next study should count ACT-original class=5 vs class=6 within the
already fixed GeoBase building-mask windows, aggregate only (no IDs,
point positions, geolocation or raw points in logs). Producer classes
are NOT independent hand-annotated ground truth and cannot automatically
become insured roof type, insured asset height, resilience score or
vulnerability category.

This source read does not alter Neon, the Pokémon database or
`model_input_admitted=false`.
