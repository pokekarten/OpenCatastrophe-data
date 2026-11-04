<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg: VDL 2019 3D buildings versus ACT 2019 LiDAR/orthophoto provenance

2026-11-04. Research only. No original individual buildings, private addresses, claims, source point-cloud ZIPs, or model-input admission.

## Starting point: previously executed actual-source receipts

Merged PR #1272 proved actual ACT BD-Adresses 2026-11-02 point containment against ACT GeoBase 2026-10-01: 51/51 city points and 6/6 Berdorf points interior to one building polygon, with 104 city and 16 Berdorf polygons intersecting the actual 100m study squares with positive area. Merged PR #1288 read actual GeoBase Source attributes: all 104 sampled city polygons are labeled **Bati3DVDL**, and all 16 Berdorf ones are **Bati3DACT**. Different source administration does not prove different field or aerial sensing. ACT addresses can be parcel/largest-building derived, not entrance controls.

## Newly verified original geospatial source metadata

1. **2019 municipality 3D buildings**. Official Luxembourg state GeoNetwork record UUID a116f21e-faf1-4bdd-9a29-064fd9a30b8d:
   https://geocatalogue.geoportail.lu/geonetwork/geoportail-lu/api/records/a116f21e-faf1-4bdd-9a29-064fd9a30b8d

   The **catalogue** describes City of Luxembourg municipality **LoD 2.2 buildings in 2019**. It lists VDL Service Topographie et géomatique as original contact and ISO metadata timestamp 2022-07-27T06:57:46 (this is NOT the building flight date). Published online links lead to maps.vdl.lu and a short link, NOT a verified downloadable original model. No VDL 2019 CityGML original SHA256, original municipality license, 2019 sensor acquisition timestamp, 2026 revision crosswalk, physical building identity, or direct full source bytes were verified. A French data.gouv mirror does not specify a dataset license; conservatively treat original VDL asset rights as **unknown, access unverified**.

2. **VDL municipal surveying authority**:
   https://www.vdl.lu/en/the-city/city-departments-at-your-service/service-topographie-et-geomatique

   Its confirmed functions include surveying, maintenance of reference networks, updating geospatial topographic databases, official georeferenced address registers and systematic 3D buildings. Official national ACT 2020 LoD2.2 dataset explicitly excludes the municipality and points to the city's surveying service:
   https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2020/

   National ACT 2020 photogrammetric date and XY/Z root mean square error MUST NOT be transferred to the VDL 2019 or Bati3DVDL 2026 source. ACT's separate 3D export site confirms the city's own administrative 3D supply channel:
   https://act.public.lu/fr/cartographie/export-print-3d.html

3. **Official original LiDAR 2019, ACT**:
   https://data.public.lu/en/datasets/lidar-2019-releve-3d-du-territoire-luxembourgeois/

   The official national source provides many classified LiDAR point-cloud ZIP tile resources; class 6 denotes buildings. Full nationwide source volumes require hundreds of GB, so NO raw LiDAR tiles are fetched here. The catalogue publishes a much smaller 2019 tile URL/footprint index, an approximately 440 kB GeoJSON:
   https://download.data.public.lu/resources/lidar-2019-releve-3d-du-territoire-luxembourgeois/20200225-183349/lidar-urls.geojson
   Resource permalink: https://data.public.lu/en/datasets/r/050a058d-8eaa-4ae7-9e05-f39e81237173
   Provider published SHA1 **6fa8f0bd8afdf87bd175c9dab2d7b479b1b18874**.

   A 0-4095 byte original HTTP range was actually inspected on 2026-11-04: GeoJSON FeatureCollection, name lidar-filenames, CRS84 native WGS84 lon/lat coordinate order, Polygon tile bounds, per-feature original provider ZIP URL. A range response verifies header structure only, **not the whole file or site coverage**. The scoped original-data runner now compares the **full** original source to publisher SHA1, computes full SHA256, validates URL origin/CRS/geometry, and counts coverage of the two *preselected* 100m study squares with no per-feature original URLs/coordinates exported. Actual full-file receipt and counts require CI success.

