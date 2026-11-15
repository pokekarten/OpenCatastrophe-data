<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WorldCover N48E009: bounded header-derived WGS84 cell lookup

**Scope:** one ESA WorldCover 2021 v200 `N48E009` Map tile; synthetic
point-to-cell indexing only. No online request, COG tile read, source raster
pixel, building lookup, insured asset, value, or model input is accepted.

## Scientific basis

[Original TIFF/header proof](esa-worldcover-v200-n48e009-tiff-header-receipt-20261101.md)
and [live georeference verification](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41321446759)
showed a stable sample SHA-256
`a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529`,
EPSG:4326, WGS84 geographic 3°x3° tile bounds
`west=9, south=48, east=12, north=51`, size 36000x36000, one
PixelIsArea band, 1024x1024 internal TIFF blocks, and
`ModelPixelScale=(3/36000,3/36000)` **in degrees**.

This spatial resolution is not a constant 10 metres on the ground,
and the raster's published class accuracy is a product-level statistic,
not a claim about any future specific pixel.

## Pure reproducible consumer

`scripts/worldcover_header_cell_index_v0.py` accepts a header-only
metadata receipt *only if* it matches the exact source identity, sampled
bytes digest, EPSG and tile bounds, dimensions, scale and explicit
no-pixels/no-model-use flags.

A synthetic WGS84 coordinate can then map into the raster grid using:

- `column = floor((longitude - 9°) / (3° / 36000))`
- `row = floor((51° - latitude) / (3° / 36000))`
- internal TIFF block indices are `floor(row/1024), floor(column/1024)`.
- Raster PixelIsArea has **west/north inclusive** and **east/south
  exclusive** bounds. Other coordinates are explicitly reported as
  outside this one tile, not assigned to another guessed source object.

For example, the **synthetic** test coordinate
`(longitude=9.5, latitude=50.5)` maps to
`(row=6000, column=6000)`, TIFF block `(5,5)`,
and local row/column `(880,880)`. These are only integer positions
within a proven header grid, **not the actual land-cover value**.

## Before any real building/insurance enrichment

Independent requirements still include verified point coordinate reference
systems, spatial/geometric validity, source-byte and licence scopes,
download limits, COG block offset/compressed byte mapping, pixel data and
class code validation, temporal consistency (2021 v200) and uncertainty.
A building footprint polygon must not be replaced by a single centroid
without explicit research review. No insurer TIV, customer location,
exposure, claim or risk capital is computed or imported here.

The geographic mapping remains isolated from Pokémon databases and any
live insurer production datasets.
