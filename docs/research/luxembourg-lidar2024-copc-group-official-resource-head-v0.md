<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT LiDAR2024: independent original resource-metadata & HEAD for 3 classified COPC archive groups

**2026-11-01 — research-only. No COPC/LAZ bytes or actual class-6/class-5 point observations.**
This follows verified original ACT LiDAR2024 index #975 and city/Berdorf paired original
2024 MNS−MNT height-proxy sample #984. We must not assert the MNS raster
measures roofs because it also contains vegetation and other returns.

## Known original source locations, *not guessed filenames*

Merged #975 acquired the exact publisher LiDAR2024 tile-assembly GeoPackage,
verified original SHA1 `3269aecb189271e7c3f86127c0e96f4e213557c9`
and independently observed whole-source SHA256
`3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8`.
Within two fixed public 100×100m study polygons the original index says:

| Site | Actual original COPC tile-name examples | Official grouped source resource ID |
| --- | --- | --- |
| Luxembourg city | `77000_75500` | `9bc4df35-4c5a-4d79-8a05-a2faadd6dab1` (`Lidar2024_C020_R013`) |
| Berdorf south | `92500_98500`, `93000_98500` | `1e68ff5f-9182-42a4-8222-7496f3b689d7` (`Lidar2024_C030_R028`) |
| Berdorf north | `92500_99000`, `93000_99000` | `ff8e2bac-b1aa-441a-82a6-9af4221a1fab` (`Lidar2024_C030_R029`) |

Publisher: https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/ .
Individual resources: https://data.public.lu/en/datasets/r/9bc4df35-4c5a-4d79-8a05-a2faadd6dab1 ;
https://data.public.lu/en/datasets/r/1e68ff5f-9182-42a4-8222-7496f3b689d7 ;
https://data.public.lu/en/datasets/r/ff8e2bac-b1aa-441a-82a6-9af4221a1fab .

These are **3 packaged original ZIP source group resources**, not 5 separately
downloadable original LAZ files. The earlier #940 city source group was about
1.70 GB, so downloading all three without a cost/contents budget is unsuitable.

## Implemented low-cost source-access gate

`research_runners/luxembourg_lidar2024_copc_group_resource_head_v0.py`
contacts exactly three fixed official public uData metadata resources, one
JSON `GET` for each original `/api/1/datasets/.../resources/{uuid}/`,
then one HTTPS `HEAD` on the original `download.data.public.lu` ZIP
address provided by that resource, only if it (a) has the correct source
group name, (b) is under an official `/resources/` HTTPS path with no
credentials or query, (c) is ZIP, (d) matches the exact official resource
UUID. Redirects are blocked rather than following unknown hosts.
Metadata is bounded to 256KiB per resource.

Original ZIP size must be >1KiB and <=4GiB; both actual `Content-Length`
and any integer publisher-reported size must agree. Valid publisher SHA1/MD5
or SHA256 metadata is reported **as *publisher-reported and unverified***,
not as if archive bytes had been rehashed. Lack of any publisher digest is
explicitly allowed but will block later identity admission until an original
full-file SHA256 is computed. The original archive is never acquired by
this step; 3 resource JSON bodies and 3 HEAD responses only.

```bash
python -m unittest tests.test_luxembourg_lidar2024_copc_group_resource_head_v0 -v
python -m research_runners.luxembourg_lidar2024_copc_group_resource_head_v0
```

A dedicated exact-head hosted GitHub Actions source run performs 11 synthetic
fake-network tests plus those six real HTTP requests. No arbitrary resource
enumeration, no full ZIP GET, no source point cloud, per-building IDs, source
tile geometries, download URL secrets, insurer values or model data are
persisted in GitHub, Neon or project artifacts.

## Acceptance gates before any class-6 / class-5 study

1. Establish exact official archival resource UUID, direct HTTPS URL, **actual**
   bytes and publisher digest or absence for all three groups through this
   metadata/HEAD audit. Freeze actual observed results in this document.
2. Independently validate an authorized **one-group** bounded archive-acquisition
   plan (separate budget; no large automatic ZIP fetch), original download SHA256,
   CRC/archive member inventory and precise internal COPC source references.
3. Consider a **range-addressable official COPC source** if genuinely provided:
   only bounded LAS/COPC header and spatially filtered class count queries, not
   whole-country point samples. Validate class 2 ground, 5 tall vegetation,
   6 buildings, CRS/vertical datum, point density, classification vintages.
4. Cross-check against the same 26 high-IoU paired city/Berdorf source
   *candidate* geometries; use an independent manual roof/tree reference holdout
   before accepting any **building heights**. ACT class-6 points and MNS
   are shared upstream, not independent truth.

No GPKG, LAZ, class point, vertical datum, source copyright approval, insurer
exposure/TIV or CAT model-input admission is established by this metadata gate.
