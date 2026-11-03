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
