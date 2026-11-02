<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First real-source one-building / WorldCover original-pixel comparison — research only

**Original provider run:** 2026-11-02 UTC,
[GitHub Actions 41499368414](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41499368414).
**Scope:** one observed original Hessen ALKIS `Building` GML member
vs one original ESA WorldCover 2021 v200 N48E009 raster block185.
**Not** an admitted insurer exposure, building census, CAT-model input,
physical building valuation, 2021 building existence check or source
accuracy certification.

## Causal scientific step and source rights

The real Hessen INSPIRE ALKIS 2D Building service had previously been
verified to expose `bu-core2d:Building`, `bu-core2d:BuildingType`
and ETRS89 EPSG:4258 (latitude-longitude WFS 2.0.0 axis order).
The [official Hessen publisher catalogue](https://www.geoportal.hessen.de/spatial-objects/711)
labels the source **DL-DE Zero 2.0**. Its exact fixed one-member
WFS response remains **internally contradictory**: one parsed GML
`Building` member, but `numberReturned=0`. A separate
`resultType=hits` request in the same bounded region reported 29
potential matching features. Neither source field independently
establishes 29 buildings.

The ESA original source is the independently verified
**WorldCover 2021 v200 Map** under CC BY 4.0:
<https://esa-worldcover.org/en/data-access>.
The comparison does not establish that the Hessen building
was built or existed in 2021; its individual survey/vintage remains
unverified.

This original research workflow uses exactly **four** reviewed,
read-only requests:

1. The **same** fixed Hessen `WFS GetFeature COUNT=1` operation
   with already-reviewed ETRS89 WFS BBOX. No paging or new
   building query is performed.
2. ESA WorldCover original TIFF header **4,096 bytes**,
   SHA-256 `a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529`.
3. Exact original TIFF tile tables **10,368 bytes**,
   SHA-256 `7de08710b64cad350b81da83a81fcfc0c74f5285e20e28b0a3e42d19151885ba`.
4. The original compressed single 1,024×1,024 block185
   **56,442 bytes**, source SHA-256
   `526eb0819a9101a4e23df17dd70a040444190bb034528237fee29b415f9dd29a`.

No new original WorldCover tile, range or rights contract was added.
The decoded original single-block pixel SHA-256 is
`5a7cd7ce34de5d054e0f134cd5823b6bac77314fd3a2431ee547fe40cc0b3b7e`
(1,048,576 original uint8 classified source pixels).
One original WFS response was **4,395 bytes**, SHA-256
`8b70c229d26726764ce0800612d373eacf9eae5fa9a5e7b384c9f3aaab43479a`.
The exact four-request-set SHA-256 is
`ffb79fc9065732a1e5af35e4d66e32073c67df2e36e998ba89eec704b222ebf5`.
Reproducible code SHA-256:
`e07a8fbdbec9b36dff37b446a5f0bd4ae50b936175d26905b4c7f54988cb0aef`.
Original execution UTC `2026-11-02T18:19:44.400637+00:00`.

## Geometry and actual raster method

The original source is parsed strictly as a single EPSG:4258
Building exterior with no holes/extra polygon parts; the existing
source provenance parser **does not waive the count contradiction**.
The original source ring and separately transformed WGS84 polygon
were independently GEOS-valid under the repository's reviewed,
pinned PyProj 3.7.2/Shapely 2.1.2 profile. A non-ballpark
offline source EPSG:4258→target EPSG:4326 coordinate operation
was used, with declared **1 m** coordinate-operation accuracy.
That accuracy is **not** a surveyed 1 m building position guarantee.

Only in memory, the transformed polygon was mapped to the exact
original TIFF block185 grid (georeferenced EPSG:4326) and
intersected against original pixel-square cells using **exact
GEOS intersection area**. Both inputs and every shifted polygon
must stay inside the reviewed block; at most **256** raster
cell candidates are visited per scenario.

## Actual one-GML/one-raster original-source results

| Diagnostic | Observed result |
| --- | --- |
| Distinct original WFS Building members parsed | **1** |
| WFS provider `numberReturned` | **0, contradictory** |
| Independently GEOS-valid original/transformed polygon | **Yes** |
| Actual original WorldCover source pixels present | **Yes**, 1,048,576 |
| Pixel cells intersected by baseline geometry | **8** |
| Baseline area-weighted class 30, grassland | **0.610846 (61.0846%)** |
| Baseline area-weighted class 50, built-up | **0.389154 (38.9154%)** |
| Fixed positional research scenarios | **17** |
| Scenario shifts | **0.25 and 1.0 source grid pixels**, not metres |
| Highest intersected-cell count among scenarios | **11** |
| Grassland share over 17 scenarios | **0.234472–1.000000** |
| Built-up share over 17 scenarios | **0.000000–0.765528** |
| Max total-variation distance from baseline | **0.389154** |
| Unique majority WorldCover class changed in some scenarios | **Yes** |
| True physical building identity + 2021-vintage corroborated | **No** |
| Insurance or hazard model input approved | **No** |

Class 50 represents *built-up land cover*, including artificial
surfaces: it is **not** a counted, surveyed or valued roof.
These are shares of the ALKIS polygon's approximate projected
**raster-cell intersection area**, not ground-truth roof
material/height/occupancy, physical square metres, exposure,
vulnerability or insurer insured value.

### Why the sensitivity matters

The earlier synthetic invented polygon fell entirely within
WorldCover class 10 for all 17 shifts. This **actual** one-source
GML polygon instead lies near a raster class boundary:
even a 0.25/1 pixel artificial translation can change its
fractional land-cover context, and some shifts change the
unique majority class. The chosen pixel shifts do **not** directly
model a ±1 m transformation error; they are a bounded
diagnostic of grid-scale instability. A defensible
spatial measurement-error model needs datum epoch, actual
survey accuracy and finer subpixel boundary sensitivity.

## Method and model admission boundaries

- Original provider `numberReturned=0` versus one actual
  GML source member remains unresolved. The research parser
  deliberately reports this as **blocked** instead of normalizing it.
- We verified coordinate-operation declared accuracy, not the
  physical survey's horizontal position/epoch accuracy.
- Original ALKIS source vintage is unknown vs WorldCover's
  **2021** landcover reference year.
- Only one GML polygon and one existing source TIFF block were
  tested, not a sample of 29 independently identified buildings,
  a regional building inventory, or a worldwide source.
- The 17 synthetic translations establish method sensitivity,
  not independently calibrated real-world geolocation uncertainty.
- No raw source GML/polygon positions, individual original
  WorldCover pixel values or source feature identifiers were
  logged, exported, committed or persisted.
- No live Neon insurance DB, Oasis OED, company asset or
  Pokémon database was mutated.

`actual_polygon_raster_research_intersection_executed=true`,
`wfs_count_discrepancy_still_blocked=true`,
`original_provider_source_feature_vintage_verified=false`,
`source_building_physical_identity_verified=false`,
`etrs89_wgs84_survey_epoch_verified=false`,
`insurer_exposure_or_tiv_inferred=false`,
`model_input_approved=false`.

**Next research gates:** independently resolve the WFS member count
semantics and survey/vintage provenance; then test a bounded,
date/accuracy-aware position-uncertainty model and
additional independently sourced building footprints before any
candidate can be considered for an insurer CAT exposure data
pipeline.
