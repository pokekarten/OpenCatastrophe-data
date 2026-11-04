<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC tax-lot versus energy-property linkage: executable research gate v0

**Reviewed 2026-11-04. Research only, no original source data, insured assets or confidential records.**

## Original authority and measured units

The [NYC DCP PLUTO 26v2 README](https://s-media.nyc.gov/agencies/dcp/assets/files/pdf/data-tools/bytes/pluto_readme.pdf)
defines one record per **tax lot** (except grouped condominium billing lots), not one
record per building, owner, policy or insured address. Its
[official data dictionary](https://s-media.nyc.gov/agencies/dcp/assets/files/pdf/data-tools/bytes/pluto_datadictionary.pdf)
defines the BBL tax-lot identifier; NumBldgs is a count of buildings on the lot
derived from building identifiers and official geosupport data; NumFloors is
the tallest building's floor count. YearBuilt can be decade-level/rounded or
unknown (0/null). AssessTot is a statutory *tax assessed value*, **not** a
market value, insured sum, reconstruction cost or insurer loss basis.

The [NYC DOB official LL84 guidance](https://www.nyc.gov/site/buildings/codes/ll84-benchmarking-law.page)
describes a 10-digit BBL and 7-digit building identification number (BIN);
a property can list **multiple** BBLs and BINs separated by semicolons.
The [NYC Open Data LL84 view 5zyy-y8am](https://data.cityofnewyork.us/d/5zyy-y8am)
contains yearly reported energy/water information for 2022 onward.
The official [campus benchmarking guidance](https://www.nyc.gov/assets/buildings/pdf/benchmarking_campus.pdf)
warns that campus energy may be allocated to only one child property despite
several buildings. Parent and child property submissions can overlap in
financial/physical scope. Data cover reportable buildings, not all NYC stock.

## Original NYC Socrata column-metadata probe (2026-11-04)

Read-only original provider metadata returned from:

- https://data.cityofnewyork.us/api/views/64uk-42ks/columns.json (PLUTO)
- https://data.cityofnewyork.us/api/views/5zyy-y8am/columns.json (LL84)

Verified PLUTO fieldName keys include **borough**, **block**, **lot**,
**bbl**, **numbldgs**, **bldgarea**, **yearbuilt** and **assesstot**.
Verified LL84 fieldName keys include **report_year**, **property_id**,
**parent_property_id**, **nyc_borough_block_and_lot**,
**nyc_building_identification** and **number_of_buildings**.
These are observed API metadata fields, *not* proof of field value quality,
one-to-one identity, API stability, source reuse rights or actual successful
data-row acquisition.

The LL84 API's cached column statistics currently describe 103,259
records across report years 2022-2024 (30,485 / 33,684 / 39,090).
Those are **provider-reported cached metadata counts**, not independently
downloaded/validated rows; the metadata can change. The BBL column's
cached top/missing-value examples include **Not Available**, artificial
formatted masks and semicolon-delimited multi-BBL strings; BIN examples
include **Not Available**, **0**, and multiple BIN strings. The research
diagnostic intentionally rejects such unnormalized strings; any future
authorized source-specific adapter must first classify missing values,
placeholder codes, multi-valued IDs and future reporting years with
a version-pinned original data dictionary. Do **not** convert invalid
identifiers to a guessed BBL/BIN or count them as matched physical assets.

## Exact read-only public API count probes (2026-11-04)

The independent public source endpoints responded successfully to bounded
Socrata SoQL aggregate-only queries, without authentication or row downloads:

- PLUTO: https://data.cityofnewyork.us/resource/64uk-42ks.json?%24select=count%28%2A%29
  returned a JSON count of **858,284** records.
- LL84 report year 2024:
  https://data.cityofnewyork.us/resource/5zyy-y8am.json?%24select=count%28%2A%29&%24where=report_year%3D2024
  returned a JSON count of **39,090** records.

These response counts validate only *public API reachability, query grammar
and query-time row counts*. A PLUTO tax lot and an LL84 annual reported property
are not a common statistical denominator: **39,090 / 858,284 is NOT a citywide
building coverage or match rate**. No original row payload, download,
individual building match, source-level rights approval, full-schema parse,
geometric join or value validation was performed. Responses may change with
provider updates; pin UTC receipt and exact query in any future measured run.

## Measured identifier complexities in LL84 2024 (read-only 2026-11-04)

Additional aggregate-only original Socrata queries against
https://data.cityofnewyork.us/resource/5zyy-y8am.json used
SoQL select=count(*) with each **report_year = 2024** filter:

| Additional where condition | Count |
| --- | ---: |
| nyc_borough_block_and_lot like '%;%' | 866 |
| nyc_building_identification like '%;%' | 3,305 |
| nyc_borough_block_and_lot = 'Not Available' | 219 |
| nyc_building_identification = 'Not Available' | 346 |
| Union: any of the four OR conditions above | **3,812** |

The union was computed **on the original API**, not by adding overlapping
individual categories. These are rows with at least one *observable*
identifier-complexity condition; not all problematic IDs are detected (e.g.,
zero/placeholder BINs, inconsistent condo billing keys and nonstandard masks).
Multiple BINs are not necessarily malformed data; many describe legitimate
campus buildings and must not be naively auto-split or joined as one asset.

Reproducible union SoQL request (one anonymous aggregate count, zero row data):

    $select=count(*)
    $where=report_year = 2024 AND (
      nyc_borough_block_and_lot like '%;%' OR
      nyc_building_identification like '%;%' OR
      nyc_borough_block_and_lot = 'Not Available' OR
      nyc_building_identification = 'Not Available'
    )

This result is a **hard lower-bound count of these four identified special
cases in the current 2024 source query**, not a validated percentage of
unmatchable records or complete data quality assessment. It confirms
that a one-row-per-building SQL join would silently misstate a material
subset of the source. Real raw acquisition, rights approval and provider
asset admission remain pending.

## Implemented bounded, offline diagnostic

The executable research-only preflight is:

    python research_runners/nyc_pluto_ll84_linkage_v0.py --input /tmp/synthetic-nyc.json

It accepts only a strictly pre-normalized, locally authorized JSON.
Example input below is **invented**, not external NYC provider data:

    {
      "pluto_release": "26v2",
      "pluto_rows": [
        {"bbl": "1008450027", "num_buildings": 1}
      ],
      "ll84_rows": [
        {"property_id": "12345", "calendar_year": 2024,
         "bbls": "1008450027", "bins": "1001234"}
      ]
    }

A tentative candidate requires one BBL, one BIN, a PLUTO tax lot with exactly
one building, and no competing property using that BBL in the same year.
Missing/invalid IDs, duplicate property-year records, multi-lot/multi-BIN
campus properties, shared lots, PLUTO multi-building lots and partial extracts
have separate explicit negative decisions. Property IDs can repeat across
years without creating a same-year collision.

The preflight reports **aggregate counts only**, never original property
identifiers, full join tables, addresses, financial values, source bytes or
inferred insurer associations. Source data remain outside Git and no Neon
write or NextGen/Oasis exposure feed occurs. A candidate is not proof of a
building match; source vintages, condominium billing versus base BBL and
original GIS geometry may still disagree.

Limits: 2 MB input, 10,000 rows per side; no network requests. The strict
26v2 release identity is a research contract, not a claim that that release
is complete/current or usable under commercial source rights.

## Executable original-source canary (added 2026-11-04)

The research source-access probe is now implemented as
research_runners/nyc_socrata_count_canary_v0.py. It supports only:

    python research_runners/nyc_socrata_count_canary_v0.py --live

Network access requires the explicit live flag. Without it, the runner refuses
to execute. Exactly **seven** GET requests are hard-coded to the original
HTTPS NYC Socrata service (resource views 64uk-42ks and 5zyy-y8am):
the PLUTO row total, the LL84 2024 row total, four named identifier-complexity
classes, and their logical OR union. Every request uses SoQL select=count(*);
there is no configurable host, field expression, geographic key, token, input
dataset or user query. Redirects and non-JSON responses are rejected and each
aggregate result is capped at 4,096 bytes.

The runner enforces that category counts cannot exceed the union, the union
cannot exceed the LL84 total, and union cannot exceed the sum of categories.
This **does not** establish that those categories cover every malformed key.
The canary emits aggregate-only JSON with explicit false flags for building
identity, insurance value or model-input admission. Its tests
(tests/test_nyc_socrata_count_canary_v0.py) use mocked response bytes only;
they can run offline under the repository unittest suite. The runner is
neither a model input, source approval nor a raw-data connector.

Important scientific limitations:
- PLUTO and LL84 row counts have incomparable grains. Do not divide their
  respective totals to claim building coverage.
- LL84 contains year-specific observations; a single property can recur in
  several years. Revisions and parent-child campuses require original review.
- Conditions overlap, so the four separate counts must not be added to
  derive a unique count; the canary queries their explicit OR union.
- The seven live counts can change if NYC refreshes tables. Store the query
  identity, source metadata release date, retrieval timestamp and scientific
  context in a separate independently reviewed receipt before comparative use.
- Authentication-free public API access is not a blanket data-reuse grant;
  raw/derived asset acquisition, crosswalk rights and all admissions remain
  unapproved.

## Next scientific and rights gate

1. Check live original NYC Socrata field metadata and pin the exact LL84
   reporting year, release date, query/revision and content hashes. Do not
   assume a convenient renamed field has unchanged meaning.
2. Require provider-specific processing of parent-child campus relationships
   and billing- versus base-BBL crosswalks; do not auto-split an energy number
   across building polygons or tax lots.
3. Evaluate the selection bias of LL84 reporting and agreement with independent
   DOB BIN polygons on an adjudicated, rights-cleared *small* sample.
4. Freeze per-source reuse/commercial rights, scientific scope and original
   data identity separately before any source admission or model use.
5. If a later adapter needs allocation, make it an explicitly probabilistic
   exposure-estimation model with loss of precision and uncertainty, **never**
   an implicit one-to-one building/insurance/TIV assertion.

Test coverage: tests/test_nyc_pluto_ll84_linkage_v0.py uses synthetic records
only and checks the most dangerous false-positive paths.
