<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT GeoBase2026: full original geometry quality gate (v0)

**Status: experimental source QA, not approved physical exposure or insurance CAT model input.**

## Purpose / official publisher source

Publisher: Luxembourg Administration du Cadastre et de la Topographie (ACT), BD-L-GeoBase Buildings-theme 1 October 2026. First-party dataset catalogue https://data.public.lu/en/datasets/bd-l-geobase/ currently lists **CC0**, EPSG:2169 and separate 37.4 MB Buildings GeoPackage ZIP https://download.data.public.lu/resources/bd-l-geobase/20261001-010523/buildings-20261001.zip. The catalog's CC0 label refers to this declared dataset, **not** an assertion that unrelated EUBUCCO, cadastral personal information, insurance policies, or other sourced layers inherit CC0.

The original **already** has previously independently established:
- exact publisher MD5 `f414154f993128a63f539aae2644c75a`;
- original archive SHA-256 `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`;
- extracted GeoPackage SHA-256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`;
- exact polygon layer `Buildings_BU_Building`, **230,353** GeoBase source objects, EPSG:2169, known schema columns `id`, `geom`, `BU_BuildingID`, `Source`;
- all 230,353 building-ID values unique within this source; 9 missing `Source` labels (source-label completeness is separate from polygon quality).

These are provider file properties, NOT proof of one building per row, stable correspondence with 2023 ACT roof polygons, construction age, occupancy, material, actual insured building, or TIV. The original data contain multiple feature/source semantics and source version relationships.

## Newly implemented QA

`research_runners/luxembourg_geobase_2026_geometry_quality_v0.py` composes the existing **exact original SHA-256 + publisher MD5 + complete GeoPackage source and ID quality gate** before streaming every original geometry blob from an immutable read-only temporary GeoPackage. New checks:

1. Decode the actual GeoPackage binary geometry header, version, envelope-length code and embedded EPSG:2169 SRS. Reject malformed/truncated/oversized headers.
2. Parse the original polygon/multipolygon WKB through pinned Shapely 2.1.2, without assuming which stored coordinate is easting/northing.
3. Categorize **every** original feature in exactly one mutually exclusive bucket: positive-area topologically valid source polygon, topologically invalid polygon, empty source geometry, zero/non-finite-area polygon, malformed/unparseable GeoPackage blob.
4. Compute only country-wide aggregate projected native area sum, median and 95th percentile for valid polygons; never log or output an original building ID, polygon, bounding box, coordinates, owner, address, cadastral identifier, location TIV, or source-label strings. Original data are downloaded only into the temporary GitHub runner and never saved to Git or Neon.
5. Explicitly retain `ground_control_axis_order_verified=false`, `physical_building_identity_verified=false`, and `building_geometry_model_input_approved=false` even if every geometry passes.

The observed source polygon count and projected area metrics are **not** national surveyed building area, number of unique built structures, footprint match precision or loss-model inputs. Because ACT2023 rooftop features and 2026 GeoBase building features differ significantly in segmentation, there must be separately adjudicated identity and vintage/axis controls before any matching or building economics.

## Run

```bash
python -m pip install shapely==2.1.2
python -m unittest tests.test_luxembourg_geobase_2026_geometry_quality_v0 -v
python -m research_runners.luxembourg_geobase_2026_geometry_quality_v0 \
  --source-zip /private/checked-original/buildings-20261001.zip
