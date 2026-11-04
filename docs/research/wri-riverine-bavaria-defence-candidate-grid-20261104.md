<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Riverine WRI Aqueduct v2 × Bavaria LfU defence geometry: candidate grid, not defended loss

**Research date: 2026-11-04.** Source-specific technical evidence and fail-closed offline implementation, not a permitted CAT-model input. Companion [full original Bavaria defence geometry validation](wri-flood-defence-source-access-and-risk-bridge-20261104.md). The earlier [three WRI coastal original/Physrisk pixel comparisons](physrisk-wri-coastal-original-zarr-metadata-20261104.md) use a **different peril** and cannot be quietly reused as inland Bavaria riverine depths.

## 1. Original WRI RIVERINE hazard data exists and is georeferenced on the exact same world grid

The canonical WRI [original Aqueduct Flood Hazard Maps v2 index](https://aqueduct.wridata.org/AqueductFloods20/index.html) lists baseline *riverine* 100-year original GeoTIFF **\`inunriver_historical_000000000WATCH_1980_rp00100.tif\`**. This **is not** the previously tested coastal \`inuncoast_historical_nosub_hist_rp0100_0.tif\`. WRI states the downloadable maps were updated on **2020-10-20**, including a riverine bias-correction update, and the original hazard depth maps are **without flood-protection interventions**.

Direct original-source HTTP Range byte reads (2026-11-04), verified **actual Classic TIFF IFD**, not merely a catalogue description:

- Original source: https://aqueduct.wridata.org/AqueductFloods20/inunriver_historical_000000000WATCH_1980_rp00100.tif
- TIFF: little-endian \`II*\`, first IFD original offset **91,989,120**, **18** original tags.
- \`ImageWidth\` **43,200**, \`ImageLength\` **21,600**, \`BitsPerSample\` **32**, \`SampleFormat\` **IEEE Float32**, \`Compression\` **LZW**, \`RowsPerStrip\` **1**.
- \`ModelPixelScaleTag\`: **(0.008333333333333333°, 0.008333333333333333°, 0)**, equivalent to **1/120° (30 arcseconds)** in longitude and latitude; **not a metre-valued raster**.
- \`ModelTiepointTag\`: **(pixel 0,0 → longitude -180°, latitude +90°)**.
- \`GeoKeyDirectoryTag\`: \`GeographicTypeGeoKey = EPSG:4326\`, \`GTRasterTypeGeoKey = RasterPixelIsArea\` (not PixelIsPoint).
- Original \`GDAL_NODATA\`: **\`-9999\`**.
- The same grid dimensions, cell resolution and global tie point as the coastal sample mean that the **spatial grid convention is compatible**. **The hazard depths/event definitions are not interchangeable**.

Six independently bounded, freshly SHA-256-pinned original HTTP Range responses (the exact source body, not full TIFF hash):

| Range / original TIFF bytes, inclusive | Received | SHA-256 |
| --- | ---: | --- |
| header \`0–4095\` | 4,096 bytes | \`19fb7bcafa37bd05cb66c5b859de2a89454868b31f4adbe4236788f1820603b0\` |
| original IFD \`91989120–91991167\` | 2,048 bytes | \`b5c2017faece776aa0baf4d3ec204b340dfd08f83913f52903ac3145c306796e\` |
| pixel scale \`92162148–92162171\` | 24 bytes | \`5028a719ed734b672befec6ed0d5c9c9ca5c97660849b79fb91ae874d219bd03\` |
| model tiepoint \`92162172–92162219\` | 48 bytes | \`2dd8ddcb9359f78996cff47a4873558e152b82f0521f5e8d78b19e0ec7a1f407\` |
| GeoKey directory \`92162220–92162283\` | 64 bytes | \`b6093cdbd0103bc46a1486c7ca6d97ab5c4dd2ebd18eb38ecf9f1590b4a9e77e\` |
| NoData string \`92162142–92162147\` | 6 bytes | \`44855a774102fff976316f1cf98c6c546ee3e34dcfc49bde3ad6d0398ff77b42\` |

All six source fragments must be checked by SHA256/length against the source bytes if the offline bridge is executed; a catalogue-only response or a modified TIFF profile must **not pass**. A full immutable TIFF source object hash, riverine flood depths in Bavaria, number of NoData cells and published scenario calibration have **not** been verified in this new metadata-only preflight. Never declare the riverine raster itself fully validated on this evidence.

## 2. Spatial grid definition and genuine LfU source extent

The actual LfU EPSG:4258 archive was independently decoded in the prior proof: **3,863 original line records, 4,834 parts, 81,805 vertex coordinates**, matching DBF/SHX/SHP, member CRC-32 and source bounding boxes. Native CRS of these coordinate arrays: **ETRS89 geographic EPSG:4258**, which must be explicitly transformed to WRI EPSG:4326, even if the values can appear numerically very close. The bridge requires **pyproj** and a transformer with reported operation accuracy at most 10 metres. No automatic "treat ETRS89 as WGS84" fallback is allowed.

For transformed longitude \`lon\`, latitude \`lat\`, the WRI raster has:

\`\`\`text
column = floor((longitude_deg + 180.0) * 120)
row    = floor((90.0 - latitude_deg) * 120)
zarr_1000x1000_candidate_spatial_tile = (row // 1000, column // 1000)
\`\`\`

These are **pixel-area** indices. Exact border touches are ambiguous if only an interior-cell \`floor\` calculation is used: the new line-cell candidate algorithm checks every grid crossing between vertices and conservatively includes both adjacent cells (or four at a grid corner), subject to bounded work quotas. A vertex-only spatial lookup would miss cells crossed by long straight dike segments.

The **real LfU source extent bounding boxes**, not full raster sampling, indicate the following four broad 1,000×1,000 WRI tile combinations could contain relevant Bavaria source lines: **\`4.22\`, \`4.23\`, \`5.22\`, \`5.23\`** (as row/column tile indices). This four-tile set is an **upper bound from source bounding boxes**, not proof that each contains a defence, any WRI nonzero riverine flood depths or insured assets. The grid boundary near Bavaria is about **48.333333°N** in latitude and **11.666667°E** in longitude; the correct WRI lon/lat axis order must be preserved.

A protective barrier can lie along a river but need not be within any nonzero modelled flood cell. The source \`deich\`, \`hwschutzwand\` and \`hwschutzsystem\` features provide only *candidate* crossing geometry. The mobile structures also require deployment/failure state assumptions that have **not been gathered or calibrated**.

## 3. Reproducible code and CI test scope

- \`research_runners/wri_bavaria_riverine_defence_spatial_candidate_v0.py\` is a **research-only** source-pinned, bounded, offline runner. It verifies the six original WRI riverine TIFF metadata byte ranges and uses \`inspect_original_zip()\` from the existing full Bavaria ZIP quality gate. It needs **pyproj EPSG:4258→4326 with \`always_xy=True\`**, walks original source line segments and aggregates source-feature counts and distinct intersected cells by coarse WRI tile without exporting source feature coordinates.
- \`tests/test_wri_bavaria_riverine_defence_spatial_candidate_v0.py\` is **synthetic-only**: checks exact riverine filename/grid indexing, boundary/corner supercover, crossing-between-vertices, erroneous CRS operation rejection, malformed SHP geometry, unreviewed original byte fragments, bounded work and no overwriting the source. It **does not claim to have executed the entire raster bridge on live, complete original source files in GitHub CI**.
- The output reports source URLs, original SHA-256 receipts, datum operation/accuracy and *aggregated candidate raster tiles* but **no full geometry, names, insurer locations, insured buildings, coordinate lists or flood-depth samples**. No third-party raw source bytes are added to the repo.

Example with original source bytes manually captured outside the repository:

\`\`\`bash
python research_runners/wri_bavaria_riverine_defence_spatial_candidate_v0.py \
  --lfu-epsg4258-original-zip /private/lfu/hwsa_epsg4258_shp.zip \
  --wri-header /private/wri-riverine-rp100/first-4096.bin \
  --wri-ifd /private/wri-riverine-rp100/ifd-2048.bin \
  --wri-scale /private/wri-riverine-rp100/scale-24.bin \
  --wri-tie /private/wri-riverine-rp100/tie-48.bin \
  --wri-geokeys /private/wri-riverine-rp100/geokeys-64.bin \
  --wri-nodata /private/wri-riverine-rp100/nodata-6.bin \
  --out /tmp/wri-riverine-bavaria-defence-candidate-grid.json

python -m unittest discover -s tests -p 'test_wri_bavaria_riverine_defence_spatial_candidate_v0.py'
\`\`\`

**Pending scientific checks**: Full WRI riverine source cells at specific LfU line positions; independent WRI riverine-to-Physrisk provenance and units; projection accuracy/release date; per-feature hydraulic side, insured building relationship, DE protected-area polygons, river flow, defence crest and condition, line continuity, protection standard vs actual exceedance/failure; OEP/AEP/IP/ELT/YLT and outward/inward reinsurance treaty treatment. None of these is established by this matching pipeline.

**Fail-closed conclusion:** \`model_input_admitted=false\`, \`riverine_flood_depth_reduced=false\`, \`any_building_insurance_exposure_matched=false\`. Keep as a Draft research PR; no automatic merging based solely on green CI.

## 4. NEW executed original riverine depth sample — 554 Bavaria-longitude cells on world row 5000

Unlike the preceding **metadata-only** WRI riverine test, this is an executed read of **original actual float32 hazard intensity values** from the 100-year riverine WRI GeoTIFF (historical WATCH 1980), inspected separately on 2026-11-04.

- Provider source: https://aqueduct.wridata.org/AqueductFloods20/inunriver_historical_000000000WATCH_1980_rp00100.tif
- Original 43,200-cell **row 5000**, approximately **48.3291667°N cell-centre**.
- **Global columns 22,684–23,237 inclusive** (**554** x 1/120° cells), cell-centre longitude approximately **9.0375°E–13.6458333°E**. This is a latitude transect bounded by the longitudes of the official Bavaria LfU source geometry, **NOT a dike-following or a randomly selected representative grid sample**.
- Original row-strip pointer **28,730,421**, LZW-compressed source strip length **6,541 bytes**, decoded to **172,800 Float32 little-endian row bytes**.
- Source depth outcome on this **single 554-cell row transect**: **25 positive finite cells**, **529 finite zero cells**, **0 NoData and 0 other invalid values**. Minimum positive depth **0.11534500122070312 m**, maximum **1.1153450012207031 m**. Example source col22,788 positive **0.18764880299568176 m**. These original data values are **not matched to physical flood-defence polygons, barrier lines or building coordinates**; any overlap requires a separate correctly reprojected geometry join and scientific hazard assessment.

Three more exact original provider byte-body SHA-256 receipts:

| Source range (inclusive) | Length | SHA-256 |
| --- | ---: | --- |
| TIFF \`StripOffsets\` entry row5000, \`92095742–92095745\` | 4 | \`a12803f9f96d7240493012204aa9c94c0f0b6663693443f8204e44a0262f6b15\` |
| TIFF \`StripByteCounts\` entry row5000, \`92009342–92009345\` | 4 | \`aded26cfbb510c2b40c76ebbba6034131b1a38780768eea915b9cef81fa6609e\` |
| Original compressed row-strip \`28730421–28736961\` | 6541 | \`35b4e90ec28ef3fbc5794ebf6bf1f9854b303571e108d47033102728e0c1becc\` |

**Executable independent reproduction**: \`research_runners/wri_riverine_bavaria_original_row5000_v0.py\` is stdlib-only and uses the already independently reviewed TIFF LZW decoder. With only those **three outside-Git original response files** it checks all three original lengths and SHA-256, strip pointer/bytecount, 43,200 Float32 row decode, selected 554 column categories and observed min/max depth. It rejects provider source drift and always emits \`model_input_admitted=false\`. The synthetic-only tests \`tests/test_wri_riverine_bavaria_original_row5000_v0.py\` cover the column math, altered positive / NoData / invalid source values, truncated input and no source overwrite.

\`\`\`bash
python research_runners/wri_riverine_bavaria_original_row5000_v0.py \
  --offset /private/wri-riverine/row5000-strip-offset-4b.bin \
  --bytecount /private/wri-riverine/row5000-strip-count-4b.bin \
  --strip /private/wri-riverine/row5000-lzw-6541b.bin \
  --out /tmp/wri-riverine-bavaria-row5000-source-proof.json

python -m unittest discover -s tests -p 'test_wri_riverine_bavaria_original_row5000_v0.py'
\`\`\`

This **does not** establish any flood-risk reduction from dikes, a protected asset's hazard, all riverine return-period surfaces, or a nationwide physical flood hazard model; the source's legal reuse and model applicability gates remain separately pending.

## 5. New executed original-source all-class geometric raster overlap audit (2026-11-05)

**Important distinction from section 3:** This exploratory audit actually fetched and decoded **all three LfU EPSG:4258 original compressed .shp members** from bounded HTTP Range reads (16 requests for the 838,652-byte original compressed \`deich\` entry, 4 for \`hwschutzwand\`, 1 for \`hwschutzsystem\`). Each decompressed source member passed its original ZIP local-entry CRC-32: \`deich=4ce85ae7\`, \`hwschutzwand=c697ecee\`, \`hwschutzsystem=1ac3f882\`. The feature, multipart and original vertex counts were checked against the prior independent all-geometry proof.

For geographical coordinate conversion, the separately reviewed PROJ/pyproj environment reports operation **"ETRS89 to WGS 84 (1)"**, a numerical \`+proj=noop\` translation with **reported accuracy 1 metre**, plus explicit XY-axis-order conversion. This **does not** establish sub-metre exact datum identity. The exploratory original-source overlap used the EPSG operation's unchanged numeric longitude/latitude with an **additional 0.0025-raster-cell boundary tolerance** (approximately 1.5–2.3 metres over Bavaria), conserving both adjacent cells near a grid boundary. Every segment between consecutive genuine SHP vertices was traversed: not merely the vertices. **This was a separate V8 in-memory research calculation**, not yet a validated invocation of the committed production \`pyproj\` source ZIP offline runner. A new committed Python-side CRS-accuracy-aware grid boundary safeguard and synthetic negative tests complement the pilot.

| Layer in original EPSG:4258 ZIP | Source feature count | Distinct WRI EPSG:4326 candidate cells **within the layer** | Feature↔cell relations (repeated cells across features included) | Features touching WRI row 5000 over Bavaria-longitude columns | Distinct row-5000 candidate cells within layer |
| --- | ---: | ---: | ---: | ---: | ---: |
| \`deich\` | **2,171** | **2,237** | **4,644** | 16 | 12 |
| \`hwschutzwand\` | **801** | **442** | **1,029** | 3 | 2 |
| \`hwschutzsystem\` | **891** | **299** | **931** | 1 | 1 |
| **Sum (all layer feature records)** | **3,863** | **2,978 sum of per-layer unique counts; not deduplicated across kinds** | **6,604** | **20** | **15 sum of per-layer unique counts; not deduplicated across kinds** |

Actual original-source WRI 100-year riverine row 5000 was previously decoded: of the **554** Bavaria-longitude cells, **25 have positive modelled depth**, 529 zero, none missing. The independent spatial overlap shows *some protection-structure candidate cells on that row*, **not** whether the 25 positive-depth cells coincide with those structures. We have **not yet proved the actual multi-layer joined distinct WRI cell count**, protected-side polygons, any structure's effectiveness or site-specific defended water depth.

Validated actual source feature-to-tile associations from the original SHP members (one line can touch more than one tile; these are **counts of features touching each coarse tile**, not independent defences or hazard pixels):

| Tile \`row/1000.column/1000\` | \`deich\` | \`hwschutzwand\` | \`hwschutzsystem\` |
| --- | ---: | ---: | ---: |
| \`4.22\` | 674 | 382 | 336 |
| \`4.23\` | 758 | 204 | 402 |
| \`5.22\` | 489 | 115 | 102 |
| \`5.23\` | 263 | 100 | 51 |

### Source/algorithm review controls

- The checks **did not persist or expose original provider vertex lists**, insured locations or raw raster pixels into Git. Only aggregate counts, source filenames and original per-member CRC proofs were kept.
- The independent V8 run and committed Python program **should not be called equivalent until the same original outside-Git archive is reprocessed with the explicit actual \`pyproj\` operation and the per-class counts reconciled**. The earlier run's coordinate operation was numerically \`noop\` for the reviewed environment, subject to its reported ~1m datum uncertainty; other environments/accuracy classifications must fail closed or adjust the tolerance.
- The Python bridge now allows a **source-CRS-accuracy-aware boundary margin**. At the validated 1m PROJ operation, its minimum **0.0025 cell** margin matches the exploratory count convention. In stricter/other geodetic environments, the configured margin can grow to cover the reported operation uncertainty (up to the fail-closed maximum); that may change aggregate cell counts, and such differences require review rather than silent adjustment.
- Full **WRI flood intensity at each candidate cell** remains **unmeasured**. Only one 554-pixel row transect was decoded separately. Matching an LfU \`deich\`, fixed wall or mobile installation with a WRI raster cell does not imply a defended building, reduced modelled depth, overtopping probability or an insurance claim outcome.
- **No CAT source, insurer exposure, protection factor, ELT/YLT, OEP/AEP/IP or reinsurance loss output is admitted.** All original LfU geometry and WRI hazard remain unmodified and unimported; \`model_input_admitted=false\`.
