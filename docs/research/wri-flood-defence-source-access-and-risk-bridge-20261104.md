<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Why WRI Aqueduct flood-depth rasters cannot yet be used as defended insurer exposure hazard

**Research snapshot:** 2026-11-04. **Scope:** official flood-defence/levee location, legal protection-norm and GIS access evidence, to complement [the three original WRI→Physrisk paired-pixel receipts and nine-RP monotonicity test](physrisk-wri-coastal-original-zarr-metadata-20261104.md). **All sources remain \`not_admitted\` for CAT/insured-loss calculation**. External byte streams are NOT included in Git, not written to Neon and not a substitute for a legally and scientifically approved defence-impact model.

## Source physics blocker: hazard intensity ≠ protected asset depth

The [WRI original Aqueduct Flood Hazard Maps data catalogue](https://datasets.wri.org/datasets/aqueduct-floods-hazard-maps) **explicitly states that these inundation depth hazard layers were simulated without considering flood protection**; the original maps were released in 2020, while the WRI catalogue page may carry newer metadata timestamps. Consequently, the exact original-to-derived WRI/Physrisk pixel matches found in this PR establish *correct copying/NoData mapping*, **not** the actual flood depth at any insured building behind a dike.

Important distinction: [WRI's separately derived Aqueduct flood-risk *population/impact indicators*](https://www.wri.org/aqueduct/help-center/water-risk-indicators) describe considering riverine or coastal defences in estimating average impacts; this **does not retroactively make the downloadable WRI v2 original flood-depth GeoTIFF rasters defended**. The product provenance and quantity must be tracked separately.

A hazard field in metres, the **location** of a defence, a legally specified **failure probability**, a *crest height*, a hydraulic water level and a *building damage ratio* are **six distinct quantities**. Do not (a) infer that a mapped asset is protected just because a dike is nearby; (b) set all depths to zero below a normative return period; (c) equate a legal breach probability or a FLOPROS policy standard to the frequency of the WRI return-period depth layer; or (d) subtract a crest elevation directly from a depth raster measured relative to local terrain. Protection needs side/topology and water level/defence failure information, and downstream loss needs an appropriate vulnerability curve and insured terms.

## Original verified source A: Netherlands formal primary defences, NBPW

**Official provider**: [Informatiehuis Water – Nationaal Basisbestand Primaire Waterkeringen](https://www.ihw.nl/nationaal-basisbestand-primaire-waterkeringen); [Netherlands government dataset catalogue](https://data.overheid.nl/en/dataset/82778-dataset-nationale-basisbestanden-primaire-waterkeringen); [Waterveiligheidsportaal data services](https://waterveiligheidsportaal.nl/data-services). NBPW records primary dike/sea-barrier line positions and accompanying legal safety norms. The government catalogues indicate **Publiek domein**, but downstream bundling/attribution should be checked against the individual authoritative metadata and the IHW data policy.

### Executed live anonymous WFS probes — note a real broken catalogue URL and a verified alternative

| Probe | Actual request / response on 2026-11-04 | Technical status |
| --- | --- | --- |
| Government catalogue's listed WFS \`GetCapabilities\` | \`https://geo.rijkswaterstaat.nl/services/ogc/wvp/ows/wfs?version=1.1.0&request=GetCapabilities\` | **Failure**, 599-byte OGC \`ExceptionReport\`, message: \`Could not determine workspace or workspace/layer-or-layergroup from request: 'ows', and global services are off.\` |
| Alternative endpoint on **same official host** | \`https://geo.rijkswaterstaat.nl/services/ogc/wvp/wvp/wfs?service=WFS&version=1.1.0&request=GetCapabilities\` | **Success**: 59,446-byte XML \`WFS_Capabilities\` version 1.1.0, explicitly advertises \`wvp:nbpw_dijktrajecten_formeel\` and in-procedure variants. This *alternate* URL is a live observed route, not yet verified as the provider's canonical permanent URI. |
| Schema | Same working WFS, \`request=DescribeFeatureType&typeName=wvp:nbpw_dijktrajecten_formeel\` | **Success**: 2,716-byte XML schema. \`TRAJECT_ID\`, \`VERSIE\`, \`NORM_SW\`, \`NORM_OG\`, \`NORM_THB\`, \`NORM_NS\`, \`geom\` all present; geom is \`gml:MultiLineStringPropertyType\`. |
| Count-only query | Same working WFS, \`request=GetFeature&typeName=wvp:nbpw_dijktrajecten_formeel&resultType=hits\` | **Success**: XML \`numberOfFeatures="237"\` at the observation time. This means **237 formal *trajectory features* in this layer**, **not** 237 individual physical dikes, and it is a live dynamic count, not a guaranteed permanent total. |
| Bounded feature query | Same working WFS, \`request=GetFeature&typeName=wvp:nbpw_dijktrajecten_formeel&maxFeatures=1&outputFormat=application%2Fjson\` | **Success**: 4,552-byte GeoJSON \`FeatureCollection\` with exactly one \`MultiLineString\` and \`totalFeatures=237\`, native CRS \`urn:ogc:def:crs:EPSG::28992\` (**RD New**, NOT longitude/latitude). One observed formal trajectory had \`TRAJECT_ID="73-1"\`, \`VERSIE="3"\`, \`NORMTYP_O="Overstromingskans"\`, \`NORM_SW=300\`, \`NORM_OG=100\`; these **remain unchanged source norm attributes**, not automatically applied CAT vulnerability or protection thresholds. |

**Norm semantics from the Dutch primary authority:** [IPLO's primary flood-barrier norms](https://iplo.nl/thema/water/waterveiligheid/primaire-waterkeringen/normen/) and [official Omgevingswet terminology](https://iplo.nl/thema/water/waterveiligheid/primaire-waterkeringen/boi-portaal/terminologie-omgevingsregeling-waterwet/) distinguish the **omgevingswaarde/ondergrens** (legally required lower-bound safety outcome) from the **signaleringswaarde** (early-warning trigger for reinforcement). The legal overstromingskans is a probability that loss of retaining function causes serious flooding/consequences behind the *trajectory*, not a point depth threshold or guaranteed achieved annual reliability. Some special barriers have **faalkans** or failure-to-close norms instead. Raw \`NORM_SW\` and \`NORM_OG\` numeric fields therefore require the official current coding, unit and trajectory law/version crosswalk before they are ever interpreted as probabilities. This service probe records them without converting their units or asserting actual protection performance.

Actual example source geometry begins near RD coordinates \`[199623.5042, 364129.9971]\`, not \`[longitude,latitude]\`. **A coordinate reprojection is mandatory** before spatially relating the formal defence geometry to WRI global \`EPSG:4326\` flood pixels or insured locations. The current service's feature types include both formal and *in-procedure* variants: **do not mix** or double count them. Formal trajectory with legal norm ≠ full physical defence line/crest geometry; NBPW source owners distinguish the normative formal trajectory and the position of the maintained waterkering. Use version/validity dates and a separate assessed physical alignment before assigning any coastal protection to a building.

**Status:** \`live_WFS_capabilities_schema_hits_one_feature_verified\`, provider metadata \`public_domain\`; **asset-level/physical effectiveness/failure probabilities unverified; no model admission**. Retain the alternative service URI as a monitored candidate and treat the original advertised \`/ows/wfs\` as **currently broken** rather than silently reporting it usable.

## Original verified source B: Bavaria LfU protection structure vectors

**Provider:** [Bayerisches Landesamt für Umwelt – Hochwasserschutzanlagen Downloaddienst](https://www.lfu.bayern.de/umweltdaten/geodatendienste/pretty_downloaddienst.htm?dld=hwsa.xml), [original ATOM feed](https://www.lfu.bayern.de/gdi/dls/hwsa.xml), and [WMS / layer descriptions](https://www.lfu.bayern.de/umweltdaten/geodatendienste/index_detail.htm?id=7f5ac6b1-a0dc-4456-94d2-a899aaadacd1&profil=WMS).

Executed **actual original HTTP response**, 2026-11-04:

- The ATOM feed returned **16,541 bytes**, confirmed \`Hochwasserschutzanlagen - Downloaddienst\`, source rights **CC BY-SA 4.0** and both exact download links:
  - \`https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg25832_shp.zip\`
  - \`https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg4258_shp.zip\`
- Both links replied to **independent 512-byte HTTP Range probes** with ZIP local-header magic \`PK\x03\x04\`, not HTML errors: EPSG:25832 ZIP's first member \`deich_epsg25832.dbf\`, EPSG:4258 ZIP's first member \`deich_epsg4258.dbf\`. **In a second source probe**, the exact final **2,048 HTTP response bytes** of each ZIP were independently fetched and their EOCD and complete central directories inspected: **12 members in each archive**, corresponding to three asset types (`deich`, `hwschutzwand`, `hwschutzsystem`) and each required `.dbf`, `.prj`, `.shp` and `.shx` sidecar. The central-directory offsets imply total ZIP lengths **1,072,960 bytes** (EPSG:25832) and **1,095,279 bytes** (EPSG:4258). Uncompressed SHX size metadata implies **2,171**, **801** and **891** *potential index slots* for `deich`, `hwschutzwand` and `hwschutzsystem`, respectively (per ZIP, **not independent assets across both projections**). **Those initial totals were metadata-derived only. The separate follow-up analysis below now independently decompresses and validates the actual EPSG:4258 DBF/SHX/SHP member contents for all three layers, including CRCs, DBF records and every polyline geometry.** The EPSG:25832 alternate-export member payloads remain unverified, as do site-specific crest heights, defence effectiveness and source version.
- WMS \`GetCapabilities\` separately returned relevant structure layers including \`deich\`, \`hwschutzwand\` and \`hwschutzsystem\`. Do not treat an imagery WMS as a vector feature endpoint. The ATOM feed's own descriptive updated timestamp is old (2015); the separately published LfU service catalogue lists a weekly update cadence, but we have **not yet established the actual version/age of the ZIP contents**.
- Provider attribution: **"Datenquelle: Bayerisches Landesamt für Umwelt, www.lfu.bayern.de"**. **CC BY-SA 4.0 share-alike conditions are distinct from WRI's CC BY 4.0 and NBPW public-domain conditions**; derivative rights and distribution require independent review.
- Physical source covers deikes, walls and **mobile** systems that may only be installed during flood events. A mobile barrier's mapped location does *not* prove deployment, state or protection success in a particular simulation year.

**Status:** \`ATOM_verified_zip_headers_and_complete_directory_verified_archive_members_unparsed\`, **not admitted**.

## Additional promising source families (research references, not byte-verified this turn)

| Source | Independent role | Provenance / limitation | This-turn status |
| --- | --- | --- | --- |
| [FLOPROS, Scussolini et al. (2016)](https://nhess.copernicus.org/articles/16/1049/2016/nhess-16-1049-2016.html) | Broad **global / sub-national protection standard** baseline from design/policy/modelled classes | Different evidence strengths: empirical *design*, normative *policy*, estimated *model*. A 2016 protection level is not automatically current. [2025 follow-up on coastal-protection information gaps](https://nhess.copernicus.org/articles/25/2075/2025/) explains uncertainty. The original supplement is offered by NHESS, but direct ZIP fetch timed out on this run. | \`paper_and_supplement_catalogued_not_downloaded\` |
| [openDELvE (2022)](https://nhess.copernicus.org/articles/22/4087/2022/) / [Dataverse DOI](https://doi.org/10.34894/2WZ0S9) | Global **river-delta levee vector locations**, useful in Bangladesh and other deltas | Coverage and data-density bias; should be independently matched to WRI riverine vs coastal perils and model year, no guarantee of crest/failure or complete local assets. | \`publication_and_data_identifier_confirmed_not_bytes\` |
| [HELCOM HOLAS 3 Coastal defence/flood protection](https://data.europa.eu/data/datasets/ae284376-defd-4288-a98e-ac14aacda28e) | Baltic Sea built structures, physical **type and status**, marine protection | Data collected in **2022**, member coverage varies, reported operational/unknown classifications have important caveats; no currently retrieved original downloadable layer or downstream rights review. | \`official_catalogue_only\` |
| [UK Environment Agency AIMS Spatial Flood Defences](https://www.data.gov.uk/dataset/cc76738e-fc17-49f9-a216-977c61858dda/aims-spatial-flood-defences-inc-standardised-attributes) | England up-to-date inspected/owned/managed defence line geometry; OGC API/WFS/GeoPackage options | Catalogue says **daily** updates and separately labels **Approval for Access product AfA345**. Open-government reuse indications need confirmation for the *specific* dataset, independent from the unrelated free real-time flood-monitoring API. **No original live OGC feature read** in this study. | \`catalogue_only_access_licence_review_required\` |

### Critical scientific modelling decision for insurance catastrophe models

Never implement \`if return_period <= protection_standard: depth = 0\` as a generic rule. It loses overtopping, breach/failure, coastal tidal interactions, defense-system topology, uncertainties in standards and the difference between a **legal risk objective** and the **actual achieved physical standard**. FLOPROS and local norms can provide **hypothesis bounds / priors** in explicit defended-vs-undefended sensitivity scenarios, *not* approved corrections to flood-depth pixels.

Suggested minimum machine-recorded source bridge, before any insured building is modified:

1. Identify distinct \`source_id\`, \`source_build_or_retrieval_time\`, licence, per-asset geometry, **native EPSG**, per-feature schema identity and spatial coverage; preserve WFS formal vs in-procedure and LfU fixed/mobile types.
2. Reproject all geometry explicitly into the desired WRI raster CRS, validate axis order, topology, metre units, source dates and nearest/inside-protection *physical* side using boundaries/inundation basins, not solely nearest-line distance.
3. Keep protection **design vs policy vs inferred/modelled** classes, observed vs assumed reliability, fixed vs deployable assets and any crest elevation in distinct nullable columns with uncertainty and evidential source IDs. Record whether each is riverine, coastal, estuarine or multi-peril.
4. Connect water-surface elevation/ground elevation, barrier side, breach/overtopping and operational failure probability *conditional on a specific event* before deriving protected-site hazard. Only then research model-vs-claims and uncertainty-based damage functions.
5. Keep immutable raw \`wri_original_depth_m\`, \`physrisk_transformed_depth_m\` and \`defended_scenario_depth_m\` separate. **Never overwrite** original hazard with assumed defence corrections. Downstream exposure/TIV, vulnerability, event catalogue dependence, ELT/YLT and reinsurance tower calculations require their **own** approvals.

## Offline source-contract preflight now in repository

\`research_runners/wri_flood_defence_source_access_preflight_v0.py\` takes **nine outside-Git original HTTP response byte files** (NL WFS capabilities, DescribeFeatureType, GetFeature resultType=hits, one GeoJSON feature, Bavarian ATOM, both first-512-byte ZIP response headers and both final-2048-byte ZIP directory suffixes). With **only Python stdlib**, it validates that the corrected NL WFS is a successful versioned service, formal layer and schema are intact, dynamic feature count is positive, sample CRS/geometry/norms are not mistaken for WGS84 or site-specific flood depth, and Bavarian ZIP endpoints expose exact ZIP local-file headers and central-directory structures containing the three expected flood-defence classes with CC BY-SA rights. It emits a **research-only** small receipt, including exact SHA-256 of whatever live original response bytes were captured, without committing source bytes or pretending WFS timestamps make a stable immutable dataset hash. Its \`model_input_admitted\` and \`protection_factor_or_return_period_threshold_inferred\` fields are always \`false\`.

Tests in \`tests/test_wri_flood_defence_source_access_preflight_v0.py\` are **entirely synthetic** and challenge wrong endpoint, XML exception, missing formal layer, missing fields, wrong CRS, zero/rejected feature counts, invalid legal norm encoding, missing attribution/licence, fake ZIP content and attempts to overwrite original source files.

Example — save exactly the small read-only provider HTTP response bodies outside Git:

\`\`\`bash
python research_runners/wri_flood_defence_source_access_preflight_v0.py \
  --nl-capabilities /private/defence/nl-wfs-caps.xml \
  --nl-schema /private/defence/nl-wfs-formal-schema.xsd \
  --nl-hits /private/defence/nl-formal-hits.xml \
  --nl-one-feature /private/defence/nl-one-formal-feature.json \
  --bavaria-atom /private/defence/by-atom-feed.xml \
  --bavaria-zip-25832-head /private/defence/by25832-zip-first512b.bin \
  --bavaria-zip-4258-head /private/defence/by4258-zip-first512b.bin \
  --bavaria-zip-25832-tail /private/defence/by25832-zip-last2048b.bin \
  --bavaria-zip-4258-tail /private/defence/by4258-zip-last2048b.bin \
  --out /tmp/wri-flood-defence-source-access-receipt.json

python -m unittest discover -s tests -p 'test_wri_flood_defence_source_access_preflight_v0.py'
\`\`\`

## NEW: EPSG:4258 original Shapefile member contents independently decoded and checked (2026-11-04)

This improves the source access preflight materially. All actual **three** flood-defence line classes in the **original official EPSG:4258** archive were decoded from *bounded original HTTP Range responses* on 4 November 2026. This is an original-provider payload test, not a synthetic-only assumption or a conclusion drawn from ZIP directory sizes. The full ZIP was **not** checked as a single SHA-256-pinned artifact. Distinct compressed members were decompressed locally in read-only memory and checked against their **original ZIP local-entry CRC-32** values.

Original provider source:

- https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg4258_shp.zip
- Publication metadata: [LfU Download service](https://www.lfu.bayern.de/umweltdaten/geodatendienste/index_detail.htm?id=52f9bb4f-6813-4721-97b9-49aa48ecb1ea&profil=Download). LfU's publication date is **2014-04-22**, nominal refresh cadence **weekly**, and provider-declared license **CC BY-SA 4.0** with mandatory attribution; *the exact contained ZIP revision/publication instant is NOT independently pinned*.

| Real EPSG:4258 source layer | Actual DBF records | Actual SHX index slots | Real SHP polyline records | Polyline parts | All inspected vertex coordinates | Invalid vertices or record structures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| \`deich\` (dikes) | **2,171** | **2,171** | **2,171** | 2,439 | 66,484 | 0 |
| \`hwschutzwand\` (flood-protection walls) | **801** | **801** | **801** | 1,338 | 12,842 | 0 |
| \`hwschutzsystem\` (mobile systems) | **891** | **891** | **891** | 1,057 | 2,479 | 0 |
| **Total (one CRS export, not both)** | **3,863** | **3,863** | **3,863** | **4,834** | **81,805** | **0** |

**What the original independent binary probes checked:**

- **SHP**: original compressed member from the official URL; raw DEFLATE decode; original ZIP CRC-32; classic ESRI Shapefile magic 9994, little-endian version 1000, polyline type 3, exact file byte lengths; sequential record numbers, every declared content length, every polyline part offset, all XY vertex coordinate pairs and all record-local XY bounding boxes. No null shapes and no invalid coordinate pairs were observed in these three layers. Source compressed \`.shp\` members: **838,652** bytes (dikes), **168,545** bytes (walls), **42,583** bytes (mobile systems); expanded into **1,186,492**, **252,576** and **90,324** bytes, respectively. Largest dike member required **18 adjacent bounded HTTP Range responses**. Every source member matched the original ZIP CRC.
- **SHX**: the actual decompressed source index arrays, including all **3,863 eight-byte index entries**, were checked for exact declared file lengths, sequential nonoverlapping record offsets, consistent source SHP file sizes, original ZIP CRC-32 and native geographic XY bounding boxes.
- **DBF**: the actual decompressed source field descriptor headers, exact record lengths and source row counts were read, with original ZIP CRC-32. All three publish the same five fields **\`WWO_KNZ\`, \`GEW_KNZ\`, \`OBJ_ART\`, \`WWA\`, \`LINK\`** (character fields); no measured crest height or physical failure rate was found in the advertised DBF *schema*. For each layer the DBF row count matches the SHX and SHP counts. Row attribute values are **not** copied or listed in this repository.

Read-only original member CRC-32 receipts (hex, as stored in local ZIP headers and independently checked against decompressed bytes):

| Layer | \`.dbf\` | \`.shx\` | \`.shp\` |
| --- | --- | --- | --- |
| \`deich\` | \`8592b2ee\` | \`ef7bdff8\` | \`4ce85ae7\` |
| \`hwschutzwand\` | \`0e1cc10d\` | \`b9dfe316\` | \`c697ecee\` |
| \`hwschutzsystem\` | \`34072e28\` | \`4284acbf\` | \`1ac3f882\` |

Independent source layer bounds (original **EPSG:4258 / ETRS89 geographic longitude-latitude**, not a metre-valued CRS and not an insured-property search result):

| Layer | Longitude min | Latitude min | Longitude max | Latitude max |
| --- | ---: | ---: | ---: | ---: |
| \`deich\` | 9.0333568892 | 47.4013258202 | 13.5790520246 | 50.4592548849 |
| \`hwschutzwand\` | 9.1348757114 | 47.4029098080 | 13.6450644934 | 50.4798543779 |
| \`hwschutzsystem\` | 9.1344456729 | 47.5004054807 | 13.6451124117 | 50.4780087167 |

**Reproducibility:** a new *stdlib-only* read-only validator, \`research_runners/bavaria_hwsa_full_shapefile_integrity_v0.py\`, accepts one or both unmodified original ZIP files located **outside Git**. Its ZIP parser checks the full 12-file manifest and each extracted member's CRC; its DBF+SHX+SHP crosscheck checks every record, part index and vertex within native source bounds. It refuses path traversal, unexpected schema, corrupt byte counts, wrong native CRS, inconsistent record counts, invalid geometry and altered ZIP. Synthetic-only adversarial regression tests are in \`tests/test_bavaria_hwsa_full_shapefile_integrity_v0.py\`. When both projection exports are passed, it verifies identical DBF member SHA-256 identifiers and does **not** double the feature counts.

\`\`\`bash
python research_runners/bavaria_hwsa_full_shapefile_integrity_v0.py \
  --epsg-4258 /private/provider-sources/hwsa_epsg4258_shp.zip \
  --epsg-25832 /private/provider-sources/hwsa_epsg25832_shp.zip \
  --out /tmp/bavaria-hwsa-structural-source-proof.json

python -m unittest discover -s tests -p 'test_bavaria_hwsa_full_shapefile_integrity_v0.py'
\`\`\`

**Critical limits:** This turn did not independently decode all original **EPSG:25832** archive members or calculate a full-object immutable ZIP SHA-256 for either projection. The original \`.prj\` source files were identified in the archive but were not independently reviewed as whole uncompressed members in these byte probes. A matching source geometry and CRC does *not* prove a currently maintained structure, completeness across all Bavaria, legal protection standard, physical crest, temporary-barrier deployment, protected-side topology, hydraulic overtopping/breach mechanism, building-level defended flood depth, vulnerability, insured TIV or reinsurance losses. The nominal provider "weekly" cadence does not prove this specific ZIP's vintage. **No original binary ZIP, DBF, SHP, SHX or insurer exposure data is committed to Git; no scientific or rights admission follows.**

**No effect on source admission:** all listed flood-defence sources remain \`not_admitted\` in the CAT/insurer model sense. This research is focused on existence, ownership and bounded technical access, not a product-grade flood protection calculation.
