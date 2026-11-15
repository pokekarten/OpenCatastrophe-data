<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT2023v2: source attribute completeness original-byte receipt

**Verified on:** 2026-11-01 UTC. **Scope:** original ACT2023v2 roof extent
GeoPackage source quality only; **not** EUBUCCO matching, building topology
approval, insured exposure or CAT model admission.

**Reproducible original provider execution:** 
https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41307228628

## Immutable source identity

- Official resource: `d62942ec-0dc8-40e2-9fa4-27841e6e1ac1`;
  `ACT2023v2_Buildings3d_Footprints`, roof-derived building extents, Luxembourg.
- Previously independently observed ZIP SHA-256:
  `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a`.
- Independently pinned original extracted GeoPackage SHA-256:
  `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`.
- Exact count **238,189 original feature records**, native **EPSG:2169**
  and **MULTIPOLYGON**, full extent and axis semantics still unvalidated.

## Actual source-level quality checks

| Field / measure | Observed source-level result |
| --- | ---: |
| `id`: distinct nonblank | 238189 |
| `buildingid`: distinct nonblank | 238189 |
| `buildingid`: missing or blank | 0 |
| `buildingid`: duplicate nonblank rows | 0 |
| `gml_id`: distinct nonblank | 238183 |
| `gml_id`: missing or blank | 6 |
| `gml_id`: duplicate nonblank rows | 0 |
| `commune`: distinct nonblank | 105 |
| `lau2`: distinct nonblank | 105 |
| `commune` / `lau2`: missing | 0 / 0 |
| `modelmodificationdate`: null or blank | 21 |
| Original `geom` null | 0 |
| `area`: null / nonnumeric SQLite types / nonpositive numbers | 0 / 0 / 0 |
| `zmin`: null / nonnumeric SQLite types / nonpositive numbers | 0 / 0 / 0 |
| Spatial RTree indexed feature rows | 238189 |
| Spatial RTree coverage difference versus features | 0 |

These are **actual aggregate SQL counts from the exact downloaded original
GeoPackage**, not a synthetic or derived market-size estimate. `commune`
and `lau2` are administrative group fields, so repeated values are
expected and not building-ID collisions. Non-null geometry is not proof that
topology is valid; complete RTree membership is not proof of precise location.
The source `area` value is not insured total-value exposure, and `zmin`
is not building height or a building-vulnerability classification.

## Execution and admission boundaries

The workflow uses one fixed, provider-hosted HTTPS download, checksum gates on
the ZIP and the extracted GeoPackage and a temporary GitHub Actions runner;
no original building records, individual IDs, geometry or file bytes were
uploaded to GitHub as artifacts or persisted in insurance Neon. Synthetic
tests also run independently.

This receipt establishes **high observed identifier completeness** and the
absence of basic field-type/null problems. It does **not** authorize production
building-to-insurer joins, risk-by-address underwriting or commercial
redistribution of EUBUCCO. Provider file-level CC0 and EUBUCCO Luxembourg
lineage/licence are distinct evidence requirements.

## Next causal work, after the measured source-quality result

1. Independently audit EPSG:2169 **native stored axis order** against external
   geodetic ground-control data and test representative original polygon
   topology; do not silently swap coordinates or reproject arbitrary axes.
2. Freeze a same-vintage, authorised EUBUCCO Luxembourg release and its
   `geometry_source` lineage; verify that ACT is not upstream of the comparison
   source before treating agreement as independent validation.
3. On a **bounded private local** geographic window, perform 2D roof
   polygon-vs-EUBUCCO overlap and a manually adjudicated match sample;
   preserve 1:n and n:1 ambiguity. Keep original per-building geometries
   outside Git and the metadata database.
4. Only then consider whether observed building geometry/attributes may
   legitimately support a separate vulnerability/asset exposure pilot.
