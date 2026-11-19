<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC 2024 building inventory: original archive evidence and fail-closed vintage gate

**Researched:** 2026-11-05. **Scope:** NYC original-provider public research,
source-specific historical-inventory readiness, **not_admitted**. No
confidential building/policy records, no original source data bytes or BIN
identifiers committed to this repository.

## Technical history so far

The merged [PR #1354](https://github.com/pokekarten/OpenCatastrophe-data/pull/1354),
[PR #1357](https://github.com/pokekarten/OpenCatastrophe-data/pull/1357) and
[PR #1365](https://github.com/pokekarten/OpenCatastrophe-data/pull/1365) have
already linked 30 nonrepresentative year-2024 LL84 property submissions
to 30 PLUTO tax/billing-lot keys, 30 distinct current OTI BIN/DOITT
features, and inspected 30 real original current MultiPolygon footprints.
The 2026 OTI source is not a historical 2024 building inventory.

## Critical new original 2024 source provenance

There are two distinct official original provider products:

1. [NYC OTI BUILDING 5zhs-2jue](https://data.cityofnewyork.us/d/5zhs-2jue):
   current, frequently refreshed **stock** features. NYC's archived
   [Building Footprints map 3g6p-4u5s](https://data.cityofnewyork.us/d/3g6p-4u5s)
   says **previously published versions are retained under Local Law 106
   of 2015 and may be provided on request to Open Data**. This view's
   published metadata points to source `5zhs-2jue`; it is a map, not a
   separate complete archived 2024 inventory.
2. [NYC OTI BUILDING_HISTORIC ipkp-snf6](https://data.cityofnewyork.us/d/ipkp-snf6):
   continuously maintained **historic-feature archive** for demolished
   or substantially altered building polygons, **not the 2024 stock**.
   [The original OTI data dictionary](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingHistoric.md)
   explicitly says that `last_edited_date` is the date a historical
   record was added to the archive, **not** the building demolition date.
   It also says historic `doitt_id` may be **0** on older archived features,
   BINs can be nonunique and borough-specific million BINs are placeholders.
   `demolition_year` may be absent and **alteration_year is not
   published** in this source. These semantics preclude guessing a
   unique 2024 risk from archive membership or nonmembership.

NYC's [official help guide](https://www.nyc.gov/opendata/get-started/user-guides/open-data-101)
explains that where the provider enables the changelog, previous full
versions may be downloadable from the dataset's Archive UI. It warns
that downloading individual parts of an archive is not supported. The
[official Open Data contact form](https://www.nyc.gov/opendata/contact-us)
also handles questions about existing datasets and archive requests.
**No dated 2024 original full-stock snapshot file, actual bytes or
verified SHA-256 has yet been acquired.** An archived current dataset's
record from 2025/2026 is not an as-of 2024 snapshot.

## Independent original aggregate readings on 2026-11-05

The following counts were obtained via bounded public Socrata `count(*)`
queries against the *current* official BUILDING_HISTORIC view
`ipkp-snf6`; the total was separately confirmed as 50,995 via the
same service. They can change after a refresh.

| Original-current archive property | Source rows |
| --- | ---: |
| Total historic-feature rows | **50,995** |
| `doitt_id = 0` (cannot treat as unique feature key) | **9,490** |
| Dummy BIN in (1000000, 2000000, 3000000, 4000000, 5000000) | **5,319** |
| Reported `demolition_year = 2024` | **1,127** |
| Reported `demolition_year = 2025` | **1,082** |
| `demolition_year` present (irrespective of value) | **47,677** |
| `last_edited_date` on/after 2025-01-01 | **3,820** |

The categories **overlap**; never sum them to infer the total number
of historic features. Published demolition years do not include
unpublished significant-alteration years, and do not establish exact
timing of individual loss events. `last_edited_date` is an *archive
ingestion/revision timestamp*, not necessarily physical demolition.

### Same 30-BIN convenience cohort: negative archive screen only

Using the exact 30 LL84 2024 candidate BINs from the previous pilots,
six independent five-BIN count-only original archive queries returned
**zero matched historic-feature rows** in the current `ipkp-snf6` view.
One initially failed request was retried successfully. This is
**not evidence of 2024 building presence**: historic archive absence is
not a complete inventory, and BINs/DOITT can change or be nonunique.
Do **not** label the 30 sites as 'survivors' from this absence.

## Reproducible bounded live canary

New stdlib-only `research_runners/nyc_oti_historic_vintage_gate_v0.py`:

    python research_runners/nyc_oti_historic_vintage_gate_v0.py --live

- Opt-in `--live`, fixed original NYC HTTPS host and two original view
  IDs only. Seven `count(*)` metric requests + 30 LL84 public BIN
  references (fixed 2024/Bbl-prefix cohort) + six five-BIN `count(*)`
  queries. No raw historic archive features, geometries, property values,
  owner names, addresses, TIV or claims are requested.
- Strict response-size and numeric-count checks, guarded public
  identifiers, no million BIN placeholders, no duplicate LL84
  properties or BINs, no inconsistent aggregate arithmetic. A **transport
  failure** in a batch is retried as independent count requests for
  each BIN. Failure of any of those individual requests aborts the whole
  result; **timeout never becomes a zero archive record**.
- Only source-wide and cohort-level **counts** are output. The result
  always marks `historical_inventory_2024_snapshot_bytes_acquired`,
  `historical_inventory_2024_verified`,
  `historical_2024_building_presence_inferred`, source admission,
  insured TIV and loss calculation **false**.
- `tests/test_nyc_oti_historic_vintage_gate_v0.py` uses only synthetic
  mocked source responses, including malformed rows, direct row
  leakage, duplicate keys, count overlap errors, source transport
  failure/retry and a zero historic-match sample.

## Next decisive input: request a full **2024 stock snapshot**

A genuine as-of 2024 exposure reconstruction requires a source-provided
**complete original BUILDING stock version**, ideally an archived
release **as close as possible to 2024-12-31**, with the file's actual
release/export date, source view ID, CRS and unchanged original
attributes (`DOITT_ID`, `BIN`, `BASE_BBL`, `MAPPLUTO_BBL`,
`FEATURE_CODE`, `CONSTRUCTION_YEAR`, `LAST_EDITED_DATE`,
and polygon geometry). The exact available archive date **must be
confirmed** rather than assuming a December 2024 release exists.

The original NYC Open Data
[Contact Us / dataset-question form](https://www.nyc.gov/opendata/contact-us)
can be used to ask the city to make such a snapshot available. This
request has **not been sent**. Suggested substance to include:

> We are evaluating historical NYC building footprints for a
> reproducible, non-personal geospatial research workflow.
> Could you provide the full archived NYC BUILDING footprint dataset
> (`5zhs-2jue`, or its predecessor) closest to 31 December 2024,
> ideally with publication/export timestamp, exact dataset/view identity,
> coordinate system, preserved original field dictionary, and any reuse,
> attribution or archival access terms? We distinguish the complete
> BUILDING inventory from BUILDING_HISTORIC demolished/altered features.
> Please indicate whether this version can be downloaded from a
> public NYC Open Data changelog archive or supplied separately.

Before any modeling integration: verify original archive **file bytes,
SHA-256, file-level rights, timestamp, complete feature count, geometry
units and independent crosswalk quality**. Check that historical
2024 BIN-to-DOITT and physical-vs-billing BBL relationships are
consistent; separately adjudicate demolitions, alterations and
splits. Do not join an incomplete 2026 footprint sample to a 2024
portfolio and call it a measured insurer exposure.

**Status:** The exact historical snapshot is still absent. The
current archive has been measured with explicit original-source
query receipts and a fail-closed executable, but cannot substitute
for a released, hash-pinned year-2024 stock inventory.
