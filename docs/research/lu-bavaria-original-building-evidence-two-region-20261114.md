<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Two-region original evidence for exposure QA — Luxembourg and Bavaria (2026-11-14)

**Research-only.** This pairs two existing but scientifically **different**
original-source investigations without confusing both as one building accuracy
estimate, a global buildings register, a loss model or verified insurer TIV.

## Luxembourg: source-to-source building geometry comparison

- Source A: original ACT building geometries 2026-10-01, pinned original
  ZIP SHA-256 `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`.
- Source B: original Overture Buildings 2026-10-21.0, original Parquet
  part 00226 / rowgroup 182. The full original Parquet file SHA remains
  **unverified**; original rowgroup geometry screening is independently
  evidenced by [Actions #41497879623](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41497879623).
- [ACT–Overture original source overlay #41498511267](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41498511267)
  gives **139 ACT** and **69 Overture** polygons in the *small research
  window*, 282 intersecting polygon pairs and **5 reciprocal one-to-one
  geometric candidates** at ellipsoidal IoU >= 0.75.
- Five selected Overture candidate source-family labels are **OpenStreetMap**;
  selected ACT digitization labels are **Bati3DVDL**. Geometric association
  does **not** establish independent same-physical-building identity,
  independent original upstream surveys, GERS membership or insurer policies.
- This branch's `research_runners/sql/lu_act_overture_geometry_readiness_v0.sql`
  was actually created as a **derived read-only VIEW** on the existing
  isolated Neon research branch `br-bold-unit-baf2smqf`, **not main**.
  It returns one internally consistent aggregate row with all model,
  rights and insured-valuation flags false; no original coordinates, WKB,
  IDs or provider feature rows are stored.

## Bavaria: official footprint polygons against a remote-sensing class mask

- Source A: the **actual fully streamed original** public BVV Oberbayern
  `hausumringe.shp` member, original compressed SHA-256
  `22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615`,
  uncompressed SHA-256
  `977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c`,
  CRC32 `55540a66`, **2,703,736** verified Shapefile records. The exact
  full-member original source scan was actually accepted in
  [Actions #43317649994](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317649994).
  This is a count of polygon *records*, **not** distinct buildings.
- Source B: original **DLR WSF2019** 10m-scale settled-class GeoTIFF,
  independent original native/GDAL bytes and raster cross-check
  [Actions #43226483288](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43226483288).
  Two **32×32** Munich research-window masks are stored as the existing
  Neon research `source_sample_v0` **#28 / #29**, not as new model data.
- Source-derived area overlaps and original member hashes are already
  stored as research **#56 / #57**. Their new read-only reproducible QA is:
  `research_runners/sql/bavaria_hu_by_wsf2019_original_pair_readiness_v0.sql`.
  It joins each **existing** BVV metadata receipt against its precise WSF
  raster sample, recomputes **both canonical JSONB SHA-256 receipts**,
  native 32×32 raster-mask SHA-256 from all 32 binary rows, settlement
  class pixel counts, verified original uncompressed/compressed SHP
  source hashes, the distinct derived grid SHA, stored area conservation,
  intersection-over-union and bounded normalised coverage ratios.
- Live **read-only Neon insurance/main** execution returned exactly **two**
  rows on 2026-11-14: window **#28**: two broad-bbox polygon candidates,
  0 positive settlement pixels, **0.242725** native-pixel-equivalent
  building-area, **IoU 0** and **WSF coverage NULL** (correct:
  denominator zero); window **#29**: 94 original broad-bbox candidates,
  482 positive settlement pixels, **251.813581** footprint area,
  **241.537835** overlap, **492.275746** union, **IoU 0.490656**,
  **0.959193** fraction of footprint area in positive WSF cells and
  **0.501116** fraction of WSF-positive area covered by footprints.
- BVV source rights are product-specific **CC BY 4.0** with attribution;
  attribution: *Datenquelle: Bayerische Vermessungsverwaltung –
  www.geodaten.bayern.de*. This does not authorize proprietary ALKIS WFS,
  ownership data or federal HU-DE. Source:
  [Official rights](https://www.geodaten.bayern.de/odd/m/3/html/nutzungsbedingungen.html).
  The separate DLR/EOC official [WSF2019 dataset catalog]
  (https://catalogue.geoservice.dlr.de/web/datasets/wsf_2019)
  and [original STAC collection](https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_2019?f=html)
  both explicitly state **CC BY 4.0** for WSF2019. This confirms the
  product-level attribution licence, **not** independently reviewed API
  automation/rate or bulk redistribution service terms, model calibration
  validity, temporal alignment or a claim that the 10 m settlement class
  represents standalone insured buildings. Record source credit and
  any derivative modifications for BOTH data products.

## Actually executed: five live, read-only Neon source-integrity challenges

On **2026-11-14**, the committed SQL `bavaria_hu_by_wsf2019_original_pair_readiness_v0.sql`
was executed against the existing `insurance/main` research samples.
No source raster rows/polygons or personal/building IDs were returned;
only per-window aggregate values. The following experiments modified
the **query in memory only**, **never database data**:

| Live query | Source-consistent receipt rows | Expected result |
| --- | ---: | --- |
| Exact committed source SHA/mask/vintage/area checks | **2** (#56/#57) | Both original windows pass |
| Tamper BVV research sample #56 canonical JSONB SHA | **1** (#57 only) | Corrupted source evidence excluded |
| Tamper both pinned native WSF mask digests | **0** | Both source combinations excluded |
| Falsely claim 2019 and BVV source have same vintage | **0** | Temporal-gate drift excluded |
| Tamper full original BVV SHP decompressed SHA-256 | **0** | Both original-source claims excluded |

These are actual SQL readbacks exercising the committed query predicates,
not invented figures or permission to import original polygons.
The source dataset rows and their SHA fields were **not modified**.
Although both source products publish CC BY 4.0, model admission and
API service-specific automation/rate limits remain independent reviews.

## Scientific limits: these TWO IoU numbers cannot be pooled

**Luxembourg** measures a *building-versus-building geometric identity
candidate threshold*: five reciprocal 0.75-IoU matches, not an estimated
physical truth match rate.

**Bavaria** measures the *area-weighted footprint-versus-2019 satellite
settlement class* overlap: the 0.490656 IoU from window #29 **cannot**
be compared to the 0.75 Luxembourg building identity cutoff, nor called
building detection accuracy. WSF-positive cells include non-building
settled surfaces; buildings can occupy only a fraction of a settled cell.
BVV original regional DBF update date is 2026-10-01 but NOT a verified
capture/survey date; WSF is 2019. One-window outcome is not population
representativeness. No bridge currently supplies independent real-world
building or insurer account identity across these regions.

**Explicit remaining NO-GO:** global exposure completeness, a census of
unique insurable buildings, any insurer market-share allocation, TIV or
policy mapping, geo-ID confidence, event loss tables, catastrophe models,
commercial service rights for *other products*, model admission, or
production Neon ingestion from these research-only results.

## Reproduce

For the fixed, verified historical source sample receipts:

```text
-- Execute the plain SQL SELECT in
research_runners/sql/bavaria_hu_by_wsf2019_original_pair_readiness_v0.sql
-- against insurance/main with read-only access. Must return *exactly*
-- sample pairs (#56, #28) and (#57, #29). Missing/corrupt source
-- receipts or original mask rows must produce fewer/zero results.
-- No CREATE, INSERT, UPDATE, DELETE or original provider GET is needed.

-- The different Luxembourg original-source view is on the
-- isolated Neon branch br-bold-unit-baf2smqf (insurance database):
SELECT * FROM research.lu_act_overture_geometry_readiness_v0;
```

Next *scientific* step: independent, source-licensed **building-versus-building**
reference in a second region with an adjudicated sample of splits, merged
footprints, disjoint regions and low-IoU source disagreements; then link only
valid physical IDs to independently sourced TIV/occupancy, hazard and
vulnerability. Existing BVV↔WSF is already real original-source research,
but cannot fill that building-identity benchmark by itself.
