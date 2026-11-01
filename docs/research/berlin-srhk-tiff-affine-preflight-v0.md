<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin Starkregen: source-TIFF affine header and 200 m pilot-coverage gate (v0)

**Research-only, 2026-11-01. This PR contains no new original provider reads.**

## Exact independent source lineage

The original Berlin official Atom child advertises separate extraordinary and
extreme water-depth ZIPs. The existing source-specific ZIP-range and TIFF
first-IFD probe, `research_runners/berlin_srhk_zip_first_tiff_header_v0.py`,
has verified 65,536 bounded original compressed bytes per source and the
internal `ProjectedCSTypeGeoKey` EPSG:25833 (source receipt in
`docs/research/berlin-starkregen-source-access-preflight-20261101.md`).
The official 2025 technical PDF generally described EPSG:25832; the original
two TIFF's internal 25833 key is stronger evidence for *those specific files*.
This separate code change does not claim to have independently re-read either
original source. The source is not admitted for CAT modelling.

## New strictly offline parser

`research_runners/berlin_srhk_tiff_grid_affine_v0.py` parses *only* an
authenticated, decompressed **classic TIFF header prefix**, capped at **1 MiB**.
The existing fixed-original 65,536-byte ZIP-range reader invokes it in the
same in-memory data path, after its pinned 512-byte source hash, HTTPS 206,
exact object length/vintage, ZIP and TIFF-first-IFD safeguards.

The new gates require:

- Explicit `ImageWidth` and `ImageLength`; <=250,000 pixels per axis
  and at most ten billion declared cells (metadata only, no allocation).
- One finite north-up `ModelPixelScaleTag` and exactly one
  `ModelTiepointTag`; rejected transform/rotation/unsupported TIFF orientation.
- Explicit projected model type, **RasterPixelIsArea** and **EPSG:25833** from
  a valid, non-duplicated `GeoKeyDirectoryTag`. If any is absent, output
  remains *unknown*: no default CRS/pixel registration is inserted.
- An affine formula using raster tiepoint indices, not just a projected
  EPSG label: `xmin = X - I*scale_x`,
  `ymax = Y + J*scale_y`,
  `xmax = xmin + width*scale_x`,
  `ymin = ymax - height*scale_y`.
- Pure header-extent intersection with the already frozen 200 m ALKIS pilot
  bounding box (EPSG:25833: 391700,5819950,391900,5820150).
  Intersection and **full** bounding-box containment are separate booleans.
  A half-covered box never becomes full valid support.

Malformed, duplicate, contradictory or unsupported tags are blocked.
Truncated/out-of-prefix tags return `header_only_georeferencing_verified=false`
and *null* coverage fields, **never** dry flood depths or false certified
source coverage. PixelIsPoint requires a separate half-pixel convention
review. No arbitrary image/file path, provider URL, feature ID, individual
building value or pixel sample is added by the parser.

## Reproduction and interpretation

```bash
python -m unittest tests.test_berlin_srhk_tiff_grid_affine_v0 -v
python -m unittest tests.test_berlin_srhk_zip_first_tiff_header_v0 -v
```

Eight local synthetic tests prove supported header, little/big-endian parsing,
tiepoint shift, partial/outside coverage, missing metadata and adversarial
CRS/convention/type cases. The original TIFF worker has existing separate
synthetic HTTP/range tests; they must pass together in repository CI.

A future **reviewed and merged** source-triggered run may report the affine
metadata of each exact original depth object if all critical tags fit the
existing capped TIFF prefix. Until an original execution is observed,
**neither actual provider affine/bounds nor Berlin pilot raster coverage is
confirmed**. Even successful header coverage is not valid depth support:
pixel value scale/units, NoData, raster tiling, full source byte digest,
source time, scientific rights and individual BLD4 building intersections
remain **unverified**. No insured value, flood loss or event frequency is
computed.

References:
- https://docs.ogc.org/is/19-008r4/19-008r4.html
- https://www.geoportal.de/info/fb5bcb65-6dcc-475b-8a37-c023ce19203b
- https://gdi.berlin.de/data/ua_srhk/docs/Datenformatbeschreibung_SRHK_2025.pdf
