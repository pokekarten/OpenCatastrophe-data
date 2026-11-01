<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin BLD4 × original BKG exterior-ring raw-code support (v0)

**Research-only.** This document defines a new, independently tested
exterior-neighborhood geometry gate for the original 5-building Berlin pilot.
No assumed water-depth physical unit, 2026 insured building stock, CAT loss,
building entry elevation or policy terms may be inferred.

## Why the previous building-interior evidence is not enough

[The previous original-source evidence](berlin-bld4-bkg-real-raw-pixel-support-v0.md)
and [original GitHub run 41349226673](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41349226673)
reported 683.311267 m² total pilot-clipped first-five WFS building area,
including 666.124849 m² masked/NoData, 14.434404 m² numeric zeros, and
2.752013 m² original **positive integer raw codes**. This is about
**97.5% NoData within original building footprints**, not observed
dryness or proven water level at entrances. BKG's nationwide 2024
hydrodynamic modelling includes building geometric inputs; it remains a
hypothesis, **not confirmed causation**, that the observed footprint
mask is partly related to building representation in the model.

## New exact geometry and scientific rules

The canonical source-ingest worker reuses the **same five original,
source-verified pilot-clipped ALKIS polygons**, projected strictly from
EPSG:25833 to the BKG TIFF's EPSG:25832, and the **same bounded original
1-m raster window**. No second WFS request or TIFF is introduced.

A single union of the five original footprint geometries generates
three **non-overlapping external distance bands** in native metric CRS:

| Distance to ANY footprint | Purpose |
| --- | --- |
| 0–1 m | immediate exterior, may describe the next raster cell |
| 1–3 m | nearby external support |
| 3–5 m | broader external support |

Each band is clipped to the **real, reprojected fixed 200×200 m pilot
polygon**, not an enlarged bounding-box approximation. Intersections
with all original footprint interiors are excluded, and overlapping
buffers from adjacent buildings are counted **once only**. Fractional
real 1-m cell intersections are classified into four mutually exclusive
classes: original raw integer positive, original valid numeric zero,
original mask/NoData, and outside the raster window. Each band separately
enforces exact projected-area conservation. The output is **only
aggregate area/count evidence**, without individual building
coordinates, IDs, geometries, cell arrays or per-building depths.

Important: positive numbers are **unscaled raw integer codes**, *not*
confirmed centimetres or metres of standing water. A NoData cell is
not observed dry; no-data under a modelled building might be expected.
Perimeter support does not establish a door/window elevation, basement
entry, water ingress, claims loss, damage fraction, financial terms,
historical flood occurrence, or annual exceedance probability.

## Original data and vintage limitations

- BKG [official HWK_SRG overview](https://www.bkg.bund.de/DE/Themen/Umwelt-und-Klimawandel/Starkregen/starkregen_cont.html):
  2024 nationwide design-storm hazard, not an observed insured loss event.
  The provider says the map cannot be treated as metre-exact site
  engineering evidence.
- BKG [official product documentation](https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/hwk_srg.pdf)
  describes 1-m EPSG:25832 spatial grids and maximum flood depths, but
  **does not establish a numeric Int16 TIFF depth-unit scale**.
  Spatial pixel size in metres must never be mistaken for depth units.
- BKG original downloaded TIFF: exactly 47,280,200 bytes, full SHA-256
  `7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f`,
  one fixed KOSTRA tile. The public original data are attributed under
  DL-DE/BY-2.0 with additional provider-source credits.
- ALKIS source is mutable 2026 current-data WFS; the BKG baseline
  uses earlier building and terrain vintages. No temporal identity
  between those sources is proven.
- In a future CAT ingestion, only a source-licensing and physically
  calibrated depth dataset with clear per-building location/entry
  uncertainty could be admitted. This PR does not add model input
  contracts or insurance database rows.

## Reproduce offline

```bash
python -m unittest tests.test_berlin_bld4_bkg_exterior_ring_raw_support_v0 -v
python -m unittest tests.test_berlin_bld4_bkg_original_raw_cell_support_v0 -v
```

The dedicated workflow runs the synthetic disjoint-ring challenges on PR
events, and runs a single strict original-provider WFS × TIFF evidence check
only on an approved main workflow change or explicit workflow dispatch.

**On this PR, actual exterior ring results are PENDING.** No prior
original-source run collected these exterior band aggregates. A successful
post-merge original run must be separately checked and documented before
claiming real perimeter support.
