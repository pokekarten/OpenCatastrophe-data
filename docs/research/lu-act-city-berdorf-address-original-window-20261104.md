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

**Actual original-source results:** pending the exact branch CI, not yet asserted in this note.
