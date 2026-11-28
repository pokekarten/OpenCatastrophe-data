<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bavaria officially protected flood areas: actual accessible HQ100 polygon sources

**Snapshot: 2026-11-05.** **Source validation, not product admission.** Companion to the [LfU 3,863 actual protection-line source proof](wri-flood-defence-source-access-and-risk-bridge-20261104.md) and the [WRI riverine 100-year original cell/line candidate pilot](wri-riverine-bavaria-defence-candidate-grid-20261104.md).

## Scientific finding: Bavaria publishes *protected area* polygons, not only dike lines

New official source family discovered and original live service queried:
[UmweltAtlas Bayern — ArcGIS REST MapServer \`wasser/naturgefahren_ftz\`](https://umweltatlas.bayern.de/arcgis/rest/services/wasser/naturgefahren_ftz/MapServer/layers).

Unlike Bavaria's \`hwsa\` \`deich\`/wall/mobile **line** locations (which by themselves do not determine which side of the line is protected), this MapServer has:

| MapServer Layer ID | Exact authoritative layer | Spatial meaning | Original provider \`returnCountOnly\` verified on 2026-11-05 |
| --- | --- | --- | ---: |
| **10** | \`hwgg_hq100\` | **Hochwassergeschützte Gebiete HQ100:** areas *behind* HQ100-designed flood barriers, not guaranteed flood-free | **80 polygons** |
| **14** | \`wt_hwgg_hq100\` | **Wassertiefen für HQ100 in geschützten Gebieten:** mapped depth *classes* under a potential defence failure scenario, **not** ordinary unconditional flooded depth | **256 polygons** |
| **8** | \`hwgf_hq100\` | **Hochwassergefahrenflächen HQ100:** official HQ100 hazard-area polygons | **1,193 polygons** |

These are source-reported **features**, not unique physical dikes, independent defended buildings, stochastic annual flood events, or proof of statewide exhaustive coverage. A single protected area may have many different water-depth class polygons and/or overlap a main HQ100 layer. Do **not** sum them into exposure counts.

Official provider original WMS \`GetCapabilities\` endpoints were both directly opened and XML successfully retrieved:

- \`https://www.lfu.bayern.de/gdi/wms/wasser/ueberschwemmungsgebiete?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities\`: **46,313 response bytes**, WMS 1.3.0, queryable layers \`hwgg_hq100\`, \`hwgf_hq100\`, \`hwgf_hqextrem\`.
- \`https://www.lfu.bayern.de/gdi/wms/wasser/wassertiefen?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities\`: **21,125 response bytes**, WMS 1.3.0, queryable \`wt_hq100\`, \`wt_hwgg_hq100\`, \`wt_hqextrem\`.
- Both named layer \`GetMap\` requests for one 128×128 test bbox \`[11.4,48.05,11.75,48.25]\` in **\`CRS:84\`** returned genuine **390-byte PNG** images. The images were **empty/transparent in this sample**: this is proof of a working rendering endpoint **only**, **not evidence for flood-free land**. \`GetFeatureInfo\` with one test location returned an empty response and **is not admitted as a reliable feature query**.
- Crucially the **independent ArcGIS vector REST endpoint** returned successful real \`FeatureCollection\` GeoJSON queries, rather than relying on a potentially blank WMS image.

## Actual original ArcGIS REST operations (observed)

The authoritative ArcGIS REST root is:

\`\`\`text
https://umweltatlas.bayern.de/arcgis/rest/services/wasser/naturgefahren_ftz/MapServer
\`\`\`

For \`ID\` = 10, 14 or 8, respectively, use only bounded, documented **read-only** operations:

\`\`\`text
/ID?f=pjson
/ID/query?where=1%3D1&returnCountOnly=true&f=pjson
/ID/query?where=1%3D1&returnIdsOnly=true&f=pjson
/ID/query?where=1%3D1&outFields=*&resultRecordCount=1&outSR=4326&f=geojson
\`\`\`

**Verified metadata for all three**: original **native EPSG:25832 (ETRS89/UTM 32N)**, \`esriGeometryPolygon\`, \`Feature Layer\`, \`maxRecordCount=2000\`, supports **pagination**, geodetic \`outSR\` and GeoJSON output. Fields include \`sl_gew_nam\` (water body), \`geb_hq\` (HQ category), \`erm_datum\` (assessment/determination date), \`webgisid\` (feature ID) and geometry; protected depth **layer 14** additionally supplies \`sl_wtiefe\` as **categorical depth description**, not a continuous metre depth raster.

- **Layer 10** actual \`returnIdsOnly=true\`: **80 distinct source feature IDs**; separate \`returnCountOnly\`: **80**. Actual bounded \`outSR=4326&f=geojson&resultRecordCount=1\`: a **19,747-byte real MultiPolygon** feature with a WGS84 longitude-latitude ring, water body identifier, \`HQ 100\` and a source assessment date **23.05.2006**. This proves an original vector geometry is directly technically retrievable, not that every area is current.
- **Layer 14** actual \`returnCountOnly\`: **256**. Separate \`outSR=4326&f=geojson&resultRecordCount=1\`: **8,397-byte real MultiPolygon**, categorical \`sl_wtiefe\` describing **greater than 0 to 0.5 metres**, an assessment date **16.07.2012**, and water body. This is a *conditional floodwater depth band*, **not a realised loss or annual probability**.
- **Layer 8** actual \`returnCountOnly\`: **1,193**; \`maxRecordCount=2000\` and pagination supported. The initial one-feature GeoJSON reply was **truncated by this research retrieval interface**, therefore a *whole real geometry* of this one particular hazard-layer feature **has not been independently validated** here. The layer's native polygon feature-type and counts **have** been verified from successful metadata and count responses. For full geometry use ArcGIS polygon spatial query, pagination, generalization, or separate original file retrieval with byte completeness / proper preservation.

### Snapshot of all 80 protected-area *attributes* (NOT the actual polygons)

A direct source query returned all **80 records with geometry disabled**, \`outFields=webgisid,geb_hq,erm_datum,sl_gew_nam&returnGeometry=false&resultRecordCount=100&f=pjson\`, **11,470 bytes**, complete population. Source \`geb_hq\`: **78 "HQ 100"**, 2 missing/blank. **Two records also lacked \`erm_datum\`** (not automatically the same records).

Original *source-dated* \`erm_datum\` year distribution across the 80 protected area records:

| Source assessment year | Records | Source assessment year | Records |
| --- | ---: | --- | ---: |
| 2005 | 1 | 2019 | 25 |
| 2006 | 1 | 2020 | 8 |
| 2007 | 1 | 2021 | 1 |
| 2012 | 2 | 2022 | 3 |
| 2013 | 7 | 2023 | 1 |
| 2014 | 10 | 2024 | 4 |
| 2017 | 1 | 2025 | 8 |
| 2018 | 2 | 2026 | 3 |
| **Missing** | **2** | **Total** | **80** |

These years are the original provider *determination/assessment* dates, **not guaranteed source publication, hydraulic model revision, barrier inspection or ZIP update dates**. Their spread from 2005 through 2026 is a strong reason to make vintage, local flood-model version and protection quality explicit in subsequent research.

### Actual server-side spatial predicate near the independent WRI 554-pixel research strip

The previously examined WRI original historical riverine RP100 global row 5000 occupies latitude **48.325 to 48.3333333°N** with geographic longitude **9.0333333 to 13.65°E**. It has 554 WRI cells and 25 positive original hazard depths, sampled separately. Instead of claiming these match LfU protected areas, the actual provider MapServer was queried with **geometryType=esriGeometryEnvelope, inSR=4326, spatialRel=esriSpatialRelIntersects, returnCountOnly=true**, using this same bbox:

\`\`\`text
/ID/query?where=1%3D1&geometry=9.0333333333%2C48.325%2C13.65%2C48.3333333333&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&returnCountOnly=true&f=pjson
\`\`\`

| Layer | Intersecting official source polygon features in the **row-envelope**, not cell or dike intersections |
| --- | ---: |
| \`hwgg_hq100\` ID 10 | **7** |
| \`wt_hwgg_hq100\` ID 14 | **30** |
| \`hwgf_hq100\` ID 8 | **74** |

Additional official server-side provider query for **central Bavaria bbox [11.2, 48, 12.4, 49]** gave **16** protected areas, **49** defended-depth class polygons and **211** HQ100 area polygons, respectively. A much broader bbox encompassing all 4 coarse WRI source tiles returned the global service counts **80, 256, 1193**, as expected.

**Strict limitation:** 7 protected-area features touching the thin envelope **does not say** how many of the 25 original WRI **positive-depth cells**, 3,863 original LfU barrier lines, or any specific insured properties are located inside those protected polygons. There is no per-cell boolean classification, water depth sampled from a protected polygon, bridge/river or canal topology, breach scenario probability, insured damage or gross/net loss estimate in this study.

## Most material scientific conclusion

The official [LfU Hochwassergefahren- und -risikokarten FAQ](https://www.lfu.bayern.de/wasser/hw_risikomanagement_umsetzung/faq_karten/index.htm) confirms:

- In hydraulic HQhäufig/HQ100 assessments, flood defence heights are included in the model, with temporary elements assumed installed as intended.
- In HQextrem scenarios, defences are generally removed from hydraulic calculations (overtopping or breakthrough assumed to be plausible).
- Special protected-area HQ100 flood-depth colour classes may show **what could happen if a barrier failed**, not depths occurring in every nominal HQ100 event.

The official [protected HQ100 areas metadata](https://www.lfu.bayern.de/umweltdaten/geodatendienste/index_detail.htm?id=4cab2c12-fa7e-49c3-97ba-f4f33af3a598&profil=WMS) explicitly warns protected regions may still flood if a dike breaks, or groundwater rises behind a barrier. And [LfU's Wassergefahren note](https://www.lfu.bayern.de/wasser/hw_ue_gebiete/hwgefahr_pruefen/index.htm) warns that hazard estimates are **not available for every Bavarian watercourse**; the absence of a polygon does **not** prove absence of local flood risk.

These official polygons are precisely what was missing when we had only the lines: **independent polygons on the nominal protected side** and **conditional inundation depth classes**. But spatial association to a protected polygon is not, by itself, a probability-weighted site-level defence model. WRI Aqueduct original 100-year flood hazard is a **coarser undefended worldwide model**, while Bavarian detailed HQ100 hydraulic risk mapping is **defended and locally derived**. The two products' nominal return periods are not automatically hydraulically equivalent.

## Reproducible next-stage source access gate, without source asset imports

Added \`research_runners/bavaria_hq100_defended_arcgis_source_preflight_v0.py\` and synthetic-only regression tests \`tests/test_bavaria_hq100_defended_arcgis_source_preflight_v0.py\`. The stdlib-only **offline** source contract takes **12 original JSON response files** from those exact official REST operations, saved privately outside Git:

- Native layer metadata for layers **8, 10, 14**
- Corresponding original whole-layer count-only JSON for **8, 10, 14**
- Their row-5000 bbox original count-only JSON for **8, 10, 14**
- One independently requested original GeoJSON source polygon for each **10 and 14** with \`outSR=4326\`
- All **80** layer-10 original attributes without geometry, full pagination validated before export

With dynamic source-vintage tolerant counts, the runner **fails closed** if provider layer name, EPSG:25832, polygon type, required source attribute fields, page safety, GeoJSON polygon ring / WGS84, count consistency, HQ100 data class, source determination dates or response completeness is wrong. It writes a small JSON receipt containing source URLs, original response SHA-256, feature counts/year distributions and hard **non-admission** flags, **without any original polygons, coordinates, insured addresses or original source attributes in Git**.

**Remaining blockers:** verify actual source rights for *this* ArcGIS vector endpoint (do not generalize WMS/LfU CC-BY-SA to all server outputs without review); original full polygon source bytes and dates for all 80 areas, full geometry for 1,193 ordinary hazard polygons, WRI coarse grid vs protected polygon containment tests, whether a particular dike line and protected zone belong to the same river/defence system, event/failure model, insured exposure, vulnerability and treaty losses. \`model_input_admitted=false\`, \`defended_site_flood_depth_calculated=false\`; retain Draft, no source auto-import.

## 2026-11-05 executed point-centre QA: 25 genuinely positive WRI riverine pixels vs official defended / HQ100 polygons

**Source-by-source actual narrow question:** "Of the 25 **positive original WRI historical riverine RP100 cell centres** on global grid row 5000 across the previously verified 554-cell Bavaria-longitude band, how many points are contained in official LfU ArcGIS protected HQ100, defended-depth-class or ordinary HQ100 hazard polygons?"

This is *not* a full WRI cell/official polygon area-overlap operation and certainly not a building-level risk classification.

1. Independently reacquired and LZW-decoded the original WRI TIFF row5000 strip bytes \`28730421–28736961\`, 6541 bytes, whose original source SHA256 is pinned in [the WRI riverine source proof](wri-riverine-bavaria-defence-candidate-grid-20261104.md): \`35b4e90ec28ef3fbc5794ebf6bf1f9854b303571e108d47033102728e0c1becc\`. From the **actual decoded original Float32 depths**, determined the exact **25 positive column IDs**, not picked source points or a derived interpolated indicator.
2. For each selected column, calculated WRI's native **EPSG:4326 PixelIsArea** centre \`lon = -180 + (col+0.5)/120\`, \`lat = 90 - (5000+0.5)/120\`.
3. Independently called the same official original read-only ArcGIS server for **75 exact point predicates**, with no original polygon geometry/insured site data exported:

\`\`\`text
https://umweltatlas.bayern.de/arcgis/rest/services/wasser/naturgefahren_ftz/MapServer/{ID}/query
?where=1%3D1
&geometry={centre_lon},{centre_lat}
&geometryType=esriGeometryPoint
&inSR=4326
&spatialRel=esriSpatialRelIntersects
&returnCountOnly=true
&f=pjson

IDs: 8 = ordinary HQ100 hazard polygons,
     10 = officially protected HQ100 polygons,
     14 = protected-area HQ100 failure-case depth-class polygons.
\`\`\`

Actual original WRI **25 positive grid columns**:

\`\`\`text
22788, 22789, 22790, 22791,
22802, 22803, 22804, 22805,
22997,
23000, 23001, 23002, 23003, 23004, 23006, 23007, 23008, 23009,
23195, 23196, 23197, 23198, 23199, 23200, 23201
\`\`\`

### Original server-side point containment outcomes

| Provider original polygon layer | Of 25 positive-WRI-cell **centre points**, how many are inside at least one official polygon? |
| --- | ---: |
| **ID 10** \`hwgg_hq100\` (officially protected area) | **0/25** |
| **ID 14** \`wt_hwgg_hq100\` (protected-area *conditional* depth class) | **0/25** |
| **ID 8** \`hwgf_hq100\` (official ordinary HQ100 hazard area) | **1/25** (only WRI global column **23200**) |

**Positive control:** Independently fetched a genuine original Polygon / GeoJSON source feature from the official ID 10 and calculated a point lying **strictly inside** its outer ring but not any holes, using the original real polygon coordinates in-memory. The exact same \`returnCountOnly=true, geometryType=esriGeometryPoint, inSR=4326, esriSpatialRelIntersects\` query returned **count=1** for this positive control. Thus the 0/25 ID 10 result is *not* simply the result of a malformed point predicate that always returns zero. The ID 8 source independently returned **count=1** for original WRI column23200, confirming the matching predicate is live on that layer.

**Numerical limits and interpretation:**

- There are **7 official protected area polygons**, **30 conditional protected-depth polygons** and **74 ordinary HQ100 hazard polygons** with **any spatial intersection** with the entire thin *row envelope* (earlier server-side envelope proof). The fact that **25 specific WRI positive-cell centres** intersect zero of those protected polygons is not contradictory: envelope intersect ≠ any one particular cell centre contained by a polygon.
- A 30-arcsecond WRI grid pixel spans roughly **hundreds of metres** across Bavaria. A centre point outside a narrow official floodplain polygon may still have the *pixel footprint* partially overlapping the official polygon. No claims of raster area-overlap percentages, official source miss rate, false-positive WRI classifications, insurer exposure agreement, or calibration skill are justified from these **one-row, 25 centre-point** probes.
- The two HQ100 products are not necessarily equivalent event simulations: **original WRI global undefended flood hazard** vs **regional Bavarian detailed hydraulic HQ100** with actual defences represented. Data vintages, river coverage, protection treatments, subgrid terrain and flow assumptions differ. Official LfU sources additionally warn that not all waterways have detailed local hazard assessments. **An absent regional polygon must never be translated into an insured building's flood probability being zero.**
- **No protected building or insurance policy was assigned**; no corrected flood depths or conditional barrier failure likelihood were estimated. The 25 point queries were a separately executed original-provider online research probe; the synthetic-only GitHub CI does **not** claim to have replayed all 75 live queries.

**Practical next gate:** download and version **complete original protected HQ100 area polygons (ID10) and defended-depth class polygons (ID14)** in an approved, attributed research staging area; compare *full raster cell footprints* to those polygons in a common, explicitly transformed CRS; join specific LfU line geometries only after topology/side and local hydraulic source/assessment date are known. Preserve the distinctions \`wri_undefended_hazard\`, \`lfu_official_hq100_protected_zone\`, \`lfu_conditional_failure_depth_class\` and \`unclassified_area_due_to_missing_hazard_assessment\`. All CAT admission and insurer loss flags remain **false**.
