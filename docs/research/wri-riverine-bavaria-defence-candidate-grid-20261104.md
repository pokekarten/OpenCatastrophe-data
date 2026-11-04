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
