<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin BLD4 polygon and synthetic flood-depth cell support v0

**Research-only prototype.** This retrieves no external flood data, creates
no source rights, and produces no actual event frequencies, losses or insured
claims. The goal is to verify exact spatial area accounting on a tiny,
explicitly synthetic hazard grid before considering reviewed real rasters.

## Independently validated building input

The real official five-building ALKIS source sample and ephemeral BLD4
SQLite staging are documented in
docs/research/berlin-alkis-buildings-wfs-access-v0.md. The source snapshot
was deleted after the real test. This script requires a separate, locally
available BLD4 file; it never reconstructs source bytes or downloads them.

The reader requires SQLite application ID 0x424c4434 (BLD4, not the source
registry application ID 0x43415434), original BLD4 schema, known WFS response
SHA-256, 2021 administrative region vintage, explicit DE3, source rights
dl-de-zero-2.0 and model_admitted=0. Oversized or symlinked files,
overlapping geometries and unsupported database schemas fail closed.

## Synthetic hazard grid JSON contract

The only supported shape is:

    {
      "profile": "synthetic-berlin-flood-depth-cells-v0",
      "source_class": "synthetic_test_only",
      "crs": "EPSG:25833",
      "peril": "flood_water_depth",
      "unit": "m",
      "top_left_x_m": 391780,
      "top_left_y_m": 5820080,
      "cell_size_m": 10,
      "width": 2,
      "height": 2,
      "cells": [[1.0, 0.0], [null, null]]
    }

All coordinates are invented projected metre coordinates, with square cells
anchored top-left, positive X columns and negative Y rows. Positive depth is
synthetic wet support, zero is valid dry support, and JSON null is NoData.
Area outside the grid is a fourth, distinct unsupported category. A pixel's
absence is never inferred as dry.

The adapter computes exact polygon-cell intersection area in m2, not a
centroid-only classification. Wet, dry, NoData and outside-grid areas must
add to the original footprint area. Limits: five distinct, non-overlapping
building polygons and 1,024 grid cells; depth values 0–30 synthetic metres.

Reported information is only aggregate area, counts, source-response and
synthetic JSON SHA-256 hashes and explicit non-admission flags. No per-building
geometry, feature ID, coordinates, attributes or monetary values leave the
local process. No persistent DB is written by this adapter.

## Reproduction

With a locally available original-derived BLD4 file and a small synthetic
grid.json matching the contract above:

    python -m pip install -r requirements-eu-flood-spatial.txt
    python -m unittest tests.test_berlin_bld4_synthetic_flood_cell_join_v0 -v
    python -m research_runners.berlin_bld4_synthetic_flood_cell_join_v0 --buildings /secure/cat-data/staging/berlin-5-buildings.cat.sqlite --synthetic-grid /secure/cat-data/staging/grid.json

Paths are illustrative and not created by the script. A dedicated GitHub
Actions workflow installs pinned Shapely/PyProj, checks their import and runs
all 10 synthetic tests, with no third-party network requests.

## Required before any real flood exposure join

A real hazard source requires rights review, exact provider identity,
source byte counts and SHA-256, a bounded raster reader, CRS and axis
order, vertical datum, depth units, validity/NoData masks, event timestamps,
return-period versus observed-event semantics, temporal alignment with the
building snapshot, and scientific uncertainty controls. The current WFS
building geometry cannot be asserted to have existed at a historic event
time. This adapter deliberately refuses a real provider grid even if the
caller tries to rename its source class. It is not a loss or CAT engine.
