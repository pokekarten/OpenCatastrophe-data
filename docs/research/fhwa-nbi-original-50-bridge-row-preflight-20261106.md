<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FHWA NBI original bridge-year row sample: bounded source-only preflight

**Research only, 2026-11-06.** Extends the original public metadata proof in
`fhwa-nbi-socrata-original-metadata-gate-20261106.md` without promoting bridges
to insurer exposure or inventing coordinates, insured ownership, CAT vulnerability,
flood depths or earthquake fragility.

Source: https://data.transportation.gov/Roadways-and-Bridges/National-Bridge-Inventory/pced-83j4 .
The publisher lists temporal applicability **2024/2025**, 124 API columns and CC0/public domain,
but the dataset update 2026-11-02 is not a 2026 bridge survey. Legacy FHWA
NBI field 16/17 coordinates use coded degrees/minutes/seconds format; numeric
Socrata field types do **not** prove they are decimal WGS84 coordinates. FHWA original
format: https://www.fhwa.dot.gov/bridge/nbi/format.cfm .
Current SNBI transition/crosswalk is distinct:
https://www.fhwa.dot.gov/bridge/nbi/nbi_data.cfm .

## Implemented fail-closed row-sample contract

`research_runners/fhwa_nbi_socrata_original_rows_v0.py` parses only an exact
50-record response to six selected public source fields:
`year,state_code_001,structure_number_008,lat_016,long_017,year_built_027`.
Strictly limits original bytes, checks full source SHA-256 receipt, rejects duplicate
JSON keys and duplicate (year/state/structure) identities, validates basic year/state
ranges without coercing textual bridge identity into a number, classifies legacy
DDMMSSss / DDDMMSSss *format plausibility* rather than geocoding any row, and
distinguishes missing/unknown construction years. It prints only aggregate counts
and SHA-bound metadata, **no identifiers, locations or third-party original rows**.

The dedicated GitHub workflow downloads at most 50 records using a deterministic
selected-field and sort query. Source identity, transport and method are supported
by the official site and explicit exact request. A checksum of that response is
**not an external independent provider signature**. This is a deliberately
nonrepresentative ordering sample; it does not estimate US bridge distributions
or imply local insurer bridge coverage.

```bash
python -m unittest tests.test_fhwa_nbi_socrata_original_rows_v0 -v
# Read an externally acquired, exact 50-row selected-field response:
python -m research_runners.fhwa_nbi_socrata_original_rows_v0 \
  --original-sample /tmp/nbi-original-selected-50.json
```

## Missing admission gates

- Source-query snapshot vintage, across-year row coverage and official 2026 SNBI
  transition/crosswalk; actual bridge identity dedup over **full original data**.
- Coordinate datum, original degrees/minutes/seconds encoding, hemisphere/sign
  conventions, bridge-location accuracy and independent geospatial QA.
- Bridge deck/type attributes, hazard and damage fragility, condition/age
  scientific calibration, protected infrastructure and insurance ownership/TIV.
- Historical common event catalogues and reinsurance contracts; **no**
  Gross/Net, AAL, OEP, AEP or insured loss projections are admitted.

Original row response bytes are ephemeral; no sources copied into public Git,
no identifiable bridge rows in GitHub artifacts and no Neon mutations.
Keep Draft and `model_input_admitted=false`.

## Original FHWA API evidence, first bounded live sample (2026-11-06)

[Exact-head GitHub source run #42257223552](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42257223552) **SUCCESS**: original API response **6,959 bytes**, SHA-256 `eb3391f675610bd10b97468f19ceee26f760ffbd3e5bf4f61eaac5a1419f1904`. The runner executed **8/8 synthetic fail-closed tests** and then the actual 50-row original source request. All 50 selected records have distinct bridge-year/state/structure keys, historical NBI DMS-format-plausible latitude/longitude and plausible construction-year ranges. All 50 report **2025** and come from **one state code** because the deterministic sort reaches that state first. This is a successful **format and bounded access proof only**, not even a cross-state distribution benchmark, and not validation of accurate GIS bridge positions.

The source response is not publisher-signed, the original rows are not saved in Git or uploaded to workflow artifacts, and the sample is intentionally nonrepresentative. A future multi-state original-source check should scope each query by a verified state/year selector, ensure original row schema/uniqueness and record aggregate results separately; it must not infer market-share, national total, fragility, insurance ownership/TIV or CAT-loss estimates. Full repository CI must be checked at the **latest head**, independent of this passing source-only workflow.
