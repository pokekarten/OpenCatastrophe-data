<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg LiDAR2024: locate actual tiles for the ACT/EUBUCCO 250 m city pilot

**Stage:** genuine original tile-index lookup; **not** a source geometry or CAT model input admission.

The ACT source lidar2024-ta.gpkg was successfully read from the official public provider and checked against the published SHA-1 on 2026-11-01 in merged PR #931:

- Original file resource: https://data.public.lu/en/datasets/r/04cfeb86-c9df-4ee6-a45a-8671af98a114 .
- Original SHA-256: 3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8 (original SHA-1 3269aecb189271e7c3f86127c0e96f4e213557c9 matches provider).
- Exact TableauAssemblage feature layer contains **10,905 EPSG:2169 polygons**, actual RTree present, original columns fid, geom, Fichier, Dossier, and DownloadLink.

## Operational lookup

research_runners/luxembourg_lidar2024_fixed_tile_candidates_v0.py validates the **original provider SHA-1 and previously observed SHA-256** before reading a single spatial row. It uses the **identical 250 m by 250 m public Luxembourg-city window** from the merged PR #924 original ACT/EUBUCCO diagnostic, centered at approximately **6.1319°E, 49.6116°N**, first defined in equal-area EPSG:3035, converted to EPSG:2169 using pinned PyProj and the same provisional as-stored XY interpretation as the earlier original-source research.

It only uses the official rtree_TableauAssemblage_geom intersection **bounding box** lookup, with a strictly capped number of tile candidates. It emits **only** candidate count and HTTPS-link host counts. It does not emit Fichier, Dossier, fid, the actual DownloadLink full path, or any source polygon/building identities. Exact polygon intersection, source axis ground controls, URL safety, actual file access and provider tile LAZ bytes remain separate gates.

Offline reproduction:

~~~bash
python -m pip install pyproj==3.7.2
python -m unittest tests.test_luxembourg_lidar2024_fixed_tile_candidates_v0 -v
python -m research_runners.luxembourg_lidar2024_fixed_tile_candidates_v0 --original-gpkg /private/official/lidar2024-ta.gpkg
~~~

The workflow .github/workflows/luxembourg-lidar2024-city-tile-lookup.yml retrieves **only the fixed 3.5 MB source index** into an ephemeral GitHub runner and produces a reproducible count/host audit, not any original LAZ or height samples. It aborts on original source drift, missing RTree, wrong schema/CRS, empty geographic coverage, malformed window or more than 12 candidate tiles.

## Next actual measurement gate

After a successful source-index spatial lookup, manually review one exact public DownloadLink format and original provider endpoint/resource licence. The index's DownloadLink is publisher data, not automatically authorised network execution. Download just **one** objectively selected authorised source LAZ group into temporary storage with SHA256, compressed/expanded limits and LAS/COPC metadata validation. Align class codes and vertical datums; derive roof versus ground 2024 height using classification building=6 versus ground=2, avoiding vegetation. Compare with EUBUCCO height (observed/estimated groups) and ACT 2023 zmin under checked dates; use height bias/MAE and uncertainty. All results research-only until independent controls, upstream overlap and rights verified.

**Do not claim:** building-construction year, precise insured location, property value/TIV, actual validated building height, scientifically independent accuracy, flooding depth, or source model admission.
