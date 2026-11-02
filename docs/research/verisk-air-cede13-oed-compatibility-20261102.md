<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Verisk AIR / CEDE 13.0 to Oasis OED — evidence, rights and compatibility gap (2026-11-02)

**Decision:** use vendor-published CEDE 13.0 **schema** for an exposure mapping research baseline, and reuse the existing Oasis ODTF mapping *design* rather than inventing a vendor loss/event parser. **Do not declare CEDE 13.0 -> OED certified, download/commit CEDE sample bytes, or treat proprietary AIR models/event sets as open.** These remain independent decisions.

## Authoritative evidence and exact identity

| Subject | Direct evidence | Finding / caveat |
| --- | --- | --- |
| CEDE 13.0 | [Verisk CEDE 13.0](https://risksolutions.verisk.com/data-standards/cede-database-2025/) and [database schema](https://docs.risksolutions.verisk.com/Database/CEDE/13.0/topic13.html) | Schema is public. Vendor offers SQL Server 2022 (16.0.1115.1) sample backups for AIRExposure, AIRReference and AIRReinsurance. Actual bytes not inspected; backups alone are *not* catastrophe event catalogues, vulnerability functions or insurer portfolios. |
| CEDE License v1.0 | [Verisk PDF, 2 Oct 2020](https://risksolutions.verisk.com/4afe7a/siteassets/airimages/data_standards/cede_openlicense_basedonapache_2oct2020.pdf), sections 1-4 and 6 | License explicitly grants broad use/reproduction/derivative/redistribution rights **to a Work identified as licensed under it**, subject to preserving license, notices and modification notices; it does not grant trademarks. The specific SQL backup payload's included notices/third-party content have **not** been inspected: no blanket raw-byte publication approval. |
| Legacy reusable mapping | [Oasis ODS Tools OED-CEDE examples](https://github.com/OasisLMF/ODS_Tools/tree/main/ods_tools/odtf/examples/oed-cede) | The **location** YAML at `ods_tools/odtf/examples/oed-cede/mapping/mapping_loc_Cede-OED.yaml` (GitHub blob `b5433d6bc7f5ecd926fba4899dc12245d9b1e64a`) and **account** YAML `mapping_acc_Cede-OED.yaml` (blob `81a0f2e0aab4d140e8dd403f16ebd12d42d804c8`) explicitly state **CEDE v10.0.0 -> OED v3.0.2** in their headers. Source mapping is BSD-3-Clause-identified; this repo does not copy the mapping. |
| Oasis runtime | [ODS Tools README](https://github.com/OasisLMF/ODS_Tools) | `pip install 'ods-tools[transform]'`; mapping-driven `ods_tools transform --config-file ...` with CSV or database examples. A CLI capability is **not** a CEDE 13.0-validated run. |
| New CEDE 13 fields | [CEDE 13.0 schema changes](https://docs.risksolutions.verisk.com/Database/CEDE/13.0/topic3.html) | Added `tLocation.AverageHazardLevel` and `AverageHazardUserID`, new renewable-energy construction/occupancy codes and perils/reference changes. These must not silently disappear or get outdated taxonomy defaults. |

### Candidate transformation crosswalk — descriptive only

The exact *legacy* Oasis mapping contains:

| Legacy CEDE extract field | Legacy OED output | Important condition |
| --- | --- | --- |
| `LocationID` | `LocNumber` | Unique identity must remain stable within the portfolio and across joins. The raw `LocationSID` is a database-internal key, not a replacement for it. |
| `ContractID` | `AccNumber` | Do not invent insurer/treaty contract identifiers. |
| `BuildingValue` | `BuildingTIV` | This is a mapping of the *example extract*, **not** an automatically validated one-to-one mapping from `tLocation.ReplacementValueA`; reconcile coverage and valuation basis explicitly. |
| `ContentsValue` | `ContentsTIV` | Check valuation basis, null handling and original coverage component. |
| `CountryISO` | `CountryCode` | ISO country code version / valid values must be checked. |
| `Currency` | `LocCurrency` | No silent FX conversion; require explicit source currency, date and rates if normalising. |
| `LayerID` | `PolNumber` and `LayerNumber` in account example | Preserve policy versus layer identity and hierarchy. Do not assume model results or reinsurance terms are equivalent. |

**Potential problem:** the legacy location YAML has long regional administrative and construction/occupancy code replacement rules. A passing transform may still be semantically lossy in unseen countries. Compare unmapped/unrecognized codes per country and peril; never map unknown codes to a plausible default. ODTF location and account extracts use distinct source fields; their SQL extract queries and joins need separate review.

### Concrete acceptance gate for CEDE 13.0 -> target OED profile

1. Pin exact CEDE `13.0`, OED *target release*, ODS Tools dependency version/commit, and both source mapping blob IDs. Mismatch blocks automated compatibility claim.
2. Obtain **asset-level** rights evidence. Check CEDE .bak package, accompanying LICENSE/NOTICE and third-party content; hash each exact artifact (outside Git) only if permitted to retrieve. Never import actual customer/insurer exposures or vendor model data as test fixtures.
3. Test restore under SQL Server 2022 compatible runtime; inventory rows/tables/reference codes and sample provenance. Missing runtime or download = operational blocker, not a successful probe.
4. For explicitly **synthetic** location/account/layer fixtures, verify keys and cardinality (exposure set -> contract -> layer -> location), latitude/longitude versus user/premium geocodes, coverages A-D versus OED TIV fields, currency, country, perils, occupancy/construction, deductibles and limits. Require failure for unknown or ambiguous codes.
5. Compare CEDE v10 versus 13 at table, field, lookup and model-taxonomy levels. Specifically treat `AverageHazardLevel`, `AverageHazardUserID`, energy occupancy/construction and peril crosswalk changes as explicit *mapped / omitted with rationale / blocked* decisions.
6. Reconcile OED source locations/accounts/RI as separate outputs. Validate with the pinned OED profile and `ods_tools check` on only synthetic fixtures; compare row counts, stable IDs, missing rates, TIV totals by currency and peril, and all deliberate losses. No live Neon production write until admitted rights and data scope.
7. Preserve provenance: source version/license, original column name, mapping code/blob SHA, semantic defaults, transformation timestamp/config, output digest and role. A field-level mapping is not physical hazard, vulnerability, insured loss or licensed AIR model result.

## Next executable slice

A bounded, offline-reproducible migration test should first use ODS Tools' original **CEDE 10.0.0/OED 3.0.2** fixture/mapping, pin its commit and run it on wholly synthetic CSV rows, then add explicit CEDE 13.0 edge-case fixtures and compare before revising the mapping. Publishing new vendor example bytes or claiming OED 4.x support would be premature.

**Status:** evidence reviewed and source registry extended in PR #1124. License describes rights for licensed Works; exact CEDE sample backup rights/bytes, SQL restore, mapping execution, and target-version scientific fidelity are **not yet verified**. All AIR sources and Oasis tools remain landscape candidates (non-admission). No external data bytes, protected assets or secrets are included.

## Executable synthetic preflight added (2026-11-02)

A dependency-free, **synthetic-only and legacy-version-only** gate now exists at:
- `scripts/cede_oed_synthetic_preflight_v0.py`
- `tests/test_cede_oed_synthetic_preflight_v0.py`

Usage on wholly invented JSON (private test data are not to be supplied):

```bash
python -m unittest tests/test_cede_oed_synthetic_preflight_v0.py -v
python scripts/cede_oed_synthetic_preflight_v0.py --synthetic-input /path/to/invented_legacy_extract.json
```

The input document requires `source_format=CEDE`, `source_version=10.0.0`, `target_format=OED`, `target_version=3.0.2`, `synthetic_only=true`, and a bounded array of rows containing only the specified nine legacy extract columns (`ExposureSetName`, `ContractID`, `LocationID`, `CountryISO`, `Currency`, `BuildingValue`, `ContentsValue`, `Latitude`, `Longitude`). Strings are required for exact decimal monetary and coordinate inputs. The report contains only aggregate synthetic totals, link/cardinality counts, field-name examples, mapping blob identities and explicit `false` flags for execution, CEDE 13 compatibility, rights and model-input admission.

This is intentionally a **preflight, not ODTF execution, OED validation, CEDE 13.0 conversion, full financial coverage mapping, or production acceptance**. Any additional CEDE 13 column (including `AverageHazardLevel`) blocks rather than being silently dropped. It also rejects wrong format versions, real/unverified input flags, duplicate composite location identities, invalid amounts and coordinate ranges, partial coordinates, unknown columns, duplicate JSON keys and nonfinite values.

**Evidence:** on local Python 3.13, `13/13` focused synthetic tests passed; hosted exact-head CI must separately confirm repository-wide rules. The local runtime lacks `ods-tools` and cannot resolve github.com, so no ODS transform execution or SQL Server restore occurred.

**Next true interoperability milestone:** acquire an authorized dependency and bounded fixture, execute the pinned Oasis ODTF CEDE 10 to OED 3 mapping with OED validation, compare the resulting values and missing fields against this preflight, then explicitly version the CEDE 13 delta. Do not mark CEDE 13 as supported from these tests.

## Independent synthetic candidate-output reconciliation (2026-11-02)

A second executable, standard-library-only check is now included:
- `scripts/cede_oed_output_reconcile_v0.py`
- `tests/test_cede_oed_output_reconcile_v0.py`

For **wholly invented** synthetic source rows and *candidate* CSV output files:

```bash
python scripts/cede_oed_output_reconcile_v0.py \
  --synthetic-input /path/to/invented_legacy_extract.json \
  --oed-location /path/to/invented_loc_oed.csv \
  --oed-account /path/to/invented_acc_oed.csv
```

The checker builds exact composite identities from `ExposureSetName/ContractID/LocationID`, checks required `PortNumber/AccNumber/LocNumber` and stable account membership, reconciles `CountryCode`, `LocCurrency`, `BuildingTIV` and `ContentsTIV` against the legacy extractor input, and optionally exact-checks provided latitude/longitude. It rejects omitted/duplicate/mismatched locations and accounts, changed values/currencies, nonfinite or overprecise losses, malformed CSVs, duplicate headers and unauthorized version drift. Totals are only compared within currency, never converted or silently summed.

**Important limitations:** The outputs can be hand-constructed for tests; the tool does not *invoke* ODS Tools, does not validate the full OED schema, has no `LayerID`/policy hierarchy in this narrow source profile, and has no CEDE 13 semantics. The original Oasis account mapping requires additional fields such as `LayerID`. Its report deliberately includes `executed_ods_tools=false`, `oed_schema_validated=false`, `cede_13_compatible=false`, `model_input_admitted=false`, and `rights_approved=false`. Any actual end-to-end declaration still requires running the pinned Oasis mapper with a complete synthetic location **and account/layer** input.

**Focused evidence:** 10 additional local synthetic tests passed, alongside the earlier 13 preflight tests (23/23 in the isolated local Python 3.13 fixture). The exact new commit still requires hosted GitHub CI. Local package acquisition is blocked by pip package-index DNS resolution; no genuine ODS Tools invocation was performed.
