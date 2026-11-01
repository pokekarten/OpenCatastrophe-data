<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg official ACT rooftops versus GeoBase building polygons

**Research-only** source-family comparison. It does not establish independent
external buildings, building-identity crosswalks, or admitted exposure.

## Why this comparison is worth executing

The full ACT2023v2 to ACT GeoBase2026 original ID diagnostic,
merged PR #932, measured **zero exact common ID texts** across 238,189
ACT2023 rooftop records and 230,353 GeoBase2026 building records.
The prior ACT2023 versus EUBUCCO Luxembourg original 250m central-city
window measured 149 ACT roofs versus 45 EUBUCCO records, nine unique
IoU≥0.60 pairs and 136 ambiguous ACT roofs. EUBUCCO's 2013 government
source is also an ACT topographic product, so neither comparison
automatically supplies independent scientific ground truth.

This pilot tests **how the two separately modelled ACT source-family
polygon definitions overlap**, rather than trying to join their incompatible
identifiers.

## Frozen providers and exact source receipts

- ACT2023v2 roof-derived MultiPolygon original GeoPackage SHA-256:
  `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`;
  ZIP SHA-256
  `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a`.
- ACT BD-L-GeoBase Buildings 2026-10-01 original GPKG SHA-256:
  `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`;
  original ZIP SHA-256
  `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`.
  Publisher MD5 also checked by its separate original source preflight.
- Both original polygon declarations are **EPSG:2169** MultiPolygon;
  this does not prove matching entity semantics or certified field control.
- Original sources are obtained only from fixed official HTTPS URLs on
  a temporary GitHub Actions runner; neither ZIP, GeoPackage nor
  temporary selected geometry leaves that runner.

## Method / reproduction

`research_runners/luxembourg_act2023_geobase2026_geometry_v0.py`
uses already tested exact-file source-GPKG and RTree validators. It
selects one fixed central Luxembourg research square of
**100m × 100m** around 6.1319°E, 49.6116°N. It reads at most
**400** ACT roof and **400** GeoBase building polygons, via the two
original GeoPackage RTree spatial indices, into automatically removed
private temporary GeoJSON files with declared native EPSG:2169.
The reviewed `scripts/building_footprint_overlap_v0.py` projects both
to European equal area EPSG:3035, applies an illustrative IoU≥0.60 and
substantial-overlap≥0.20 research classification, and outputs **only**
aggregate unique candidates, ambiguous splits/merges, weak/no overlap,
bounded pair counts and median candidate IoU.

```bash
python -m pip install -r requirements-eu-flood-spatial.txt
python -m unittest tests.test_luxembourg_act2023_geobase2026_geometry_v0 -v
python -m research_runners.luxembourg_act2023_geobase2026_geometry_v0 \
  --act-gpkg /private/original-ACT2023v2.gpkg \
  --geobase-gpkg /private/original-GeoBase20261001.gpkg
```

A source-hash drift, absent index, empty/too-dense window, invalid
geometry or source population drift must fail closed. Both original
fixed-source URLs and zip/GPKG hashes are independently checked before
extracting any comparison window.

## Interpretation limits

- An **exact text ID match is absent** in both original full populations.
  A high IoU is not equivalent to an official mapping between ID namespaces.
- One ACT2023 rooftop can cover several GeoBase buildings, or the reverse.
  Without a manually adjudicated crosswalk these must stay **ambiguous**.
- ACT is the publisher of both, so this is **correlated source-family**
  research, not independent ground truth.
- Differences in observation date (2023 versus 2026), roof/ground/record
  definitions, surveying detail, segmentation, CRS and completeness are
  confounded. No count is interpreted as a construction/demolition,
  property-level insurance exposure, replacement value, claim or catastrophe
  loss. Even a precise overlap is **not a model-input admission**.

Next: stratify urban/rural manually adjudicated windows with independently
verified coordinate controls, survey date and dimensional semantics; consider
an official ACT ID crosswalk if the publisher makes one available.

## Fixed-window adjustment after real source run

The first exact-original job, https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41310830197, **correctly failed closed**: the initial 250m × 250m city-centre extraction produced **more than the permitted 400 RTree candidate rows** on at least one source. This is a genuine source-density bound, not a checksum or provenance failure. No sample was silently truncated or counted as a real comparison.

The fixed one-time region was reduced to **100m × 100m** around the same public centre, without increasing the 400-object safety cap, changing source files or relaxing validity checks. The revised original-source workflow must independently pass before any aggregate comparison result is claimed.

## Actual pinned-original research result (2026-11-01)

**Successful source workflow:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41310996649

The original two publisher ZIPs and extracted GeoPackages matched their
pre-existing exact SHA pins. The fixed **100 m × 100 m** city-centre
research square was compared in native EPSG:2169 and European EPSG:3035,
using the same validated spatial pipeline. Only source-aggregate diagnostic
counts were printed, not matched building IDs or source geometry.

| Real source measure | Observed |
| --- | ---: |
| ACT2023 roof polygons intersecting the research square | **55** |
| GeoBase2026 building polygons intersecting the square | **107** |
| STRtree bounding-box candidate-pairs checked | **322** |
| Unique ACT roof candidates with IoU ≥0.60 | **12** |
| Ambiguous ACT roofs (1:n / n:1 candidate relations) | **39** |
| Unique ACT roof candidate below IoU 0.60 | **4** |
| ACT roofs without substantial overlap | **0** |
| Median IoU among the 12 unique candidates | **0.879775** |

The ACT-side counts conserve the sample (12+39+4+0 = 55).
These numbers must **not** be interpreted as 55 physical buildings,
107 different buildings, 39 source duplicates, 12 verified common
building identities or an estimate of growth/removal. Distinct source
segmentation is clearly material even with same-ACT-family origin.
The prior full-national exact-ID test found **0 common text IDs**;
the 12 spatial candidates are **not** an official ID crosswalk.

The 100m research square was chosen as a safe narrowed region only after
the 250m fixed window exceeded the predeclared source sample cap;
it was **not** tuned to maximize IoU. No per-building source records,
GEOS geometries, original ZIPs or database rows were persisted.

**Next research action:** manually adjudicate preselected, versioned urban
and rural footprint samples with independent control coordinates and
source-object definitions, and compute per-source false-match rates by
1:n/n:1 grouping. Only with such proof plus legal and scientific
admission may an external source-aware crosswalk be considered.
