<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BKG original Berlin depth raster – native band unit/scale preflight

**Research-only. Actual results PENDING post-merge source workflow.**

The five-building Berlin BLD4 pilot now has verified *original*
signed-Int16 BKG KOSTRA raw-code support both inside footprints and
across 0–1, 1–3 and 3–5 m exterior rings
([GitHub original source run 41352574515](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41352574515)).
Positive signed integers are **not** a verified water-depth measurement
in centimetres or metres. Physical 1 m raster **cell size** has a
different meaning from water-depth **unit**.

The original BKG
[HWK_SRG product page](https://www.bkg.bund.de/DE/Themen/Umwelt-und-Klimawandel/Starkregen/starkregen_cont.html)
and [official documentation](https://sg.geodatenzentrum.de/public/gdz/dokumentation/deu/hwk_srg.pdf)
describe 2024 KOSTRA/100 mm design-event simulation and 1 m horizontal
GeoTIFF grids but do not certify the exact signed-Int16 raw→physical
depth conversion of the specific Berlin sample.

## New bounded metadata-only step

The reviewed same-source worker
`research_runners/probe_bkg_original_depth_unit_claims_v0.py`
inspects **only TIFF band metadata already present** in the ONE
exact original BKG file while the existing Berlin workflow already
holds it in temporary storage. No second source GET, additional TIFF,
ZIP decompression, pixel arrays or insurer data are added.

- Verify complete original file **47,280,200 bytes** and full-source SHA-256
  `7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f`.
- Verify raster CRS EPSG:25832, 10000×10000 original source pixels,
  one signed Int16 band, declared NoData -9999.
- Report the *candidate* unit string from GDAL/rasterio band units and
  strict candidate UNITTYPE/UNITS tags, plus runtime scale and offset.
  Do not emit arbitrary provider metadata text or original pixel values.
- Distinguish **implicit GDAL defaults** (e.g., scale 1, offset 0)
  from proven source-declared physical conversion. Even matching
  `cm`/`m` labels are candidates only, not scientific certification.
- Fail closed on source digest drift, wrong georeferencing, invalid unit
  metadata, contradictory unit labels or nonfinite scalar parameters.
- Keep `source_units_and_scale_physically_calibrated=false` and
  `model_input_approved=false` unconditionally.

Synthetic tests cover missing/default scale and unit, valid candidate
units, conflict, unsupported text, numeric invalids and tag caps.
Only the original source main workflow (or explicit reviewed dispatch)
may produce a real unit-tag receipt; PR checks perform no provider GET.
The original file and any source tag text stay ephemeral.

## Acceptance before depth modelling

The most important outcome may be **UNKNOWN**. If the GeoTIFF lacks
explicit scale and physical unit evidence, do not guess that a raw
code of 108 is 108 centimetres or 1.08 m. Ask the BKG for the
specific original KOSTRA maxdepth GeoTIFF encoding/scale, its
applicable product/version and precise NoData/zero semantics, or
obtain independent authoritative, same-version format documentation.

Until then, exterior raw-code support is a useful **coverage**
measurement, not a validated physical water depth and not a
loss/vulnerability or insured-risk input. The current Berlin 2026
municipal detailed storm model has **different spatial coverage and
1D sewer/2D overland simulation**; it cannot be silently treated
as interchangeable with the nationwide BKG source.