```

The optional automatic GitHub original-byte test is `.github/workflows/luxembourg-geobase-2026-geometry-quality.yml`, limited to this exact source. It requires an exact immutable checksum match before the full scan; only aggregated results are printed. **Do not claim measured valid/invalid counts or median area until an actual original-source job completes successfully.**

## Verified original-source outcome (1 November 2026)

The full original-content workflow [GitHub Actions run 41353560374](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41353560374) **passed** after authenticating the same fixed ZIP and GeoPackage SHA-256 digests. All five synthetic regression tests passed. The scan processed **all 230,353 original polygon features**, without saving building IDs/geometries or writing to Neon.

| Exact source-wide geometry metric | Observed aggregate |
| --- | ---: |
| Original GeoBase features scanned | 230,353 |
| Valid topology with positive projected area | **230,287** |
| Topologically invalid polygons | **66** |
| Corrupt/unparseable original GeoPackage geometries | **0** |
| Empty original geometries | **0** |
| Nonpositive/nonfinite valid polygon area | **0** |
| Median area of valid source polygons | 119.20 projected m² |
| P95 area of valid source polygons | 521.73 projected m² |
| Sum of valid source polygon areas | 47,489,787.71 projected m² |

**Interpretation:** The 66 invalid geometries are topological failures, *not* missing source records or evidence of 66 destroyed buildings. They require quarantining, original-quality reporting, and a separate source-geometry-repair policy **before** performing spatial joins or area-based valuation. The observed area values are source projected-geometry measurements, not parcel areas, surveyed ground-floor areas, insurer building counts or TIV.

The follow-up exact-original source run [41353703644](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41353703644) **passed** and classified **all 66 invalid polygons as `Ring Self-intersection`** using coordinate-free GEOS reason categories. No feature identifier or offending coordinate was emitted. This is an actual reproducible source-quality signal: repair or quarantine must distinguish topological invalidity from a missing building, and any geometry repair requires separate before/after area and identity audits. No cross-source building identity or spatial accuracy claim is implied.

## Quarantined repair comparison of the 66 invalid original polygons

The follow-up module `research_runners/luxembourg_geobase_2026_repair_diagnostic_v0.py` examines **only geometries already rejected for invalid source topology**, in the same fixed-source temporary process as the original full scan. The method is `Shapely 2.1.2 / GEOS make_valid(method="linework")`. It is intentionally a diagnostic, **not** a source correction or an automatic model input.

For every invalid input, it checks that the GEOS repair output is topologically valid and has at least one positive-area polygonal component. It separately counts outcomes that remain unusable, split into multiple polygonal components, or contain lower-dimensional line/point debris. It computes only anonymous aggregate absolute/relative changes between the invalid original's **nominal GEOS area** and the repaired polygonal area. The original's area is ambiguous for a self-intersecting ring and **is not physical ground truth**; a percentage of that nominal area cannot validate a footprint.

The report must keep all repaired candidates **quarantined**, including single-polygon repairs with small numeric area deltas. No original ID, coordinates, per-object area, repaired WKB, new geometry or candidate footprint is written to files, stdout, Git, Neon, insurer portfolios or Oasis exposure. Any repairs later used in a hazard overlay would require independent source-axis/geodetic control, source-specific rights and survey-vintage review, split/merge identity review, manual sample adjudication and a separately accepted repair algorithm.

The follow-up source workflow is the same `.github/workflows/luxembourg-geobase-2026-geometry-quality.yml`; synthetic tests include an invalid bow-tie source ring where `make_valid(linework)` yields multiple positive-area components and the invalid source's nominal area is zero. **Actual original repair outcomes must be read from the newest independently successful source workflow**, not inferred from this synthetic example.

## Actual first linework-repair comparison (2026-11-01)

The exact-source workflow [run 41354238423](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354238423) completed **successfully** with Shapely 2.1.2 / GEOS `make_valid(method="linework")`. All 66 originally-invalid ACT2026 polygons yielded **one** valid positive-area polygon each; **0** produced multipart polygon repairs, **0** were unusable and **0** left nonpolygon line/point remnants. Among all 66 polygons with positive **nominal invalid-input** GEOS area, the sum and median of the absolute original-versus-repaired area differences rounded to **0.00 m²**, and none exceeded 1% of nominal area.

**Do not interpret 0.00 m² as positional or shape equality**; a ring self-touch can be repaired by changing ring structure without changing computed area, and the invalid source's nominal area is not a validated surveyed footprint. The repair is not persisted or accepted for catastrophe-model inputs.

A further independent diagnostic now challenges the same in-memory invalid polygons using `make_valid(method="structure", keep_collapsed=True)`. It reports only anonymous counts of valid alternate repairs, polygon-component-count disagreements, alternate area disagreements, **topological polygon-set disagreements and repaired-set symmetric-difference area disagreements** over `max(1e-6 m², 1e-8 × larger area)`. These are *algorithm-comparison metrics*, not an independent geodetic field survey or a scientific approval. The full original-source independent-algorithm challenge [run 41354434288](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354434288) subsequently **passed**. The GEOS `structure` algorithm also returned **66 usable polygon repairs**, none unusable. Compared with `linework`, it had **0 disagreements in polygon-component counts** and **0 repaired-area disagreements above the declared tolerance**. Thus two GEOS algorithms agree on the diagnostic counts and area for all 66; this **still does not establish positional identity, exact ring semantics, independent ground survey accuracy, or permission to use any repaired polygons in production CAT calculations**.

## Actual repaired-shape agreement (2026-11-01)

A further independent exact-original workflow [run 41354618145](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354618145) **passed**, including complete original SHA verification and source-wide scan. On all **66** previously invalid source polygons, `make_valid(linework)` and `make_valid(structure)` both yielded one valid polygon. The two repaired *polygonal sets* showed **0 topological equality disagreements**, **0 symmetric-difference area disagreements** above the declared small numeric tolerance and **0 component count disagreements**. No input or repaired source geometry was emitted or persisted.

This verifies **agreement of two GEOS reconstruction algorithms for this fixed original source**, not correctness of source geometry against surveyed coordinate control, insured risk identity or building vintage. Neither candidate is approved for hazard overlays or financial/insurance inference. A controlled spatial accuracy/identity and provider source-science review is still required before any model-input promotion.

## Separate geodetic reference-station screen and 2026 frame transition

The published ACT [SPSLux 2026-04 station-coordinate table](https://act.public.lu/content/dam/act/fr/publications/documents-techniques/202604-dtech-coordinates-reference-station.pdf) contains non-personal national GNSS reference station coordinates with both **ITRF2020 @ 2025.83** published longitude/latitude (publisher labels them approximately WGS84) and **LUREF LTM East/North** measurements. A separate [official ACT geodetic reference notice](https://act.public.lu/fr/gps-reseaux/spslux1/spsluxgeodeticdatum.html) specifies that the official ETRS89-to-LURES realization **LUREF2025 superseded LUREF2020 on 31 October 2026**, with updated station coordinates effective on that date. ACT also explicitly states that there is **no official direct WGS84-to-LURES transformation** and notes epoch-dependent ITRF/ETRS/WGS84 drift. We must not silently treat a generic EPSG operation as a certified 2026 ground-survey transform.

`research_runners/luxembourg_spslux_202604_axis_station_screen_v0.py` freezes **seven public non-personal station reference coordinate pairs** from the April 2026 table and uses pinned `pyproj==3.7.2` to challenge two hypothesized EPSG:2169 inputs: (E,N) versus (N,E). Residuals are calculated from projected-to-approximate-WGS84 using geodesic distance only; only the **aggregate count, native maximum/median and swapped minimum** are printed. A deliberately loose **20m native / 1000m swapped** gate tests coordinate-interpretation plausibility, **not sub-meter survey precision**. Program provenance includes official publisher URLs, published reference epoch, source-release date and frame transition. Any anomalous station, repeated ID or invalid projected/numeric value blocks the check.

This control source comes from **the same ACT agency** as the official GeoBase building product, but from a separate measured GNSS network. It is a useful *independent measurement modality*, **not independent producer corroboration of cadastral building locations**. Critically, none of the control stations has been identified as a surveyed vertex on an original GeoBase building, so the script always emits `individual_geobase_geometry_axis_ground_control_verified=false`, `station_frame_epoch_tied_to_geobase_original_proven=false` and `CAT_model_input_admitted=false`.

**Executed official-data result (1 November 2026):** [GitHub Actions run 41355664692](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41355664692) **passed**, including all four station-screen negative/synthetic tests and the existing complete 230,353-feature original GeoBase integrity/topology/repair scan. With pinned `pyproj==3.7.2`, all seven published April 2026 GNSS reference station pairs favor conventional LUREF E/N order: **maximum and median rounded native screen residual = 0.9 m**, while the **minimum swapped-coordinate residual = 3,703.1 m**. The maximum is *not* the geometry positional error, and the April reference station pairs are not certified post-transition LUREF2025 coordinates. No original buildings or repaired geometries were admitted, and all scientific/insurer model flags remain false.

The GeoBase2026 source was released **1 October 2026**, before the 31 October 2026 official frame transition. Do not retroactively relabel that source as LUREF2025, interpret the old April 2026 station table as a current post-transition certification, or infer that EPSG:2169 transformation residuals directly measure actual building-outline positional error. A future genuinely ground-controlled study needs a source-dated survey point *on an identifiable original building corner*, verified national datum and epoch, and a separately reviewed crosswalk; compare multiple sites in the original footprint with retained internal source context and **aggregate-only** public outputs.

## Source-boundary shape challenge (follow-on)

The repaired-area equivalence in the initial 66 cases and agreement between two `make_valid` algorithms are useful but **insufficient to establish that the original source contour was preserved**. A polygon can retain the same area while removing a spike, changing a ring path, or altering the original invalid boundary. See the Shapely 2.1.2 documentation for [discrete Hausdorff distance](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.hausdorff_distance.html) and [make_valid repair semantics](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.make_valid.html).

The original-source code therefore adds a third, **quarantined and ephemeral** challenge: compute the *discrete, densified Hausdorff distance* between the boundary of each invalid original polygon and the boundary of its in-memory linework-repaired polygonal set, with densification fraction `0.25`. Also compare source and repaired boundary *lengths*. The report contains **only country-wide aggregates**: comparable/failed counts, maximum and median (rounded to 0.0001 native projected units), numbers with Hausdorff distance above 1cm, 10cm and 1m, and aggregate absolute boundary-length change. The diagnostic cannot export original/repaired geometries, per-feature values, coordinates or identifiers; it retains `source_boundary_position_accuracy_ground_control_verified=false`.

The discrete Hausdorff implementation is a **vertex-sampled approximation** of boundary distance, not continuous Hausdorff error or certified metric accuracy. `EPSG:2169` declares metres, but the actual building-coordinate reference epoch, source axis/vertex accuracy and current `LUREF2025` realization still require separate ground control. This diagnostic alone cannot establish source provenance, human-adjudicated building identity or fit for flood-depth overlays. Large changes should quarantine repairs for manual challenge; **small or zero changes do not approve any source polygon**.

A synthetic regression explicitly creates an invalid polygon with an inward retraced **2m spike**. Its nominal area is unchanged by `make_valid`, yet the repaired boundary differs by metres. This prevents area-only tests from incorrectly declaring original geometry preservation. Record actual original data counts only after a successful exact-source GitHub workflow run.

### Integration boundary

This research evidence may later support a **physical building source intake** with a separate scientific-quality review, source-specific CC0 terms/rights record, pinned artifact identity and verified coordinate-axis semantics. It must **not** populate `exposure.exposure_unit.insured_value`, `insurance.policy_v1`, `insurance.policy_tiv_component_v1`, or real insurer-specific portfolios: none of those can be inferred from official building footprints. Keep the raw geometry out of the CAT-only Neon metadata registry until an explicitly approved persistent storage and admission design exists.
