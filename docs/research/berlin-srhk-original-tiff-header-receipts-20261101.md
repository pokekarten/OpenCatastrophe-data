<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Verified original Berlin SRHK GeoTIFF header evidence — 2026-11-01

**Status: authenticated, limited original-source header observations only.**
Machine-readable metadata-only research receipt:
[berlin-srhk-original-tiff-header-receipts-20261101.jsonl](berlin-srhk-original-tiff-header-receipts-20261101.jsonl).

## Exactly what was observed

Two independent source-bound GitHub Actions runs used already pinned original
official GDI Berlin water-depth ZIP URLs. In each case the source worker requested
**only bytes 0–65,535** per scenario, required original HTTP 206, a matching
first-512-byte source SHA, and capped the in-memory TIFF Deflate prefix at
**1 MiB**. The two full ZIPs (~619 MB and ~563 MB) were **not** downloaded.

- [Original affine/header run 41334867841](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41334867841) — merged main commit `e6b0831bf7f64b72e109fa111bf8af9664d88fd6`.
- [Original NoData/band-header run 41335440273](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41335440273) — merged main commit `383ab39fb6f7612660476b7b5992b9df76c012c3`.

| Original source TIFF metadata | Extreme | Extraordinary |
| --- | --- | --- |
| Original prefix, SHA-256 (65,536 ZIP bytes, **not** archive hash) | `9b86b039e4c0915b76f4ea64bc13c201f43483a2585dcdd8f6650d6e1a70579f` | `ba22dae2169f3ffab268f9411099e98c5fc3a15cfd8094d6b486b6e9a0c32149` |
| Internal projected CRS | EPSG:**25833** | EPSG:**25833** |
| Declared TIFF raster size | **63,882 × 54,756** cells | **63,882 × 54,756** cells |
| Declared pixel scale | **1 × 1 metre** | **1 × 1 metre** |
| Full fixed 200 m pilot bbox inside *header extent* | **Yes** | **Yes** |
| Declared GDAL_NODATA (42113) | **−9999** | **−9999** |
| SampleFormat (339), BitsPerSample (258) | 3 (IEEE floating point), 32-bit | 3, 32-bit |
| SamplesPerPixel (277), Compression (259) | 1, LZW (code 5) | 1, LZW (code 5) |
| GDAL_METADATA (42112) | **Absent** | **Absent** |
| GDAL `UNITTYPE`, `SCALE`, `OFFSET` | **Not declared in checked header** | **Not declared in checked header** |
| Full ZIP digest / pixel blocks / mask verified | **No** | **No** |
| Insurer exposure / CAT hazard model input admitted | **No** | **No** |

Both original TIFFs declare an identical *projected header bounding box*
(`EPSG:25833`, metres):

```
xmin = 360768.970463454    ymin = 5789616.562878486
xmax = 424650.970463454    ymax = 5844372.562878486
```

The pre-existing **fixed and synthetic-tested** Berlin 200 × 200 m pilot bbox
(`391700, 5819950, 391900, 5820150` EPSG:25833) is *contained*
in the declared header bounds. This proves header-level coordinate coverage
only. It does not prove that any of the pilot's individual **real buildings**
overlap valid, non-NoData, flooded pixels.

## Scientific and safety boundaries

`GDAL_NODATA=-9999` is an explicit TIFF **metadata declaration**. It is
**not** a sampled valid-data mask, not a zero, and not a proof that any given
cell has that value. Neither original file exposes a reviewed GDAL
`UNITTYPE`, `SCALE` or `OFFSET` in the inspected prefix; **do not assume
metres**, centimetres, or a specific physical scaling for source pixels.

"2022" in source object names is not a verified event or modelling vintage:
ZIP HTTP Last-Modified evidence was 2025 and these source reads took place
2026-11-01 UTC. Provider scenario semantics, source rights, complete CRC,
true pixel contents and validity mask, exact building–cell intersection,
water-depth units, secondary uncertainty and portfolio admission all remain
**separate explicit gates**. No raw source/provider bytes have been committed.

## Offline integrity check

```bash
python -m unittest tests.test_berlin_srhk_original_tiff_header_receipts_v0 -v
```

The test guards receipt uniqueness, pinned source URLs/partial hashes, original
run identities, declared CRS, bbox arithmetic, explicit no-model-admission,
NoData-vs-zero separation and source-unit unknowns. It **cannot** establish
remote source authenticity by itself; the linked original workflow logs are
the source evidence. No external requests, ZIP downloads, raster pixels or
insurance values are part of this reproducibility check.

Next stage: separately review official water-depth **units/scenario semantics**
and license; only then design an explicitly bounded sample of real TIFF
pixels with verified internal LZW tile offsets, NoData masking and exact
geospatial footprint joins.
