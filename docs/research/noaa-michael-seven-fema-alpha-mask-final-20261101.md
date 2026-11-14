<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA Hurricane Michael 2018: exact original alpha-mask versus seven public FEMA classifications

**Evidence date:** 2026-11-01. **Original-source automated evidence:** [GitHub Actions source-proof run 41331414001](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41331414001), same PR #955. **Strict scope:** NOAA Digital Coast 2018 Michael collection `8883`, original tile `20181011aC0853300w302100n`; public FEMA historical geospatial layer 0, `DR-4399`, `RS` remote-sensed wind `WI`. No individual FEMA record, building coordinate, address, insured exposure or original raster pixels were retrieved from FEMA or committed to Git.

## Source identity, image integrity and provenance

- NOAA [STAC item](https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0853300w302100n.json) with source GeoTIFF [exact public asset](https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/20181011aC0853300w302100n.tif). The original source first 4096-byte TIFF IFD and original block 324, **HTTP Range `bytes=66694287-66776265`**, were fetched in-memory with **HTTP 206**, exact `Content-Range`, ETag continuity, TIFF/STAC consistency, zlib **Adler-32**, and 8-bit four-band **TIFF horizontal Predictor=2** checks.
- Original block 324 compressed **81,979 bytes**, SHA-256 `61640a5e3a0ab60f46eb257f27089ea792f28239be0ff44f32931bc0de8461ff`. Its 512×512 original valid pixels contain **39,316 alpha-positive** and **222,828 alpha-zero**; the visible-pixel bounding rectangle encloses many transparent pixels.
- Provider **HTTP `Content-Range` object length `67,126,397` bytes** is independently consistent with the original TIFF IFD block extent, not the stale/incompatible 18.94 MB HTML index display. **No full-file TIFF SHA-256, original capture-time proof, independent FEMA label-image lineage, or license admission** was established.
- Source STAC item claims `NLPL` and NOAA InPort dataset lists `CC0-1.0`. The two source-specific license scopes, downstream third-party imagery and use for model training still require explicit review. All commercial/model gates remain **NO-GO**.

## Exact pixel-mask research experiment and positive controls

Instead of the **overinclusive WGS84 bbox** (which returned one FEMA candidate), the new `research_runners/noaa_fema_exact_alpha_mask_v0.py` converts **each of the 39,316 individually decoded alpha-positive source pixel squares** into an exact unified WGS84 polygon representation. The pixel union has **372 rings, 2,842 ring vertices** and a 99,530-byte original query geometry. Pixel area is checked against the original **39,316** positive-alpha census; holes and diagonal-connected components are preserved and validated by synthetic tests. No geometry or original image pixels are emitted to logs, files or Git.

The run submitted **four explicit `esriGeometryPolygon` public FEMA count-only POST requests** against exactly `DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'`, `inSR=4326`, `spatialRel=esriSpatialRelIntersects`, `returnCountOnly=true`, `returnGeometry=false`. Only `{"count":n}` provider replies were accepted. This corrects the previously observed WGS84-envelope versus native FEMA UTM (`EPSG:32616`) overlap error. The query geometry was not disclosed; only source geometry complexity and aggregate counts were logged.

| Real source-spatial query on the same TIFF block 324 | FEMA point aggregate |
| --- | ---: |
| Full source 512×512 pixel block (positive control) | **1** |
| Simple geographic polygon bounding *all* nontransparent pixels (positive control) | **1** |
| **Actual union of all 39,316 nontransparent original pixel squares** | **0** |
| **Conservative alpha-positive union expanded two full source pixels in each direction**, clipped to the source raster | **0** |

Both **positive controls returned 1**, proving this exact public FEMA API and its WGS84 polygon query can see the scoped candidate under broad source geometry. The true exact and two-pixel-padded alpha-positive shapes both returned **0**. The extra padding is a controlled **~0.6m source-grid sensitivity check**, not a proven global bound on FEMA georeferencing error, label location uncertainty, or airborne-orthorectification error.

Successful live output: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41331414001 ; ten strictly offline synthetic geometry tests passed in the same execution, covering source byte-integrity requirements, TIFF predictor2, alpha-mask union area, holes, disconnected pixels, diagonal contacts, and two-pixel sensitivity. A successful zero count does **not** mean the image is blank or that the original FEMA classification is false.

## Revised seven-count evidence decision

The earlier corrected **true geographic polygon** census for the *whole NOAA tile* is **seven** `RS/WI AFF` public FEMA classifications, not eight (eight came from an overinclusive projected envelope). Twelve source block polygons independently sum to seven. Five counts fall within fully byte-verified all-alpha-zero source blocks **305, 306, 325, 326**. Another one in block **344** lies outside the bounding polygon of *all* its alpha-positive pixels. The final one in block **324** was previously inside the alpha-positive **bounding box**, but the actual original alpha-mask query and two-pixel sensitivity test both return **zero**.

**Result: 0 of 7 FEMA classifications can presently be independently visually corroborated at their locations using this single NOAA image tile.** It would be scientifically invalid to call this a seven-building damage validation sample, to calculate a damage rate, or to train CAT vulnerability labels from the comparison. This result applies **only to this exact source TIFF and the stated ArcGIS point geometry**, and does **not** invalidate FEMA's remote-sensing labels or establish the absence of damage, nor rule out other available imagery.

**Remaining substantive work:** identify the independently sourced image(s) actually used for the original FEMA RS labels (the public DR-4399 subset has missing IMG_DATE/PROD_DATE); locate independently versioned **2018-era** building footprints or Florida DEP field-survey comparison where truly relevant; and review original NOAA TIFF asset rights/orthorectification accuracy. The next primary output should be a new source-admitted candidate from different, verifiably independent imagery or time-stamped footprints, rather than treating source-area intersections as causal proof.

## Code and data-admission boundary

- `research_runners/noaa_fema_exact_alpha_mask_v0.py`: bounded original NOAA HTTP206/ETag source check, original 512×512 block decompression, exact alpha pixel union, WGS84 multipolygon + buffered sensitivity aggregate FEMA POST **with two independent spatial positive controls**. No original bytes or point geometry persisted.
- `tests/test_noaa_fema_exact_alpha_mask_v0.py`: deterministic synthetic-only tests for masks, topology, pixel area, corrupt Deflate data and two-pixel dilation. Offline and safe for whole-repository Python matrix.
- Independent earlier source receipts: `docs/research/noaa-michael-324-344-original-alpha-provenance-20261101.md` and `docs/research/noaa-fema-michael-2018-three-tile-spatial-receipt-20261101.md`.

**Decision:** preserve the complete source attribution and *negative* suitability proof. **No source data admitted** as directly validated damaged buildings, insured claims, insured property locations, loss-frequency estimates, or commercial CAT-model loss labels.
