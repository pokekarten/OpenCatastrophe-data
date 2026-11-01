<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EMSN028 original Flooded_area: three-method repair challenge, 2026-11-01

**Reproducible proof:** [successful live GitHub Actions run 41349861341](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41349861341), executed with the pinned original Copernicus France 2016 ZIP, Fiona 1.10.1, Shapely 2.1.2 and Python 3.12. See [machine-readable research receipt](cems-emns028-invalid-original-flood-repair-sensitivity-20261101.toml) and the [original-source FileGDB audit](cems-emns028-filegdb-topology-audit-20261101.md).

## Source and failure

The FileGDB `Flooded_area` is a **single invalid original MultiPolygon** (not 2016 AOI04-specific yet), containing **59,755 source coordinates** and the error
`Ring Self-intersection[485697.5986 5358841.9696]` in **EPSG:32631**.

The source ZIP was checked again against SHA-256
`7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2`.
No original or derived polygons were committed, extracted into Git, persisted into Neon, or published. Temporary runner source data are automatically deleted.

## Three distinct in-memory repairs, no auto-fix

| Research repair | Output valid | Multipolygon pieces | Area (m²) |
| --- | --- | ---: | ---: |
| GEOS/Shapely `make_valid(method="linework")` | Yes | 2,075 | 12,166,174.82 |
| GEOS/Shapely `make_valid(method="structure", keep_collapsed=False)` | Yes | 2,075 | 12,166,174.82 |
| GEOS/Shapely `buffer(0)` | Yes | 2,075 | 12,166,174.82 |

All produce **59,770** coordinates. The linework-versus-structure and linework-versus-zero-buffer **symmetric difference areas each round to 0.00 m²**, and the polygon intersection-over-union metrics each round to **1.0000000000**. Such numerical equality is a positive **method sensitivity test**, **not a publisher-certified spatial accuracy finding**. In particular, the invalid input's arithmetic `area` was **never used as a reference truth**; no source-versus-repaired area-change percentage is justified without an independently accepted original geometry.

Shapely officially documents different linework and structure semantics and potential geometry collections. A valid result alone does not establish which recovery represents the actual floodwater: [Shapely 2.1.2 make_valid](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.make_valid.html). This case happened to produce indistinguishable outputs to the reported precision.

## Independent point-context check (not an inundation finding)

The previously sourced public Ponthierry gauge control (WGS84 2.547772811°, 48.536875139°), transformed for the comparison to EPSG:32631, is **not within or on the boundary** of any of the three repaired candidate polygons. Its shortest planar distance to each candidate is **335.15 m**. All three methods agree.

This is a source geometry-to-control-point spatial diagnostic only. It cannot show that Ponthierry was dry during the 2016 event, that the gauge had no high discharge, that either current RNB building was unaffected, or that insurer exposures/losses were zero. The 2016 original archive aggregates activation data; the `aoi` layer is **one broad area**, not a proven separate AOI04 polygon. Satellite acquisition coverage and sensor limits are additional confounders. Different 2016 hazard products must not be conflated.

## What changed in OpenCatastrophe-data

- [Repair comparison code](../../research_runners/cems_emns028_topology_repair_challenge_v0.py), pure in-memory; explicitly refuses valid source input, nonpolygons and excessive coordinate expansion; no scientific auto-admission.
- [Priority-layer original-byte runner](../../research_runners/cems_emns028_priority_layer_semantics_v0.py) calls the comparison only on the known-invalid `Flooded_area` source and reads the public gauge point solely as context.
- [Offline synthetic tests](../../tests/test_cems_emns028_topology_repair_challenge_v0.py) test non-admission flags, valid/nonpolygon rejections and non-evidentiary control-point semantics.
- [Mandatory geospatial GitHub Actions workflow](../../.github/workflows/cems-emns028-priority-layer-semantics.yml) pins the dependencies and checks SHA-256 every fresh run; its latest challenge run completed successfully.
- This report and its TOML receipt are metadata-only; actual Copernicus bytes and repair geometries were not published.

## Decision

**Technical geometry recovery is now reproducible at the source-archive level**, but **no CAT model input is authorised**. Further independent gates remain:

1. Verify precise third-party and activation-specific commercial/research use rights; the original EMSN028 map products have displayed *Restricted Use* conditions.
2. Locate and validate the **observed AOI04** extent and its satellite acquisition metadata, not just the activation-wide `Flooded_area` and `Estimated_Max_Flood_Extent`.
3. Establish independent 2016-vintage building geometry and uncertainty, and a legally usable exposure population. The open [BD TOPO D077 2016 research PR #937](https://github.com/pokekarten/OpenCatastrophe-data/pull/937) is a *candidate*, not an imported approved inventory.
4. Only after scientific signoff may a **research-only** overlay on a separate validation branch be considered. Geospatial overlap is not a measure of flood depth, insured TIV, losses, reinsurance contracts, or 10,000-year annual event distributions.

No Neon writes, schema migrations, automatic repairs or CAT model authorizations were made in this work.
