<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Geocoding evidence challenge v0 — executable offline QA

**2026-11-04. Status:** diagnostic only; no rights clearance, scientific validation, physical building match, source admission, insured exposure or CAT loss. Implements a bounded, source-aware *rank-one evaluation* for a future Luxembourg geocoder benchmark; complements rather than duplicates [toolchain PR #1240](https://github.com/pokekarten/OpenCatastrophe-data/pull/1240).

## Exact implementation

- `scripts/geocode_evidence_quality_v0.py` — standard-library-only `benchmark(rows, threshold_metres=50.0)` function; no web requests, filesystem writes or new dependencies.
- `tests/test_geocode_evidence_quality_v0.py` — 15 deterministic tests using wholly invented coordinates and source IDs.
- Input case fields: `case_id`, `engine`, `reference` and `candidates`. The independent *declared* reference supplies `lat`, `lon`, `crs=EPSG:4326`, `source_family`, `as_of`. Each ranked candidate supplies `rank`, WGS84 coordinates and CRS, `source_family`, `source_id`, `snapshot`, `as_of`, `precision` (one of `address_point`, `building_rooftop`, `parcel_centroid`, `street_interpolation`, `place_centroid`, `unknown`).
- Only **declared rank one** is scored against truth. The reference coordinate is never used to rank or promote a candidate. Great-circle distance assumes spherical Earth radius 6,371,008.8 metres; this is a QA approximation, not parcel-survey accuracy.
- Fail closed for malformed coordinates (including `bool` and NaN), non-WGS84/unknown CRS, bad source IDs/snapshots, invalid dates, duplicate cases, duplicate source features, duplicate/gapped ranks, invalid precision, invalid thresholds.
- Outcomes: `no_result`, `known_shared_lineage`, `post_reference_snapshot`, `ambiguous_candidates`, `coarse_precision`, `outside_threshold`, `within_threshold_analysis_only`. Last outcome **does not accept any physical asset association**. All outputs carry `analysis_only: true`, counts and rank-one error metrics only.
- Source-family equality detects **known overlap**, not lineage independence: distinct strings may still share Google/OSM/Overture upstream imagery, geometry or government registries. Historical snapshots newer than the control date are quarantined, not silently backdated. An address point is not an insured building or TIV.
- The **50 m default is illustrative** and must be predeclared/replaced for a real region by a sourced tolerance and independently selected holdout. For physical footprint acceptance, downstream point-in-polygon, vintage, parts/units and original CRS evidence are still required.

## Reproducible focused checks

In an ordinary Git checkout with Python 3.11+:

```bash
python -m unittest tests.test_geocode_evidence_quality_v0 -v
python scripts/check_all.py
```

On 2026-11-04 the 15/15 synthetic focused tests were run successfully on Python 3.13.5 in an isolated Linux working directory using the exact 8,005-byte module and 5,234-byte test contents subsequently committed to the branch. **Not established:** complete repository `check_all.py` at exact PR head, public-provider retrieval, source-file rights, live Pelias/Photon install, accuracy on real addresses, geodetic survey-grade distance or downstream asset joins. The source checkout cannot be cloned through the isolated container DNS; keep PR in draft pending the full CI gate.

## Provider-specific blockers

- **OpenAddresses:** catalog source JSON is CC0, but the processed address/parcel/centerline bytes are **not relicensed**; each upstream license and geography must be reviewed: https://github.com/openaddresses/openaddresses#license .
- **Pelias:** can import OA, OSM, GeoNames and WOF; geocoder/ingested feature IDs from OA and OSM may change between imports, unlike generally stable GeoNames/WOF IDs. Preserve `engine`, `source_id`, `source_family`, `snapshot` together: https://github.com/pelias/pelias and https://github.com/pelias/documentation/blob/master/place.md .
- **Photon:** public demo may throttle extensive use and does not provide a bulk-processing SLA; do not design benchmarking around scraping its public endpoint: https://github.com/komoot/photon .
- **Microsoft TEMPO:** published *raster* bands are density fraction (0–1) and predicted height fraction (0–1; multiply by 100 for metres), NoData = −1, worldwide ~100 m coverage for 2020 Q4 and 2023 Q4. These are **not independent footprint coordinates** and must be assessed separately: https://github.com/microsoft/buildings .

## Next causal test

Select 20–50 independently verified, non-personal original-provider address reference points for one narrow Luxembourg pilot with separately checked usage rights; freeze source snapshot, geometry/CRS and date. Evaluate geocoder output with this offline module **without** copying raw household addresses into public Git. Compare `rank-one` error, null, ambiguous, temporal and known-lineage counts; then run a separate admitted-footprint polygon join and retain unresolved cases. Only after independent licensing/science review should any geocoded association appear in a model-input manifest.
