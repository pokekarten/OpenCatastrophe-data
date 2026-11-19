<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hurricane Michael 2018 NOAA: exact original 324/344 alpha proof and FEMA polygon envelope challenge

**Date:** 2026-11-01. **Original evidence:** successful [GitHub Actions live original-source execution](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41329301340), executed on PR #955. The new `research_runners/noaa_michael_exact_alpha_live_v0.py` fetched only original NOAA STAC JSON, the first 4,096 bytes of one selected GeoTIFF, and the exact two unresolved compressed TIFF source blocks; the source bytes were used in memory and **not added to Git or redistributed**. The command checked the original source `HTTP 206`, exact `Content-Range`, matching source object `ETag` where present, original TIFF IFD and STAC identities, Deflate/zlib Adler-32, TIFF Predictor=2 and fourth unassociated-alpha sample. Seven offline synthetic tests also ran successfully in the isolated job. The **entire GeoTIFF was not downloaded** and its full-file SHA-256 is unknown.

## Proven original file identity and two remaining blocks

- Original STAC item:
  https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0853300w302100n.json
- Original GeoTIFF:
  https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/20181011aC0853300w302100n.tif
- TIFF first 4096-byte original header SHA-256: `2cdd8249e197d364c8c67fcecf92f0c06e963c62b410cd7c88dc5268afcb89fd`
- **Provider's authoritative HTTP `Content-Range` total: 67,126,397 bytes**, matching the largest `offset + byte_count` from the original 361-block TIFF IFD. The server supplied an `ETag` and accepted the exact conditional range requests; the public HTML directory's previously observed display of **18.94 MB** for this name is not the current original object byte identity. No exact `Content-Length` HEAD result or full-asset checksum was obtained.

| Field | Original TIFF block **324** | Original TIFF block **344** |
| --- | ---: | ---: |
| Source raster row / column | 17 / 1 | 18 / 2 |
| Original HTTP Range bytes inclusive | `66694287-66776265` | `67029595-67050833` |
| Original compressed bytes | **81,979** | **21,239** |
| Original compressed SHA-256 | `61640a5e3a0ab60f46eb257f27089ea792f28239be0ff44f32931bc0de8461ff` | `3bf7fffaf8f6acb516e12001d27b4e28077174596ffea5d186a003282d1e5eef` |
| Source pixels inside valid raster footprint | **262,144** | **63,488** (512 × 124, bottom edge) |
| **Alpha-positive** source pixels | **39,316** | **7,948** |
| Alpha-zero source pixels | **222,828** | **55,540** |
| Fully opaque source pixels (alpha=255) | 37,384 | 7,127 |
| Conservative pixel-grid bbox of **all** alpha-positive pixels `[x_min,y_min,x_max,y_max]` (inclusive, local block) | `[0,328,415,511]` | `[0,40,191,123]` |
| FEMA DR-4399 RS/WI full block true-polygon count | **1** | **1** |
| FEMA count within the enclosing bbox of all source alpha-positive pixels | **1** | **0** |
| **Direct NOAA-visible image point conclusion** | **Unresolved**; inside bounding box is not proof of a nontransparent pixel | **Excluded**; none of the original FEMA points in this block falls even inside the conservative polygon enclosing *all* visible NOAA pixels |

All original source blocks were decompressed into the expected 512×512×4 8-bit sample raster with the zlib checksum validated. TIFF `Predictor=2` was reversed **row by row for the fourth interleaved alpha sample** before measuring it. The bottom-edge block was clipped to 124 valid source-image rows; transparent padding beyond the raster was not counted as imagery pixels.

