<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ponthierry: source-linked building ↔ PPRI zoning probe (2026-11-01)

Research-only source receipt and **negative/positive-control QA** on separate
CAT-only Neon `insurance-risk-core/main`, database `insurance`. This is
**not** a certified 2016 flood extent, insurer exposure or CAT loss model.

## Exact stored sample

- Two contemporary buildings: RNB IDs `5TR6PNH2YQPT` and
  `TCHNNF59Y27V`. RNB and IGN footprints are source-coherent but
  share BD TOPO upstream lineage; IGN updates are from **2021** and
  **2024**, later than the event of interest (2016).
- The ArcGIS [PPRI regulatory zone layer 17](https://sig.seinegrandslacs.fr/arcgis/rest/services/Gestion_Eaux_Inondations_GP/MapServer/17)
  supports polygon-feature queries and GeoJSON responses. Three
  separately stored original response receipts were reviewed:
  two full-building query footprints returned **0** zone features;
  a gauge control footprint (`F447000302`) returned **1**
  `zone rouge` feature, objectid **574**, regulatory-plan label
  `31 décembre 2002`.
- Independent PostGIS join demonstrates
  **100% footprint intersection-over-union** between both submitted
  ArcGIS input polygons and the original research RNB polygons:
  `ST_Equals` true for both. Geographic separation from the **gauge
  query control** is **112.82 m** and **72.17 m** respectively.
  This measures proximity, **not** river stage, flood depth or
  probability of flood loss.
- Each input response was SHA-256-labelled and the source URLs
  were retained. Both building query responses have the same SHA,
  consistent with identical empty feature responses, but they
  correspond to **two distinct query URLs and different input polygons**.

## Executed reproducible diagnostics

- `research_runners/sql/fr_ponthierry_ppri_building_query_link_v0.sql`:
  2/2 matches with exact input geometry and SHA receipt evidence, both
  `NO_ZONE_FEATURE_RETURNED_NOT_PROOF_OF_SAFETY`. All scientific and
  model admission booleans false.
- `research_runners/sql/fr_ponthierry_ppri_query_link_invariants_v0.sql`:
  **13/13 read-only assertions passed** against the live main branch
  (two buildings, three responses, receipt format, red-zone positive
  control, source rights and historical non-admission).
- The independent `research.fr_ponthierry_building_2016_exposure_gate_v0`
  records **2** building gate rows with **0** model approved; the wider
  `research.cat_source_bridge` remains **9 design-only** proposals,
  **0** fully verified source-artifact pairs.

## Live original service: simplified polygon problem

A fresh official ArcGIS feature query for objectid 574 returned a
`MultiPolygon` with `code_zone=zone rouge`, represented as GeoJSON.
It is a *regulatory PPRI polygon*, **not a map of the actual 2016 flood**.

- An unsimplified original full-precision feature-response body was
  **not completely captured** using the available research extraction
  interface; it clips large JSON responses. No full original bytes,
  original response hash or geometry archive is claimed.
- A bounded research query requested `outSR=4326`,
  `geometryPrecision=6` and `maxAllowableOffset=0.00003` degrees,
  explicitly **rounded/generalized**, for topology analysis only.
  Its response parsed into **one** PPRI feature, **48** component
  polygons, **3,286** vertices, SRID 4326.
- The generalized geometry **failed `ST_IsValid`** with
  `Self-intersection[2.548688 48.5359735436242]`. A direct
  `ST_Intersects` consequently produced a GEOS TopologyException.
  This is a **negative geometry QA result**, not evidence of a
  valid building intersection or proof the unsimplified provider
  geometry is invalid. Do not automatically `ST_MakeValid` without
  recording changes, source identity, area/topology effects and
  acceptance criteria.

## Safe original-geometry intake

`research_runners/ppri_polygon_geometry_preflight_v0.py` provides a
strict **offline** validator using Shapely. It takes a source GeoJSON
file, the exact source query URL and objectid. It checks:
- source-host/path and exact objectid selector; geometry request
  `outSR=4326` and `f=geojson`;
- one object of type `Polygon` or `MultiPolygon`, finite bounds
  in the declared pilot region, unambiguous feature/property identity;
- source response byte SHA, topological validity and reason;
- request-specified rounding/generalization flags that block
  **precise** overlay use even if the returned shape is valid.

Run on locally acquired authorized original-response bytes only:

```bash
python -m research_runners.ppri_polygon_geometry_preflight_v0 \
  --source-file /private/ppri-574.geojson \
  --query-url 'https://sig.seinegrandslacs.fr/arcgis/rest/services/Gestion_Eaux_Inondations_GP/MapServer/17/query?where=objectid%3D574&outFields=objectid%2Ccode_zone%2Cnom_zone&returnGeometry=true&outSR=4326&f=geojson' \
  --objectid 574
python -m unittest tests/test_ppri_polygon_geometry_preflight_v0.py
```

The code prints only summarized geometry diagnostics and SHA-256.
No actual provider polygon bytes are committed. Unknown exact
ArcGIS per-layer rights remain explicitly
`PENDING_EXACT_ARCGIS_LAYER_RIGHTS`. The offline unit tests cover
valid, rounded, malformed, wrong-CRS and self-intersecting samples;
their independent execution status should be read from GitHub CI.

## Next causal evidence needed

Obtain exact complete source geometry bytes and rights record for the
specific approved PPRI layer; run offline topology QA **before**
considering any overlay. For real historical CAT modelling, obtain
independently dated 2016 building footprints and historical flood
extent/depth or physical intensity with source/vintage/CRS and
validation. Next add building values, policy coverages and insurer
loss observations; present-day PPRI regulatory zones cannot replace
those pieces. No Neon source, status, link, schema or model admission
was written during this audit.
