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

## Follow-up: source-specific multi-state diagnostic (2026-11-06)

The initial first 50 sorted 2025 records come from only one state; to avoid treating that convenience sample as a spatial validation, the research workflow now independently probes **25 rows each** for explicit 2025 original NBI state codes **6** and **36**, using separate `$where`-bounded fixed-field source requests. The Python adapter now independently rejects any original row that does not match the explicitly chosen year or state, even if the API returns HTTP 200. One new offline test challenges wrong-year, wrong-state, boolean and impossible selectors; the original 50-row gate remains unchanged. No sample is random or statistically representative, and these are source field/format diagnostics, not a US spatial/CAT model.

At the time this change is authored, the exact provider original 25+25 live run and latest-head full CI have **not** yet been observed; a green older-head check does not prove this follow-up. Validate against the new GitHub Actions source run and record source SHA receipts before interpreting its results. Exact row-level identifiers and geocodes continue to stay in the ephemeral runner only.

## Exact live original multi-state source result (2026-11-06)

The new [public source workflow run #42257973013](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42257973013) completed **SUCCESS at commit `41c169fa9c203fe2d456899a64e9d8f8fcdfc26d`**. The single bounded source job executed all offline tests and read the independently requested real public API responses. This result is source-transport / format evidence only, not randomized sampling:

| Explicit request | Source bytes | Original response SHA-256 | Audit result |
|---|---:|---|---|
| 50 sorted rows (2025, first source state) | 6,959 | `eb3391f675610bd10b97468f19ceee26f760ffbd3e5bf4f61eaac5a1419f1904` | 50 distinct bridge-year IDs, 50 DMS-format plausible, 50 year-built plausible |
| 25 records with `year=2025 AND state_code_001=6` | 3,676 | `f20c98b58f3b34cb14d6370ce61d418ace0c90e734b392e763422b3f3b8a687f` | 25 distinct bridge-year IDs, 25 DMS-format plausible, 25 year-built plausible; all selector checks pass |
| 25 records with `year=2025 AND state_code_001=36` | 3,676 | `895903b99f08b3c6c5878433cc53d01febd3af22a4245c0d5f588c31d87e9e73` | 25 distinct bridge-year IDs, 25 DMS-format plausible, 25 year-built plausible; all selector checks pass |

Exactly **100 source-row observations across three nonrandom, potentially overlapping selection groups** were inspected; their aggregate numbers cannot be extrapolated into national counts, independent source-site geolocation, insured exposure or financial model admission. Original row responses and building identifiers remain only in ephemeral runner storage. Source hashes bind exact responses on that run but are **not independent signatures**. Latest-head repository CI must still be independently inspected after this documentation commit.

## Exact historical angular encoding proof, no WGS84/GeoJSON admission

Official FHWA [Legacy NBI record format](https://www.fhwa.dot.gov/bridge/nbi/format.cfm) explicitly allocates item 16 latitude **8 digits** and item 17 longitude **9 digits**. FHWA's historical Coding Guide `https://www.fhwa.dot.gov/bridge/mtguide.pdf` illustrates `35271855` for 35°27'18.55" and `081055065` for 81°05'50.65". The published official [ASCII archive](https://www.fhwa.dot.gov/bridge/nbi/ascii.cfm) confirms **2025 was the last Coding Guide ASCII submission year**. The [SNBI transition portal](https://www.fhwa.dot.gov/bridge/nbi/nbi_data.cfm), last updated 2026-10-21, separately describes 2026–2027 crosswalk/temporary-code limitations; do not treat old item 16/17 encoding as the SNBI decimal-coordinate schema.

The new pure `_coded_hundredths()` decoder uses integer hundredths of an arcsecond, equivalent to **360,000 units per degree**, preserving source precision exactly before optional decimal magnitude display. It does **not** assume latitude hemisphere, west/east longitude sign, NAD83 versus WGS84, bridge point position or an actual validated geographical coordinate. FHWA legacy source may encode all-zero latitude/longitude when location is unavailable (depending on facility classification); a zero code is explicitly flagged as an **unknown-position sentinel**, never interpreted as a geographic (0,0) point. The original-source aggregate receipt counts such pairs only, without storing or emitting individual site coordinates.

Two new offline unit tests exercise exact official numerical examples, lost leading-zero formatting, 0/unknown sentinels and invalid degree/minute/second codes. These strengthen historic text interpretation but still **do not independently establish individual bridge positions, state boundary membership or scientific CAT admission**. Keep separate modern SNBI crosswalk and spatial-validation research gates.
