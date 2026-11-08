<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Correct BKG 2022 GF=4 land / GF=2 water semantics in Germany polygon challenge

**2026-11-08. Original bytes replayed; RESEARCH ONLY / NO commercial
GADM permission / NO R+V insurer exposure admission.**

## Why this fixes the earlier geometry study

The previously merged original-byte Germany geometry audit (PR #1436)
united **all 430** BKG KRS shape records into 400 administrative AGS groups.
That is useful as an entire administrative area comparison, but it is an
invalid default for a **land-building footprint** comparison.

The original BKG documentation distinguishes its geographic factor GF:
- GF=4: structured administrative **land** polygon, required one per Kreis.
- GF=2: additional administrative **water** polygon in the North Sea,
  Baltic Sea or Lake Constance; must not be mistaken for buildings on land.

BKG official VG250 documentation, section 3.2, attribute GF:
https://sg.geodatenzentrum.de/web_public/gdz/dokumentation/deu/vg250.pdf

BKG 2022 authentic archive, **unaltered**:
https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/vg250_12-31.gk3.shape.ebenen.zip
SHA-256 dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de.

The exact archived DBF has **400 GF4 land records and 30 additional
GF2 water records covering 27 AGS administrative districts**. In
particular, it is wrong to treat the 430 physical source records as
430 separate Kreise, or to add marine polygon areas to land-only
building exposure support.

## Exact-source four-archive replay

The updated runner research_runners/materialcities_bkg_gadm_geometry_overlap_v0.py
now:
1. Reuses the existing exact-ZIP SHA-256 and original 400-Kreis
   BKG↔GADM↔MaterialCities↔Destatis administrative code preflight.
2. Parses each BKG original shape record's GF attribute; requires
   exactly one GF4 land record for each of 400 unique AGS, 30 GF2
   water records and **no other** GFs.
3. Projects GF4 polygons and separate historical GADM groups to
   ETRS89 LAEA EPSG:3035, then computes area, intersection and
   intersection-over-union (IoU) for the **land-only** primary metric.
4. Separately retains the original all-BKG-surfaces comparison so
   prior source results are not silently rewritten.
5. Emits only non-admitted research diagnostics, threshold-flagged
   official AGS codes and selected example metrics. It does NOT
   emit source geometry, a full region-by-region geographic crosswalk,
   actual buildings, insurer sites or MaterialCities source GFA rows.

### Original replay measured 2026-11-08

| Original Germany source diagnostic | Before GF correction | Correct GF4 land |
| --- | ---: | ---: |
| AGS source groups compared | 400 | 400 |
| Land GF4 components | Included | 400 |
| Additional GF2 water components | Included | Excluded (30) |
| IoU >= 0.95 | **389** | **391** |
| IoU < 0.95 | **11** | **9** |
| Median IoU | 0.993805 | 0.993835 |
| Smallest IoU | 0.708987 | 0.708987 |

The improvement is **net two**: four districts previously below 95%
cross the threshold when GF2 marine areas are excluded, while **two**
formerly above 95% become below it. This is important: suppressing water
does not monotonically increase IoU when the GADM polygon's water/shore
support is different.

Selected source-original geographically compared examples:

| Official AGS | Kreis | Prior all-surface IoU | GF4 land-only IoU | Source GF2 water area km2 |
| --- | --- | ---: | ---: | ---: |
| 01001 | Flensburg | 0.857607 | **0.981986** | 7.602 |
| 01002 | Kiel | 0.920450 | **0.970677** | 6.895 |
| 01059 | Schleswig-Flensburg | 0.923179 | **0.958424** | 79.979 |
| 03359 | Stade | 0.949752 | **0.993175** | 59.493 |
| 04012 | Bremerhaven | 0.772162 | **0.944927** | 17.380 |
| 03405 | Wilhelmshaven | 0.940559 | **0.939912** | 0.744 |
| 08335 | Konstanz | 0.941656 | **0.941297** | 0.311 |
| 01054 | Nordfriesland | 0.941529 | **0.941502** | 0.527 |
| 16054 | Suhl | 0.708987 | **0.708987** | 0.000 |
| 16070 | Ilm-Kreis | 0.947693 | **0.947693** | 0.000 |
| 16072 | Sonneberg | 0.933896 | **0.933896** | 0.000 |

The lower-IoU Thüringen cases remain unresolved by water filtering.
Suhl's ~40.3 square km area discrepancy remains compatible with
documented historical annexation but exact causal polygon reconciliation
requires a municipality-level, source-original vintage challenge.
Flensburg was mainly a GF2 coastline-definition comparison problem.

**Not all historical/exact coastline differences are explained** by
the correction. Exact AGS lists are retained by the new
manual_review_AGS_source_keys research diagnostic; no more than a
bounded list of threshold-flagged source identifiers is exposed, no
per-Kreis geometries or full 400-row derived table is published.

### Exact original source identity

- GADM 4.1 Germany ADM2 original ZIP SHA-256:
  add290173fedaca349d9bd312523d63bf7f9ef9389d473a78e1ce530c3450d7a.
- MaterialCities 2026.9 original ZIP SHA-256:
  ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38.
- Existing pinned Destatis Zensus source original workbook SHA-256:
  82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551.
- Original geometry run: Python 3.11, Shapely 2.1.2,
  pyproj 3.7.2, pyshp 2.3.1; byte-authenticated source geometry.
  These spatial packages are optional and **not** required by standard CI.

## Reproduction and negatives

Run the original spatial replay with the same options in
docs/research/materialcities-bkg-gadm-original-geometry-overlap-20261108.md
using verified original source files **outside Git**. No new network
acquisition or rights escalation is hidden in the CLI.

Run the dependency-free negative tests:

    python -m unittest discover -s tests \
      -p 'test_materialcities_bkg_gadm_geometry_overlap_v0.py' -v

**23/23 focused synthetic unit tests passed** against the exact research
branch source. They include old projection and region-level conservation
logic, exact GF4 land cardinality, separately counted GF2, fake GF values,
missing land records, cross-mode comparison and no-admission semantics.

## Source licensing / model admission boundary

BKG's data-licence obligations remain separate. GADM limits commercial
use and redistribution without permission: https://gadm.org/license.html .
The MaterialCities Zenodo CC BY 4.0 record does not supersede the
independent upstream GADM licensing terms. The successful original
source geometry comparison is **not authority** to reuse the geometry
or source-derived MaterialCities regional construction-type areas in
commercial CAT modelling.

No actual insurer R+V geocoded sites, 2025 R+V portfolio allocations,
property TIV, building-material truth, vulnerability functions, Oasis
GUL/IL/RI runs or OEP/AEP are constructed or approved here. A 95%
IoU source agreement is not a scientific model calibration threshold.
The remaining nine cases require independent jurisdiction/vintage and
geometry-specific review before any regional building enrichment.
