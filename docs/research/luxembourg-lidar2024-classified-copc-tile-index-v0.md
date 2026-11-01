<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT Luxembourg LiDAR2024 — original classified COPC point-cloud tile index

**Date:** 2026-11-01. **Research-only, no source admission.**

## Independent new signal: building vs vegetation classification

The existing OpenCatastrophe building height and interior surface gradient
proxies in two fixed 100m × 100m windows use official ACT 2024 MNT (terrain)
and MNS (surface) COGs and October 2026 GeoBase footprints. The
MNS contains **both** building *and* vegetation objects, so a positive
MNS–MNT difference and an apparent within-polygon slope **cannot establish**
roof height, actual roof angle, roof material, or clean roof support.

The same official 2024 campaign published an **original classified COPC
LiDAR point cloud** alongside the COG rasters, unlike the mixed surface
raster. In the ACT official source catalogue:

- Ground `class 2`
- Low vegetation `class 3`
- Medium vegetation `class 4`
- **High vegetation `class 5`**
- **Buildings `class 6`**
- Other/artifact classes `1, 7, 9, 13, 15`.

Source: <https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/>,
**CC0** original product as declared by publisher. Original 2024
survey published December 2024 / updated February 2025.
The 0.5m cloud-optimized MNT/MNS are derived from this same source family,
therefore classified points are **not scientifically independent of
MNS**, despite their greater class specificity. `Class=6` is a
producer algorithm label, not human-certified true roofs.

The COPC files contain 500m×500m LAZ tiles, grouped up to 9 tiles per
ZIP archive (1.5km×1.5km). Total country point-cloud data exceed
**2 TB**, so downloading all files is neither necessary nor acceptable
for this bounded research experiment.

## First preflight: exact original small public tile-assembly GeoPackage

Publisher exact tile index resource:
<https://data.public.lu/en/datasets/r/04cfeb86-c9df-4ee6-a45a-8671af98a114>.
Immutable candidate original HTTPS URL:
<https://download.data.public.lu/resources/lidar-2024-releve-3d-du-territoire-luxembourgeois/20250117-095958/lidar2024-ta.gpkg>.

The publisher lists **3.4 MB** and source SHA-1
`3269aecb189271e7c3f86127c0e96f4e213557c9`
(not self-computed). The new
`research_runners/luxembourg_lidar2024_classified_tile_index_v0.py`:
1. Downloads **only** this official small index through the isolated
   GitHub runner workflow; max 6 MiB, HTTPS-only, timeout and no retries.
2. Requires the file's actual original SHA-1 match the **publisher's
   already-published** digest; prints newly computed SHA-256 separately.
3. Parses the immutable SQLite GeoPackage only in read-only mode,
   verifies a genuine EPSG:2169 source polygon layer, bounds count
   to <=25,000, and rejects malformed WKB/CRS/data.
4. Selects **the exact predeclared fixed 100m study ROIs**: Luxembourg
   city centre (6.1319E, 49.6116N) and Berdorf village centre
   (6.348821E, 49.820946N), under the existing *unverified native
   axis* assumption, never arbitrary private addresses. The original
   100m equal-area windows, not ad hoc site sizes, remain unchanged.
5. Returns **bounded tile/package reference fields and counts**, without
   opening COPC/LAZ, reading building point positions or exporting original
   tile geometry.

The exact 3.4MB GeoPackage schema and the actual small overlap
counts must be reported from successful GitHub Actions original bytes,
rather than guessed from the filename or national tile count.
Reject unsupported index schema and avoid blindly downloading a >1GB
archive from a guessed tile/group identifier.

## Actual original-source index receipt — successful 2026-11-01 test

Original provider-download GitHub Actions run:
<https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41319076447>.
**All ten synthetic tests passed**, and actual ACT source bytes were
successfully acquired, SHA-1 validated against the **original publisher
catalogue**, read as read-only GeoPackage and intersected with the
two predeclared fixed public 100m research polygons.

| Verified property | Original measured result |
| --- | --- |
| Source index GeoPackage full bytes | **3,518,464** |
| ACT-published SHA-1, independently matched | `3269aecb189271e7c3f86127c0e96f4e213557c9` |
| Independently computed whole-index SHA-256 | `3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8` |
| Actual table | `TableauAssemblage` |
| Geometry / CRS | `geom` Polygon, **EPSG:2169** |
| Original source tile-index rows | **10,905** |
| Actual columns | `fid, geom, Fichier, Dossier, DownloadLink` |
| Original tile polygons overlapping fixed Luxembourg-city ROI | **1** |
| Original tile polygons overlapping fixed Berdorf village ROI | **4** |
| Original point-cloud/LAS/LAZ record values read | **0** |

**City Luxembourg:** official tile `77000_75500`, original package
permalink <https://data.public.lu/fr/datasets/r/9bc4df35-4c5a-4d79-8a05-a2faadd6dab1>.

**Berdorf village:** original tiles
`92500_98500` and `93000_98500` share source package
<https://data.public.lu/fr/datasets/r/1e68ff5f-9182-42a4-8222-7496f3b689d7>;
`92500_99000` and `93000_99000` share
<https://data.public.lu/fr/datasets/r/ff8e2bac-b1aa-441a-82a6-9af4221a1fab>.

Thus **five 500m×500m tiles** located in **three source group-archive
resources** are sufficient to geographically cover the two preselected
100m×100m research windows. These source IDs are **real original tile
directory references**, not guessed archives. The two separate groups
near Berdorf meet at a 500m tile-grid boundary, but a tile polygon
overlap is not evidence the full source LAZ points have been obtained,
classified accurately, or approved as model inputs.

No 2024 classified point records have yet been downloaded. The
original SHA-1 integrity success applies to the **tile index only**, not
to any of the three ZIP archives or their internal COPC/LAZ tiles.
Original ZIP sizes, declared hashes and actual LAS point-class
histograms remain to be verified independently. Scientific
independence, class-6 rooftop accuracy and the vertical datum remain
unproven.

## Next stage, only after the index validates

Choose precisely one publisher-original group archive covering the
fixed study area, with source URL, complete file size, original
SHA-1/SHA-256, point-classification schema, CRS/vertical-datum provenance
and extracted exact per-tile COPC metadata. If the archive is too large,
evaluate a publisher-approved bounded COPC range-query implementation.
Do **not** attempt unauthorized bulk scraping or bypass restrictions.

At the next scientific gate, compare **inside the same GeoBase footprint
masks**:
- MNS2024 minus MNT2024 existing mixed-object height proxy,
- original source `class=6` building-point heights and density,
- presence/density of `class=5` high-vegetation points,
- undecidable / class-uncertain footprints.

A discrepancy can flag *possible* canopy contamination, but classes
are still the producer's classified data (not independent truth).
Manual reference roofs/vegetation checks and source-specific legal/
scientific review remain necessary before any validated building
attributes, roof angle or vulnerability modelling.

**Never:** upload raw LAZ/COPC, point clouds, exact building IDs or
per-household spatial data to the public GitHub, light Neon metadata
registry, Pokémon database or insurer exposure tables. No rights
promoted and no CAT model inputs admitted by an index receipt.
