<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC first original 30-footprint geometry / vintage smoke (2026-11-05)

**Status:** original-provider small-cohort geometry check, **not_admitted**,
no confidential records, no raw original source bytes or coordinates committed.

## Causal purpose and verified upstream identities

The merged [PLUTO-LL84 tax-lot PR #1354](https://github.com/pokekarten/OpenCatastrophe-data/pull/1354)
and [official OTI BIN / MAPPLUTO-BBL PR #1357](https://github.com/pokekarten/OpenCatastrophe-data/pull/1357)
found 30 candidate properties in a deliberately selected **nonrepresentative**
2024 LL84 cohort, mapping to 30 distinct OTI `DOITT_ID` features. Eight had
`BASE_BBL` (physical parcel) different from the billing BBL, but the original
published `MAPPLUTO_BBL` confirmed all 30 billing links. Neither prior probe
read actual polygon coordinate rings.

Original providers:

- [NYC OTI BUILDING 5zhs-2jue](https://data.cityofnewyork.us/d/5zhs-2jue):
  current, city-maintained building footprints, weekly refresh, original
  public multi-polygon column `the_geom` and the matching `bin`,
  `doitt_id`, `base_bbl`, `mappluto_bbl`, `feature_code`,
  `geom_source`, `construction_year`, `last_edited_date` fields.
  The original NYC [OTI footprint data dictionary](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md)
  describes the role of photogrammetry/manual digitization, placeholder
  geometries, 1:n BIN-to-feature relationships and physical/billing tax lots.
- [NYC LL84 property-year 2024 view 5zyy-y8am](https://data.cityofnewyork.us/d/5zyy-y8am):
  first 30 `property_id` values after ascending sort, with year 2024 and
  literal BBL prefix `1000%`. Only the year and ID/campus/count columns
  are read. This convenience sample cannot support NYC-wide inference.

## Observed original-provider geometry results

On **2026-11-05**, a fresh read-only live pass selected the 30 original LL84
BINs from that deterministic cohort, then fetched the matching current OTI
polygons using fixed, five-BIN, original Socrata queries. One timed-out
five-BIN group was recovered with per-BIN queries; **all 30** matched and
the ring and coordinate diagnostics below completed. No individual original
BIN, BBL, DOITT, address, polygon or owner attributes were committed.

| Original-source observation | Value |
| --- | ---: |
| 2024 LL84 candidate rows | 30 |
| Current OTI footprint features / distinct BIN / DOITT | 30 / 30 / 30 |
| `MultiPolygon` with valid closed ring framing and broad NYC coordinate bounds | 30 |
| Structurally invalid/missing rings in this sample | 0 |
| Multipart objects / inner-hole objects in this sample | 0 / 0 |
| Total ring coordinates | 737 |
| Minimum / maximum ring coordinates per feature | 7 / 69 |
| Photogrammetric / Other (Manual) source | 20 / 10 |
| Construction year absent or 0 | 1 |
| Construction year reported after 2024 | 0 |
| Last-edited timestamp reported after 2024 | 0 |
| Physical BBL equal / different vs matched PLUTO billing BBL | 22 / 8 |
| **Spherical diagnostic** minimum / median / maximum footprint area (rounded) | **518 / 2,137 / 11,467 m²** |
| **Spherical diagnostic** summed 30-feature footprint areas (rounded) | **100,143 m²** |

**Interpretation and limits:** This is not an estimate of insured building
area, floor area, market/replacement value, policy count, historical exposure,
claim loss or model calibration. The spherical area diagnostic integrates
longitude × sine(latitude) over rings using mean Earth radius, a convenient
non-authoritative non-ellipsoidal screen. It is **not an EPSG:2263/area-
preserving projection**, surveyed area, ground-truth polygon topology
test, corrected floor-area measurement or an OED area attribute.
No geometric self-intersections, hole containment or overlap with adjacent
tax lots were certified. Geometry may still be outdated or incorrectly
digitized even when its coordinate/ring framing passes.

Since LL84 has **2024** reporting year while OTI is a **current 2026**
footprint service, construction-year and last-edit hints do not establish
the shape, coverage or property ownership **as of 2024**.
Current OTI records can be revised between runs: verify view metadata and
source revision/archive references before comparing cohorts.

## Independent historical feature availability

The original [NYC OTI BUILDING_HISTORIC data view ipkp-snf6](https://data.cityofnewyork.us/d/ipkp-snf6)
is a separate **archive of demolished or substantially modified structures**,
not a complete 2024 building snapshot. Read-only original provider
`select=count(*)` returned **50,995** historic feature rows on 2026-11-05.
The provider lists an attachment named `Building_Historic_20241026.zip`.
That filename refers to a historic-feature archive and must **not** be
mistaken for the entire then-current 2024 building inventory. A
BIN-restricted matching attempt did not complete due to source timeouts;
do not claim a negative historic match rate for the 30 BINs.
Source: [NYC OTI original historic footprint documentation](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingHistoric.md).

## Reproducible source-specific executable and safety contract

New standalone stdlib-only runner:

    python research_runners/nyc_oti_geometry_smoke_v0.py --live

Without explicit `--live`, there is **no network request**. The read-only
runner uses a fixed original NYC host, two source-view IDs, the same 30 LL84
properties, and only the nine required OTI geometry/identity/vintage
columns. It queries at most five numeric BINs per geometry request, with
per-BIN transport retries. It caps bytes per response, source row fanout,
per-feature/total coordinate vertices, accepts only proper 2D geographic
MultiPolygon structures and rejects malformed coordinates, invalid
crosswalks, unexpected/dummy/duplicate identifiers, an unapproved feature
code, malformed timestamps and insufficient source responses. The runner
never saves original polygon bytes or raw source IDs, writes Neon, or creates
OED/NextGen model inputs. Its JSON output contains only cohort-level
counts and approximate rounded area descriptors with explicit
`false` model/admission/insurance-provenance flags.

Synthetic-only offline tests:
`tests/test_nyc_oti_geometry_smoke_v0.py`. These test invalid and 3D
rings, wrong CRS/bounds, unknown `BIN` and duplicate `DOITT`, million BIN
placeholders, mismatched `MAPPLUTO_BBL`, bad feature codes, temporal flags,
batch timeout fallback, budget ceilings and the absence of source bytes
in the report. No real provider geometry is embedded in tests.

## Next scientific gate for actual CAT exposure use

1. Original provider rights, exact 2026 OTI view/version and downstream
   reuse/attribution review before promotion of any source row.
2. Reconstruct an actual **2024 inventory vintage** from properly dated
   original current/historic feature versions; independently adjudicate
   demolition, splits, condominium billing relationships and orphan BINs.
   Neither historic-only archive nor 2026 current footprints accomplish this.
3. Execute a bounded, reproducible **projected equal-area** polygon
   topology/overlap and original DOITT ID test, ideally with an approved
   geometry engine and independently verified reference footprints.
4. Calibrate construction/occupancy/number-of-floors archetypes and
   independent cost priors with measured uncertainty before introducing
   synthetic **TIV**; insurer-specific attachment probabilities require
   separate distribution/channel and insurer public evidence.
5. Only after building-risk admission plus hazard/vulnerability validation
   should synthetic gross/net insurance losses and OEP/AEP curves be tested.

The evidence supports **research-level ID and polygon framing plausibility
for exactly 30 nonrandom 2024 LL84 candidate records, using current footprint
geometry**. No claim is made about true building count, source-wide quality,
insurer portfolios or actual year-2024 physical exposure.
