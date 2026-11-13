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

The original BVV/SHX source cardinality, source-byte footprint
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


## Actual same-ROI original-data research comparison accepted — 2026-11-13

The acceptance prerequisites above are **now satisfied**, independently
from the original-source read itself:

- Real [BVV original full SHP GitHub Actions #43471636096](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43471636096):
  **20 individually verified contiguous original HTTP206 ranges,
  166,172,236 compressed member bytes SHA-256
  `22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615`,
  501,212,696 original uncompressed SHP bytes SHA-256
  `977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c`,
  original ZIP member CRC32 `55540a66`, and exactly 2,703,736 native
  original Polygon frames**. The full original *SHP member*, not the
  entire original *ZIP archive*, has been completely SHA/CRC validated.
  Original file SHA matches earlier independently executed Neon
  source metadata receipts #56/#57.
- The original public BVV HU-BY source is product-scope **CC BY 4.0**,
  attribution required; publisher dataset ATOM's `rights=TODO`
  is still an unresolved catalogue metadata field, not a restriction
  transference from national HU-DE or closed ALKIS.
- The original E2020 BUILT-S and BUILT-V raster research values
  were already independently reproduced by
  [trusted-main GDAL run #43317950827](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317950827)
  from original JRC TIFF blocks, matching source and native-window
  hashes in Neon research samples **#49** and **#50**.
- New BVV source-complete research sample **#94**, canonical
  PostgreSQL JSONB SHA-256
  `c32c7336571d820d0b73813cdb58afcff50d105f2899640d4ab5214b35165482`,
  records source provenance, **417,565 actually ROI-intersecting**
  original polygons, **431,083** broad ROI bbox candidates and
  all source-CRC/SHA and original area-union receipts. Only
  aggregate footprint statistics were saved, never a polygon,
  coordinate, individual building ID or insurer/location record.
- The **offline comparability guard** was independently synthetic-tested
  in [PR #1547](https://github.com/pokekarten/OpenCatastrophe-data/pull/1547),
  all 6 source/SCI gates successful, and the entire GitHub CI green.
  This is **not a claim the CLI was run against actual private
  exports**: actual source-backed numeric values below come from a
  separately executed **read-only Neon SQL join** with fail-closed
  source/rights/full-SHP/hash/window checks.

### Real same-ROI descriptive aggregates, original science units

| Research question | Full original verified research result |
| --- | ---: |
| GHSL BUILT-S E2020, entire frozen 32×32 native window | **74,802,406 m²** (74.802406 km²) |
| BVV current-era registered source Polygon union inside exactly that ROI | **56,791,644.170 m²** (56.791644 km²) |
| BVV raw area sum of clipped official polygons before overlap correction | **56,871,811.455 m²** |
| Official polygon self-overlap removed by union | **80,167.285 m²** |
| Same ROI total physical EPSG:25832 area | **588,514,088.109 m²** |
| BVV union / GHSL E2020 source surface area | **0.7592222** (**75.9222%**) |
| BVV current-era union minus GHSL E2020 modeled surface | **−18,010,761.830 m²** (−18.010762 km²) |
| GHSL BUILT-V E2020 modeled volume (**not** 2D validation) | **520,775,503 m³** |

All source figures above refer to **the same fixed original
EPSG:4326 32×32 window** at native col=22973, row=4899,
with the BVV polygon ROI built by densifying the geodetic envelope
and projecting to original Shapefile EPSG:25832. In the BVV source
there are **zero GEOS-invalid ROI rings and Polygon reconstructions**
under the checked orientation/topology contract.

These real values were confirmed with a **read-only Neon SQL query**
that required original samples #49/#50/#94, canonical PostgreSQL
`sample_sha256` validity, exact reviewed product/source identities,
the original full-SHP CRC/hash and 2,703,736 record counts,
all 20 original HTTP-206 segments, the exact 32×32 original
window, research-only flags, source rights
`commercial_reuse_verdict=allowed_verified`,
and `admission_status=not_admitted`.

A compact independent read-only replay for **already accepted**
full-source receipts, with fail-closed direct sample-hash and
unit checks, is:

```sql
WITH s AS (
 SELECT sample_json AS j FROM research.source_sample_v0
 WHERE sample_id=49
 AND source_id='ec-jrc.ghsl.ghs-built-s.r2023a'
 AND sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
 AND model_input_approved=false
 AND sample_json->>'fixed_window_positive_sum_raw_source_units'='74802406'
), b AS (
 SELECT sample_json AS j FROM research.source_sample_v0
 WHERE sample_id=94 AND source_id='de.bayern.hausumringe'
 AND provider_response_sha256=
   '22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615'
 AND sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex')
 AND sample_json->>'original_full_decoded_shape_crc32'='55540a66'
 AND sample_json->>'original_full_native_records_checked'='2703736'
 AND sample_json->>'provider_original_206_segments_verified'='20'
 AND sample_json->>'roi_complete_for_this_verified_SHAPE_archive_only'='true'
 AND sample_json->>'historical_2020_ground_truth_verified'='false'
 AND model_input_approved=false
)
SELECT ROUND(
 (b.j->>'roi_original_polygon_areas_union_m2')::numeric /
 (s.j->>'fixed_window_positive_sum_raw_source_units')::numeric,
 7) AS descriptive_cross_epoch_ratio_not_model_accuracy
FROM s CROSS JOIN b;
```

### Crucial scientific and insurance interpretation

The observed **75.9222% is not an accuracy, sensitivity,
specificity, loss, market share, 2020 validation benchmark or
insurable-building count**. It is a **strictly descriptive**
ratio between a **2020 model-derived built-surface estimate**
and a **current-era cadastral-derived footprint union**. The
building observation/survey dates of the BVV source have not been
independently established. Source definitions and footprint
completeness may also differ. Without a temporal harmonization
strategy, independent hold-out samples and explicit definitions
of which structures qualify, the numerical discrepancy cannot
be allocated to GHSL model error or real construction growth.

Furthermore GHSL BUILT-V is itself dependent on built surface
and modelled building height; its **520.8 million cubic metres**
cannot directly validate the BVV 2D footprint, TIV,
construction/occupancy attributes or physical loss.

No production source approval, loss estimation, insurer capital
modelling, synthetic OED building values, or active CAT calibration
was performed: both data sources remain research-only and
`model_input_approved=false`.
