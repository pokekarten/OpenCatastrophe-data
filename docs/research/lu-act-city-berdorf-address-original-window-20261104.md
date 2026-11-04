<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BD-Adresses / GeoBase: city-centre versus Berdorf exact-area original-source challenge

**2026-11-04. Original-source research only, no insurer asset or CAT exposure admission.** This follow-up builds on PR #1269 rather than reimplementing address and polygon original-receipt validators.

## Two preselected source locations

Both sites were previously fixed in the original ACT GeoBase / LiDAR investigations; no site is selected by address-match performance.

| Public research area | WGS84 centre | Equal-area window | Previous official ACT GeoBase polygon count |
| --- | --- | --- | ---: |
| Luxembourg city centre | 6.1319 E / 49.6116 N | EPSG:3035 100 m × 100 m | 107 |
| Berdorf St John the Baptist church village-centre | 6.348821 E / 49.820946 N | EPSG:3035 100 m × 100 m | 16 |

Berdorf has been checked against the original official GeoBase / 2024 LiDAR source by prior merged PRs #968/#976. These are two **purpose-selected public centre points**, not stratified random, population-weighted rural/urban locations or nationally representative sites.

## Source integrity and fixed-date inputs

1. ACT BD-Adresses original 2026-11-02 CSV, full SHA-256: f163ed856200eedd8b501da2d7787e01ee373be1a55a4d79abcf57c96982a99c. Full original 179,768 address rows from prior original byte proof #1260.
2. ACT GeoBase Buildings original 2026-10-01 ZIP, full SHA-256: 6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3. Inner Buildings GeoPackage SHA-256 ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676 and 230,353 source building objects.
3. Same source organisation ACT: addresses may be placed at parish/parcel/building centroids. Pairs must be treated as *candidate spatial links*, not independent site controls.

## Precisely corrected geospatial semantics

The GeoPackage original RTree returns **bounding-box intersections**, which need not intersect the rotated original EPSG:3035 square. The research runner now takes those bounded original candidates, maps the four equal-area square corners back to EPSG:2169, forms the actual projected polygon and retains only **positive-area intersections**. Boundary-only or enclosing-bbox-only candidates are excluded before counting either official site. Hard fail if exact populations differ from the earlier source-verified 107-city / 16-Berdorf counts. Address points are selected inside the exact EPSG:3035 equal-area square and compared with the original exact EPSG:2169 building polygons; the source-family/internal-coordinate agreement remains a dependency and **not** survey-level ground truth.

The original-source workflow uses exactly one verified original download of each permitted dataset, then executes BOTH fixed sites with separate aggregate outputs. There is no externally supplied coordinate, site string other than these two choices, place search, or trial-and-error sampling of better outcomes. Every original byte, address, ID, point and polygon remains in ephemeral runner storage. Only aggregate point-in-polygon statuses, polygon candidate usage, multiplicity and distances are logged.

## Falsification / expected outcome

- Separate national original-data SHA and structure validation; original CSV and ZIP/GPKG hashes unchanged.
- Four additional fictional tests cover both frozen site controls, unknown-site rejection *before* source IO, boundary/bbox filtering and invalid geometry. The previous 13 synthetic regressions remain.
- Source CI must confirm the site-specific **observed** matched, ambiguous, uncontained and multiple-address outcomes. No village results are inferred from city.
- A mismatch with the prior fixed-window count is a useful **scientific fail**, not permission to adjust the site or remove a safeguard to get a green job.

## CAT exposure boundary

A 51/51 interior result in Luxembourg city centre from PR #1269 reflects two source products from ACT and should not be treated as accuracy, completeness or one-to-one insurance exposure. A village comparison may identify different candidate multiplicity, but no national/urban/rural causal estimate can be inferred from two preselected 100 m squares. Independent building entry points, survey-grade holdouts, dates, address-unit semantics, source-specific rights and risk asset linkage remain separate admission decisions.

**Original-source results:** verified in the hosted source workflow, as documented below.


## Executed original-source results (2026-11-04)

**GitHub original-source workflow:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41819391418 (successful; exact code head 163eb2e4c4a109ef3fc9411294126438e8df3e42). Both exact original ACT source objects were SHA-validated; 17/17 synthetic tests passed. The same downloaded originals were processed sequentially at the two sites, no source data or individual matches were uploaded.

| Measured original-source aggregate | Luxembourg city | Berdorf |
| --- | ---: | ---: |
| Address points in the fixed EPSG:3035 100m square | **51** | **6** |
| GeoBase polygons intersecting original enclosing RTree rectangle | **107** | **18** |
| GeoBase polygons with **positive area inside exact rotated square** | **104** | **16** |
| Polygons excluded as rectangle-only spatial candidates | **3** | **2** |
| Address points in exactly one original building polygon | **51** | **6** |
| Ambiguous, boundary-only, or exterior address points | 0 | 0 |
| Polygons containing exactly one sampled address point | **37** | **4** |
| Polygons containing multiple sampled address points | **6** | **1** |
| Addresses in these multi-address polygons | **14** | **2** |
| Polygons without uniquely contained sampled address points | **61** | **11** |
| Repeated CACLR address identifier rows inside the fixed window | 0 | 0 |

**Count conservation:** city 104 = 37 + 6 + 61, and 51 = 37 + 14. Berdorf 16 = 4 + 1 + 11, and 6 = 4 + 2.

### Method correction: 107 is not 104

Parent PR #1269 originally reported **107 GeoBase polygons**, the number intersecting an enclosing EPSG:2169 bounding rectangle, not necessarily the exact equal-area square. The corrected positive-area city denominator is **104**. Three RTree/rectangle candidates had no positive-area overlap with the actual rotated square. Berdorf similarly had **18** rectangle candidates but **16** polygons crossing the true window with positive area. These were empirically observed differences of selection semantics; original bytes and hashes did not drift. Keep the original rectangle counts visible as historical evidence and use exact-area counts for new geographic comparisons.

The original 51 city address points were still uniquely inside one actual positive-area polygon, so the point status is robust to this correction in the observed sample. The reduction of sampled polygon count is **not a loss of original buildings from the official dataset**; it is simply a change in geographic clipping.

### Scientific limits

- These are **two purposively preselected public-centre windows**, not random or representative urban/rural strata. No inference about national address coverage or geocoding accuracy is supported.
- ACT address points can originate from parcel or largest-building centroids; both inputs are from ACT and may reuse the same cadastral source, so the 100% contained-point rate is **not independent ground truth**.
- The 61 city and 11 Berdorf polygons without a sampled address *inside these small squares* are not proven unaddressed buildings. The polygon may be partially inside while its address point is outside, have different segmentation or lack an official georeferenced address.
- The address snapshot is 2026-11-02, building snapshot 2026-10-01. These are candidate spatial links, not a verified temporal building-change history or a physical building/insurance unit ID.
- No original source rows, polygons, IDs or private insurance data were saved to Git/Neon. No commercial rights, scientific model input, hazard/loss calculation or TIV admission is asserted.
