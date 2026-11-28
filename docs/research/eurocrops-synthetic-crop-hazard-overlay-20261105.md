<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EuroCrops synthetic agricultural parcel × flood/hail support pilot (2026-11-05)

RESEARCH ONLY / NOT ADMITTED. This is an offline synthetic geometric test, NOT verified JRC source geometry, a German insurer portfolio, observed flood/hail intensities, crop damage, insured loss, OEP/AEP or an Oasis model run.

## Implementation and use

The new runner is research_runners/synthetic_crop_hazard_area_overlay_v0.py, and the test suite is tests/test_synthetic_crop_hazard_area_overlay_v0.py.

Run:

    python -m unittest discover -s tests -p test_synthetic_crop_hazard_area_overlay_v0.py -q

Local initial proof: **10/10 tests passed**, using only fictional rectangular polygons and a polygon with a hole; full repository GitHub CI must also pass separately.

Both inputs must explicitly declare the fictional projected-metre frame as EPSG:3035, synthetic_only=true, external_source_rows_used=0. Only strictly invented parcel/zone IDs and a fixed small set of fictional crop classes are accepted. The real EuroCrops 2023 GeoParquet cannot be passed to this helper. CLI inputs are local JSONs limited to 200 KB and additionally SHA-256 checked to caller-pinned hashes:

    python research_runners/synthetic_crop_hazard_area_overlay_v0.py \
      /tmp/invented-parcels.json /tmp/invented-hazard.json \
      --parcels-sha256 <sha256-of-first-fictional-file> \
      --hazard-sha256 <sha256-of-second-fictional-file>

Input JSON envelopes and examples can be constructed from the fixtures in the test file, without publishing a separate canonical mock dataset. No external provider bytes, source secrets or insurance contracts are committed.

## Key model semantics

- One invented event per call. Peril flood has hypothetical intensity in metres; hail has hypothetical hail diameter in millimetres. The code enforces the unit distinction but does not calibrate either variable to damage.
- GeoJSON Polygon or MultiPolygon is required. Reject zero-area, invalid, oversized or overlapping crop parcels. Opposed field boundaries may touch but must not overlap in positive area.
- Hazard support polygons for the same invented event may overlap. The intersection area is attributed to the **maximum** intensity at each coordinate. No hazard area may count twice, and exposure area is conserved.
- Explicit numeric zero intensity means **known zero hazard support**. An external location outside all zones is **unknown coverage**, not dry. Explicit nodata polygons are separately identified and forbidden to overlap valid hazard support.
- Output gives per-fictional-field and aggregate areas in square metres by intensity, unknown outside support, and explicit nodata. It never creates insured values, insurance policies, damage factors, ground-truth flood depths, or loss curves. The result always says original_source_rows_used=0, insurer_tiv_used=false, vulnerability_applied=false, insured_losses_calculated=false and cat_model_ready=false.

## Executed entirely fictional example

Two invented square crop parcels each measure 100 m × 100 m (10,000 m² each). In the one-event flood example, one 1 m zone covers the first parcel and half of the second; a 2 m zone overlaps half of the first; a nodata zone covers the remaining half of the second.

| Area-based quantity | Exact synthetic result |
| --- | ---: |
| Total area | 20,000 m² |
| Known hazard support (including overlap de-duplicated) | 15,000 m² |
| Nodata support | 5,000 m² |
| Outside-support unknown | 0 m² |
| First parcel, maximum-intensity depth 2 m | 5,000 m² |
| First parcel, remaining depth 1 m | 5,000 m² |
| Second parcel, depth 1 m | 5,000 m² |
| Actual insurer TIV, economic damage and insured loss | None |

These results are geometrical checks only. Do not call a water-depth fixture an observed flood, or area at an intensity a probability of loss.

## Why this is not yet a CAT model

EuroCrops source geometry, 2023 parcel counts and exact corrected Parquet bytes remain **unverified and unadmitted**. Original German crop codes must be joined on the exact NUTS+original_code composite and their HCAT4 gaps preserved, as documented in eurocrops-hcat4-codebook-original-audit-20261105.md. No national agricultural declaration source may be treated as insured field inventory.

For production-intent modelling, first secure original JRC checksum/metadata, spatial coverage, rights and taxonomy. Then separately validate real dated flood/hail hazard grids and their units, no-data, event support, and footprint uncertainty. Next define an agricultural OED-compatible schema and scientifically reviewed crop-specific stage/season damage functions, explicitly hypothetical values/coverages, and documented event occurrence rates. Only then attempt stochastic event-loss tables, AEP/OEP, gross/net treaty and retro modelling. Existing OED building TIV must **not** be relabelled as crop insured value.

No original GeoParquet was downloaded or committed during this work.