4. **2019 national ACT orthophoto** original geocatalogue UUID 97c88ef6-6c64-4cb0-a134-06bb42b2b448:
   https://geocatalogue.geoportail.lu/geonetwork/geoportail-lu/api/records/97c88ef6-6c64-4cb0-a134-06bb42b2b448

   The publisher states **4–5 July and 22 August 2019** original flights, GSD less than 0.20m, special Luxembourg City perspective constraint, official map service and a CC0 catalogue label. It is an **ACT imagery source**, NOT proof of independent city imagery acquisition or VDL 2019 model observations; no original image scene SHA, tile raster or building-roof truth was examined.

5. **Published independent-processing research**, not independent ground truth: Zięba-Kulawik et al., Spatiotemporal Changes in 3D Building Density with LiDAR and GEOBIA: A City-Level Analysis, Remote Sensing 12(21):3668 (2020).
   https://www.mdpi.com/2072-4292/12/21/3668

   The scientists reconstructed 2019 city building roof models using 2019 ALS point clouds and historical orthophoto GEOBIA. However, they also incorporated cadastral information and separate development/demolition records. The paper establishes a possible *separately executed method*, not proof its raw sensor and geometry are independent of the city authority's 2019 3D assets. No paper building vectors downloaded or matched.

## Technical original-source gate

Research runner: research_runners/lu_act2019_original_lidar_tile_index_v0.py
Offline tests: tests/test_lu_act2019_original_lidar_tile_index_v0.py
Official GitHub workflow: .github/workflows/luxembourg-act2019-original-lidar-index.yml

This CI gate:
- accepts only a bounded original local GeoJSON file (at most 600000 bytes) and checks the published full source SHA1;
- calculates but does not yet preclaim a full original SHA256;
- checks CRS84, GeoJSON Polygon coordinate validity, file count, unique provider ZIP URL, strictly approved official URL path, no duplicate JSON keys or nonfinite values;
- evaluates tile intersections only with the same previously registered equal-area 100m squares at Luxembourg city and Berdorf, using pinned GIS reprojection libraries;
- emits only national tile totals, fixed-window covering tile counts, original file size, SHA hashes and explicit non-admission flags.
No per-tile URLs, source geometry, original raster/point cloud or raw building IDs printed, saved to Git or uploaded as artifacts.

## Scientific and legal gates still open

A VDL municipal metadata catalogue record does not prove 2019 original asset availability, licensing or exact Bati3DVDL 2026 lineage. ACT LiDAR/orthophoto 2019 provides a potential different *observational processing route*, but may share flights or common ACT cadastral priors with city 3D geometries. Before a genuinely independent 2019/2026 blind challenge:

1. Obtain VDL original 2019 model metadata and legal reuse terms, original asset digest, actual 3D capture dates, prior sources, roof-versus-ground segmentation, imagery/survey acquisition and revisions through 2026.
2. Freeze original LiDAR2019 ZIP tiles for the two preselected sites with original tile byte checksums and classification QA, in disposable private processing only; do not bulk-download the nationwide 500GB resource set.
3. Reconstruct LiDAR-derived 2019 roof masks using a separately documented method and check source overlap against municipality 2019 model; compare epochs and require a blinded manual ground-control sample. A 2019-vs-2026 geometric mismatch is NOT automatically model geocoding error or building demolition.
4. Explicitly review municipal 3D original rights and separate source-fusion independence. No rights approval, individual insured asset ID, TIV, claims, vulnerability, model input or insurer portfolio admission follows from index coverage.

No new separate canonical source registry is created in this research note. After original index verification, promote the metadata candidate to the existing canonical landscape source catalogue and regenerate its derived public view, preserving rights/science/admission blocks.

**Actual full-index and site-coverage results are not yet verified pending exact-head original-source workflow.**
