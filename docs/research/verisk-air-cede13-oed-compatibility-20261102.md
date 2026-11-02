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

## Multi-layer account integrity preflight (2026-11-02)

The previous output check counts unique accounts. This is **not sufficient** for a real account extract with multiple insurance layers under the same account; Oasis ODS Tools' published CEDE v10 -> OED v3.0.2 account mapping sends `LayerID` to both `PolNumber` and `LayerNumber`.

The bounded layer-aware synthetic reconciliation adds:
- `scripts/cede_oed_layer_identity_v0.py`
- `tests/test_cede_oed_layer_identity_v0.py`

Its inputs are a wholly invented legacy CEDE-v10/OED-v3.0.2 exposure JSON (the pre-existing nine-column profile), a **separate** invented layer JSON document with `ExposureSetName, ContractID, LayerID, Currency`, and candidate OED location/account CSVs. The layer document declares `synthetic_only=true`, `source_version=10.0.0`, `target_version=3.0.2`. Multiple layers may belong to one account. Every source account must have at least one layer and every layer must match exactly one source account and its currency.

Run:

```bash
python -m unittest tests/test_cede_oed_layer_identity_v0.py -v
python scripts/cede_oed_layer_identity_v0.py \
  --synthetic-exposure /path/to/invented_exposure.json \
  --synthetic-layers /path/to/invented_layers.json \
  --oed-location /path/to/candidate_location.csv \
  --oed-account /path/to/candidate_account.csv
```

The account CSV must contain at least `PortNumber,AccNumber,PolNumber,LayerNumber,AccCurrency`. The checker fails on missing, duplicated, additional or altered layer identities, unexpected accounts, mixed within-account source currencies and changed account currency. Location values are reconciled with the prior synthetic TIV checks, and the report exposes only counts, aggregates and explicit `false` execution/rights/OED-schema/CEDE-13/financial-terms flags.

**Focused evidence:** 12 new pure-stdlib synthetic tests passed in the local Python runtime, bringing the three CEDE/OED scripts to **35/35 focused tests**. Hosted CI must still pass on the latest head. **Not demonstrated:** actual ODS Tools execution, full OED validity, policy financial terms/coverage/peril mapping, CEDE 13.0 compatibility, license/admission or Neon integration. These remain separate gates.

## Real ODTF executable smoke workflow (2026-11-02)

New script `scripts/cede_oed_ods_tools_live_smoke_v0.py` and isolated PR workflow `.github/workflows/cede-oed-ods-tools-smoke.yml` attempt a **real** Oasis ODTF engine execution using `ods-tools[transform]==5.0.10` (PyPI release 2026-10-29), independently synthetic CEDE-v10-like location CSV rows (two invented DE locations, one fictional account) and two completely invented layer records. The CSVs, two bounded ODTF mapping YAML files, and input/output files exist in a disposable runner temporary directory only; no third-party vendor/source bytes or customer exposures are downloaded or committed.

The new mapping is **original minimal direct-field-only**, not a copy/execution of Oasis' comprehensive 80 KB example. It intentionally tests `ExposureSetName -> PortNumber`, `ContractID -> AccNumber`, `LocationID -> LocNumber`, `CountryISO -> CountryCode`, `Currency -> LocCurrency`, `BuildingValue -> BuildingTIV`, `ContentsValue -> ContentsTIV`, basic coordinates, and `LayerID -> PolNumber + LayerNumber`. If the actual CLI returns zero and both CSVs pass the synthetic location/layer reconciler, this is a narrow successful *engine smoke*, **not** CEDE 13, complete upstream mapping support, OED schema acceptance, peril/financial/treaty conversion, loss model execution, or data admission.

Local environment does not provide `ods_tools` or functioning pip index resolution; this task is run in **dedicated GitHub Actions**. Record its exact run ID, commit SHA, and conclusion after completion. Do not claim a successful actual transform based solely on workflow creation, launch or local YAML parsing.

Manual reproduction after approved installation:

```bash
python -m pip install 'ods-tools[transform]==5.0.10'
python scripts/cede_oed_ods_tools_live_smoke_v0.py
```

Review the new dependency separately from routine validation dependency pins; its network/package provenance and transitive dependencies are a separate execution lane. No source data assets, OED-schema validity or rights scope are changed.

## Official OED schema challenge — detected policy/layer type mismatch (2026-11-02)

The isolated GitHub ODTF smoke now **attempts** explicit OED **3.0.2** validation with `ods_tools.oed.OedExposure(oed_schema_info="3.0.2")` and all default validation rules in return mode. This is distinct from a successful transformation: validity is `true` only if the real OED validator returns **zero findings**. The ODS Tools CLI's `check` wrapper catches an `OdsException` and logs it, therefore its process exit status alone is **not** accepted as proof of validation.

