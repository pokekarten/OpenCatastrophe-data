<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg 2024 LiDAR: reproduce strict source-paired pixel mask comparison in Berdorf

**Research-only, 2026-11-01. No verified physical building identity, model admission or per-building heights.**

## Why an independent village control site matters

Merged PR #976 compared the **full** original ACT2023 rooftop outlines and ACT GeoBase2026 building polygons in a fixed 100m city-centre research ROI. With source-schema SHA256 receipts and a full-original-polygon IoU≥0.60 plus conservative split/merge conflict rule, it found **32 high-IoU candidates, 20 rejected ambiguities and 12 unchallenged one-to-one spatial candidates**. The 12 retained candidates had valid unique LiDAR2024 0.5m surface/terrain cells and each source-geometry median DSM−DTM proxy differed by **<0.5m** across alternate polygon masks. These are geometric *candidates*, not verified physical identities.

Merged PR #968 ran a second original LiDAR2024 × GeoBase2026 cohort for the **predeclared Berdorf village centre** (public church St John the Baptist, 6.348821 E, 49.820946 N), finding **16** intersecting GeoBase2026 polygons and **16** provisional footprint-median height proxies. It does NOT answer how many of those 16 coincide with ACT2023 rooftop polygons or how strongly geometry masks differ.

## This change

Instead of a new implementation of raster measures, the exact existing original-source [#976] pairing script has two **named** allowed research sites: `luxembourg-city` (unchanged default) and `berdorf-village`. The geometry is still a predeclared **100×100m** EPSG3035 equal-area square transformed to native EPSG2169 under the same as-stored field-axis assumption. It is *not* a representative random selection of rural Luxembourg.

The same original-source workflow now runs **both** city and Berdorf after just one SHA-pinned download of ACT2023 original 2D roof GPKG and one of GeoBase2026 original Buildings GPKG, and only bounded HTTP206 official 2024 MNT/MNS source TIFF windows. Existing source pins, national source populations, max 400 polygons per source, max 200k original raster cells, double-ownership exclusion, 8-cell per-pair minimum, full-source IoU≥0.60 and split/merge competitor≥20% of either polygon's area are unchanged. Each run prints **only aggregate pair count, height proxy difference bins, valid pixels and research flags**. No building IDs, original polygons, raw LiDAR values, per-pair heights or original data files persist in Git/Neon.

Additional synthetic tests ensure the two geographically distinct public centre ROIs remain fixed and that unknown/site-injection/private address arguments fail closed before source IO.

## Scientific boundaries

1. A true IoU candidate from two **ACT-family** building products does not prove independent observation or individual building identity.
2. Source rooftop polygons and GeoBase building objects differ in segmentation/vintage. Even a high IoU subset may be strongly biased towards ordinary, easy-to-match geometries; uncertain or split/multi-part polygons must be reported as excluded rather than silently treated as modelled assets.
3. MNS−MNT is a **surface elevation** proxy, not actual building height; includes trees, roof fittings and nonbuilding returns. LiDAR point classification and independent survey/vertical datum are still needed.
4. A 100m village church-centre block is not nationally representative; compare *research-local* inclusion rates and proxy stability, not city-versus-rural causal heights.
5. The 40GB COG files' full SHA256s and individual insurer TIV/occupancy are not established. Nothing enters approved exposure, hazard or CAT model tables.

## Original provider evidence

- ACT2023 roof original GeoPackage SHA256 `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf` (238,189 rooftop source polygons).
- ACT GeoBase2026 original Buildings GeoPackage SHA256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c` (230,353 building source polygons).
- LiDAR2024 official MNT/MNS public COG resources: https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/ .
- No full COG file hash; bounded exact-range/small window from previous #945/#950 original source runs.
- Prior pair research #976: https://github.com/pokekarten/OpenCatastrophe-data/pull/976 .

**The Berdorf match count and difference bins must be read from the new exact-head hosted official workflow, never guessed from the city counts. If no acceptable village pair is found, report the negative result and retain the fail-closed gate rather than changing site selection to get a favourable outcome.**

## Executed original-provider result: city baseline and Berdorf held-out predeclared site

**Source workflow:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41320503803 (2026-11-01). Both actual official-source runs succeeded, including **16 synthetic** field-bound/source-privacy regressions. A single controlled acquisition of **two whole SHA256-checked original building GPKGs** was followed by small-range original 2024 MNT and MNS raster samples for each fixed study site. No raw source data, personally identifying information, per-building IDs, per-polygon medians, individual point locations or original rasters were persisted in Git/Neon.

| Actual same-method evidence | City-control 100m | Berdorf village-control 100m |
| --- | ---: | ---: |
| ACT2023 roof actual-intersection polygons | **54** | **16** |
| GeoBase2026 actual-intersection polygons | **104** | **16** |
| Full-source polygon IoU≥0.60 high candidates | **32** | **15** |
| Split/merge high candidates rejected (>=20% overlap of either source polygon) | **20** | **1** |
| Uncontested unique original spatial candidates | **12** | **14** |
| Paired candidates with enough valid unique original MNT/MNS pixels | **12** | **14** |
| Paired unique/shared source raster pixels | **3,977** | **14,675** |
| Source-MNT/MNS joint valid pixels in fixed window | **44,521** | **44,521** |
| Paired median DSM–DTM proxy absolute differences <0.5m | **12** | **14** |
| Paired differences 0.5–<2m | **0** | **0** |
| Paired differences 2–<5m | **0** | **0** |
| Paired differences ≥5m | **0** | **0** |

City control reproduced the existing #976 baseline exactly. For Berdorf the GPKG RTree returned **18 candidate rows** for each source, of which **2** from each failed the positive-area intersection with the exact rotated 100m research square, leaving **16** source roof polygons and **16** source building polygons. All **14** strict accepted geometric candidates had >=8 uniquely and jointly valid original 2024 LiDAR raster cells; no pair failed insufficient pixels, negative median or source grid checks. The 14 pairs together had **14,675** shared valid cells, **14,996** uniquely owned roof-mask cells and **14,702** uniquely owned building-mask cells.

**Interpretation:** in two very small predeclared test locations, conditional on conservative high-IoU matchability, alternate ACT2023 rooftop versus GeoBase2026 building-geometry masks produced similar *median surface-minus-terrain proxies*. This is a useful **source-definition consistency check**, not two independently measured roof heights, not a sampling-design proof of rural/urban generalization, and not evidence that all original unmatched objects are duplicate/incorrect/insured. Upstream ACT survey/processing dependence, acquisition-year differences, vegetation and source axis/vertical datum controls remain unverified. No approved CAT model/exposure units created.

**Next scientifically causal work:** label/classify LiDAR point cloud as building versus ground versus tree on a bounded sample (classified COPC index located in #975), or manually survey a small independent holdout, then stress-test matched-pair medians on additional predeclared sites, including fail-fast source quality gates. Do not describe matching to a common original LiDAR raster as external ground truth.