The source TIFF pixel-grid transform `ModelTiepoint=(-85.5500986509636, 30.3500986509636)`, `ModelPixelScale=(0.000002698072805138984, 0.0000026980728051393644)`, EPSG:4326 was used to produce two conservative WGS84 `esriGeometryPolygon` rings that fully enclose **all original alpha-positive pixel footprint rectangles** in each block (including each last pixel's east/south boundary):

- **Block 324** alpha-positive enclosing geographic bbox `[W,S,E,N]=[-85.54871723768737,30.325233211991435,-85.54759483940043,30.32572965738758]`. Separate source FEMA `returnCountOnly=true`, `returnGeometry=false` result: **1**.
- **Block 344** alpha-positive enclosing geographic bbox `[W,S,E,N]=[-85.54733582441115,30.324898650963597,-85.54681779443256,30.325125289079228]`. Separate source FEMA count-only response: **0**.

Both queries used `DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'`, explicit closed 5-vertex WGS84 polygon rings with `inSR=4326` and `geometryType=esriGeometryPolygon`, not the known overinclusive `esriGeometryEnvelope` approach. Neither query requested individual FEMA geometry, object IDs or insured properties.

## Scientific conclusion: six exclusions, one unresolved, zero positively validated

The entire NOAA source tile corrected true-polygon FEMA count is **seven** and the 12 TIFF-block source-grid polygon counts sum independently to **seven**. Four earlier exact source Deflate streams (blocks 305/306/325/326) proved **all alpha zero**, containing **five** of those public aggregate point counts. Block 344 contains one further FEMA count but its **entire alpha-positive source footprint's conservative enclosing geographic polygon** contains **zero** public FEMA points; it therefore excludes a **sixth** original-NOAA-pixel-verifiable label. Block 324 contains the final one FEMA count inside its alpha-positive *bounding polygon*, but the polygon includes transparent pixels; **no actual visible alpha at that FEMA point has been proved**.

| Status of seven corrected FEMA source count scopes | Count |
| --- | ---: |
| In four independently proved entirely transparent NOAA image blocks | **5** |
| In block 344, outside the enclosing polygon of all alpha-positive source pixels | **1** |
| In block 324, inside the enclosing polygon but direct pixel overlap not verified | **1** |
| Verified FEMA point on NOAA nontransparent image pixel | **0** |

This is **not** a finding that the six FEMA labels are wrong; only that the one investigated NOAA raster **cannot directly validate these six** as visible imagery observations. Nothing proves that a FEMA classifier used NOAA imagery, that any assessment corresponds to a unique versioned building, or that there is an insured policy, claim or monetary loss. Aggregate count conservation alone does not prove per-feature boundary ownership; differences in source epochs / georeferencing still require validation.

## Executable fail-closed continuation

- `research_runners/noaa_michael_exact_alpha_live_v0.py`: explicit opt-in original-source **two-block** HTTP206+ETag, Deflate/Adler32 and TIFF predictor analysis. Its `run_bounded_original_probe()` requires unchanged source identities, only two original byte ranges and no original-file persistence; no network request runs during import or deterministic offline tests.
- `research_runners/noaa_fema_alpha_visible_bbox_v0.py`: source-IFD-bound original Deflate input produces an explicit **conservative alpha-positive enclosing WGS84 polygon count-only query**; count validation strictly rejects invalid/reversed parent–child source counts or unauthorized point data. A **positive** enclosing-bbox query is never positive pixel coverage proof.
- `tests/test_noaa_michael_exact_alpha_live_v0.py` and added synthetic tests in `tests/test_noaa_michael_tiff_header_v0.py`: exercise bounded HTTP206/ETag, original zlib checksum and malformed payloads, predictor2 row reset, bottom-edge clipping, conservative bbox coordinates, and no-model-admission flags.
- **Source rights:** STAC labels individual tiles `NLPL` (recognized permissive SPDX No Limit Public License) while NOAA InPort dataset says `CC0-1.0`; the mapping to derived assets and independent labels remains reviewed as **not admitted**. This pilot does **not** establish a complete source-date/label independence, a full-asset SHA-256 or a model-ready building/vulnerability product.

## Superseding exact alpha-mask experiment (later on 2026-11-01)

**The one unresolved FEMA source point in block 324 has now been tested against the exact original positive-alpha pixel union.** The independently executed exact-mask source proof (https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41331414001) produced 372 rings over 39,316 source alpha-positive pixel squares. Two control queries against the original block polygon and the bounding polygon of all visible pixels each returned **1**, but the exact alpha mask returned **0**, and its **two-pixel-dilated source-grid mask also returned 0**. Thus the earlier "one unresolved" status is superseded: **no public FEMA source count is located on a proven visible pixel of this one NOAA TIFF**, under the provided source point geometry and limited coordinate-tolerance test. This is a negative image-coverage finding, not independent proof that FEMA's labels are wrong. Full details and exact source-scoped limitations: `docs/research/noaa-michael-seven-fema-alpha-mask-final-20261101.md`.

**Next high-value validation:** Identify an independent, time-appropriate 2018 building footprint/reference for the one block 324 source candidate. Prove exact alpha-pixel overlap, source photograph date and field-observation independence before making **any** damaged-building or insured-loss assertion; do not infer from a bounding-box count alone.
