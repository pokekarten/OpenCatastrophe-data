<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# DLR/MindEarth WSF Tracker: original GeoZarr access and non-admission preflight (2026-11-03)

**Outcome:** Provider original *metadata endpoints* were successfully fetched; two exact source-body SHA-256s, source type and array shape are recorded. An offline, fail-closed Python validator plus deterministic synthetic tests were added. **No raster chunks, building coordinates, insurer customer values or original asset bytes are committed or model-admitted.** The source candidate is the existing `dlr.eoc.wsf-tracker.2016-2026`; no duplicate source ID is created.

## Two distribution paths for one source

1. [DLR EOC official WSF Tracker](https://web.geoservice.dlr.de/web/datasets/wsf_tracker), [original STAC collection](https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_TRACKER?f=json): published CC BY 4.0, approx 10 m, global latitude limit approx 60 S to 78 N, original COG link at the item. The STAC metadata advertises a `P1Y` cube step but the text says biannual updates. Observed STAC single global COG asset grid shape: **1,536,210 × 4,007,502**; band `uint8`; `nodata=0`.
2. [MindEarth official WSF GeoZarr distribution](https://source.coop/mindearth/wsf), also linked via [WSF's official raster access page](https://worldsettlementfootprint.com/raster-download). Public direct data at `https://data.source.coop/mindearth/wsf/World_WSF_20160701-20260101.zarr` with no authentication. Zarr v3 groups `0` (native) and `1`–`12` (overview). The source `wsf_tracker` variable is `int8`, code `0` = **no detected settlement or nodata**, codes `1`–`20` = *earliest detected built-up period*, half-year epochs from 2016-07-01 to 2026-01-01. Code 1 means **already built-up at first observation**, not a measured construction date in 2016. Because changes of use/urbanization and demolition are not explicitly recorded by this earliest-onset code, do not infer contemporary building counts or demolition from it.

### Exact read-only original metadata receipts (3 November 2026)

| Source file | Returned bytes | SHA-256 over original body | Decoded shape and type |
| --- | ---: | --- | --- |
| [GeoZarr native `0/wsf_tracker/zarr.json`](https://data.source.coop/mindearth/wsf/World_WSF_20160701-20260101.zarr/0/wsf_tracker/zarr.json) | 1961 | `c9247cdba4b7f5d5652941015510f870969987b3287fe549fd9c52ca20829333` | Zarr v3 `int8`; **1,536,433 × 4,007,502**; fill `0`; valid index 0–20 |
| [GeoZarr overview `12/wsf_tracker/zarr.json`](https://data.source.coop/mindearth/wsf/World_WSF_20160701-20260101.zarr/12/wsf_tracker/zarr.json) | 1953 | `b7e289dd728e12ef69d8ad4a2ae8aa9623ca95e678073953d7560813ba8e6dd1` | Zarr v3 `int8`; **375 × 978**; same index domain |

The metadata is source-provided JSON, independently read via a bounded read-only HTTP interface and hashed as returned. The SHA-256 fingerprints are **source-response identities for this inspection only**, not guaranteed future immutable versions. The JSON metadata describes storage with **8192 × 8192 Zarr shards and 256 × 256 inner chunks**, `sharding_indexed` and compressed `blosc`/`zstd`.

### Three non-negotiable modelling guards

- **Overview bias:** GeoZarr overview groups 1–12 are produced using **minimum index aggregation**, not sums/means/majorities. Any output from these levels can understate built-up fractions and shift apparent built-up dates, especially because zero may be nodata/unbuilt. **Always use native group 0 for exact area and vintage summaries**; even native group 0 needs uncertainty, geolocation and external validation.
- **COG/GeoZarr alignment unproven:** DLR STAC reports **1,536,210** rows; MindEarth GeoZarr native metadata reports **1,536,433**. Difference **223 rows**, while both report 4,007,502 columns. Never claim cellwise equality, direct spatial overlay or identical support before comparing geotransform, coordinate bounds, resampling and nodata. The provider products may encode slightly different registration/coverage.
- **Detection is not replacement value:** Pixel 1 indicates pre-existing built-up, not observed 2016 construction, footprint, building type, height, dwellings, insured value, or demolition. All exposure/calibration downstream decisions remain source-licence and scientific gates.

## Offline source-metadata preflight

`research_runners/dlr_wsf_tracker_geozarr_metadata_preflight_v0.py` requires the original two separately SHA-pinned source-body files. It accepts only strict JSON, exact expected Zarr v3/int8/shape/epoch code metadata, shard layout, and `min` overview semantics; it produces a small aggregate receipt with **`model_input_admitted=false`** and forbids an output path that overwrites original bytes.

```bash
# Obtain original JSON source bytes from the exact URLs above using an
# approved read-only metadata-fetch workflow; never download the whole raster
# implicitly, do not commit the provider files and freeze their retrieval time.
python research_runners/dlr_wsf_tracker_geozarr_metadata_preflight_v0.py \
  /secure/original/level0-zarr.json /secure/original/level12-zarr.json \
  --expected-level0-sha256 c9247cdba4b7f5d5652941015510f870969987b3287fe549fd9c52ca20829333 \
  --expected-level12-sha256 b7e289dd728e12ef69d8ad4a2ae8aa9623ca95e678073953d7560813ba8e6dd1 \
  --out /tmp/wsf-geozarr-original-metadata-receipt.json

python -m unittest discover -s tests -p 'test_dlr_wsf_tracker_geozarr_metadata_preflight_v0.py'
python scripts/check_all.py
```

`earliest_detection_epoch(index)` maps 1 to `2016-07-01`, 2 to `2017-01-01`, and 20 to `2026-01-01`; zero returns `None`, which **must not** be interpreted as an insured property count of zero. Values outside 0–20, including booleans, block.

## Next causal actions

1. Resolve actual exact-pixel **coordinate transform and nodata** differences between COG and GeoZarr. No pixel overlay until this is done.
2. Complete CC BY 4.0 attribution and redistribution obligations for the *specific original GeoZarr asset* and its underlying Sentinel-source scope. Open accessibility alone is not scientific/commercial admission.
3. For a limited location in a properly versioned and rights-cleared source, make a bounded native-group-0 subset proof using exact Zarr sharding/chunk positions and independent building inventory; no unbounded global raster ingestion.
4. Contrast **observed flood extent** against exposure raster and independently observed damages at matching acquisition dates. Do not infer affected buildings from a mere event point.

Only the registry entry, this reproducible research document, the offline validator and synthetic tests are in this PR. No database mutation or production loss-model dependency is introduced.
