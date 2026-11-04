<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Global Dam Watch v1.0 — original archive receipt and next geometry source check
**Review date:** 2026-11-04

## First independently executed original archive receipt

The source-specific main-branch GitHub workflow (fully completed):
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41885048219

- Original Figshare article/version: https://api.figshare.com/v2/articles/25988293/versions/1
- Exact original file: `GDW_v1_0_shp.zip`, Figshare file **47913754**.
- Original byte count: **69,745,749**.
- Figshare declared MD5: **5064cf2315ef6159d9133b03596e761a**; actual source MD5 matched.
- Independently computed SHA-256 of the downloaded original ZIP:
  **2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae**.
- ZIP entries: **16**; CRC, SHP and SHX offsets, DBF record counts and
  positive unique numeric `GDW_ID` validated.
- Actual original point count: **41,145**; reservoir polygon count **35,295**;
  valid polygon-ID subset and **5,850** point-only barrier IDs.
- Geographic WGS 84 declaration, finite lon/lat bounds and exact ring
  closure checked. All structural checks passed.

Only the aggregate, nonidentifying receipt was logged. The original ZIP
remained in `RUNNER_TEMP` and was removed after execution; it is not committed
or attached to the workflow. A provider MD5 match is not independent proof of
authorship, but a source exact-byte SHA-256 is now reproducibly pinned from a
first complete original download.

## Second original-source gate — geometry and spatial pairing

The next check uses an **independent second original download** and
compares its SHA-256 to the pinned first original receipt before opening
source features. Pinned `pyshp==2.3.1` and `Shapely==2.1.2` count:

- valid versus invalid native reservoir polygons under GEOS;
- source shapes that could not be converted safely;
- point containment for the exact paired `GDW_ID`, separated into
  strict interior, boundary and outside;
- unassessable relationships where the native polygon is invalid or
  cannot be parsed. **No automatic make_valid, snapping, buffering or
  out-of-bound relocation** is performed.

The executable is `research_runners/gdw_v1_original_spatial_quality_v0.py`.
It runs synthetic fixtures only in pull requests. Its fixed original-source
acquisition is allowed only on `main`, in an ephemeral runner, with no
original geometry, IDs, rows or source ZIP outputs. The first original
GEOS receipt should be read from the source-workflow's actual run log after
this workflow is reviewed/merged.

## Scientific boundary

GDW v1 is a *dam/barrier and reservoir inventory*. Geometry containment is
not hydraulic connectivity, breach probability, flood inundation, insured
loss, operational state, or model calibration. The source manual warns that
reservoir boundaries may be snapshots at lower water levels. Point-only
barriers are valid source entities; a point outside a valid polygon may be
a true upstream/downstream proxy or a data-quality defect, not necessarily a
reason to delete or automatically move the source point.

The final author's manual documents `-99` numeric missing values and
`-9999` missing elevations, plus unknown text fields. This workflow does
not yet assess attribute completeness or value provenance.

The dataset is CC BY 4.0; its final original manual asks not to rehost the
entire unmodified source release without written consent. All provider
bytes remain outside Git. Neither the structural proof nor GEOS audit
grants CAT-model admission, redistribution or production DB writes.

## Subsequent original GEOS result (verified 2026-11-04)

The above second-stage audit subsequently **completed successfully** on the
reviewed main revision, in the original-data runner:
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41886824276

The fresh original download reproduced the **exact same full-archive
SHA-256** `2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae`.
Using pinned pyshp 2.3.1 / Shapely 2.1.2 (GEOS), the actual original-source
aggregate receipt reported:

| Source geometry diagnostic | Original source count |
| --- | ---: |
| Barrier point records | 41,145 |
| Reservoir polygon records | 35,295 |
| Point-only barrier IDs (no polygon) | 5,850 |
| GEOS-valid native reservoir polygons | 35,074 |
| GEOS-invalid native reservoir polygons | **221** |
| Conversion/unparseable polygons | 0 |
| Paired points strictly inside valid polygons | 35,074 |
| Paired points on valid polygon boundaries | 0 |
| Paired points outside valid polygons | 0 |
| Pairs not assessable due to invalid native polygon | **221** |

Thus all **assessable valid source polygons** contain their paired point;
**221 / 35,295 = approximately 0.626%** of the source reservoir polygons are
GEOS-invalid in the tested original Shapefile representation. This is not
proof that the remaining 221 paired source points lie inside or outside
those invalid geometries. A passing job confirms these *measurements*, not
universal geometry validity or model readiness. Neither georeferencing nor
original coordinate order was changed; no auto-repair was applied.

Source evidence is frozen in
`research_runners/gdw_v1_original_spatial_source_receipt_v0.py`.
The next safety-preserving diagnostic classifies the **invalidity reasons**
into coarse aggregate families (never printing GEOS' original-coordinate
explanations). Only after reviewing those families should we evaluate
whether an author-supported fix or an alternative original GDB representation
changes the outcome. A secondary GEOS-based parser is not an independent
hydraulic or scientific validation.
