<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC independent December 2024 hosted building-footprint copy: first polygon cross-vintage proof

**Observed:** 2026-11-05. **Research status:** `source_candidate / unadmitted`.
This is **NOT** the official NYC Office of Technology and Innovation's
archived release, a dated certified 2024-12-31 building stock or a
real insured portfolio. No source polygons/IDs/rows or property/claim
data were added to GitHub/Neon.

## Material independent finding

A live original-provider ArcGIS REST service is readable:
[NYC Building Footprint, layer 0](https://services2.arcgis.com/IsDCghZ73NgoYoz5/ArcGIS/rest/services/NYC_Building_Footprint/FeatureServer/0)
with public [ArcGIS catalog item](https://www.arcgis.com/home/item.html?id=66e3c725ad9843569da25ce1059a3807)
and original machine-readable
[item JSON](https://www.arcgis.com/sharing/rest/content/items/66e3c725ad9843569da25ce1059a3807?f=json).
The item is **owned by `rm4068_columbia`**, and is not the original
NYC OTI tenant or government-issued archive. Its recorded public
catalog `created` and `modified` timestamps are both **2024-12-07**
UTC (created 21:45:35, modified 22:02:00); layer
`editingInfo.dataLastEditDate`, `lastEditDate`,
`schemaLastEditDate` are **2024-12-07 22:01:53 UTC**.
Its provider reports **1,082,964 feature rows** via original ArcGIS
`returnCountOnly=true`. The native spatial reference is
**EPSG:2263**, NY Long Island State Plane; REST queries can reproject
actual polygon rings to **EPSG:4326**.

Crucially, the item exposes `BIN`, `DOITT_ID`, `BASE_BBL`,
`MPLUTO_BBL`, `FEAT_CODE`, construction year, date and real
polygon geometry. The original NYC OTI [current BUILDING
source 5zhs-2jue](https://data.cityofnewyork.us/d/5zhs-2jue)
provides matching independently published identifiers and GeoJSON
polygon coordinates. `MPLUTO_BBL` and `BASE_BBL` have **distinct**
billing and physical tax-lot semantics, as documented in the original
[NYC OTI footprint data dictionary](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md).

**Limits of these timestamps:** Creation/update metadata supports the
claim that the **ArcGIS-hosted derivative copy** was published and
last updated in December 2024. It does **not prove** the date at which
NYC originally captured each polygon; that the item remains untouched
by any undocumented server-level changes; that all 1,082,964 source
features are complete; that the copy matches NYC's authentic
2024-12-31 stock; or that third-party rights allow use in our models.
A current REST service is not a cryptographically pinned original
archive. Public visibility alone is not a complete re-use license.

## Live source-vs-source comparison for the same 30 LL84 candidates

A deterministic fixed cohort of the first 30 year-2024 LL84
`property_id` sorted ascending with BBL prefix `1000%` was used.
Only non-campus, individually numbered, single-BIN properties were
included (this is an **intentionally nonrepresentative selection**).
The previous PRs
[#1354](https://github.com/pokekarten/OpenCatastrophe-data/pull/1354),
[#1357](https://github.com/pokekarten/OpenCatastrophe-data/pull/1357),
[#1365](https://github.com/pokekarten/OpenCatastrophe-data/pull/1365)
already verified the current 2026 source for that exact cohort.

On 2026-11-05 six separate five-BIN source requests to each of
**the Columbia-hosted 2024 copy** and **the current NYC OTI source**
reconciled all 30 public BINs, all 30 DOITT IDs, both tax-lot
namespaces, and actual polygon envelopes (not geometry topology).
The original live requests encountered intermittent provider
responses; failed source groups were retried successfully and were
**never** interpreted as zero/missing records.

| Independently requested finding | Count |
| --- | ---: |
| Requested 2024 LL84 candidate BINs | 30 |
| Columbia-hosted Dec 2024 features found | **30** |
| Current NYC OTI features found | **30** |
| DOITT IDs unchanged across copy/current | **30** |
| Physical BASE_BBL unchanged | **30** |
| PLUTO billing MPLUTO_BBL unchanged | **30** |
| Copy billing BBL matches LL84 2024 BBL | **30** |
| Copy physical BASE_BBL matches LL84 2024 BBL | **22** |
| Copy physical BASE_BBL differs from LL84 billing BBL | **8** |
| Standard building `FEAT_CODE = 2100` in the hosted copy | **30** |
| Same total polygon-ring vertex count, copy/current | **30** |
| Polygon bounding boxes agree to ≤ 10⁻⁹ degrees | **29** |
| Polygon bounding boxes agree to ≤ 10⁻⁵ degrees | **30** |
| Largest observed bounding-box coordinate difference | **≈ 1.48 × 10⁻⁷ degrees** |

The tiny bounding-box discrepancy in one feature is **not** a proof
of geometrical equivalence; matching ring vertex counts likewise
do not certify identical topology, exact polygons or planar area.
We did not measure a surveyed building or insurer insured value,
and this 30-row sample **does not** imply good quality across
1,082,964 source records.

Source attribution and reuse require additional provider/license
review. The true **NYC government-origin full archived BUILDING
stock from 2024** is still missing, along with a verifiable archive
revision/file SHA-256. The 2024 hosted copy is promising cross-check
evidence, **not** an admitted original release.

## Reproducible, bounded opt-in public-source runner

`research_runners/nyc_columbia_dec2024_copy_compare_v0.py`

```bash
python research_runners/nyc_columbia_dec2024_copy_compare_v0.py --live
```

The runner is stdlib only and has **no network without `--live`**.
It pins the original ArcGIS public item ID and owner, its
Dec 7 2024 creation and modification date, layer edit times,
EPSG:2263 native CRS, exact baseline full-copy feature count,
the fixed OTI and LL84 original dataset IDs and public HTTPS hosts.
It rejects ownership/provenance metadata drift before consulting
the convenience cohort. No fuzzy source resolution.

It requests **only** a fixed 30-property LL84 identity sample,
**at most five BINs per API call**, source-specific public
ArcGIS fields and projected polygon rings, and the corresponding
current NYC OTI GeoJSON rings. Timeout fallback is per-BIN
and still requires **one complete provider response** for every
original item. It checks original BIN/DOITT, building feature
code, physical-versus-billing BBL key agreement, basic ring framing,
expected WGS84 coordinate ranges, vertex counts and polygon
bounding-box divergence. Every request is bounded by response-byte,
feature, source host/path, and vertex caps, with no HTTP redirects.
It **does not** download the 1.08M source stock or invent a snapshot.

Only cohort-level aggregate counts and the maximum
rounded geographic bounding-box difference appear in output.
No raw building identifiers, source rows, polygons, private
property data, exact building locations, or file bytes are logged,
committed or uploaded to a database.

`tests/test_nyc_columbia_dec2024_copy_compare_v0.py` uses
**synthetic-only** in-memory features for identity, 30-case
conservation, source-ownership/date/CRS/schema drift, malformed
geometry and source errors, batch timeout recovery and critical
scientific nonadmission flags.

## Scientific gates before CAT portfolios

1. Acquire the official **NYC OTI version-dated 2024 BUILDING
   inventory** from original historical dataset version export
   or NYC Open Data by formal request. Capture exact revision/date,
   original full-file bytes and SHA-256, original schema,
   feature counts, 2024 `DOITT_ID`/`BIN`/physical-vs-billing
   relations, geometry CRS and usable data rights. The verified
   public university copy is a **separate** source and should be
   compared to this official snapshot once available.
2. Before any wider use of this independent copy, confirm public
   service stability, who originally supplied the data,
   derivative license/right to reuse and a stable **whole-file
   immutable original artifact** with authoritative provenance,
   not just editable hosted-feature-layer metadata.
3. Extend from 30 deliberate LL84 records to an explicitly
   representative stratified sample across NYC boroughs and
   building types; reconcile splits, condo billing BBLs, missing
   DOITT IDs and rights. Use actual equal-area geometry projection
   and polygon topology tests before deriving footprint/floor area.
4. Independently align 2024 PLUTO 24v4 tax-lot data and
   physical building envelopes to dated LL84/industry exposure
   priors, construction and valuation inputs. Only then
   test synthetic **TIV**, insurer-specific assignment,
   hazard/vulnerability and eventual gross/net OEP/AEP losses.

**Research-grade conclusion:** an independently hosted early
December 2024 set of NYC building polygons can be queried **now**,
and it has remarkably stable identifier and bounding-box structure
for exactly 30 selected buildings. It is not yet a validated,
legally reusable, complete **official NYC 2024-12-31 insurer
exposure** dataset.
