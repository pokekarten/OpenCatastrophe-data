<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GHSL BUILT-S/V E2020 ↔ BVV HU-BY recent footprint — offline comparability gate

**Purpose:** make one limited research calculation possible **only after**
the original full 501,212,696-byte Bavarian Shapefile has been independently
read in exact public HTTP-206 segments, all 2,703,736 original native
records have passed, original ZIP-member CRC32 matches `55540a66`,
and the fixed 32×32 Munich-region source support has a complete official
footprint union. This code makes **no external HTTP requests or database
writes** and never persists pixels, polygons or individual building
locations. It is not a historical 2020 truth label or any CAT-model input.

## Frozen provenance

- JRC original `ec-jrc.ghsl.ghs-built-s.r2023a`, original Neon
  research-only observed-value **sample #49**, canonical JSONB SHA
  `9b3e183d113c10f0fa1a1142ce9041813043874980eac67f038ef39802fd0ed5`;
  original native E2020 32×32-window **74,802,406 m²** of source-modelled
  built-up surface, 937 positive/87 zero original uint32 cells, fixed
  origin col 22973,row 4899
- JRC original `ec-jrc.ghsl.ghs-built-v.r2023a`, sample **#50**,
  canonical JSONB SHA
  `a9bf86d9fbbe6c84fbd81ad6050a2d8774171af38953b7976e6dd48eabc01876`;
  original native E2020 **520,775,503 m³** modelled built volume,
  same 32×32 native geographical support. It is **not** an additional
  independent building survey, and a volume cannot be divided by
  a 2D footprint to infer insured exposure/TIV without an approved model.
- Original geographic source support is **EPSG:4326, 30 arcsec,
  col=22973,row=4899, width=32,height=32** and its edges are
  independently recomputed and densified in the existing
  `frozen_roi_geometries()` method before projecting to
  original Bavarian public Shapefile **EPSG:25832**.
- Original official BVV Oberbayern HU-BY source:
  `https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip`,
  product-scoped **CC BY 4.0**, attribution:
  **Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de**.
  Publisher's dataset-ATOM `rights=TODO` remains a documented
  incompleteness, not a blanket extension to the restricted
  ALKIS WFS or national HU-DE.
- Prior authentic source evidence includes the first 64 native
  source polygons, original 2.7m SHX index and original DBF row count;
  the separate **complete original SHP** proof is required.
  Neither 64 polygons nor a truncated 1-million-record run may
  pass this gate.

## Exact source completeness checks (deny by default)

`research_runners/ghsl_bvv_cross_epoch_area_gate_v0.py` requires
three **offline locally supplied JSON objects**:

1. Neon row #49 of source BUILT-S R2023A E2020, complete
   `source_id`, `sample_kind`, `sample_sha256`,
   `provider_response_sha256`, `research_only=true`,
   `model_input_approved=false` and unmodified `sample_json`
   aggregate
2. Same original Neon fields for row #50 BUILT-V
3. The successful **trusted-main original full SHP streaming source
   JSON receipt** from the same reviewed full-region range-stream
   code, after verifying **all** 20 contiguous source reads, original
   first response SHA, complete uncompressed Shape SHA/CRC and
   2,703,736 original frame/Polygon counts

The original BGG/SHX source cardinality, source-byte footprint
`501212696`, ZIP original CRC32 `55540a66`, original
49,197-byte SHA-256, exact source URL and logical ranges, complete
ROI Boolean, no source-byte/coordinate retention and
`model_input_approved=false` must all match frozen expectations.
Both original full compressed and native decoded SHA-256 fields
must be correctly formatted and nonempty, *but the offline
comparator is not itself a second download or independent full-file
hash recheck*. The original streamed SHA + CRC and real trusted-main
workflow must be inspected separately before relying on those values.

For the exact same projected geographic footprint,
`roi_original_polygon_areas_union_m2` must be finite, positive,
no greater than the independently projected ROI, and less than the
plain clipped-area sum. GEOS union overlap identity is checked to
within 0.02 m² rounding. Any missing/intermediate 1-million-record
receipt, source CRC drift, extra/missing 8-MiB segment, source mismatch,
inconsistent projected area, invalid GEOS ring, or model admission
**blocks the calculation**.

No real comparability result is asserted until the complete original
Shapefile run has succeeded and its source logs have been verified.

## Deliberately restricted calculation

Only the following descriptive aggregate is calculated:

```text
recent BVV cadastral outline union footprint area (m²)
-------------------------------------------------------   = descriptive source-area ratio
GHSL E2020 originally modelled built surface (74,802,406 m²)
```

Also show the direct difference (current BVV union minus 2020 GHSL
surface) in m², and the projected study ROI area. The volume
`520,775,503 m³` is only shown as **separate context**, never
as a direct 2D footprint comparison.

**Important scientific interpretation:** this is a **cross-epoch
2020 model vs current-era cadastral product**. It cannot be
interpreted as a 2020 accuracy, a calibrated bias, a recall/precision
metric, an independent unique-building count, a ground-truth city
exposure, insured value, insurer-specific portfolio or an approval
for CAT model input. Cadastre survey dates and change histories
are not verified; both product definitions also differ and
could affect totals. GHSL BUILT-S and BUILT-V are dependent
model estimates, not independent statistical validation samples.
Every successful comparison labels
`ratio_is_accuracy_or_model_calibration_metric=false`,
`research_only=true`, `model_input_approved=false`.

## Execution after complete original source success

Export only the two aggregate Neon rows read-only, casting the
bigint sample ID to JSON integer:

```sql
SELECT sample_id::int AS sample_id, source_id, sample_kind,
       sample_sha256, provider_response_sha256,
       research_only, model_input_approved, sample_json
FROM research.source_sample_v0 WHERE sample_id IN (49, 50)
ORDER BY sample_id;
```

Prepare those as two local files (no real source raster).
Copy only the exact **successful, verified** original BVV full-member
research receipt JSON into a third private local file. Then:

```bash
python -m research_runners.ghsl_bvv_cross_epoch_area_gate_v0 \
  --ghsl-s-neon /private/neon-ghsl-s-49.json \
  --ghsl-v-neon /private/neon-ghsl-v-50.json \
  --bvv-full-source-receipt /private/bvv-complete-original-shp.json
```

The tool outputs only the provenance and descriptive ratio JSON
to stdout. It performs **no Internet connection**, no Neon mutation,
no raw Shape/Pixels persistence and no automatic admission.
The CI workflow `.github/workflows/ghsl-bvv-cross-epoch-area-gate.yml`
runs **synthetic research receipts only** with pinned GEOS/PROJ,
including cases for nonexistent complete original sources,
partial SHA/CRC, source identity drift, missing ranges, an unmatched
spatial ROI and false scientific/model promotion.
