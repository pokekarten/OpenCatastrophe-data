<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WorldCover 2021 v200: bounded synthetic polygon shift sensitivity on real pixels

**Run date:** 2026-11-02. **Method:** 17 fixed invented polygon translations
over a *single previously verified real* ESA WorldCover 2021 v200 N48E009
TIFF block. **Not** a test of the observed Hessen ALKIS building geometry.

## Why this test

The [existing original Hessen ALKIS ETRS89→WorldCover CRS review](hessen-original-building-etrs89-worldcover-crs-review-20261101.md)
has verified one non-ballpark offline EPSG:4258→EPSG:4326
coordinate operation, with declared 1.0 m operation accuracy. Its
actual source polygon had at least one transformed vertex within
1 m of the nearest WorldCover raster-grid line. This is a reason to
**test sensitivity**, not to assume any particular real building
land-cover class or transform accuracy.

No metre translation is claimed here: the new shifts are instead
**0.25 and 1.0 WorldCover grid pixels** in the north/south and
east/west directions, separately and diagonally. They form 17
deterministic scenarios including the original invented footprint.
The 2021 raster's pixel pitch is **1/12000 geographic degrees**,
not a uniform ground distance in metres.

## Real original ESA source evidence

[Successful exact original-source GitHub Actions run 41495881246](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41495881246)
completed 7 original class/HTTP negative tests, 5 existing synthetic
footprint tests and **5 new synthetic shift tests** before its
live provider request.

The **unchanged exact three fixed original TIFF byte ranges** were
requested against the same publicly available 2021 WorldCover Map
tile with no new source permissions:

- 4,096-byte original TIFF header, SHA-256
  `a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529`.
- 10,368-byte original TIFF offset/size tables, SHA-256
  `7de08710b64cad350b81da83a81fcfc0c74f5285e20e28b0a3e42d19151885ba`.
- Exactly one original 56,442-byte Deflate compressed block 185
  (range `43278196–43334637`), SHA-256
  `526eb0819a9101a4e23df17dd70a040444190bb034528237fee29b415f9dd29a`.
- Decoded source block: exactly 1,048,576 original class pixels,
  SHA-256 `5a7cd7ce34de5d054e0f134cd5823b6bac77314fd3a2431ee547fe40cc0b3b7e`.
- Original source operation UTC `2026-11-02T17:56:52.149918+00:00`.
  The source block contained six WorldCover classes in total.
- Immutable source request-set SHA-256
  `353f60d08a9793c8a7a55d9882802734115c42adaa8020224725254d8fb6be03`.
- Executed pixel decoder code SHA-256
  `711be5de8f0f0fa32bdc4dc68338636ccb73c9d887892e6265d0dafa16aabc1d`.

No image pixels, provider source bytes, geometry vertices,
coordinates or original TIFF were committed or persisted.
Existing original provider licensing and sample-access contract remain
unchanged.

## Source-pixel + invented polygon result

The historical synthetic rectangle around the invented geodetic test
coordinate was shifted by exactly 0, ±0.25 and ±1 pixel in each
grid axis. Its *actual pixel clipping* was repeated independently
for all 17 fixed scenarios on the transient decoded original block.

| Metric | Observed live result |
| --- | --- |
| Fixed shifts | 17 |
| Source pixels evaluated within the one original block | 1,048,576 decoded |
| Invented polygon area in pixel-square units | 14.08 |
| Baseline fraction of class 10, trees | 100% |
| Class-10 minimum/maximum fraction across shifts | 100% / 100% |
| Maximum total-variation distance from baseline | 0.0 |
| Any shift changing the unique majority class | **No** |

This result is **local stability for one made-up polygon**;
it must never be used to declare the observed ALKIS building
world-cover share, survey accuracy, insurable exposure or vulnerability.

The **independent, purely synthetic** contrast fixture contains
a fabricated sharp tree/built-up edge passing through the same
invented polygon. Under the same allowed offsets, its nominal
fractions are 50% tree cover / 50% built-up and the maximum
total-variation distance is **greater than 0.2**. This demonstrates
that sensitivity is *not* automatically zero for all land-cover
transitions. No original ESA class pixel was modified or redisclosed.

## Unresolved admission barriers

- One real Hessen ALKIS polygon has been parsed and GEOS/CRS validated
  separately, but it was **not used here**: provider `numberReturned=0`
  vs one `Building` member remains contradictory; the separate
  hits-only query's count 29 is not an independent building census.
- The ALKIS survey/source vintage and geodetic position accuracy
  remain unverified, and its observation epoch differs or may differ
  from WorldCover's **2021** observation year.
- A **1 metre nominal PROJ coordinate operation accuracy** cannot
  be replaced with ±0.25/±1 pixel artificial shifts; ETRS89 to WGS84
  needs its own error propagation and building-specific pixel
  sensitivity work.
- No real polygon/pixel class intersection, insurer TIV, loss,
  building count, vulnerability or CAT model input was admitted.

`real_building_geometry_used=false`,
`actual_transform_accuracy_in_metres_inferred=false`,
`actual_building_worldcover_overlap_verified=false`,
`source_building_survey_vintage_verified=false`,
`provider_wfs_count_discrepancy_resolved=false`,
`model_input_approved=false`.

**Next causal step:** separate the *independent provider WFS feature
count discrepancy* from geometry validation, then perform a true
one-geometry class sensitivity experiment only after exact source
vintage/CRS uncertainty and rights are reviewed. No Neon or Pokémon
database updates are part of this research pilot.
