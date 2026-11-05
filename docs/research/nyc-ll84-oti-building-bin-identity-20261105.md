<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC LL84 property-year → city-maintained BIN building footprint identity v0

**Evidence checked:** 2026-11-05. **Decision:** research-only, not a building
identity proof, not a licensed/admitted model input, not a real insured asset.

## Why this is the next causal step

The already merged [first NYC PLUTO/LL84 30-row pilot](https://github.com/pokekarten/OpenCatastrophe-data/pull/1354)
identified 28 single-building PLUTO tax lots and two tax lots with multiple
buildings. PLUTO is a **tax-lot/condominium-billing grain** and does not by itself
prove the observed building's independent physical footprint or insurer
exposure. A third **independently maintained feature dataset** can test the
BIN references without silently reallocating values.

## Original government sources and semantics

- [NYC OTI official building footprints dataset 5zhs-2jue](https://data.cityofnewyork.us/d/5zhs-2jue)
  and [exact published Socrata columns](https://data.cityofnewyork.us/api/views/5zhs-2jue/columns.json):
  `bin`, `doitt_id`, `base_bbl`, `feature_code` (spatial
  `the_geom` exists but is intentionally NOT requested in this diagnostic).
- [NYC OTI GitHub original Building Footprints metadata](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md)
  explicitly distinguishes: `DOITT_ID` is a consistent feature identifier;
  `BIN` may be duplicated, unknown or a borough-specific dummy 'million BIN';
  `BASE_BBL` is the physical tax lot; `MAPPLUTO_BBL` is the PLUTO
  tax/billing-lot join key for condo complexes. The Socrata 5zhs-2jue
  public projected columns inspected for this research **do not expose
  `MAPPLUTO_BBL`**. An apparent `BASE_BBL` mismatch is not a proven
  mismatch of a physical building to its PLUTO condominium billing lot.
- [NYC LL84 official 2024 source 5zyy-y8am](https://data.cityofnewyork.us/d/5zyy-y8am)
  provides EPA property ID, a BIN and BBL list, parent property state,
  reported number of buildings and reporting year, not necessarily a
  single insured structure.
- [NYC PLUTO 26v2](https://data.cityofnewyork.us/d/64uk-42ks)
  was previously read for the same convenience cohort; 2026 PLUTO
  and OTI current footprints can disagree with 2024 LL84 historical observations.

The footprint source metadata warns that polygon `feature_code=1003` is
a **placeholder** and not a surveyed building outline, that other
feature codes represent ancillary structures, and that one BIN can correspond
to multiple polygon features. `feature_code=2100` describes a building,
but does NOT establish complete geometry, insurable unit, historical
existence, polygon accuracy, ownership, structural replacement cost or
insurance policy.

## Actual independent original public API evidence

On 2026-11-05, read only the first 30 LL84 year-2024 rows with BBL prefix
`1000%` in ascending EPA property ID order, selecting identifiers and
building-count/parent flags only. Query the same 30 unique valid BINs
against the official OTI building-footprints table with four projected
non-geometry fields (`bin`, `doitt_id`, `base_bbl`, `feature_code`).
The original source queries returned:

| Observed source feature | Number | Safe interpretation |
| --- | ---: | --- |
| LL84 2024 property-year observations | 30 | Deliberate Manhattan convenience cohort |
| OTI public footprint features for those 30 BINs | 30 | Read-only independent identity presence |
| Distinct OTI DOITT feature IDs / BINs | 30 / 30 | No duplicate in this small convenience cohort |
| Real building feature code `2100` | 30 | Only type classification, no polygon verification |
| OTI `BASE_BBL` equals LL84 BBL | 22 | **Unverified** tax-lot agreement |
| OTI `BASE_BBL` differs from LL84 BBL | 8 | **Unresolved** physical-vs-billing-lot relationship |

All counts were derived from original official provider read-only responses.
During the exploratory live pass, 20 BINs were resolved in five-BIN groups
and ten initial batch failures were subsequently resolved via individual
BIN requests. A later full live pass retrieved all 30 in six five-BIN
queries; no BIN or DOITT_ID was missing in the resulting cohort.
**A network timeout is not a verified absent feature.**

The source data were held transiently in memory and **no individual BIN,
property ID, BBL, address, polygon, property value, source row or company
identity has been committed**. The table is a tiny research measurement,
not statistically representative of NYC buildings or condominium prevalence.
In particular, the **eight BASE_BBL differences are not eight proven errors**.

## Reproducible bounded research tool

`research_runners/nyc_ll84_building_bin_identity_v0.py`

    python research_runners/nyc_ll84_building_bin_identity_v0.py --live

Only the explicit `--live` argument initiates provider reads.
The script uses exactly the original NYC HTTPS host and view IDs;
a fixed 30-property LL84 selection; at most five BINs per
footprint query; four non-geometry columns; capped result sizes;
no access tokens; no addresses, raw source dumps, insurer names or spatial
coordinates. Failed group transports are retried as five single BIN
queries; persistent individual failures abort the complete result,
not count as unmatched. Unexpected response columns, decimal/invalid IDs,
duplicate DOITT IDs and response truncation block output.

Only mutually exclusive **aggregate reason counts** are emitted.
Different `BASE_BBL` and LL84 BBL remain explicitly unresolved;
`BIN` uniqueness is a sample observation, not a global provider guarantee.
The runner does **not** download `the_geom`, allocate insurable sums,
save source rows, write to Neon, or produce OED/NextGen model inputs.

Test suite: `tests/test_nyc_ll84_building_bin_identity_v0.py`;
all fixtures are invented and offline. It covers dummy BINs, duplicated
BIN/DOITT identities, parent-child/campus records, multi-BBL/BIN properties,
malformed fields, no-network defaults and transport fallback.

## Exact next scientific gate

1. Source-identity and commercial-rights review for the specific OTI
   footprint vintage. A public URL alone does not automatically admit
   the source into the CAT engine.
2. Resolve the eight unmatched BASE_BBL/billing-BBL cases using the
   documented **MAPPLUTO_BBL** crosswalk from an official source that
   actually exposes this attribute. Do not invent such values from the
   public 5zhs-2jue view.
3. Conduct a bounded rights-cleared polygon and DOITT-ID shape inspection
   to evaluate splits, overlapping outlines, dummy features, construction
   periods, area accuracy and condo multiplicity. Reproject into an
   area-preserving CRS before calculating areas; provider auto-generated
   Web Mercator `shape_area` is expressly not an equal-area metric.
4. Only after independent calibration, estimate occupancy, construction cost,
   contents and BI uncertainty by **explicit models**. Then separately
   validate any hypothesis connecting physical risks to an insurer;
   no claims of actual policies, TIV, AEP/OEP, or insured CAT losses
   follow from these 30 footprint matches.