**Observed failure:** original synthetic account output mapped `LayerID="L1"` to both `PolNumber` and `LayerNumber`, which the official API could not parse (GitHub smoke run #5: `ValueError: Unable to parse string 'L1' at position 0`). The public Oasis OED `OEDInputFields.csv` specifies `PolNumber` as `varchar(20)` and `LayerNumber` as **positive integer**, not a general string. These are different semantics: a stable policy identifier must not silently be repurposed into an integer layer ordinal. The *upstream legacy example* makes this same direct field copy; when source LayerID is nonnumeric, it cannot safely produce a valid OED LayerNumber without an explicit source-to-number crosswalk.

The research-only bounded synthetic direct-field fixture now uses `LayerID=1,2` for compatibility and adds explicit invented `LocPerils=WEC`, `OtherValue=0`, `TimeElementValue=0` and account `Perils=WEC` to populate OED `LocPerilsCovered`, `OtherTIV`, `BITIV` and `PolPerilsCovered`. These are **assumptions for synthetic testing only**, never inferred real insured perils or values. The layer checker independently rejects noncanonical, zero, negative or alphanumeric LayerID when used as the legacy OED LayerNumber; positive integer policy test IDs are bounded to nine decimal digits for safe parsing.

**Validation status:** Official OED 3.0.2 validation remains **unconfirmed** until the exact-head test reports `oed_schema_validated=true`. Merely reaching the schema parser, or passing the custom matching/TIV checks, does **not** confer full OED validity. Future real CEDE interfaces must separately preserve policy identity and explicit layer-number ordering; do not silently replace arbitrary insurer-provided identifiers with numeric surrogates.

## Full original Oasis example execution — exact reproducible defect inventory (2026-11-02)

A new isolated research job checks out **unchanged** public Oasis ODS Tools commit
[`17f1c25b095bb40111f83a6f0abc58c087652538`](https://github.com/OasisLMF/ODS_Tools/commit/17f1c25b095bb40111f83a6f0abc58c087652538),
checks the original location and account YAML **blob IDs**, and runs the pinned `ods-tools[transform]==5.0.10` executable against generated **independently synthetic** inputs. Neither vendor data nor copied upstream mapping files are committed into OpenCatastrophe. Source inputs contain one invented row per file, not customer records.

**Untouched full-reference YAML (GitHub Actions [#16](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41524553442)):**

| File | Actual synthetic input columns | Declared OED outputs | Result |
| --- | ---: | ---: | --- |
| Location | 156 | 188 | No CSV. ODTF error: unrecognised source type `ODTF Data Type`. |
| Account | 70 | 36 | No CSV. ODTF tries to use the **string content** `SYNTHETIC-ONLY` from `ExposureSetName` as a dataframe boolean filter / column reference; this is not a valid boolean `when` condition. |

**Safety warning:** the upstream ODTF transform CLI returned exit code **0 despite both batch errors and no output**. The research runner correctly requires a real nonempty CSV plus one expected row; it reports `full_mapping_executed_both=false`. A green workflow indicates the diagnostic probe completed; **it does not mean the untreated full mapping works**.

**Two strictly temporary diagnostic workarounds, not production patches:** remove the illustrative `Cede Field: type: ODTF Data Type` placeholder from a temporary location YAML copy, and change one `when: ExposureSetName` in each temporary YAML to a value-checked boolean condition. The original upstream mapping SHA remains pinned and untouched. With these two controlled changes, the same [#16 research run](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41524553442) produced **one location CSV with 188 columns** and **one account CSV with 36 columns** from wholly invented input. The account warning log was empty; the location stderr contained a Python assignment warning. Neither artifact was validated against the OED 3.0.2 schema in this first workaround run.

**Additional independently inspected upstream issue:** location source `types:` declares `MinDeduct` **twice**, making schema interpretation vulnerable to duplicate-key overwrite. Original location has 157 syntactic type lines but only 156 unique source fields. For real data, reject ambiguous YAML duplicate keys rather than selecting a silent winner.

**New targeted follow-up:** the workaround runner has been extended to attempt the **official OED 3.0.2 validation** on the resulting CSVs (including required and conditional fields). Until a specific exact-head workflow returns its actual outcome, no OED-validity or scientific parity conclusion for the full mapping is claimed. This test also cannot validate the 2025 CEDE 13.0 changes, vulnerability modules, licensed AIR event catalogs, policy/treaty economics, or rights to vendor sample SQL backups.

**Reproduction:** `python scripts/cede_oed_upstream_full_mapping_probe_v0.py --upstream-checkout <pinned-Oasis-checkout>` and `python scripts/cede_oed_upstream_mapping_workarounds_v0.py --upstream-checkout <pinned-Oasis-checkout>`, after `ods-tools[transform]==5.0.10` is installed. This is an exploratory research lane, not an admission or model-input gate.
