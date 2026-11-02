<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg AGE HQ100: exact original 2021-model / 2022-release archive receipt

**Status: read-only provider file-format and provenance gate. No flood depth / hazard footprint admission.**

## Publisher source and version

Publisher is the Administration de la gestion de l'eau (AGE). The official
[HWGK2021 HQ100 catalogue](https://data.public.lu/en/datasets/flood-hazard-maps-100-year-flood/)
describes *modelled 100-year floodplain and water depth* pursuant to Directive 2007/60/EC.
It lists the original [ZIP resource](https://download.data.public.lu/resources/flood-hazard-maps-100-year-flood/20220613-154804/hwgk2021-hq100.zip)
as **3.9MB** with resource UUID `1f529004-dd4d-42f1-8bd3-3b33a3f54ffd`,
publisher SHA-1 `41b58cb5e0c9509d39824919dce85702ceda0540`,
updated **13 June 2022** and catalogue label **CC0**. The paired 63.4MB
GeoJSON resource has a *separate* original SHA-1 and must not be assumed
byte- or object-equivalent before independent comparison.

**Separate product:** The INSPIRE Natural Risk Zones HQ100 catalogue
https://data.public.lu/en/datasets/inspire-annex-iii-theme-natural-risk-zones-flood-hazard-maps-100-year-flood-3/
lists its GML asset as **modified 8 December 2025**, not 11 August 2026.
Its separately listed WMS service was updated **16 February 2026**.
A WMS publication date is not an underlying hazard model date; never assume
those products share feature IDs, depth intensity semantics or vintage.

## Reproducible exact-original source gate

`research_runners/luxembourg_age_hq100_2021_original_preflight_v0.py`:

1. Requires a regular non-symlink ZIP within a fixed byte limit, exact
   **publisher SHA-1**, and records an additional SHA-256 receipt. SHA-1 is
   publisher-reported version identity, not a secure signature or independent
   authenticity guarantee.
2. Rejects ZIP path traversal, symlinks, encryption, duplicate members,
   decompression bombs, oversized expansion and inconsistent or malformed
   SHP/DBF/PRJ headers.
3. Fully streams every member for CRC checking. Reads *only* SHP main
   header (shape type), DBF metadata/field descriptor names and declared row
   count, and bounded PRJ text for **keyword hints**, without emitting any
   source feature, coordinate, geometry, depth measurement or identifier.
4. Prints only archive-level member suffix counts and bounded file-header
   findings, with explicit `depth_units_verified=false`,
   `actual_hazard_geometry_read=false` and
   `model_input_admitted=false`. Original bytes are deleted in the
   GitHub runner, not stored in Git/Neon, or exposed in action artifacts.
5. Uses synthetic-only regressions to reject changed source SHA, unsafe
   ZIP paths, symlinks and corrupt inputs.

The separately scoped GitHub Actions workflow
`.github/workflows/luxembourg-age-hq100-2021-original.yml` fetches only
the exact resource at the fixed official HTTPS URL, and runs this script
after its synthetic gate. **Actual file structure and observations must be
taken from a successful real-original run, not inferred from the catalogue
description.**

## First actually verified original ZIP outcome (2 November 2026)

Full exact-origin [GitHub workflow 41408171685](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41408171685) **passed**, including four synthetic archive-integrity regressions. The official ZIP matched publisher SHA-1 `41b58cb5e0c9509d39824919dce85702ceda0540`; its reproducibility SHA-256 is `a2b107c577a06ea2d6264ef916c954767e5d9b11899b9298f58d3c18b7e35571`. Original compressed size is **4,093,773 B**, eight ZIP members (seven regular members and one directory), with aggregate expanded bytes **21,408,941 B**.

The archive contains **one shapefile group**, with exactly one each of `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`, `.sbn`, and `.sbx`. SHP main header declares **ESRI Polygon shape type 5** and its physical file size is **21,407,956 B**; the DBF header declares **exactly one row**, fields **OBJECTID (integer-like numeric), Shape_Leng (float), Shape_Area (float)**. The PRJ WKT currently has only a `LUXEMBOURG` keyword match; no source-specific CRS/axis has been independently approved.

**Important content correction:** This actual official 3.9 MB ZIP contains **no DBF depth field at all**. Although the AGE dataset catalogue mentions modelled floodplain and water depths, this ZIP **does not provide a DBF numeric intensity attribute for depth**, so it cannot be used to produce building-specific flood depth, vulnerability or loss calculations. Its one DBF row suggests an aggregate spatial zone or multipart shape; the **actual SHP record count, number of rings and coordinates still require a separate bounded, checksum-pinned source-record structural scan**. Do not equate one DBF record with a single physical flood zone, property, gauge or event, or infer that the companion GeoJSON contains the same semantics without independently inspecting it.

Source bytes, geometry and attributes were never logged, committed, uploaded to an artifact or written to Neon. `model_input_admitted=false`.

## Actual full original SHP record structure (2 November 2026)

The second fixed-original [GitHub workflow 41408573653](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41408573653) **passed** after verifying the same exact SHA-1, SHA-256 and ZIP CRC receipts. The enhanced standard-library source reader scans *only structural SHP record metadata*, validates record byte conservation, rejects impossible part-index sequences and skips the raw coordinate bytes without decoding or exporting them.

**Measured from the actual provider polygon source:**

| Original source measurement | Full source result |
| --- | ---: |
| SHP record count | **1** |
| DBF record count | **1** (matches SHP) |
| ESRI polygon shape type | **5** |
| Ring/part offsets in that one record | **6,379** |
| Polygon coordinate pairs skipped without decoding | **1,336,393** |
| Shape bytes declared and verified | **21,407,956** |
| Source attribute field for flood water depth | **none** |

**Interpretation:** this is one **very large multipart polygon record** with 6,379 declared parts. The count of parts is neither an independently validated count of connected floodplain regions nor a count of rivers, buildings, claims or flood events; polygon validity, hole/shell semantics and geographic CRS are not yet approved. The format can support an *extent-only* spatial screening only after a bounded actual geometry integrity/CRS gate. The ZIP's `Shape_Area` field is geometry area, **not simulated water depth**, and must never be reinterpreted as intensity.

The newly added source regression must reject malformed SHP record lengths/part offsets, source checksum drift, unsafe archive members, nonpolygon shapes, and SHP-vs-DBF population mismatches. No original coordinates or hazard values were persisted or printed.

## Original PRJ geodetic metadata screen (2 November 2026)

Dedicated fixed-provider-content [GitHub Actions run 41408965658](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41408965658) **passed**, including pinned `pyproj==3.7.2`, synthetic valid/invalid WKT cases and the real official ZIP. After independently validating the original file and all ZIP structure/CRCs, `research_runners/luxembourg_age_hq100_2021_prj_crs_screen_v0.py` read **only the original 445-byte PRJ WKT** and reported:

| Declared original-source PRJ property | Verified parser outcome |
| --- | --- |
| WKT parsed | true |
| CRS authority match ≥90% confidence | **EPSG:2169** |
| Coordinate system projected | true |
| Axis unit name | **metre** |
| Original polygon coordinate order and survey epoch field-controlled | **false** |
| Physical ACT2026 building location matched to this 2021 HQ100 scenario | **false** |
| CAT input authorized | **false** |

The 2021 AGE flood archive and 2026 ACT building data both declare **EPSG:2169**. This removes an important **declared CRS namespace mismatch**, not actual original *axis-byte-order*, precision, flood geometry validity or survey-vintage discrepancies. A projected CRS identity is not an independent check of 1,336,393 polygon coordinate pairs, actual flood intensities, 100-year recurrence calibration or physical insured building location. Never auto-approve a spatial join on this result alone.

**Depth next-step source strategy:** an official 2021 flood hazard map is independently exposed as a Geoportal WMS/WMTS render layer `eau_Hochwassergefahrenkarten_HQ100_2021`, while the 2021–2027 flood risk management plan and official gauge information describe classified depth bands. A rendered hazard map legend is **not** a raw raster or per-building depth value. Verify exact numeric depth layer access, temporal/return-period semantics, provider use rights and numeric units independently; if numeric surfaces are not public, request period-correct modelled depths or water-surface elevation layers from AGE. Do not infer flood depth from polygon extent, `Shape_Area` or map pixel colors.

## Actual original coordinate/ring scan (2 November 2026)

[Full original-data workflow 41414516498](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41414516498) **passed** using exact original 2022 ZIP SHA-1 and SHA-256, a pinned PROJ/pyproj runtime, and synthetic malformed-coordinate, invalid-ring-offset, truncation and axis-hypothesis regression cases. The scan read all **1,336,393 stored projected XY coordinate pairs into ephemeral memory**, retained **no per-ring/feature geometry**, and reported:

| Source-wide property | Actual original |
| --- | ---: |
| Source ESRI polygon records | 1 |
| Total ring parts | **6,379** |
| Closed source rings (first XY equals last XY) | **6,379** |
| Open rings / nonfinite XY / rings with near-zero signed area | **0 / 0 / 0** |
| Negative ring winding | **3,724** |
| Positive ring winding | **2,655** |
| All-source projected XY bbox (rounded 0.1 m) | **48,893.0 / 59,515.0 / 106,138.3 / 137,088.0** |
| Native file/record XY bounding boxes agree with actual vertices | **both true** |
| Source stored XY -> WGS84 bbox (approx, 4 decimals) | **5.7328–6.5340°E, 49.4696–50.1673°N** |
| Reversed XY -> WGS84 bbox (approx, 4 decimals) | **5.8831–6.9625°E, 49.3722–49.8892°N** |
| Buffered EPSG2169 area-of-use envelope challenge | **native-only plausible** |

**Narrow conclusion:** Original HQ100 ring linework is complete, entirely finite, individually closed, and has nonzero signed area under the tested aggregate metric; the source's stored XY is geographically consistent with Luxembourg, while the swapped interpretation is not. **This does not prove OGC validity** of individual rings (they may self-intersect), correct assignment of polygon exteriors/holes, inter-ring nesting, stable shape IDs, coordinate-frame epoch, actual flood depth, hydraulic hazard intensity or building overlap. The original multipart polygon **must remain unadmitted** until a separately isolated topology/polygonization check and source-epoch geodetic review pass.

## Source-wide independent-ring topology challenge

A further read-only original SHA-pinned analyzer,
`research_runners/luxembourg_age_hq100_2021_ring_topology_v0.py`,
evaluates each original polygon ring **as a separate ephemeral GEOS
Polygon** under `shapely==2.1.2`. It reports only counts of individually
valid/invalid rings, low-precision whitelisted validity reason classes,
GEOS failures, and any rings over the 250,000-vertex complexity cap.
Rings over the cap are **quarantined as untested**, not optimistically
marked valid. Regression tests include a valid square, a self-crossing
bow-tie and an intentionally overcomplex ring.

**Interpretation boundary:** even if all source rings pass individually,
that does not prove the **entire 6,379-part polygon record is OGC-valid**:
an exterior ring can overlap another, two holes can overlap, ring
orientation alone does not prove exterior/hole identity, and the original
2021 flood scenario may not precisely match the ACT 2026 building survey
date. The only defensible next geometry check is complete original
multipart polygonization and exact original-source geometry validity
with a bounded, fully reviewed parser and no feature export.

## Next exact numerical flood-depth source access

The official [Luxembourg flood data request page](https://inondations.public.lu/en/demande-donnees.html)
identifies **zones.inondables@eau.etat.lu** for flood maps and related
water-level information. The HQ100 map is also exposed as a
[Geoportal rendered WMTS layer](https://wms.geoportail.lu/mapproxy_4_v3/demo/?type=external&wmts_capabilities=),
`eau_Hochwassergefahrenkarten_HQ100_2021`, which provides map imagery
and is **not** verified to provide numeric water depths.

A precise request should ask AGE for the **original numerical HQ100
2021 water-depth surface** (per-cell metres with NoData semantics),
provider-vintage elevation/depth model, extent, geographic CRS and axis
order, vertical datum and geodetic epoch, grid resolution, permanent
download link and file SHA-256, availability for all catchments and
exact rights for model calibration/derivative works, and matching HQ10
and HQextrem scenarios. Ask whether the 2022 ZIP source's floodplain
polygon is the exact dry/wet mask of that depth grid; **do not infer
this equivalence**. If only classified depths are available, request
the class thresholds, units, inclusive boundaries and original source
geometry of each class. No source depth values or independent insurer
assets have been obtained as part of this PR.

## Complete original-source per-ring GEOS findings (2 November 2026)

The final **entire 6,379-ring original source** [GitHub Actions run 41415231242](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41415231242) **passed**, including checksum/CRC/PRJ/coordinate checks and synthetic self-crossing-ring and complexity-quarantine regressions. A bounded Shapely/GEOS per-ring validity test determined:

| GEOS per-ring classification | Count |
| --- | ---: |
| Individually valid positive-area rings | **6,305** |
| Individually invalid rings | **74** |
| All invalidity classes | **74 × Ring Self-intersection** |
| Rings left untested due to complexity | **0** |
| GEOS parsing/testing errors | **0** |
| Original rings checked and conserved | **6,379** |

The initial stricter audit with a 250,000-point per-ring limit was [run 41414976854](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41414976854): it observed 73 invalid rings **plus one untested overcomplex ring**. Increasing the safely bounded original-ring limit to 2 million points resulted in 74 invalid rings, no skips. **Use 74/6,379 as the complete documented result**, not the preliminary 73.

Important: each ring was evaluated **individually** as a polygon, so even the 6,305 valid rings do not establish that the original multipart hazard polygon is jointly topologically valid. No exterior/hole containment, between-ring intersections or actual hazard intensity were validated. No original polygon, ring, coordinate, record geometry or location was emitted or persisted. The source is not yet authorised for intersection with ACT buildings or insurer exposures.

## Bounded 74-invalid-ring repair-method challenge — original result, 2 Nov 2026

[Exact-original provider run 41435194967](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41435194967) **PASS** with all synthetic negative controls. The new `luxembourg_age_hq100_2021_invalid_ring_repair_challenge_v0.py` compares in memory Shapely/GEOS `make_valid(method="linework")` and `method="structure"` **only for ring geometries individually invalid under the original 2021 AGE source**. No original geometry or repair is written to the repository, artifacts or Neon.

| Exact provider source diagnostic | Count |
| --- | ---: |
| Original rings classified invalid | **74** |
| Bounded repair comparisons completed | **73** |
| Originally invalid ring exceeding the strict 50,000-vertex repair cap | **1** |
| Linework repair usable | **73** |
| Result a single polygon / multiple polygons | **11 / 62** |
| Both GEOS methods yield topologically equal polygon sets | **73** |
| Original invalid ring boundary lineal point set unchanged | **73** |
| Non-polygon debris in completed linework outputs | **0** |
| Structure challenger failures or computed differences | **0** |

The 73 challenged original rings have **6,890,737.09 m² aggregate nominal signed-input area**, the same rounded sum as their 73 repaired polygonal candidates. **This is *not* a measure of the union of inundated terrain or independently verified inundation area.** Rings may be holes, overlap or represent distinct and nested levels; raw source invalid-ring nominal area has no scientific ground-truth status. The maximum source-ring nominal area among these 73 was **1,543,891.58 m²**, without publishing the ring identity or coordinates.

**Critical finding:** 62 of 73 technically recoverable rings result in **more than one polygon**. Treating each original invalid ring as a simple one-for-one recovered floodplain polygon would be wrong. The 74th unusually complex ring has **not been repaired or automatically approved**; source-wide full multipolygon assembly, shell/hole relationships and original hydraulic-mask lineage remain unverified. Even a repaired individual ring does not tell us which portion is permanently flooded or what depth to assign. All CAT-model/exposure admissions stay false.

## Exact original AGE HQ10 and HQextreme sibling sources, 2 November 2026

The separate first-party [AGE HQ10 catalogue](https://data.public.lu/en/datasets/flood-hazard-maps-10-year-flood/) and [AGE HQextreme catalogue](https://data.public.lu/en/datasets/flood-hazard-maps-extreme/) provide distinct original 2021-model/2022-publication ZIP files and **different independent publisher SHA-1 checksums**. The new read-only `research_runners/luxembourg_age_hq2021_sibling_source_receipts_v0.py` only accepts the pinned exact official resource for each named scenario. It reuses the reviewed strict ZIP CRC and SHP record/DBF schema validator, but assigns source-specific identity and never trusts the HQ100 wrapper's model label for the two other original scenarios.

The official [GitHub original-source workflow 41435808291](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41435808291) **passed** for all three scenarios, including negative synthetic source-label checks. For the two previously unexamined scenarios:

| Original audited source | HQ10 | HQextrem |
| --- | ---: | ---: |
| Provider SHA-1 | `08c75a51c0d2f42b9f95530494320ec085203d89` | `a32da12e9c41275466c07d51fff72a8c518eaf26` |
| Observed additional SHA-256 | `f5bf50e49f8e47207782e9030c6644594121c661cf31f4acb1bf292e5837b8fa` | `c26e81026bad0cad19e41086a905d7709bcf4cfd11341db2259aaa9d4d529888` |
| Compressed original ZIP | **4,699,796 bytes** | **3,932,876 bytes** |
| ZIP members / original SHP record | **8 / 1** | **8 / 1** |
| SHP polygon type code | **5** | **5** |
| Original polygon-ring parts (from SHP headers) | **13,439** | **5,108** |
| Original point pairs skipped without decoding | **1,493,429** | **1,288,014** |
| Original DBF fields | `OBJECTID`, `Shape_Leng`, `Shape_Area` | `OBJECTID`, `Shape_Leng`, `Shape_Area` |
| Numeric water-depth attribute | **Not present in DBF** | **Not present in DBF** |

Both official provider catalogues label the datasets CC0. **Original source SHP geometry topology, original CRS PRJ, stored-axis order, hydrological meaning and scientific reuse fitness for these *siblings* remain untested.** The source record/ring count is *not* evidence of scenario area, river coverage or actual flood risk monotonicity. In particular, **HQ10 having more ring parts than HQ100 or HQextrem does not mean a larger area**; multipart segmentation is not a monotone proxy for inundation area. Never infer it. Before any cross-scenario scientific comparison the original extent/mask topology, geodetic reference and 2021 model version must be independently checked for all three sources.

The three files have now passed first-stage original acquisition and structural-integrity research, but **none has numeric depth semantics or CAT-model input admission**. No original source bytes, original individual geometry, coordinates, depth values or insured exposures were committed, logged or imported to Neon.

## Full original coordinate and independent-ring topology QA: HQ10 and HQextrem (2 November 2026)

The sibling-specific pinned-original source workflow [41471764396](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41471764396) **passed** with `pyproj==3.7.2`, `shapely==2.1.2`, source-specific original published SHA-1 checks, previously observed independent SHA-256 pins and complete ZIP CRC checks. A separate new runner scans *all* original polygon source XY pairs in memory, verifies file/record bbox and closed/finite/non-degenerate rings, decodes only the PRJ as WKT, checks both as-stored and coordinate-swapped envelope hypotheses, and diagnoses every original individual ring with GEOS. All provider coordinates and ring geometries are transient, and the workflow outputs only aggregate source-wide figures.

| Verified original-source property | HQ10 | HQ100 (prior check) | HQextrem |
| --- | ---: | ---: | ---: |
| Original polygon-ring parts examined | **13,439** | **6,379** | **5,108** |
| Original coordinate pairs read | **1,493,429** | **1,336,393** | **1,288,014** |
| Closed source rings | 13,439 | 6,379 | 5,108 |
| Open / nearly zero signed-area rings | **0 / 0** | **0 / 0** | **0 / 0** |
| Individually GEOS-valid positive-area rings | **12,883** | **6,305** | **5,056** |
| Individually GEOS-invalid rings | **556** | **74** | **52** |
| GEOS invalidity reason | Ring Self-intersection | Ring Self-intersection | Ring Self-intersection |
| GEOS test error / ring untested | **0 / 0** | **0 / 0** | **0 / 0** |
| Source projected bbox xmin/ymin (rounded m) | **48,893.0 / 59,518.0** | **48,893.0 / 59,515.0** | **48,893.0 / 59,507.0** |
| Source projected bbox xmax/ymax (rounded m) | **106,138.3 / 137,076.0** | **106,138.3 / 137,088.0** | **106,138.3 / 137,098.0** |
| Declared CRS recognized from each *original PRJ* | **EPSG:2169** | **EPSG:2169** | **EPSG:2169** |
| Country-envelope plausibility, source XY | **plausible** | **plausible** | **plausible** |
| Country-envelope plausibility, swapped XY | **not plausible** | **not plausible** | **not plausible** |

All original source file and record bounding boxes matched the measured finite coordinates. Ring-winding counts among new siblings: HQ10 **8,188 negative / 5,251 positive**, HQextrem **2,819 negative / 2,289 positive**. Winding does **not** prove correct exterior/hole hierarchy.

**Scientific interpretation:** This upgrade establishes complete structural integrity and diagnoses the type and number of individual invalid rings in both newly covered sources. The HQ10 result of **556** invalid rings is materially different from **74** HQ100 and **52** HQextrem, but the ring count is **not a flood surface size, event damage ratio, hazard return-period failure, or vulnerability weight**. All three sets contain multiple individual source ring self-intersections and their full one-record multipart polygon shell/hole topology remains unproven. A geographic envelope is a weak spatial support check only; it is **not** an independent building-control-point, accuracy or geodetic epoch proof. No model loss, building overlay, depth or synthetic insurer TIV was calculated, and no producer geometry/attribute values were written to Neon or Git.

**Next scientific gate:** Build an original multipart assembly audit with actual Shapefile signed-winding and shell/hole hierarchy interpretation, bounded inter-ring topology and source-specific repair-effect challenge. A normal `make_valid` of isolated rings cannot substitute for true hole/shell semantics or establish scenario nesting. Separately obtain original numerically machine-readable, source-vintage-compatible HQ10/HQ100/HQextrem flood depth surfaces from AGE under verified rights, unit and vertical datum documentation.

## Original multipart shell/hole hierarchy falsifier: two winding interpretations (2 Nov 2026)

New `research_runners/luxembourg_age_hq2021_ring_hierarchy_challenge_v0.py` runs an **exact-original, checksum-pinned, aggregated-only Shapefile ring hierarchy research challenge**. It uses a bounded spatial index and exact **GEOS `shell.covers(hole)`** predicates only for *individually valid* original rings, and separately records how many candidate holes *might* have been affected by original-invalid outer-ring envelopes. Invalid original rings **are never repaired or silently declared actual floodplain boundaries**. The two competing interpretations are deliberately both tested:

- **Standard Esri Shapefile hypothesis:** clockwise (negative winding) = source exterior; counterclockwise (positive) = source hole.
- **Reversed hypothesis:** counterclockwise (positive) = source exterior; clockwise (negative) = source hole.

The original-file source run [41484031247](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41484031247) **passed** on the complete original three archives under **both interpretations**, with no candidate-limit quarantines and no GEOS covers errors:

| Exact-source original ring hierarchy *hypothesis* | HQ10 | HQ100 | HQextrem |
| --- | ---: | ---: | ---: |
| Standard: individually valid proposed holes | **4,742** | **2,593** | **2,243** |
| Standard: valid proposed holes with exactly one valid fully covering proposed exterior | **97** | **93** | **157** |
| Standard: valid proposed holes with no fully covering valid proposed exterior | **4,645** | **2,500** | **2,086** |
| Standard: valid proposed holes with *possible* original-invalid exterior **bbox** cover (not actual topology) | **4,742** | **2,588** | **2,243** |
| Reversed: individually valid proposed holes | **8,141** | **3,712** | **2,813** |
| Reversed: valid proposed holes with exactly one valid fully covering proposed exterior | **1,190** | **632** | **367** |
| Reversed: valid proposed holes with no fully covering valid proposed exterior | **6,951** | **3,080** | **2,446** |
| Reversed: valid proposed holes with possible original-invalid exterior **bbox** cover | **674** | **157** | **46** |
| Any interpretation: valid proposed holes with multiple fully covering valid proposed exteriors | **0** | **0** | **0** |
| Any interpretation: GEOS cover errors / candidate budget quarantines | **0 / 0** | **0 / 0** | **0 / 0** |

**Interpretation and limitations:** The reverse-winding hypothesis leads to *more* individually contained proposed holes in every tested original scenario, but this **does not prove that the issuer used reversed winding or that these are actual holes**. Most proposed interior rings remain unmatched even under the reversed interpretation. In particular an invalid outer ring may have a very broad **bounding box**, so a bbox plausibility count is deliberately not a proof that a hole is spatially contained by that invalid exterior; do not interpret the Standard-hypothesis source invalid bbox candidates as real interior containment. The source files may contain other ring nesting/overlap defects or source-specific export semantics. A single topological containment test is **not** a sufficient multipart Shapefile reconstruction, and no original hydraulic flood extent or flooded building was approved.

The new code and synthetic tests detect the standard hypothesis, independent reversed hypothesis, orphaned hole, doubly enclosing shell, original-invalid shell, bounded candidate budgets and source count conservation. Original geometries, ring IDs, coordinates and repaired candidates are neither persisted nor emitted. The scientific solution requires source-producer confirmation of SHP export conventions and a separately reviewed polygon shell/hole hierarchy and joint OGC-validity check. Combined with the still-missing actual numeric flood-depth grids, **all three sources remain excluded from production CAT-loss or insurer portfolio calculations**.

## Independent original publisher GeoJSON and grouped-polygon source challenge (2 November 2026)

A second, **publisher-issued** original format is available for each 2021 AGE HQ scenario. These [AGE HQ10](https://data.public.lu/en/datasets/flood-hazard-maps-10-year-flood/), [HQ100](https://data.public.lu/en/datasets/flood-hazard-maps-100-year-flood/) and [HQextrem](https://data.public.lu/en/datasets/flood-hazard-maps-extreme/) GeoJSON files were all separately published **13 June 2022**, with **their own** SHA-1, resource identifiers and original bytes (never reuse the SHP source checksum). The check is a separate [read-only GitHub Actions workflow](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41493462939), with transient raw files, bounded size and complete original SHA-1 gate. This independent representation should not be mistaken for independent hydraulic research: it is the same publisher/scenario, but offers an explicitly grouped polygon representation.

### Published original GeoJSON versus same-publisher Shapefile

| Byte-pinned original AGE resource | HQ10 | HQ100 | HQextrem |
| --- | ---: | ---: | ---: |
| Original GeoJSON publisher SHA-1 | `aeeaa1555eb769560d3d83c1e32450ee6a78e755` | `070966eac7451d9a4f5aeba1d2b7a3f25bf07f51` | `c85a4b3de65170fa93406ef76a77ccfd4cf75124` |
| Observed new GeoJSON SHA-256 | `063692d6445039e8ef50d7eb4320ba61d19b0d0c4e3f014ec42e35ae16d19b97` | `667eb1955ab8d45d40bd75b2d53b6e564661e336eeb417476171f0596d864be1` | `61eed6c7cc0374419d2debbabba04fe4df7f06680c777666ad7d36b918668943` |
| Original GeoJSON byte size | **74,317,579** | **66,435,657** | **63,175,318** |
| Source FeatureCollection / features | **1 / 1** | **1 / 1** | **1 / 1** |
| Publisher-encoded polygon groups | **8,188** | **3,724** | **2,819** |
| Publisher-encoded hole rings | **5,251** | **2,655** | **2,289** |
| Publisher GeoJSON rings / same-publisher SHP rings | **13,439 / 13,439** | **6,379 / 6,379** | **5,108 / 5,108** |
| Publisher GeoJSON points / same-publisher SHP points | **1,493,429 / 1,493,429** | **1,336,393 / 1,336,393** | **1,288,014 / 1,288,014** |
| Open source polygon rings | **0** | **0** | **0** |

The **published GeoJSON exterior/hole counts match the standard ESRI clockwise-exterior/CCW-hole assignment** from the Shapefile ring winding observations. This is useful original-provider representation evidence, **not** a proof that all original polygon groups or holes are spatially topologically valid. The previous GEOS ring screen found invalid individual rings. The GeoJSON therefore remains an **unadmitted research source**.

**Crucial interoperability warning:** All three original AGE GeoJSONs store coordinates in a **Luxembourg projected numeric XY domain**, consistent with the corresponding Shapefile's declared EPSG:2169 (source PRJ). They are **not WGS84 longitude/latitude coordinate values**. [RFC 7946 Section 4](https://www.rfc-editor.org/rfc/rfc7946#section-4) specifies WGS84 longitude/latitude for interoperable GeoJSON, so **naively loading these originals as default RFC 7946 WGS84 is wrong**. A future reader must explicitly record/project the original source CRS and transformations, not reinterpret the coordinate values as lon/lat. Full original field survey epoch and control accuracy are still unverified.

### GEOS OGC check of the publisher's own polygon groups

A separate **checksum-gated, ephemeral Shapely/GEOS 2.1.2** group-level challenge evaluates the official source GeoJSON `Polygon` groups **with the provider's assigned holes**, not just the raw individual ring direction. Every individual original group is either checked, rejected or explicitly quarantined by a hard **120,000 original-coordinate-pair** per-group cap. The [full source run 41493898032](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41493898032) **passed** with:

| Individual OGC group-validity result | HQ10 | HQ100 | HQextrem |
| --- | ---: | ---: | ---: |
| Publisher polygon groups | 8,188 | 3,724 | 2,819 |
| Individually valid groups | **8,139** | **3,710** | **2,811** |
| Individually invalid groups | **48** | **13** | **7** |
| All group invalidity reasons | Ring Self-intersection | Ring Self-intersection | Ring Self-intersection |
| Oversized original group (not tested) | **1** | **1** | **1** |
| Technical GEOS errors | **0** | **0** | **0** |

The follow-up [exact original source run 41494330342](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41494330342) **passed** and measured how much source geometry is concentrated within that **one untested giant group** in each scenario:

| Quarantined one-group burden | HQ10 | HQ100 | HQextrem |
| --- | ---: | ---: | ---: |
| Original coordinate pairs in giant group | **961,634** | **964,658** | **1,059,581** |
| Share of all source coordinate pairs | **64.39%** | **72.18%** | **82.26%** |
| Publisher-assigned hole rings in giant group | **4,152** | **2,103** | **2,056** |
| Share of all published holes | **79.07%** | **79.21%** | **89.82%** |
| All other publisher groups with holes (total) | HQ10 63 | HQ100 30 | HQextrem 20 |

*Last row gives the total number of groups with >=1 hole across the entire original scenario, not how many holes are in those groups.*

**Interpretation:** The original publisher's own GeoJSON makes explicit that **one very large polygon group per scenario contains most of the original ring hierarchy complexity**. This explains why the earlier per-ring `shell.covers(hole)` challenge (which excluded invalid shells) left thousands of would-be hole rings unresolved. It does **not** mean that one giant group causes all invalidity or that it can be repaired safely. All three giant groups remain quarantined and have not been evaluated as valid or invalid polygons; no national joint MultiPolygon OGC-validity claim exists. A bounded separate megagroup check plus a scientifically reviewed repair/area-overlap challenge are prerequisites before comparing flood areas or overlaying ACT2026 buildings.

No publisher original coordinates, per-feature identifiers, sample points, per-group geometry or real hazard depths were exported, put into Git artifacts or stored in Neon. No insurer TIV, real exposure, event loss, or country-specific flood model input was admitted.

## Next scientific steps

- Verify the original actual file format, complete record and field counts,
  CRS and axis ordering; identify how the provider encodes simulated
  water depths and units (or whether the ZIP contains only polygons).
- Freeze source release, coordinate transformation, scenario, depth units,
  and numeric decoding rules with a separate, small *real original-feature*
  inspection, whose detailed locations never enter Git.
- Make a bounded exact-source spatial overlap study against the separately
  tested Luxembourg ACT 2026 GeoBase physical polygons; distinguish
  independent source vintages and interpretation of 100-year scenario.
- **No real insurance portfolio or insured property value is available from
  official flood and building geometry alone.** A model loss requires
  separately sourced physical exposure meaning, vulnerability, insurer TIV,
  policy and reinsurance conditions and an admitted hazard intensity layer.

