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

### Integration boundary

This research evidence may later support a **physical building source intake** with a separate scientific-quality review, source-specific CC0 terms/rights record, pinned artifact identity and verified coordinate-axis semantics. It must **not** populate `exposure.exposure_unit.insured_value`, `insurance.policy_v1`, `insurance.policy_tiv_component_v1`, or real insurer-specific portfolios: none of those can be inferred from official building footprints. Keep the raw geometry out of the CAT-only Neon metadata registry until an explicitly approved persistent storage and admission design exists.
