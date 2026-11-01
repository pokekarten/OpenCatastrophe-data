<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Building-masked Luxembourg LiDAR 2024 **surface steepness**, not measured roof pitch

**Research state: 2026-11-01. Research-only.** No insurer exposure data, property-level gradients, roof facet attribution or source admission.

## Why this is the next causal experiment

The Luxembourg **solar** WMS roof-facet endpoint returned **401 Unauthorized** without credentials in merged PR #954, even though its documentation names `tilt`, `aspect` and `area3d`. Its separate downloadable building DBF (merged #951) does **not** contain those fields. An alternative is to test whether approved building masks and **actual official** 2024 airborne LiDAR MNS (surface) / MNT (terrain) spatial tiles support a limited geometric steepness diagnostic.

Merged PR #957 already acquired the actual publisher-hosted 2026 GeoBase building GeoPackage and 0.5m original remote MNS and MNT raster windows: a fixed **100×100m Luxembourg-city equal-area region**, 104 true intersecting polygons, 97 eligible MNS-minus-MNT object-height proxies, 23,293 uniquely assigned pixels and 350 multiply assigned pixels excluded. All these values remain research proxies, **not certified building heights**.

This PR builds on the **same exact original sources and same already-reviewed small 100m geospatial read**: no additional source downloads, original file copies or source-specific access endpoints are introduced.

## Safeguarded local surface-gradient method

`research_runners/luxembourg_lidar2024_building_interior_gradient_v0.py` is a helper invoked by the existing original-source
`research_runners/luxembourg_geobase_lidar2024_object_proxy_v0.py` after its standard original-source hash/range/CRS, polygon and raster checks. It uses only in-memory MNS/MNT arrays and clipped GeoBase polygons.

- First mask the exact source footprints to the exact study ROI, and compute a per-raster-cell occupancy count. Exclude pixels covered by **two or more** footprint polygons from slope calculation.
- Require each **five-point central-difference stencil** (center, left, right, up and down) to be valid, within the **same single footprint**, with valid coincident surface and ground elevations, and `MNS−MNT ≥ 3m`. This excludes outer polygon margins and adjacent building facades as far as the discrete 5-cell stencil permits.
- Compute local MNS surface gradient using the native 0.5m pixel spacing. Reject uncalibrated MNS−MNT >200m or nonfinite values and do not infer ground truth from invalid coordinates.
- Exclude local slopes of 70° or greater as potential facades/artificial vertical edges; these excluded pixels are explicitly counted. Require **at least 12 valid interior stencils per polygon**.
- Classify only the **median local surface-steepness angle per eligible object** into predefined histogram bins 0–5°, 5–15°, 15–30°, 30–50° and 50–70°. Never export any individual building ID, geometry, local slope or raster values. Conserve source object counts between eligible and rejected classes.
- Test synthetic continuous planar gradients, flat surfaces, overlap exclusions, no-data, invalid CRS pixel geometry, area boundaries, steep facades and nonphysical height differences with pinned NumPy/Rasterio/Shapely.

**Important scientific distinction:** MNS gradients may be driven by dormers, parapets, vegetation, cranes, aerial sampling, mixed elevations, façade inclusion and edge artifacts. A *surface-steepness proxy within a polygon* **does not measure true roof facet slope**, and angle/sun orientation are not inferred. Using a 3m above-terrain filter does not prove all retained cells represent roofs. The 2024 LiDAR and 2026 GeoBase vintages may contain newly built/demolished buildings, and the original CRS axis direction, vertical datum, complete 40GB COG SHA and independent ground truth remain unchecked.

## Original source read and acceptance

The existing dedicated `.github/workflows/luxembourg-geobase-lidar-object-proxy.yml` now exercises both the previous 13 synthetic mask tests and the new gradient tests in a pinned spatial environment, then runs the original GeoBase ZIP/GPKG SHA check and **the same original remote 100m MNT/MNS bounded-read job**. No original building records, dense rasters, per-object gradients, private residential addresses or photogrammetric models enter GitHub artifacts or the independent Neon insurance database.

The report explicitly contains:
- `true_roof_pitch_validated = false`;
- `solar_facet_tilt_or_aspect_observed = false`;
- `vegetation_and_rooftop_equipment_separated = false`;
- `model_input_admitted = false`.

A successful execution demonstrates **only** that a bounded physical source gradient can be measured within existing building mask pixels, and yields **aggregate** diagnostic bins.

**Next, before scientific admission:** compare to independently measured roof-facet polygons and original classified LAZ building/vegetation labels, use independent geodetic/vertical control points, manually review a stratified rural/urban source sample, and measure estimator bias/precision on agreed roof segments. Insured values, structural vulnerability classes and PV system equipment remain separate evidence questions.
