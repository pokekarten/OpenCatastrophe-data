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
- `COPC` capability is **not** established by the `.laz` extension
  or by the LAS point format; original LAS VLR/EVLR metadata must
  be separately read and validated first.

The original-source GitHub workflow triggers one read-only acquisition,
without files or artifacts, and includes 15 synthetic format/safety tests.
Strict HTTP206 and `Content-Range` validation abort before touching
a potentially huge HTTP200 body. No arbitrary source or network redirects.

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
